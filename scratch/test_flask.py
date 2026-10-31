import sys
import json
sys.path.insert(0, 'd:/Assessment/as/backend')
from app import app

with app.test_client() as c:
    # Test accuracy - show what actually came back
    r = c.get('/api/accuracy')
    d = r.get_json()
    print('ACCURACY status:', r.status_code)
    print('success:', d.get('success'))
    summary = d.get('summary', {})
    print('summary:', json.dumps(summary, indent=2))
    data = d.get('data', [])
    print('data length:', len(data))
    daily = d.get('dailySummary', [])
    print('dailySummary length:', len(daily))
    if data:
        print('first row:', json.dumps(data[0], indent=2))
        print('last row:', json.dumps(data[-1], indent=2))
    if daily:
        print('first daily:', json.dumps(daily[0], indent=2))
