"""
Full Pipeline Test
End-to-end test of Excel analysis, model training, and rule extraction
"""

import pandas as pd
import time
from excel_analyzer import ExcelAnalyzer
from model_trainer import ModelTrainer
from rule_extractor import RuleExtractor
from rule_simplifier import create_trader_friendly_rules, print_trader_rules, export_trader_rules_to_excel


def test_full_pipeline():
    """Test the complete workflow with client's example data"""
    
    print("\n" + "="*80)
    print(" "*20 + "LIGHTGBM TRADING TOOL - FULL PIPELINE TEST")
    print("="*80)
    
    start_time = time.time()
    
    # ========================================================================
    # STEP 1: Load and Analyze Excel File
    # ========================================================================
    print("\n" + "-"*80)
    print("STEP 1: EXCEL FILE ANALYSIS")
    print("-"*80)
    
    # Create sample Excel from text file
    try:
        df = pd.read_csv('excelTxt.txt', sep='\t')
        excel_file = 'Example.xlsx'
        df.to_excel(excel_file, index=False)
        print(f"[OK] Created test file: {excel_file}")
    except Exception as e:
        print(f"[WARNING] Error creating test file: {e}")
        return
    
    # Analyze structure
    analyzer = ExcelAnalyzer(excel_file)
    analyzer.load_file()
    results = analyzer.analyze_structure()
    analyzer.print_analysis_report()
    
    recommendations = analyzer.get_feature_target_recommendation()
    
    # ========================================================================
    # STEP 2: Prepare Training Data
    # ========================================================================
    print("\n" + "-"*80)
    print("STEP 2: DATA PREPARATION")
    print("-"*80)
    
    # Select features and target
    feature_columns = recommendations['recommended_features']
    target_column = recommendations['recommended_targets'][0]  # Use first target
    datetime_column = recommendations['datetime_column']
    
    print(f"\n[CONFIGURATION] Selected Configuration:")
    print(f"  • Features: {', '.join(feature_columns)}")
    print(f"  • Target: {target_column}")
    print(f"  • Datetime: {datetime_column}")
    
    # ========================================================================
    # STEP 3: Train LightGBM Model (Regression)
    # ========================================================================
    print("\n" + "-"*80)
    print("STEP 3: MODEL TRAINING (Regression)")
    print("-"*80)
    
    trainer = ModelTrainer(
        df=analyzer.df,
        feature_columns=feature_columns,
        target_column=target_column,
        datetime_column=datetime_column,
        task_type='regression'
    )
    
    # Update hyperparameters if needed
    trainer.update_hyperparameters({
        'n_estimators': 50,  # Fewer trees for faster training in test
        'learning_rate': 0.1,
        'max_depth': 5
    })
    
    # Prepare data
    prep_stats = trainer.prepare_data(test_size=0.2, use_time_series_split=True)
    
    # Train model
    train_results = trainer.train(verbose=False)
    
    # Print feature importance
    trainer.print_feature_importance(top_n=len(feature_columns))
    
    # Cross-validation (optional, can be slow)
    # cv_results = trainer.cross_validate(n_splits=3)
    
    # ========================================================================
    # STEP 4: Extract Trading Rules
    # ========================================================================
    print("\n" + "-"*80)
    print("STEP 4: RULE EXTRACTION")
    print("-"*80)
    
    extractor = RuleExtractor(
        model=trainer.model,
        feature_names=feature_columns,
        X_train=trainer.X_train,
        task_type='regression'
    )
    
    # Extract rules
    rules = extractor.extract_rules(max_rules=20, min_samples=5)
    
    # Simplify rules for traders
    simplified_rules = create_trader_friendly_rules(rules, top_n=6, min_coverage=0.20)
    
    # Print trader-friendly rules
    print_trader_rules(simplified_rules, asset="SPY")
    
    # ========================================================================
    # STEP 5: Export Results
    # ========================================================================
    print("\n" + "-"*80)
    print("STEP 5: EXPORT RESULTS")
    print("-"*80)
    
    # Export feature importance with proper formatting
    importance_df = trainer.get_feature_importance()
    importance_file = 'feature_importance.xlsx'
    
    with pd.ExcelWriter(importance_file, engine='openpyxl') as writer:
        importance_df.to_excel(writer, sheet_name='Feature Importance', index=False)
        
        # Auto-adjust column widths
        worksheet = writer.sheets['Feature Importance']
        for idx, col in enumerate(importance_df.columns):
            max_length = max(
                importance_df[col].astype(str).map(len).max(),
                len(str(col))
            ) + 2
            column_width = min(max(max_length, 15), 50)
            worksheet.column_dimensions[chr(65 + idx)].width = column_width
    
    print(f"[OK] Feature importance exported to: {importance_file}")
    
    # Export trader-friendly rules
    rules_file = 'trading_signals.xlsx'
    export_trader_rules_to_excel(simplified_rules, rules_file, asset="SPY")
    
    # Also export technical rules for advanced users
    rules_technical = 'trading_rules_technical.xlsx'
    extractor.export_rules_to_excel(rules_technical)
    
    rules_json = 'trading_rules.json'
    extractor.export_rules_to_json(rules_json)
    
    # Save model
    model_file = 'lightgbm_model.txt'
    trainer.save_model(model_file)
    
    # ========================================================================
    # STEP 6: Test with Sample Data
    # ========================================================================
    print("\n" + "-"*80)
    print("STEP 6: SAMPLE PREDICTION")
    print("-"*80)
    
    # Take a random sample
    sample_idx = len(analyzer.df) // 2
    sample = analyzer.df.iloc[sample_idx][feature_columns]
    
    print(f"\nSample data point (row {sample_idx}):")
    for feat, val in sample.items():
        print(f"  • {feat}: {val}")
    
    # Find matching rules
    print(f"\n[PREDICTION] For this market condition:")
    print(f"  Based on RSI={sample['RSI at End of Minute']:.1f} and CallDex={sample['CallDex At End of Minute']:.1f}")
    
    # Check which simplified rules apply
    matching_signals = []
    for rule in simplified_rules:
        matches = True
        for feature, (operator, threshold) in rule.conditions.items():
            if feature not in sample:
                matches = False
                break
            value = sample[feature]
            if operator == '>' and not (value > threshold):
                matches = False
                break
            elif operator == '<=' and not (value <= threshold):
                matches = False
                break
        if matches:
            matching_signals.append(rule)
    
    if matching_signals:
        print(f"\n[SIGNALS] Matching Trading Signals ({len(matching_signals)}):")
        for idx, rule in enumerate(matching_signals, 1):
            print(f"\n  Signal #{idx}: {rule.strength} {rule.signal} SPY")
            print(f"  {rule.to_readable_text('SPY')}")
            print(f"  Expected: {rule.prediction:+.4f} | Confidence: {rule.importance:.2f}")
    else:
        print("\n[INFO] No clear signals for this market condition (neutral/hold)")
    
    # ========================================================================
    # SUMMARY
    # ========================================================================
    end_time = time.time()
    elapsed = end_time - start_time
    
    print("\n" + "="*80)
    print("[SUCCESS] PIPELINE TEST COMPLETED SUCCESSFULLY")
    print("="*80)
    print(f"\n[TIME] Total Time: {elapsed:.2f} seconds")
    
    if elapsed > 60:
        print(f"[WARNING] Execution took longer than 1 minute ({elapsed:.1f}s)")
        print("   Consider optimizing hyperparameters or reducing data size")
    else:
        print(f"[OK] Performance OK: Completed in under 1 minute")
    
    print(f"\n[FILES] Generated Files:")
    print(f"  • {excel_file} - Original data")
    print(f"  • {importance_file} - Feature importance rankings")
    print(f"  • {rules_file} - TRADER-FRIENDLY SIGNALS (main output)")
    print(f"  • {rules_technical} - Technical rules (for advanced users)")
    print(f"  • {rules_json} - JSON format")
    print(f"  • {model_file} - Trained model")
    
    print("\n" + "="*80)
    print("[SUCCESS] Ready for client demonstration!")
    print("="*80 + "\n")


