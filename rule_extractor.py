"""
Rule Extractor Module
Extracts human-readable IF-THEN trading rules from trained LightGBM models
"""

import lightgbm as lgb
import pandas as pd
import numpy as np
from typing import Dict, List, Tuple, Optional
from collections import defaultdict
import json


class Rule:
    """Represents a single trading rule"""
    
    def __init__(self, conditions: List[Dict], prediction: float, 
                 coverage: float, importance: float, tree_id: int):
        """
        Initialize a trading rule
        
        Args:
            conditions: List of condition dictionaries
            prediction: Expected output value
            coverage: Percentage of samples covered
            importance: Rule importance score
            tree_id: ID of source tree
        """
        self.conditions = conditions
        self.prediction = prediction
        self.coverage = coverage
        self.importance = importance
        self.tree_id = tree_id
    
    def to_text(self, target_name: str = "Profit", is_classification: bool = False) -> str:
        """
        Convert rule to human-readable text
        
        Args:
            target_name: Name of target variable
            is_classification: Whether this is a classification task
        
        Returns:
            Formatted rule text
        """
        if not self.conditions:
            return "No conditions (root prediction)"
        
        # Build IF clause
        if_clause = "IF "
        condition_texts = []
        
        for cond in self.conditions:
            feature = cond['feature']
            operator = cond['operator']
            threshold = cond['threshold']
            
            # Format threshold with appropriate precision
            if abs(threshold) < 0.01:
                threshold_str = f"{threshold:.6f}"
            elif abs(threshold) < 1:
                threshold_str = f"{threshold:.4f}"
            elif abs(threshold) < 100:
                threshold_str = f"{threshold:.2f}"
            else:
                threshold_str = f"{threshold:.1f}"
            
            condition_texts.append(f"{feature} {operator} {threshold_str}")
        
        if_clause += " AND ".join(condition_texts)
        
        # Build THEN clause
        if is_classification:
            signal = "BUY" if self.prediction > 0.5 else "SELL"
            confidence = self.prediction if self.prediction > 0.5 else (1 - self.prediction)
            then_clause = f"THEN {signal} (Confidence: {confidence:.2%})"
        else:
            then_clause = f"THEN Expected {target_name}: {self.prediction:+.4f}"
        
        # Add metadata
        metadata = f"    [Coverage: {self.coverage:.1%} | Importance: {self.importance:.2f}]"
        
        return f"{if_clause}\n{then_clause}\n{metadata}"
    
    def to_dict(self) -> Dict:
        """Convert rule to dictionary format"""
        return {
            'conditions': self.conditions,
            'prediction': float(self.prediction),
            'coverage': float(self.coverage),
            'importance': float(self.importance),
            'tree_id': int(self.tree_id)
        }


