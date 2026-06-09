import urllib.request
import json
import sys

def test_endpoints():
    print("==================================================")
    print("  ARA Connection and API Diagnostics Verification")
    print("==================================================")

    endpoints = [
        {"name": "System Stats (Port 8080)", "url": "http://localhost:8080/api/system", "method": "GET"},
        {"name": "Maintenance Status (Port 8080)", "url": "http://localhost:8080/api/maintenance/status", "method": "GET"},
        {"name": "CAD Files List (Port 8000)", "url": "http://localhost:8000/api/list_files", "method": "GET"},
        {"name": "Local Execute API (Port 8000)", "url": "http://localhost:8000/api/execute", "method": "POST", "payload": {"target": "notepad"}}
    ]

    all_passed = True

    for ep in endpoints:
        print(f"Testing {ep['name']}...")
        try:
            req = urllib.request.Request(ep['url'], method=ep['method'])
            req.add_header('Content-Type', 'application/json')
            
            data = None
            if ep['method'] == 'POST' and 'payload' in ep:
                data = json.dumps(ep['payload']).encode('utf-8')
            
            # Use 10s timeout to allow for disk traversal
            with urllib.request.urlopen(req, data=data, timeout=10) as response:
                status = response.status
                body = response.read().decode('utf-8')
                
                if status == 200:
                    print(f"  [PASS] Status: {status} (Success)")
                    # Print snippet of response
                    try:
                        parsed = json.loads(body)
                        snippet = str(parsed)[:120] + "..." if len(str(parsed)) > 120 else str(parsed)
                        print(f"         Data: {snippet}")
                    except Exception:
                        print(f"         Data: {body[:120]}")
                else:
                    print(f"  [FAIL] Status: {status}")
                    all_passed = False
        except Exception as e:
            print(f"  [FAIL] Connection error: {str(e)}")
            all_passed = False
        print("-" * 50)

    if all_passed:
        print("RESULT: All local server connections and diagnostics passed successfully! [OK]")
        sys.exit(0)
    else:
        print("RESULT: Connection or API check failed. Please check running servers. [FAIL]")
        sys.exit(1)

if __name__ == '__main__':
    test_endpoints()
