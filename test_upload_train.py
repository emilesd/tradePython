"""
Simple test using built-in urllib (no external dependencies)
"""

import urllib.request
import urllib.parse
import json
import os
import time

print("="*80)
print("Testing Flask API with Example.xlsx")
print("="*80)

# Wait for server
time.sleep(2)

# Test 1: Health check
print("\n[1] Health check...")
try:
    response = urllib.request.urlopen('http://localhost:5000/health')
    data = json.loads(response.read().decode('utf-8'))
    print(f"    [OK] Server is running: {data['message']}")
except Exception as e:
    print(f"    [ERROR] Server not responding: {e}")
    print("    Please make sure 'python app.py' is running!")
    exit(1)

# Test 2: Upload file
print("\n[2] Uploading Example.xlsx...")
try:
    # Read file
    with open('Example.xlsx', 'rb') as f:
        file_data = f.read()
    
    # Create multipart form data manually
    boundary = '----WebKitFormBoundary7MA4YWxkTrZu0gW'
    body = (
        f'--{boundary}\r\n'
        'Content-Disposition: form-data; name="file"; filename="Example.xlsx"\r\n'
        'Content-Type: application/vnd.openxmlformats-officedocument.spreadsheetml.sheet\r\n'
        '\r\n'
    ).encode('utf-8')
    body += file_data
    body += f'\r\n--{boundary}--\r\n'.encode('utf-8')
    
    req = urllib.request.Request(
        'http://localhost:5000/upload',
        data=body,
        headers={
            'Content-Type': f'multipart/form-data; boundary={boundary}'
        }
    )
    
    response = urllib.request.urlopen(req)
    upload_data = json.loads(response.read().decode('utf-8'))
    
    print(f"    [OK] Upload successful!")
    print(f"      Filename: {upload_data['filename']}")
    print(f"      Rows: {upload_data['rows']}")
    print(f"      Columns: {upload_data['columns']}")
    print(f"      Features: {upload_data['recommended_features']}")
    print(f"      Targets: {upload_data['recommended_targets']}")
    
    # Extract cookie for session
    cookies = response.getheader('Set-Cookie')
    
except Exception as e:
    print(f"    [ERROR] Upload failed: {e}")
    import traceback
    traceback.print_exc()
    exit(1)

# Test 3: Train model
print("\n[3] Training model...")
try:
    train_params = {
        'features': upload_data['recommended_features'],
        'target': upload_data['recommended_targets'][0],
        'task_type': 'regression',
        'n_estimators': 50,
        'learning_rate': 0.1,
        'max_depth': 5
    }
    
    print(f"    Parameters:")
    print(f"      Features: {train_params['features']}")
    print(f"      Target: {train_params['target']}")
    
    body = json.dumps(train_params).encode('utf-8')
    
    headers = {
        'Content-Type': 'application/json',
    }
    if cookies:
        headers['Cookie'] = cookies.split(';')[0]  # Use session cookie
    
    req = urllib.request.Request(
        'http://localhost:5000/train',
        data=body,
        headers=headers,
        method='POST'
    )
    
    print(f"    Training... (this takes 5-10 seconds)")
    response = urllib.request.urlopen(req)
    train_data = json.loads(response.read().decode('utf-8'))
    
    print(f"\n    [OK] Training successful!")
    print(f"      Feature importance: {len(train_data['feature_importance'])} features")
    print(f"      Trading signals: {len(train_data['trading_signals'])} signals")
    print(f"      Task type: {train_data['model_performance']['task_type']}")
    print(f"      Test RMSE: {train_data['model_performance']['test_metrics']['rmse']:.4f}")
    
    print(f"\n    Top 3 Signals:")
    for i, signal in enumerate(train_data['trading_signals'][:3], 1):
        print(f"      {i}. {signal['Signal']}: {signal['Condition']}")
        print(f"         Coverage: {signal['Coverage_%']}%, Expected: {signal['Expected_Profit']:+.4f}")
    
    print(f"\n    Generated files:")
    print(f"      • {train_data['importance_file']}")
    print(f"      • {train_data['signals_file']}")

except urllib.error.HTTPError as e:
    print(f"    [ERROR] Training failed with HTTP {e.code}")
    error_body = e.read().decode('utf-8')
    print(f"    Response body (first 500 chars):")
    print(f"    {error_body[:500]}")
    
    # Check if it's HTML or JSON
    if error_body.strip().startswith('<'):
        print(f"\n    [WARNING] ERROR: Server returned HTML instead of JSON!")
        print(f"    This suggests an unhandled exception in Flask.")
        print(f"\n    Check the Flask server terminal for the full error trace.")
    else:
        try:
            error_json = json.loads(error_body)
            print(f"\n    Error message: {error_json.get('error', 'Unknown')}")
            if 'details' in error_json:
                print(f"    Details: {error_json['details']}")
        except:
            print(f"\n    Could not parse error as JSON")
    
except Exception as e:
    print(f"    [ERROR] Training failed: {e}")
    import traceback
    traceback.print_exc()

print("\n" + "="*80)
print("Test completed")
print("="*80)

