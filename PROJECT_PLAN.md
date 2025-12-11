# LightGBM Excel Trading Tool - Project Plan

## 📋 Client Requirements Summary

### Project Overview
Create a no-code tool that allows traders to:
- Upload Excel/CSV files with price data and technical indicators
- Train LightGBM models automatically
- Extract human-readable trading rules (IF-THEN statements)
- View feature importance rankings

### Budget & Timeline
- **Budget**: $250 USD
- **Timeline**: 7-9 days
- **Deadline**: Must deliver working prototype ASAP

---

## 🎯 Core Deliverables

### 1. **Excel File Analyzer** ✅ (COMPLETED)
- [x] Dynamic column detection
- [x] Identify datetime, numeric, feature, and target columns
- [x] Data quality assessment
- [x] Missing data analysis
- [x] Feature/target recommendations

**File**: `excel_analyzer.py`

### 2. **LightGBM Model Trainer** (IN PROGRESS)
- [ ] Automatic feature preparation
- [ ] Target column selection
- [ ] Cross-validation (time-series aware)
- [ ] Hyperparameter configuration
- [ ] Model training with sensible defaults
- [ ] Regression vs Classification support
- [ ] Feature importance calculation

**File**: `model_trainer.py`

### 3. **Rule Extractor** (TODO)
- [ ] Extract decision paths from LightGBM trees
- [ ] Convert to IF-THEN statements
- [ ] Rank rules by importance
- [ ] Human-readable output
- [ ] Export rules to text/Excel

**File**: `rule_extractor.py`

### 4. **Flask Web Interface** (TODO)
- [ ] File upload (Excel/CSV)
- [ ] Column selection UI
- [ ] Parameter adjustment panel
- [ ] Progress indicators
- [ ] Results display (importance + rules)
- [ ] Export functionality
- [ ] Visual charts (optional)

**Files**: `app.py`, `templates/`, `static/`

### 5. **Testing & Documentation** (TODO)
- [ ] Test with client's example data
- [ ] Performance optimization (<1 minute)
- [ ] User guide
- [ ] Installation instructions

---

## 🏗️ Project Structure

```
lightgbm-trading-tool/
│
├── excel_analyzer.py          ✅ Excel file structure analyzer
├── model_trainer.py            🔄 LightGBM model training
├── rule_extractor.py           ⏳ Rule extraction from trees
├── app.py                      ⏳ Flask web interface
│
├── templates/                  ⏳ HTML templates
│   ├── index.html
│   └── results.html
│
├── static/                     ⏳ CSS/JS assets
│   ├── css/
│   └── js/
│
├── uploads/                    ⏳ Temporary file storage
├── outputs/                    ⏳ Generated results
│
├── test_analyzer.py            ✅ Test analyzer module
├── requirements.txt            ✅ Python dependencies
├── PROJECT_PLAN.md             ✅ This file
└── README.md                   ⏳ User documentation
```

---

## 🔧 Technical Specifications

### Data Flow
```
1. User uploads Excel/CSV file
   ↓
2. ExcelAnalyzer detects structure
   ↓
3. User selects target column & parameters
   ↓
4. ModelTrainer prepares data & trains LightGBM
   ↓
5. RuleExtractor generates IF-THEN rules
   ↓
6. Results displayed: Feature Importance + Trading Rules
   ↓
7. Export to Excel/PDF
```

### LightGBM Configuration
**Default Hyperparameters**:
- `num_leaves`: 31
- `learning_rate`: 0.05
- `n_estimators`: 100
- `max_depth`: -1 (no limit)
- `min_child_samples`: 20
- `subsample`: 0.8
- `colsample_bytree`: 0.8

**Adjustable by User**:
- Number of trees (50-500)
- Learning rate (0.01-0.3)
- Max depth (3-15)
- Regression vs Classification mode

### Rule Extraction Strategy
1. Extract decision paths from top N most important trees
2. Simplify complex conditions
3. Rank by:
   - Tree importance
   - Sample coverage
   - Prediction strength
4. Format as: `IF (RSI < 30 AND CallDex > 19) THEN [BUY Signal]`

### Performance Requirements
- Load & analyze file: < 5 seconds
- Train model: < 30 seconds
- Extract rules: < 10 seconds
- **Total runtime: < 1 minute** ✅

---

## 📊 Example Data Structure

### Input (Client's Example.xlsx)
```
Date/Time              | SPY Price | RSI  | CallDex | Profit Long | Profit Short
-----------------------|-----------|------|---------|-------------|-------------
11/20/2025 9:30 AM     | 672.99    | 0.00 | 18.61   | 0.66        | -0.66
11/20/2025 9:31 AM     | 673.65    | 0.00 | 18.47   | -0.08       | 0.08
...
```

**Identified Columns**:
- **Datetime**: Date/Time
- **Features**: SPY Price, RSI, CallDex
- **Targets**: Profit Long, Profit Short

### Output Example

**Feature Importance**:
```
1. RSI                  : 45.2%
2. CallDex              : 32.8%
3. SPY Price            : 22.0%
```

**Trading Rules**:
```
Rule 1 (Importance: 8.5%)
  IF RSI <= 30.5 AND CallDex > 19.0
  THEN Expected Profit: +0.34
  Coverage: 12.5% of samples

Rule 2 (Importance: 7.2%)
  IF RSI > 65.0 AND SPY Price > 660.0
  THEN Expected Profit: -0.28
  Coverage: 8.3% of samples
...
```

---

## ✅ Testing Checklist

### Phase 1: Core Functionality
- [x] Excel Analyzer works with client's data
- [ ] Model trains successfully
- [ ] Rules are extracted
- [ ] Results are accurate

### Phase 2: User Interface
- [ ] File upload works
- [ ] All parameters adjustable
- [ ] Results display correctly
- [ ] Export functions work

### Phase 3: Performance
- [ ] Full workflow < 1 minute
- [ ] Memory efficient (<500 MB)
- [ ] No crashes on large files (10K+ rows)

### Phase 4: Client Validation
- [ ] Client can run tool independently
- [ ] Results meet expectations
- [ ] Documentation is clear
- [ ] Installation is simple

---

## 🚀 Next Steps (Priority Order)

1. **✅ DONE**: Excel Analyzer Module
2. **NEXT**: LightGBM Model Trainer Module
3. **THEN**: Rule Extractor Module
4. **THEN**: Flask Web Interface (Basic)
5. **FINALLY**: Testing & Polish

---

## 📝 Notes & Considerations

### Client Feedback Integration
- Client confirmed: "Interface will allow adjusting LightGBM variables"
- Client confirmed: "Rules can use SPY, CallDex, or any indicator - nothing hardcoded"
- Client note: "Happy to pay bonus for great work" 💰

### Flexibility Requirements
- Must handle any number of feature columns
- Must handle different timeframes (1-min, 5-min, daily, etc.)
- Must work with any target column name
- Must detect column types automatically

### Windows 10/11 Compatibility
- Flask server runs locally (localhost:5000)
- No complex installation required
- Dependencies via pip install
- Option: Create .exe with PyInstaller later

---

## 💡 Future Enhancements (Post-Delivery)
- Multi-timeframe feature engineering
- Walk-forward optimization
- Backtesting module
- Live trading integration
- Model comparison (XGBoost, Random Forest)
- Advanced visualization dashboard

---

**Status**: 🔄 IN PROGRESS  
**Last Updated**: Dec 10, 2025  
**Developer**: Nations (Freelancer Project #40047202)

