"""
LightGBM Model Trainer Module
Handles data preparation, model training, and feature importance calculation
"""

import lightgbm as lgb
import pandas as pd
import numpy as np
from sklearn.model_selection import TimeSeriesSplit, train_test_split
from sklearn.metrics import mean_squared_error, mean_absolute_error, accuracy_score, classification_report
from typing import Dict, List, Tuple, Optional, Union
import warnings
warnings.filterwarnings('ignore')


class ModelTrainer:
    """Trains LightGBM models for trading rule extraction"""
    
    def __init__(self, 
                 df: pd.DataFrame,
                 feature_columns: List[str],
                 target_column: str,
                 datetime_column: Optional[str] = None,
                 task_type: str = 'regression'):
        """
        Initialize the model trainer
        
        Args:
            df: Input DataFrame
            feature_columns: List of feature column names
            target_column: Target column name
            datetime_column: Optional datetime column for time-series split
            task_type: 'regression' or 'classification'
        """
        self.df = df.copy()
        self.feature_columns = feature_columns
        self.target_column = target_column
        self.datetime_column = datetime_column
        self.task_type = task_type.lower()
        
        self.model = None
        self.X_train = None
        self.X_test = None
        self.y_train = None
        self.y_test = None
        self.feature_importance = None
        self.training_history = {}
        
        # Default hyperparameters
        self.params = {
            'objective': 'regression' if task_type == 'regression' else 'binary',
            'metric': 'rmse' if task_type == 'regression' else 'binary_logloss',
            'num_leaves': 31,
            'learning_rate': 0.05,
            'n_estimators': 100,
            'max_depth': -1,
            'min_child_samples': 20,
            'subsample': 0.8,
            'colsample_bytree': 0.8,
            'random_state': 42,
            'verbose': -1,
            'force_col_wise': True
        }
    
    def update_hyperparameters(self, params: Dict):
        """
        Update model hyperparameters
        
        Args:
            params: Dictionary of hyperparameters to update
        """
        self.params.update(params)
        print(f"[OK] Updated hyperparameters: {list(params.keys())}")
    
    def prepare_data(self, test_size: float = 0.2, use_time_series_split: bool = True) -> Dict:
        """
        Prepare data for training
        
        Args:
            test_size: Proportion of data for testing
            use_time_series_split: Use time-series aware split (respects temporal order)
        
        Returns:
            Dictionary with data preparation statistics
        """
        print("\n[PREPARING] Preparing data...")
        
        # Remove rows with missing values in features or target
        initial_rows = len(self.df)
        clean_df = self.df[self.feature_columns + [self.target_column]].dropna()
        rows_removed = initial_rows - len(clean_df)
        
        if rows_removed > 0:
            print(f"  [WARNING] Removed {rows_removed} rows with missing values")
        
        X = clean_df[self.feature_columns]
        y = clean_df[self.target_column]
        
        # For classification, convert target to binary if needed
        if self.task_type == 'classification':
            if y.nunique() > 2:
                # Convert to binary: positive profit = 1, non-positive = 0
                y = (y > 0).astype(int)
                print(f"  ℹ️  Converted target to binary classification")
                print(f"     Class 0 (negative/zero): {(y == 0).sum()} samples")
                print(f"     Class 1 (positive): {(y == 1).sum()} samples")
        
        # Split data
        if use_time_series_split and self.datetime_column:
            # Time-series split: earlier data for training, later for testing
            split_idx = int(len(X) * (1 - test_size))
            self.X_train = X.iloc[:split_idx]
            self.X_test = X.iloc[split_idx:]
            self.y_train = y.iloc[:split_idx]
            self.y_test = y.iloc[split_idx:]
            split_method = "Time-series split"
        else:
            # Random split
            self.X_train, self.X_test, self.y_train, self.y_test = train_test_split(
                X, y, test_size=test_size, random_state=42
            )
            split_method = "Random split"
        
        stats = {
            'total_samples': len(clean_df),
            'training_samples': len(self.X_train),
            'test_samples': len(self.X_test),
            'features_count': len(self.feature_columns),
            'rows_removed': rows_removed,
            'split_method': split_method
        }
        
        print(f"\n[OK] Data prepared:")
        print(f"  • Total samples: {stats['total_samples']:,}")
        print(f"  • Training samples: {stats['training_samples']:,} ({stats['training_samples']/stats['total_samples']*100:.1f}%)")
        print(f"  • Test samples: {stats['test_samples']:,} ({stats['test_samples']/stats['total_samples']*100:.1f}%)")
        print(f"  • Features: {stats['features_count']}")
        print(f"  • Split method: {split_method}")
        
        return stats
    
    def train(self, verbose: bool = True) -> Dict:
        """
        Train the LightGBM model
        
        Args:
            verbose: Print training progress
        
        Returns:
            Dictionary with training results
        """
        if self.X_train is None:
            raise ValueError("Data not prepared. Call prepare_data() first.")
        
        print("\n[TRAINING] Training LightGBM model...")
        
        # Create datasets
        train_data = lgb.Dataset(self.X_train, label=self.y_train)
        test_data = lgb.Dataset(self.X_test, label=self.y_test, reference=train_data)
        
        # Callbacks for monitoring
        callbacks = []
        if verbose:
            callbacks.append(lgb.log_evaluation(period=20))
        
        # Train model
        self.model = lgb.train(
            self.params,
            train_data,
            valid_sets=[train_data, test_data],
            valid_names=['train', 'valid'],
            callbacks=callbacks
        )
        
        # Calculate feature importance
        self.feature_importance = pd.DataFrame({
            'feature': self.feature_columns,
            'importance': self.model.feature_importance(importance_type='gain'),
            'split_importance': self.model.feature_importance(importance_type='split')
        }).sort_values('importance', ascending=False)
        
        # Calculate percentage
        self.feature_importance['importance_pct'] = (
            self.feature_importance['importance'] / 
            self.feature_importance['importance'].sum() * 100
        )
        
        print("\n[OK] Training completed!")
        
        # Evaluate model
        results = self.evaluate()
        
        return results
    
    def evaluate(self) -> Dict:
        """
        Evaluate the trained model
        
        Returns:
            Dictionary with evaluation metrics
        """
        if self.model is None:
            raise ValueError("Model not trained. Call train() first.")
        
        # Predictions
        y_train_pred = self.model.predict(self.X_train)
        y_test_pred = self.model.predict(self.X_test)
        
        results = {
            'task_type': self.task_type,
            'train_metrics': {},
            'test_metrics': {}
        }
        
        if self.task_type == 'regression':
            # Regression metrics
            results['train_metrics'] = {
                'rmse': np.sqrt(mean_squared_error(self.y_train, y_train_pred)),
                'mae': mean_absolute_error(self.y_train, y_train_pred),
                'r2': np.corrcoef(self.y_train, y_train_pred)[0, 1]**2 if len(self.y_train) > 1 else 0
            }
            
            results['test_metrics'] = {
                'rmse': np.sqrt(mean_squared_error(self.y_test, y_test_pred)),
                'mae': mean_absolute_error(self.y_test, y_test_pred),
                'r2': np.corrcoef(self.y_test, y_test_pred)[0, 1]**2 if len(self.y_test) > 1 else 0
            }
            
            print("\n[PERFORMANCE] Model Performance (Regression):")
            print(f"\n  Training Set:")
            print(f"    • RMSE: {results['train_metrics']['rmse']:.6f}")
            print(f"    • MAE:  {results['train_metrics']['mae']:.6f}")
            print(f"    • R²:   {results['train_metrics']['r2']:.4f}")
            
            print(f"\n  Test Set:")
            print(f"    • RMSE: {results['test_metrics']['rmse']:.6f}")
            print(f"    • MAE:  {results['test_metrics']['mae']:.6f}")
            print(f"    • R²:   {results['test_metrics']['r2']:.4f}")
            
        else:
            # Classification metrics
            y_train_pred_class = (y_train_pred > 0.5).astype(int)
            y_test_pred_class = (y_test_pred > 0.5).astype(int)
            
            results['train_metrics'] = {
                'accuracy': accuracy_score(self.y_train, y_train_pred_class),
                'positive_rate': y_train_pred_class.mean()
            }
            
            results['test_metrics'] = {
                'accuracy': accuracy_score(self.y_test, y_test_pred_class),
                'positive_rate': y_test_pred_class.mean()
            }
            
            print("\n[PERFORMANCE] Model Performance (Classification):")
            print(f"\n  Training Set:")
            print(f"    • Accuracy: {results['train_metrics']['accuracy']:.4f}")
            print(f"    • Positive Rate: {results['train_metrics']['positive_rate']:.4f}")
            
            print(f"\n  Test Set:")
            print(f"    • Accuracy: {results['test_metrics']['accuracy']:.4f}")
            print(f"    • Positive Rate: {results['test_metrics']['positive_rate']:.4f}")
        
        return results
    
    def get_feature_importance(self, top_n: Optional[int] = None) -> pd.DataFrame:
        """
        Get feature importance rankings
        
        Args:
            top_n: Return only top N features (None = all)
        
        Returns:
            DataFrame with feature importance
        """
        if self.feature_importance is None:
            raise ValueError("Model not trained. Call train() first.")
        
        importance_df = self.feature_importance.copy()
        
        if top_n:
            importance_df = importance_df.head(top_n)
        
        return importance_df
    
    def print_feature_importance(self, top_n: int = 10):
        """
        Print feature importance in a formatted way
        
        Args:
            top_n: Number of top features to display
        """
        if self.feature_importance is None:
            raise ValueError("Model not trained. Call train() first.")
        
        print("\n" + "="*70)
        print(f"[IMPORTANCE] TOP {top_n} FEATURE IMPORTANCE")
        print("="*70)
        
        top_features = self.feature_importance.head(top_n)
        
        for idx, row in top_features.iterrows():
            bar_length = int(row['importance_pct'] / 2)  # Scale to fit terminal
            bar = '#' * bar_length
            print(f"\n{idx+1:2d}. {row['feature']:<30s}")
            print(f"    {bar} {row['importance_pct']:.2f}%")
            print(f"    Gain: {row['importance']:.1f} | Splits: {row['split_importance']:.0f}")
        
        print("\n" + "="*70)
    
    def cross_validate(self, n_splits: int = 5) -> Dict:
        """
        Perform time-series cross-validation
        
        Args:
            n_splits: Number of cross-validation splits
        
        Returns:
            Dictionary with cross-validation results
        """
        print(f"\n[CV] Performing {n_splits}-fold time-series cross-validation...")
        
        X = self.df[self.feature_columns].dropna()
        y = self.df[self.target_column].dropna()
        
        # Align X and y
        common_idx = X.index.intersection(y.index)
        X = X.loc[common_idx]
        y = y.loc[common_idx]
        
        tscv = TimeSeriesSplit(n_splits=n_splits)
        
        cv_scores = []
        
        for fold, (train_idx, val_idx) in enumerate(tscv.split(X), 1):
            X_train_cv = X.iloc[train_idx]
            X_val_cv = X.iloc[val_idx]
            y_train_cv = y.iloc[train_idx]
            y_val_cv = y.iloc[val_idx]
            
            # Train
            train_data = lgb.Dataset(X_train_cv, label=y_train_cv)
            model_cv = lgb.train(self.params, train_data, verbose_eval=False)
            
            # Predict
            y_pred_cv = model_cv.predict(X_val_cv)
            
            # Score
            if self.task_type == 'regression':
                score = np.sqrt(mean_squared_error(y_val_cv, y_pred_cv))
                metric_name = 'RMSE'
            else:
                y_pred_class = (y_pred_cv > 0.5).astype(int)
                score = accuracy_score(y_val_cv, y_pred_class)
                metric_name = 'Accuracy'
            
            cv_scores.append(score)
            print(f"  Fold {fold}/{n_splits}: {metric_name} = {score:.4f}")
        
        results = {
            'cv_scores': cv_scores,
            'mean_score': np.mean(cv_scores),
            'std_score': np.std(cv_scores),
            'metric_name': metric_name
        }
        
        print(f"\n[OK] Cross-validation completed:")
        print(f"  • Mean {metric_name}: {results['mean_score']:.4f} (±{results['std_score']:.4f})")
        
        return results
    
    def save_model(self, filepath: str):
        """
        Save trained model to file
        
        Args:
            filepath: Path to save model
        """
        if self.model is None:
            raise ValueError("No model to save. Train model first.")
        
        self.model.save_model(filepath)
        print(f"[OK] Model saved to: {filepath}")
    
    def load_model(self, filepath: str):
        """
        Load trained model from file
        
        Args:
            filepath: Path to model file
        """
        self.model = lgb.Booster(model_file=filepath)
        print(f"[OK] Model loaded from: {filepath}")


def main():
    """Demo function"""
    print("LightGBM Model Trainer Module - Ready for integration")
    print("\nUsage Example:")
    print("  trainer = ModelTrainer(df, features, target, task_type='regression')")
    print("  trainer.prepare_data()")
    print("  trainer.train()")
    print("  trainer.print_feature_importance()")


if __name__ == "__main__":
    main()

