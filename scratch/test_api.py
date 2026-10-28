import requests, json, time
url='http://127.0.0.1:5000/api/actuals'
try:
    r=requests.get(url, timeout=10)
    print('status', r.status_code)
    print(r.text[:200])
except Exception as e:
    print('error', e)
