# 🚀 LightGBM Excel Trading Tool

**No-code solution for extracting trading rules from Excel/CSV data using LightGBM**

---

## 📋 Overview

This tool allows traders to:
- ✅ Upload Excel/CSV files with price data and technical indicators
- ✅ Automatically train LightGBM models
- ✅ Extract human-readable trading rules (IF-THEN statements)
- ✅ View feature importance rankings
- ✅ Adjust model parameters through simple interface

**No coding required!** Simply upload your data, click a button, and get actionable trading rules.

---

## 🎯 Key Features

### 1. **Automatic Data Analysis**
- Detects datetime, numeric, and target columns automatically
- Identifies potential features and targets
- Analyzes data quality and missing values
- Provides recommendations

### 2. **LightGBM Model Training**
- Time-series aware cross-validation
- Adjustable hyperparameters
- Support for regression and classification
- Feature importance calculation
- Fast training (<1 minute on typical datasets)

### 3. **Rule Extraction**
- Converts complex models into simple IF-THEN rules
- Rules ranked by importance and coverage
- Human-readable format
- Export to Excel/JSON

### 4. **Flexible Input**
- Works with any Excel (.xlsx, .xls) or CSV file
- Handles any number of indicator columns
- Supports multiple timeframes (1-minute, daily, etc.)
- No hardcoded assumptions

---

## 🛠️ Installation

### Requirements
- Python 3.8 or higher
- Windows 10/11 (or macOS/Linux)

### Setup Steps

1. **Clone or download this project**
```bash
cd lightgbm-trading-tool
```

2. **Install dependencies**
```bash
pip install -r requirements.txt
```

3. **Verify installation**
```bash
python test_analyzer.py
```

---

## 📊 Quick Start

### Command Line Interface

#### 1. Analyze an Excel file
```python
from excel_analyzer import ExcelAnalyzer

analyzer = ExcelAnalyzer('your_file.xlsx')
analyzer.load_file()
analyzer.analyze_structure()
analyzer.print_analysis_report()
```

#### 2. Train a model and extract rules
```python
from model_trainer import ModelTrainer
from rule_extractor import RuleExtractor

# Train model
trainer = ModelTrainer(
    df=analyzer.df,
    feature_columns=['RSI', 'CallDex', 'SPY At End of Minute'],
    target_column='Profit If Long at End of Previous Minute',
    task_type='regression'
)

trainer.prepare_data()
trainer.train()
trainer.print_feature_importance()

# Extract rules
extractor = RuleExtractor(
    model=trainer.model,
    feature_names=trainer.feature_columns,
    X_train=trainer.X_train
)

rules = extractor.extract_rules(max_rules=20)
extractor.print_rules(top_n=10)
extractor.export_rules_to_excel('trading_rules.xlsx')
```

#### 3. Run full pipeline test
```bash
python test_full_pipeline.py
```

### Web Interface (Coming Soon)
```bash
python app.py
# Then open browser to http://localhost:5000
```

---

## 📂 Example Data Format

Your Excel/CSV file should have:

| Date/Time           | Price | Indicator 1 | Indicator 2 | Target (Profit/Direction) |
|---------------------|-------|-------------|-------------|---------------------------|
| 2025-01-01 09:30:00 | 100.5 | 45.2        | 18.5        | 0.25                      |
| 2025-01-01 09:31:00 | 100.7 | 46.8        | 18.6        | 0.15                      |
| ...                 | ...   | ...         | ...         | ...                       |

**Columns**:
- **Datetime** (optional): Timestamp for time-series split
- **Features**: Any numeric indicators (RSI, moving averages, etc.)
- **Target**: What you want to predict (profit, direction, signal)

---

## 🎛️ Configuration Options

### Model Hyperparameters

You can adjust these parameters:

| Parameter          | Default | Range      | Description                    |
|--------------------|---------|------------|--------------------------------|
| `n_estimators`     | 100     | 50-500     | Number of trees                |
| `learning_rate`    | 0.05    | 0.01-0.3   | Learning rate                  |
| `max_depth`        | -1      | 3-15       | Maximum tree depth             |
| `num_leaves`       | 31      | 15-255     | Maximum leaves per tree        |
| `min_child_samples`| 20      | 5-100      | Min samples in leaf            |

Example:
```python
trainer.update_hyperparameters({
    'n_estimators': 200,
    'learning_rate': 0.03,
    'max_depth': 7
})
```

### Rule Extraction Options

| Parameter     | Default | Description                          |
|---------------|---------|--------------------------------------|
| `max_rules`   | 20      | Maximum number of rules to extract   |
| `min_samples` | 10      | Minimum samples for valid rule       |

---

## 📈 Output Examples

### Feature Importance
```
🎯 TOP 3 FEATURE IMPORTANCE
══════════════════════════════════════════════════════════════════════

 1. RSI at End of Minute           
    ████████████████████ 45.23%
    Gain: 1234.5 | Splits: 89

 2. CallDex At End of Minute       
    ██████████████ 32.87%
    Gain: 897.3 | Splits: 67

 3. SPY At End of Minute           
    █████████ 21.90%
    Gain: 598.2 | Splits: 45
```

