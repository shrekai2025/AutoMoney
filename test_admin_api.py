#!/usr/bin/env python3
"""测试 Admin API 返回 agent_weights"""

import requests
import json

# 获取管理员 token (从数据库获取)
import psycopg2

conn = psycopg2.connect("dbname=automoney")
cur = conn.cursor()
cur.execute("SELECT google_id FROM \"user\" WHERE role = 'admin' LIMIT 1")
admin_uid = cur.fetchone()
if admin_uid:
    admin_uid = admin_uid[0]
    print(f"Admin Google ID: {admin_uid}")
else:
    print("No admin user found")
    exit(1)
cur.close()
conn.close()

# 测试 Admin API
url = "http://localhost:8000/api/v1/admin/strategies"
headers = {
    "Authorization": f"Bearer {admin_uid}"
}

print(f"\nTesting Admin API: {url}")
response = requests.get(url, headers=headers)
print(f"Status Code: {response.status_code}")

if response.status_code == 200:
    data = response.json()
    print(f"\nTotal strategies: {data.get('total', 0)}")

    for strategy in data.get('strategies', []):
        print(f"\n{'='*60}")
        print(f"Strategy: {strategy['name']}")
        print(f"ID: {strategy['id']}")
        print(f"Rebalance Period: {strategy.get('rebalance_period_minutes')} minutes")
        print(f"Agent Weights: {strategy.get('agent_weights')}")
        print(f"Consecutive Signal Threshold: {strategy.get('consecutive_signal_threshold')}")
        print(f"Acceleration Multiplier Min: {strategy.get('acceleration_multiplier_min')}")
        print(f"Acceleration Multiplier Max: {strategy.get('acceleration_multiplier_max')}")
else:
    print(f"Error: {response.text}")
