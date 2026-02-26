import requests
import json

url = 'http://splunk:8088/services/collector/event/1.0'
headers = {
    'Authorization': 'Splunk 1ae86e64-87f7-4011-b97f-74bf2621bfb7',
    'Content-Type': 'application/json'
}
payload = {
    'event': {'msg': 'test from container'},
    'source': 'ai-agent',
    'sourcetype': '_json',
    'index': 'main'
}

try:
    r = requests.post(url, json=payload, headers=headers, timeout=5)
    print(f'Status: {r.status_code}')
    print(f'Response: {r.text}')
except Exception as e:
    print(f'Error: {e}')