### Trading Rules
```
📜 TOP 3 TRADING RULES
══════════════════════════════════════════════════════════════════════

Rule #1 (Importance Score: 8.52)
──────────────────────────────────────────────────────────────────────
IF RSI at End of Minute <= 30.5000 AND CallDex At End of Minute > 19.0000
THEN Expected Profit If Long: +0.3421
    [Coverage: 12.5% | Importance: 8.52]

Rule #2 (Importance Score: 7.18)
──────────────────────────────────────────────────────────────────────
IF RSI at End of Minute > 65.0000 AND SPY At End of Minute > 660.0000
THEN Expected Profit If Long: -0.2815
    [Coverage: 8.3% | Importance: 7.18]
```

---

## 🧪 Testing

### Run Tests
```bash
# Test 1: Excel analyzer
python test_analyzer.py

# Test 2: Full pipeline
python test_full_pipeline.py
```

### Expected Output
- ✅ All modules load without errors
- ✅ Sample data analyzed correctly
- ✅ Model trains in <60 seconds
- ✅ Rules extracted and displayed
- ✅ Files exported successfully

---

## 📁 Project Structure

```
lightgbm-trading-tool/
│
├── excel_analyzer.py       # Analyzes Excel/CSV structure
├── model_trainer.py         # Trains LightGBM models
├── rule_extractor.py        # Extracts IF-THEN rules
├── app.py                   # Flask web interface (TODO)
│
├── test_analyzer.py         # Test analyzer module
├── test_full_pipeline.py    # End-to-end test
│
├── requirements.txt         # Python dependencies
├── README.md                # This file
├── PROJECT_PLAN.md          # Detailed project plan
│
└── outputs/                 # Generated results
    ├── feature_importance.xlsx
    ├── trading_rules.xlsx
    ├── trading_rules.json
    └── lightgbm_model.txt
```

---

## 🔧 Troubleshooting

### Common Issues

**1. "Module not found" error**
```bash
pip install -r requirements.txt
```

**2. "File not found" error**
- Ensure Excel file path is correct
- Use forward slashes (/) or raw strings (r"C:\path\to\file")

**3. "Not enough data" error**
- Minimum 50 rows recommended
- Ensure target column has valid numeric values

**4. Model takes too long**
- Reduce `n_estimators` (try 50-100)
- Increase `learning_rate` (try 0.1)
- Set `max_depth` (try 5-7)

**5. Rules don't make sense**
- Check feature importance first
- Increase `min_samples` for more robust rules
- Ensure data quality (no errors in indicators)

---

## 🎓 Tips for Best Results

### Data Preparation
1. **Clean your data**: Remove or fill missing values
2. **Use meaningful column names**: "RSI_14" better than "Column1"
3. **Include enough history**: 100+ samples recommended
4. **Check for outliers**: Extreme values can skew results

### Feature Selection
1. **Start simple**: Use 3-5 well-known indicators
2. **Avoid redundancy**: Don't use highly correlated features
3. **Use lagged features**: Previous period values often more predictive
4. **Domain knowledge**: Include features you trust

### Model Training
1. **Start with defaults**: Only tune if needed
2. **Use cross-validation**: Ensures robust performance
3. **Check overfitting**: Test performance should be reasonable
4. **Time-series split**: Use for realistic trading simulation

### Rule Interpretation
1. **Focus on top rules**: Most important rules first
2. **Check coverage**: Rules covering 5-20% of data often best
3. **Verify logic**: Do rules make trading sense?
4. **Backtest carefully**: Always validate on out-of-sample data

---

## 📞 Support

For issues or questions:
1. Check this README
2. Review `PROJECT_PLAN.md` for technical details
3. Run test scripts to verify setup
4. Contact project developer

---

## 🚀 Roadmap

### Current Version (v1.0)
- ✅ Excel/CSV file analysis
- ✅ LightGBM model training
- ✅ Rule extraction
- ✅ Command-line interface
- ✅ Export to Excel/JSON

### Planned Features (v1.1)
- ⏳ Flask web interface
- ⏳ Visual charts and graphs
- ⏳ Multi-timeframe features
- ⏳ Advanced rule simplification
- ⏳ Batch processing

### Future Enhancements (v2.0)
- 💡 Walk-forward optimization
- 💡 Backtesting module
- 💡 Live data integration
- 💡 Model comparison tools
- 💡 Advanced visualizations

---

## 📄 License

This project was developed as a freelance project for trading analysis purposes.

---

## 🙏 Acknowledgments

- **Client**: Scott N. (Freelancer.com Project #40047202)
- **Developer**: Nations
- **Framework**: LightGBM by Microsoft
- **Budget**: $250 USD
- **Timeline**: Dec 2025

---

**Made with ❤️ for traders who want powerful ML tools without the complexity**

Last Updated: December 10, 2025

