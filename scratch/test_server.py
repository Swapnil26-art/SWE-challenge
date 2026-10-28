import time, requests, sys
time.sleep(2)
try:
    r = requests.get('http://127.0.0.1:5000/')
    print('Root status', r.status_code)
    print('Root snippet', r.text[:200])
    r2 = requests.get('http://127.0.0.1:5000/api/actuals')
    print('Actuals status', r2.status_code)
    print('Actuals snippet', r2.text[:200])
    r3 = requests.get('http://127.0.0.1:5000/api/forecasts')
    print('Forecasts status', r3.status_code)
    print('Forecasts snippet', r3.text[:200])
    r4 = requests.get('http://127.0.0.1:5000/api/accuracy')
    print('Accuracy status', r4.status_code)
    print('Accuracy snippet', r4.text[:200])
except Exception as e:
    print('Error', e)
