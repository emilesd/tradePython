"""
Excel File Analyzer Module
Dynamically analyzes Excel/CSV file structure for LightGBM trading tool
"""

import pandas as pd
import numpy as np
from typing import Dict, List, Tuple, Optional
from datetime import datetime
import os


class ExcelAnalyzer:
    """Analyzes Excel/CSV files to understand their structure and content"""
    
    def __init__(self, file_path: str):
        """
        Initialize analyzer with file path
        
        Args:
            file_path: Path to Excel or CSV file
        """
        self.file_path = file_path
        self.df = None
        self.file_type = None
        self.analysis_results = {}
        
    def load_file(self) -> pd.DataFrame:
        """
        Load Excel or CSV file into pandas DataFrame
        
        Returns:
            Loaded DataFrame
        """
        file_ext = os.path.splitext(self.file_path)[1].lower()
        
        try:
            if file_ext in ['.xlsx', '.xls']:
                self.df = pd.read_excel(self.file_path)
                self.file_type = 'excel'
            elif file_ext == '.csv':
                self.df = pd.read_csv(self.file_path)
                self.file_type = 'csv'
            else:
                raise ValueError(f"Unsupported file type: {file_ext}")
            
            print(f"[OK] Successfully loaded {self.file_type} file")
            print(f"  Shape: {self.df.shape[0]} rows × {self.df.shape[1]} columns")
            return self.df
            
        except Exception as e:
            raise Exception(f"Error loading file: {str(e)}")
    
    def analyze_structure(self) -> Dict:
        """
        Analyze the structure and content of the loaded file
        
        Returns:
            Dictionary with analysis results
        """
        if self.df is None:
            raise ValueError("No file loaded. Call load_file() first.")
        
        results = {
            'basic_info': self._get_basic_info(),
            'column_types': self._analyze_column_types(),
            'datetime_columns': self._identify_datetime_columns(),
            'numeric_columns': self._identify_numeric_columns(),
            'potential_features': self._identify_potential_features(),
            'potential_targets': self._identify_potential_targets(),
            'missing_data': self._analyze_missing_data(),
            'data_quality': self._assess_data_quality()
        }
        
        self.analysis_results = results
        return results
    
    def _get_basic_info(self) -> Dict:
        """Get basic information about the dataset"""
        return {
            'rows': len(self.df),
            'columns': len(self.df.columns),
            'column_names': list(self.df.columns),
            'memory_usage': f"{self.df.memory_usage(deep=True).sum() / 1024**2:.2f} MB"
        }
    
    def _analyze_column_types(self) -> Dict:
        """Analyze data types of each column"""
        col_types = {}
        for col in self.df.columns:
            dtype = str(self.df[col].dtype)
            col_types[col] = {
                'dtype': dtype,
                'unique_values': self.df[col].nunique(),
                'sample_values': self.df[col].dropna().head(3).tolist()
            }
        return col_types
    
    def _identify_datetime_columns(self) -> List[str]:
        """Identify columns that contain datetime information"""
        datetime_cols = []
        
        for col in self.df.columns:
            # Check if already datetime type
            if pd.api.types.is_datetime64_any_dtype(self.df[col]):
                datetime_cols.append(col)
                continue
            
            # Try to parse as datetime
            try:
                if self.df[col].dtype == 'object':
                    sample = self.df[col].dropna().head(10)
                    pd.to_datetime(sample)
                    datetime_cols.append(col)
            except:
                pass
        
        return datetime_cols
    
    def _identify_numeric_columns(self) -> Dict[str, List[str]]:
        """Identify numeric columns and categorize them"""
        numeric_cols = self.df.select_dtypes(include=[np.number]).columns.tolist()
        
        # Separate into integer and float columns
        int_cols = self.df.select_dtypes(include=['int64', 'int32', 'int16', 'int8']).columns.tolist()
        float_cols = self.df.select_dtypes(include=['float64', 'float32']).columns.tolist()
        
        return {
            'all_numeric': numeric_cols,
            'integer_columns': int_cols,
            'float_columns': float_cols,
            'count': len(numeric_cols)
        }
    
    def _identify_potential_features(self) -> List[str]:
        """
        Identify columns that could be used as features (indicators)
        Excludes datetime and potential target columns
        """
        datetime_cols = self._identify_datetime_columns()
        numeric_info = self._identify_numeric_columns()
        all_numeric = numeric_info['all_numeric']
        
        # Exclude datetime columns and common target keywords
        target_keywords = ['profit', 'return', 'target', 'label', 'direction', 'signal']
        
        features = []
        for col in all_numeric:
            col_lower = col.lower()
            is_target = any(keyword in col_lower for keyword in target_keywords)
            is_datetime = col in datetime_cols
            
            if not is_target and not is_datetime:
                features.append(col)
        
        return features
    
    def _identify_potential_targets(self) -> List[str]:
        """
        Identify columns that could be used as prediction targets
        (e.g., profit, return, direction)
        """
        target_keywords = ['profit', 'return', 'target', 'label', 'direction', 'signal', 'gain', 'loss']
        numeric_cols = self._identify_numeric_columns()['all_numeric']
        
        targets = []
        for col in numeric_cols:
            col_lower = col.lower()
            if any(keyword in col_lower for keyword in target_keywords):
                targets.append(col)
        
        return targets
    
    def _analyze_missing_data(self) -> Dict:
        """Analyze missing data in the dataset"""
        missing_info = {}
        
        for col in self.df.columns:
            missing_count = self.df[col].isna().sum()
            if missing_count > 0:
                missing_info[col] = {
                    'count': int(missing_count),
                    'percentage': round(missing_count / len(self.df) * 100, 2)
                }
        
        return missing_info
    
    def _assess_data_quality(self) -> Dict:
        """Assess overall data quality"""
        numeric_cols = self._identify_numeric_columns()['all_numeric']
        
        quality_metrics = {
            'total_missing_values': int(self.df.isna().sum().sum()),
            'missing_percentage': round(self.df.isna().sum().sum() / (self.df.shape[0] * self.df.shape[1]) * 100, 2),
            'duplicate_rows': int(self.df.duplicated().sum()),
            'numeric_columns_stats': {}
        }
        
        # Statistics for numeric columns
        for col in numeric_cols[:5]:  # Limit to first 5 for brevity
            quality_metrics['numeric_columns_stats'][col] = {
                'min': float(self.df[col].min()) if not self.df[col].isna().all() else None,
                'max': float(self.df[col].max()) if not self.df[col].isna().all() else None,
                'mean': float(self.df[col].mean()) if not self.df[col].isna().all() else None,
                'std': float(self.df[col].std()) if not self.df[col].isna().all() else None
            }
        
        return quality_metrics
    
    def print_analysis_report(self):
        """Print a formatted analysis report"""
        if not self.analysis_results:
            print("No analysis results available. Run analyze_structure() first.")
            return
        
        print("\n" + "="*70)
        print("[ANALYSIS] EXCEL FILE ANALYSIS REPORT")
        print("="*70)
        
        # Basic Info
        print("\n[INFO] BASIC INFORMATION:")
        basic = self.analysis_results['basic_info']
        print(f"  • Rows: {basic['rows']:,}")
        print(f"  • Columns: {basic['columns']}")
        print(f"  • Memory Usage: {basic['memory_usage']}")
        
        # Column Names
        print(f"\n  Column Names:")
        for i, col in enumerate(basic['column_names'], 1):
            print(f"    {i}. {col}")
        
        # Datetime Columns
        print("\n[DATETIME] DATETIME COLUMNS:")
        datetime_cols = self.analysis_results['datetime_columns']
        if datetime_cols:
            for col in datetime_cols:
                print(f"  • {col}")
        else:
            print("  • None detected")
        
        # Numeric Columns
        print("\n[NUMERIC] NUMERIC COLUMNS:")
        numeric = self.analysis_results['numeric_columns']
        print(f"  • Total: {numeric['count']}")
        print(f"  • Float columns: {len(numeric['float_columns'])}")
        print(f"  • Integer columns: {len(numeric['integer_columns'])}")
        
        # Potential Features
        print("\n[FEATURES] POTENTIAL FEATURES (Indicators):")
        features = self.analysis_results['potential_features']
        if features:
            for feat in features:
                print(f"  • {feat}")
        else:
            print("  • None detected")
        
        # Potential Targets
        print("\n[TARGETS] POTENTIAL TARGET COLUMNS:")
        targets = self.analysis_results['potential_targets']
        if targets:
            for target in targets:
                print(f"  • {target}")
        else:
            print("  • None detected")
        
        # Missing Data
        print("\n[WARNING] MISSING DATA:")
        missing = self.analysis_results['missing_data']
        if missing:
            for col, info in missing.items():
                print(f"  • {col}: {info['count']} ({info['percentage']}%)")
        else:
            print("  • No missing values detected [OK]")
        
        # Data Quality
        print("\n[QUALITY] DATA QUALITY METRICS:")
        quality = self.analysis_results['data_quality']
        print(f"  • Total Missing Values: {quality['total_missing_values']} ({quality['missing_percentage']}%)")
        print(f"  • Duplicate Rows: {quality['duplicate_rows']}")
        
        print("\n" + "="*70)
        print("[OK] Analysis Complete")
        print("="*70 + "\n")
    
    def get_feature_target_recommendation(self) -> Dict[str, List[str]]:
        """
        Provide recommendations for feature and target selection
        
        Returns:
            Dictionary with recommended features and targets
        """
        if not self.analysis_results:
            self.analyze_structure()
        
        return {
            'recommended_features': self.analysis_results['potential_features'],
            'recommended_targets': self.analysis_results['potential_targets'],
            'datetime_column': self.analysis_results['datetime_columns'][0] if self.analysis_results['datetime_columns'] else None
        }


def main():
    """Demo function to test the analyzer"""
    print("Excel Analyzer Module - Ready for integration")
    print("\nUsage Example:")
    print("  analyzer = ExcelAnalyzer('your_file.xlsx')")
    print("  analyzer.load_file()")
    print("  results = analyzer.analyze_structure()")
    print("  analyzer.print_analysis_report()")


if __name__ == "__main__":
    main()