class RuleExtractor:
    """Extracts interpretable rules from LightGBM models"""
    
    def __init__(self, model: lgb.Booster, feature_names: List[str], 
                 X_train: pd.DataFrame, task_type: str = 'regression'):
        """
        Initialize rule extractor
        
        Args:
            model: Trained LightGBM model
            feature_names: List of feature names
            X_train: Training data (for coverage calculation)
            task_type: 'regression' or 'classification'
        """
        self.model = model
        self.feature_names = feature_names
        self.X_train = X_train
        self.task_type = task_type
        self.rules = []
        self.model_dump = None
    
    def extract_rules(self, max_rules: int = 20, min_samples: int = 10) -> List[Rule]:
        """
        Extract rules from the model
        
        Args:
            max_rules: Maximum number of rules to extract
            min_samples: Minimum samples required for a rule
        
        Returns:
            List of Rule objects
        """
        print("\n[EXTRACTING] Extracting rules from LightGBM model...")
        
        # Get model structure
        self.model_dump = self.model.dump_model()
        tree_info = self.model_dump['tree_info']
        
        print(f"  • Total trees: {len(tree_info)}")
        
        all_rules = []
        
        # Extract rules from each tree
        for tree_idx, tree in enumerate(tree_info):
            tree_structure = tree['tree_structure']
            tree_rules = self._extract_rules_from_tree(tree_structure, tree_idx)
            all_rules.extend(tree_rules)
        
        print(f"  • Total paths extracted: {len(all_rules)}")
        
        # Calculate importance and coverage for each rule
        self._calculate_rule_metrics(all_rules, min_samples)
        
        # Sort by importance
        all_rules.sort(key=lambda r: r.importance, reverse=True)
        
        # Keep top rules
        self.rules = all_rules[:max_rules]
        
        print(f"  • Top rules selected: {len(self.rules)}")
        print(f"[OK] Rule extraction completed!")
        
        return self.rules
    
    def _extract_rules_from_tree(self, node: Dict, tree_id: int, 
                                  conditions: Optional[List[Dict]] = None) -> List[Rule]:
        """
        Recursively extract rules from a tree
        
        Args:
            node: Current node in tree
            tree_id: Tree identifier
            conditions: Accumulated conditions
        
        Returns:
            List of rules from this tree
        """
        if conditions is None:
            conditions = []
        
        # Leaf node - create rule
        if 'leaf_value' in node:
            rule = Rule(
                conditions=conditions.copy(),
                prediction=node['leaf_value'],
                coverage=0.0,  # Will be calculated later
                importance=0.0,  # Will be calculated later
                tree_id=tree_id
            )
            return [rule]
        
        # Internal node - recurse on children
        rules = []
        
        if 'split_feature' in node:
            feature_idx = node['split_feature']
            feature_name = self.feature_names[feature_idx]
            threshold = node['threshold']
            
            # Left child (<= threshold)
            if 'left_child' in node:
                left_conditions = conditions.copy()
                left_conditions.append({
                    'feature': feature_name,
                    'operator': '<=',
                    'threshold': threshold
                })
                rules.extend(self._extract_rules_from_tree(
                    node['left_child'], tree_id, left_conditions
                ))
            
            # Right child (> threshold)
            if 'right_child' in node:
                right_conditions = conditions.copy()
                right_conditions.append({
                    'feature': feature_name,
                    'operator': '>',
                    'threshold': threshold
                })
                rules.extend(self._extract_rules_from_tree(
                    node['right_child'], tree_id, right_conditions
                ))
        
        return rules
    
    def _calculate_rule_metrics(self, rules: List[Rule], min_samples: int):
        """
        Calculate coverage and importance for each rule
        
        Args:
            rules: List of rules
            min_samples: Minimum samples for valid rule
        """
        total_samples = len(self.X_train)
        
        for rule in rules:
            # Calculate coverage (% of samples matching conditions)
            mask = np.ones(total_samples, dtype=bool)
            
            for cond in rule.conditions:
                feature = cond['feature']
                operator = cond['operator']
                threshold = cond['threshold']
                
                if feature in self.X_train.columns:
                    values = self.X_train[feature].values
                    
                    if operator == '<=':
                        mask &= (values <= threshold)
                    elif operator == '>':
                        mask &= (values > threshold)
            
            samples_covered = mask.sum()
            rule.coverage = samples_covered / total_samples
            
            # Calculate importance based on:
            # 1. Absolute prediction value (stronger signals are more important)
            # 2. Coverage (rules covering more samples are more important)
            # 3. Number of conditions (simpler rules are slightly preferred)
            
            prediction_strength = abs(rule.prediction)
            coverage_bonus = rule.coverage
            simplicity_bonus = 1.0 / (1.0 + len(rule.conditions) * 0.1)
            
            rule.importance = (
                prediction_strength * 10.0 +  # Prediction is most important
                coverage_bonus * 5.0 +          # Coverage is secondary
                simplicity_bonus * 1.0          # Simplicity is tertiary
            )
            
            # Penalize rules with too few samples
            if samples_covered < min_samples:
                rule.importance *= 0.1
    
    def print_rules(self, top_n: int = 10, target_name: str = "Profit"):
        """
        Print rules in human-readable format
        
        Args:
            top_n: Number of top rules to print
            target_name: Name of target variable
        """
        if not self.rules:
            print("No rules extracted. Call extract_rules() first.")
            return
        
        is_classification = (self.task_type == 'classification')
        
        print("\n" + "="*70)
        print(f"[RULES] TOP {min(top_n, len(self.rules))} TRADING RULES")
        print("="*70)
        
        for idx, rule in enumerate(self.rules[:top_n], 1):
            print(f"\n{'-'*70}")
            print(f"Rule #{idx} (Importance Score: {rule.importance:.2f})")
            print(f"{'-'*70}")
            print(rule.to_text(target_name, is_classification))
        
        print("\n" + "="*70)
    
    def export_rules_to_dataframe(self) -> pd.DataFrame:
        """
        Export rules to pandas DataFrame
        
        Returns:
            DataFrame with rules
        """
        if not self.rules:
            return pd.DataFrame()
        
        data = []
        
        for idx, rule in enumerate(self.rules, 1):
            # Combine conditions into single string
            condition_str = " AND ".join([
                f"{c['feature']} {c['operator']} {c['threshold']:.4f}"
                for c in rule.conditions
            ])
            
            data.append({
                'Rule_ID': idx,
                'Conditions': condition_str,
                'Prediction': rule.prediction,
                'Coverage_%': rule.coverage * 100,
                'Importance': rule.importance,
                'Num_Conditions': len(rule.conditions),
                'Tree_ID': rule.tree_id
            })
        
        return pd.DataFrame(data)
    
    def export_rules_to_excel(self, filepath: str):
        """
        Export rules to Excel file with auto-adjusted column widths
        
        Args:
            filepath: Path to save Excel file
        """
        df = self.export_rules_to_dataframe()
        
        if df.empty:
            print("No rules to export.")
            return
        
        # Create Excel writer with xlsxwriter engine for formatting
        with pd.ExcelWriter(filepath, engine='openpyxl') as writer:
            df.to_excel(writer, sheet_name='Trading Rules', index=False)
            
            # Get the worksheet
            worksheet = writer.sheets['Trading Rules']
            
            # Auto-adjust column widths
            for idx, col in enumerate(df.columns):
                max_length = max(
                    df[col].astype(str).map(len).max(),  # Max length in column
                    len(str(col))  # Length of column name
                ) + 2  # Add padding
                
                # Set minimum width of 10 and maximum of 100
                column_width = min(max(max_length, 10), 100)
                worksheet.column_dimensions[chr(65 + idx)].width = column_width
        
        print(f"[OK] Rules exported to: {filepath}")
    
    def export_rules_to_json(self, filepath: str):
        """
        Export rules to JSON file
        
        Args:
            filepath: Path to save JSON file
        """
        if not self.rules:
            print("No rules to export.")
            return
        
        rules_data = [rule.to_dict() for rule in self.rules]
        
        with open(filepath, 'w') as f:
            json.dump(rules_data, f, indent=2)
        
        print(f"[OK] Rules exported to: {filepath}")
    
    def get_rules_for_sample(self, sample: pd.Series, top_n: int = 3) -> List[Tuple[Rule, bool]]:
        """
        Find which rules apply to a specific sample
        
        Args:
            sample: Single data sample (pandas Series)
            top_n: Return top N matching rules
        
        Returns:
            List of (Rule, matches) tuples
        """
        matching_rules = []
        
        for rule in self.rules:
            matches = True
            
            for cond in rule.conditions:
                feature = cond['feature']
                operator = cond['operator']
                threshold = cond['threshold']
                
                if feature not in sample:
                    matches = False
                    break
                
                value = sample[feature]
                
                if operator == '<=' and not (value <= threshold):
                    matches = False
                    break
                elif operator == '>' and not (value > threshold):
                    matches = False
                    break
            
            if matches:
                matching_rules.append((rule, True))
        
        # Sort by importance and return top N
        matching_rules.sort(key=lambda x: x[0].importance, reverse=True)
        return matching_rules[:top_n]
    
    def simplify_rules(self, correlation_threshold: float = 0.9):
        """
        Simplify rules by removing redundant conditions
        
        Args:
            correlation_threshold: Correlation threshold for merging features
        """
        # This is a placeholder for advanced rule simplification
        # Can be implemented based on feature correlations
        print("[WARNING] Advanced rule simplification not yet implemented")
        pass


def main():
    """Demo function"""
    print("Rule Extractor Module - Ready for integration")
    print("\nUsage Example:")
    print("  extractor = RuleExtractor(model, features, X_train)")
    print("  rules = extractor.extract_rules(max_rules=20)")
    print("  extractor.print_rules()")
    print("  extractor.export_rules_to_excel('rules.xlsx')")


if __name__ == "__main__":
    main()