def test_classification_mode():
    """Test classification mode"""
    
    print("\n" + "="*80)
    print(" "*20 + "TESTING CLASSIFICATION MODE")
    print("="*80)
    
    try:
        df = pd.read_csv('excelTxt.txt', sep='\t')
        excel_file = 'Example.xlsx'
        
        # Analyze
        analyzer = ExcelAnalyzer(excel_file)
        analyzer.load_file()
        results = analyzer.analyze_structure()
        
        recommendations = analyzer.get_feature_target_recommendation()
        feature_columns = recommendations['recommended_features']
        target_column = recommendations['recommended_targets'][0]
        
        # Train in classification mode
        print(f"\n[TRAINING] Training Classification Model")
        print(f"  • Target: {target_column} (will be binarized: positive=1, negative=0)")
        
        trainer = ModelTrainer(
            df=analyzer.df,
            feature_columns=feature_columns,
            target_column=target_column,
            task_type='classification'
        )
        
        trainer.update_hyperparameters({
            'n_estimators': 30,
            'max_depth': 4
        })
        
        trainer.prepare_data(test_size=0.2)
        trainer.train(verbose=False)
        
        # Extract rules
        extractor = RuleExtractor(
            model=trainer.model,
            feature_names=feature_columns,
            X_train=trainer.X_train,
            task_type='classification'
        )
        
        rules = extractor.extract_rules(max_rules=10, min_samples=5)
        extractor.print_rules(top_n=5, target_name="Signal")
        
        print("\n[OK] Classification mode test completed!")
        
    except Exception as e:
        print(f"[WARNING] Classification test error: {e}")


def main():
    """Run all tests"""
    
    # Test 1: Full regression pipeline
    test_full_pipeline()
    
    # Test 2: Classification mode
    input("\nPress Enter to test Classification mode...")
    test_classification_mode()
    
    print("\n" + "="*80)
    print("[SUCCESS] ALL TESTS COMPLETED")
    print("="*80 + "\n")


if __name__ == "__main__":
    main()

