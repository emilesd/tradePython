"""
Simulate exactly what the browser does - upload then train
"""

import urllib.request
import urllib.parse
import json
import http.cookiejar
import time

print("="*80)
print("Simulating Browser Workflow")
print("="*80)

# Create cookie jar to maintain session (like browser)
cookie_jar = http.cookiejar.CookieJar()
opener = urllib.request.build_opener(urllib.request.HTTPCookieProcessor(cookie_jar))
urllib.request.install_opener(opener)

time.sleep(2)

# Step 1: Load homepage (establish session)
print("\n[1] Loading homepage...")
try:
    response = opener.open('http://localhost:5000/')
    print(f"    [OK] Homepage loaded, status: {response.status}")
    print(f"    Cookies: {len(cookie_jar)} cookie(s) set")
except Exception as e:
    print(f"    [ERROR] {e}")
    exit(1)

# Step 2: Upload file
print("\n[2] Uploading Example.xlsx...")
try:
    with open('Example.xlsx', 'rb') as f:
        file_data = f.read()
    
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
        headers={'Content-Type': f'multipart/form-data; boundary={boundary}'}
    )
    
    response = opener.open(req)
    upload_data = json.loads(response.read().decode('utf-8'))
    
    print(f"    [OK] Upload successful!")
    print(f"    Features: {upload_data['recommended_features']}")
    print(f"    Targets: {upload_data['recommended_targets']}")
    print(f"    Cookies after upload: {len(cookie_jar)} cookie(s)")
    
except Exception as e:
    print(f"    [ERROR] {e}")
    import traceback
    traceback.print_exc()
    exit(1)

# Step 3: Train model (exactly like browser JavaScript)
print("\n[3] Training model (simulating browser fetch)...")
try:
    train_params = {
        'features': upload_data['recommended_features'],
        'target': upload_data['recommended_targets'][0],
        'task_type': 'regression',
        'n_estimators': 100,  # Browser default
        'learning_rate': 0.05,  # Browser default
        'max_depth': 5  # Browser default
    }
    
    print(f"    Parameters (browser defaults):")
    print(f"      Features: {train_params['features']}")
    print(f"      Target: {train_params['target']}")
    print(f"      n_estimators: {train_params['n_estimators']}")
    print(f"      learning_rate: {train_params['learning_rate']}")
    print(f"      max_depth: {train_params['max_depth']}")
    
    body = json.dumps(train_params).encode('utf-8')
    
    req = urllib.request.Request(
        'http://localhost:5000/train',
        data=body,
        headers={'Content-Type': 'application/json'},
        method='POST'
    )
    
    print(f"\n    Sending request to /train...")
    print(f"    (Using session cookies from upload)")
    
    try:
        response = opener.open(req)
        response_text = response.read().decode('utf-8')
        
        print(f"\n    [OK] Response received!")
        print(f"    Status: {response.status}")
        print(f"    Content-Type: {response.headers.get('Content-Type')}")
        print(f"    Response length: {len(response_text)} chars")
        
        # Try to parse as JSON
        train_data = json.loads(response_text)
        
        print(f"\n    [SUCCESS] Training completed!")
        print(f"      Signals: {len(train_data['trading_signals'])}")
        print(f"      Test RMSE: {train_data['model_performance']['test_metrics']['rmse']:.4f}")
        
        print(f"\n    First signal:")
        first_signal = train_data['trading_signals'][0]
        print(f"      {first_signal['Signal']}: {first_signal['Condition']}")
        print(f"      Coverage: {first_signal['Coverage_%']}%")
        print(f"      Expected: {first_signal['Expected_Profit']:+.4f}")
        
    except urllib.error.HTTPError as e:
        print(f"\n    [ERROR] HTTP {e.code} {e.reason}")
        error_body = e.read().decode('utf-8')
        
        print(f"\n    Response body (first 500 chars):")
        print(f"    {error_body[:500]}")
        
        if error_body.strip().startswith('<'):
            print(f"\n    *** THIS IS THE PROBLEM ***")
            print(f"    Server returned HTML instead of JSON!")
            print(f"    This means Flask hit an unhandled exception.")
            print(f"\n    Check the Flask terminal for error details.")
            
            # Save full error to file
            with open('flask_error_response.html', 'w', encoding='utf-8') as f:
                f.write(error_body)
            print(f"\n    Full error saved to: flask_error_response.html")
        else:
            try:
                error_json = json.loads(error_body)
                print(f"\n    JSON error:")
                print(f"      Error: {error_json.get('error', 'Unknown')}")
            except:
                pass
                
except Exception as e:
    print(f"    [ERROR] {e}")
    import traceback
    traceback.print_exc()

print("\n" + "="*80)
print("Test completed")
print("="*80)

