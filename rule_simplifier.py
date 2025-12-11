"""
Rule Simplifier Module
Converts raw LightGBM rules into trader-friendly signals
"""

import pandas as pd
from typing import List, Dict, Tuple
from collections import defaultdict


class SimplifiedRule:
    """Represents a simplified, trader-friendly rule"""
    
    def __init__(self, conditions: Dict, prediction: float, coverage: float, importance: float):
        self.conditions = conditions  # {feature: threshold}
        self.prediction = prediction
        self.coverage = coverage
        self.importance = importance
        self.signal = "LONG" if prediction > 0 else "SHORT"
        self.strength = self._calculate_strength()
    
    def _calculate_strength(self) -> str:
        """Calculate signal strength based on prediction magnitude"""
        abs_pred = abs(self.prediction)
        if abs_pred > 0.002:
            return "Strong"
        elif abs_pred > 0.001:
            return "Moderate"
        else:
            return "Weak"
    
    def to_readable_text(self, asset: str = "SPY") -> str:
        """Convert to human-readable trading rule"""
        # Build condition text
        conditions_text = []
        
        for feature, (operator, threshold) in self.conditions.items():
            # Clean feature name
            clean_feature = feature.replace(" at End of Minute", "").replace(" At End of Minute", "")
            
            # Round threshold to 1 decimal place for readability
            rounded_threshold = round(threshold, 1)
            
            # Convert operator to readable form
            if operator == "<=":
                op_text = "<"
            elif operator == ">":
                op_text = ">"
            else:
                op_text = operator
            
            conditions_text.append(f"{clean_feature} {op_text} {rounded_threshold}")
        
        condition_string = " AND ".join(conditions_text)
        
        # Build signal with strength
        signal_text = f"{self.strength} {self.signal} {asset}"
        
        return f"IF {condition_string} THEN {signal_text}"
    
    def to_dict(self, asset: str = "SPY") -> Dict:
        """Convert to dictionary for DataFrame export"""
        # Build simple condition string
        conditions_list = []
        for feature, (operator, threshold) in self.conditions.items():
            clean_feature = feature.replace(" at End of Minute", "").replace(" At End of Minute", "")
            op = "<" if operator == "<=" else ">"
            rounded_threshold = round(threshold, 1)
            conditions_list.append(f"{clean_feature} {op} {rounded_threshold}")
        
        return {
            'Condition': " AND ".join(conditions_list),
            'Signal': f"{self.strength} {self.signal}",
            'Asset': asset,
            'Expected_Profit': round(self.prediction, 4),
            'Coverage_%': round(self.coverage * 100, 1),
            'Confidence': round(self.importance, 2)
        }


def simplify_conditions(conditions: List[Dict]) -> Dict:
    """
    Simplify redundant conditions
    
    Example: CallDex > 15.8 AND CallDex > 16.2 AND CallDex > 16.5
    Becomes: CallDex > 16.5 (only the most restrictive)
    """
    # Group conditions by feature
    feature_conditions = defaultdict(list)
    
    for cond in conditions:
        feature = cond['feature']
        operator = cond['operator']
        threshold = cond['threshold']
        feature_conditions[feature].append((operator, threshold))
    
    # Simplify each feature's conditions
    simplified = {}
    
    for feature, ops_thresholds in feature_conditions.items():
        # Separate > and <= conditions
        greater_than = [t for op, t in ops_thresholds if op == '>']
        less_equal = [t for op, t in ops_thresholds if op == '<=']
        
        # Keep only the most restrictive
        if greater_than:
            # For >, keep the maximum (most restrictive)
            simplified[feature] = ('>', max(greater_than))
        elif less_equal:
            # For <=, keep the minimum (most restrictive)
            simplified[feature] = ('<=', min(less_equal))
    
    return simplified


def create_trader_friendly_rules(rules: List, top_n: int = 6, min_coverage: float = 0.15) -> List[SimplifiedRule]:
    """
    Convert raw rules to trader-friendly format
    
    Args:
        rules: List of Rule objects from RuleExtractor
        top_n: Number of top rules to return (default 6)
        min_coverage: Minimum coverage threshold (default 15%)
    
    Returns:
        List of SimplifiedRule objects
    """
    simplified_rules = []
    
    for rule in rules:
        # Skip low-coverage rules
        if rule.coverage < min_coverage:
            continue
        
        # Simplify conditions
        simplified_conditions = simplify_conditions(rule.conditions)
        
        # Skip if too many conditions (still complex)
        if len(simplified_conditions) > 3:
            continue
        
        # Skip if conditions are empty
        if not simplified_conditions:
            continue
        
        # Create simplified rule
        simple_rule = SimplifiedRule(
            conditions=simplified_conditions,
            prediction=rule.prediction,
            coverage=rule.coverage,
            importance=rule.importance
        )
        
        simplified_rules.append(simple_rule)
    
    # Sort by importance and return top N
    simplified_rules.sort(key=lambda r: r.importance, reverse=True)
    
    return simplified_rules[:top_n]


def export_trader_rules_to_excel(simplified_rules: List[SimplifiedRule], 
                                  filepath: str, 
                                  asset: str = "SPY"):
    """
    Export simplified rules to trader-friendly Excel format
    
    Args:
        simplified_rules: List of SimplifiedRule objects
        filepath: Output Excel file path
        asset: Asset name (default "SPY")
    """
    # Convert to DataFrame
    data = [rule.to_dict(asset) for rule in simplified_rules]
    df = pd.DataFrame(data)
    
    # Add rule numbers
    df.insert(0, 'Rule', range(1, len(df) + 1))
    
    # Create Excel with formatting
    with pd.ExcelWriter(filepath, engine='openpyxl') as writer:
        df.to_excel(writer, sheet_name='Trading Signals', index=False)
        
        # Auto-adjust column widths
        worksheet = writer.sheets['Trading Signals']
        for idx, col in enumerate(df.columns):
            max_length = max(
                df[col].astype(str).map(len).max(),
                len(str(col))
            ) + 2
            column_width = min(max(max_length, 12), 80)
            worksheet.column_dimensions[chr(65 + idx)].width = column_width
    
    print(f"[OK] Trader-friendly rules exported to: {filepath}")


def print_trader_rules(simplified_rules: List[SimplifiedRule], asset: str = "SPY"):
    """
    Print rules in trader-friendly format
    
    Args:
        simplified_rules: List of SimplifiedRule objects
        asset: Asset name (default "SPY")
    """
    print("\n" + "="*80)
    print(f"[TRADING SIGNALS] TOP {len(simplified_rules)} ACTIONABLE TRADING RULES")
    print("="*80)
    
    for idx, rule in enumerate(simplified_rules, 1):
        print(f"\n{'-'*80}")
        print(f"Signal #{idx} - {rule.strength} {rule.signal} {asset}")
        print(f"{'-'*80}")
        print(rule.to_readable_text(asset))
        print(f"  Expected Profit: {rule.prediction:+.4f} per trade")
        print(f"  Coverage: {rule.coverage*100:.1f}% of samples")
        print(f"  Confidence Score: {rule.importance:.2f}")
    
    print("\n" + "="*80)
    print(f"[INFO] These rules are ranked by confidence and filtered for clarity")
    print("="*80 + "\n")


def main():
    """Demo function"""
    print("Rule Simplifier Module - Ready for integration")
    print("\nUsage Example:")
    print("  from rule_simplifier import create_trader_friendly_rules, print_trader_rules")
    print("  simplified = create_trader_friendly_rules(raw_rules, top_n=6)")
    print("  print_trader_rules(simplified, asset='SPY')")


if __name__ == "__main__":
    main()

