"""
Test script for Excel Analyzer
Demonstrates analysis on the client's example data
"""

import pandas as pd
from excel_analyzer import ExcelAnalyzer


def create_sample_data_from_txt():
    """
    Create a sample Excel file from the excelTxt.txt for testing
    """
    print("Creating sample Excel file from client's example data...")
    
    # Read the tab-separated text file
    try:
        df = pd.read_csv('excelTxt.txt', sep='\t')
        
        # Save as Excel for testing
        output_file = 'Example.xlsx'
        df.to_excel(output_file, index=False)
        print(f"✓ Created {output_file}")
        return output_file
    except FileNotFoundError:
        print("⚠️  excelTxt.txt not found. Please ensure it's in the current directory.")
        return None
    except Exception as e:
        print(f"Error creating sample file: {str(e)}")
        return None


def test_analyzer():
    """Test the Excel Analyzer with sample data"""
    
    # Create sample Excel file
    excel_file = create_sample_data_from_txt()
    
    if not excel_file:
        print("\n⚠️  Could not create test file. Exiting.")
        return
    
    print("\n" + "="*70)
    print("🧪 TESTING EXCEL ANALYZER")
    print("="*70)
    
    # Initialize analyzer
    print("\n1. Initializing analyzer...")
    analyzer = ExcelAnalyzer(excel_file)
    
    # Load file
    print("\n2. Loading file...")
    analyzer.load_file()
    
    # Analyze structure
    print("\n3. Analyzing structure...")
    results = analyzer.analyze_structure()
    
    # Print report
    print("\n4. Generating report...")
    analyzer.print_analysis_report()
    
    # Get recommendations
    print("\n5. Getting feature/target recommendations...")
    recommendations = analyzer.get_feature_target_recommendation()
    
    print("\n📌 RECOMMENDATIONS FOR LIGHTGBM MODEL:")
    print(f"\n  Datetime Column: {recommendations['datetime_column']}")
    
    print(f"\n  Recommended Features ({len(recommendations['recommended_features'])}):")
    for feat in recommendations['recommended_features']:
        print(f"    • {feat}")
    
    print(f"\n  Recommended Target Columns ({len(recommendations['recommended_targets'])}):")
    for target in recommendations['recommended_targets']:
        print(f"    • {target}")
    
    # Preview data
    print("\n" + "="*70)
    print("📊 DATA PREVIEW (First 5 rows)")
    print("="*70)
    print(analyzer.df.head().to_string())
    
    print("\n" + "="*70)
    print("✅ TEST COMPLETED SUCCESSFULLY")
    print("="*70)


if __name__ == "__main__":
    test_analyzer()

