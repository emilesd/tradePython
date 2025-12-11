"""
Test script for web interface file upload
"""

import requests
import json

# Create a session to maintain cookies
session = requests.Session()

# Test health endpoint
print("="*80)
print("Testing Flask Server Health...")
print("="*80)

response = session.get('http://localhost:5000/health')
print(f"Status: {response.status_code}")
print(f"Response: {response.json()}")
print()

# Test file upload
print("="*80)
print("Testing File Upload...")
print("="*80)

with open('Example.xlsx', 'rb') as f:
    files = {'file': ('Example.xlsx', f, 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet')}
    response = session.post('http://localhost:5000/upload', files=files)

print(f"Status: {response.status_code}")
if response.status_code == 200:
    data = response.json()
    print(f"\n[SUCCESS] Upload Successful!")
    print(f"\nFilename: {data['filename']}")
    print(f"Rows: {data['rows']}")
    print(f"Columns: {data['columns']}")
    print(f"\nColumn Names:")
    for col in data['column_names']:
        print(f"  • {col}")
    
    print(f"\nRecommended Features:")
    for feat in data['recommended_features']:
        print(f"  • {feat}")
    
    print(f"\nRecommended Targets:")
    for target in data['recommended_targets']:
        print(f"  • {target}")
    
    # Now test model training
    print("\n" + "="*80)
    print("Testing Model Training...")
    print("="*80)
    
    train_data = {
        'features': data['recommended_features'],
        'target': data['recommended_targets'][0],
        'task_type': 'regression',
        'n_estimators': 50,
        'learning_rate': 0.1,
        'max_depth': 5
    }
    
    response = session.post('http://localhost:5000/train', json=train_data)
    
    print(f"Status: {response.status_code}")
    if response.status_code == 200:
        result = response.json()
        print(f"\n[SUCCESS] Training Successful!")
        
        print(f"\n[IMPORTANCE] Feature Importance:")
        for feat in result['feature_importance'][:3]:
            print(f"  • {feat['feature']}: {feat['importance_pct']:.1f}%")
        
        print(f"\n[SIGNALS] Trading Signals ({len(result['trading_signals'])} total):")
        for signal in result['trading_signals'][:3]:
            print(f"\n  Signal #{signal['rule_number']}: {signal['Signal']}")
            print(f"  Condition: {signal['Condition']}")
            print(f"  Coverage: {signal['Coverage_%']}% | Confidence: {signal['Confidence']}")
        
        print(f"\n[FILES] Generated Files:")
        print(f"  • {result['importance_file']}")
        print(f"  • {result['signals_file']}")
        
        print("\n" + "="*80)
        print("[SUCCESS] WEB INTERFACE TEST COMPLETED SUCCESSFULLY!")
        print("="*80)
    else:
        print(f"[ERROR] Training Error: {response.json()}")
else:
    print(f"[ERROR] Upload Error: {response.json()}")

