import sys
sys.path.append('d:/Assessment/as/backend')
from app import app
with app.test_client() as client:
    resp = client.get('/api/actuals')
    print('Actuals status', resp.status_code)
    print('Actuals body', resp.get_data(as_text=True)[:200])
    resp2 = client.get('/api/forecasts')
    print('Forecasts status', resp2.status_code)
    print('Forecasts body', resp2.get_data(as_text=True)[:200])
    resp3 = client.get('/api/accuracy')
    print('Accuracy status', resp3.status_code)
    print('Accuracy body', resp3.get_data(as_text=True)[:200])
