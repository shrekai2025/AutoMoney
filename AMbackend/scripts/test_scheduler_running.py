"""测试调度器是否在运行"""
import requests
import time

print("=" * 80)
print("测试调度器运行状态")
print("=" * 80)

# 检查后端健康
try:
    response = requests.get("http://localhost:8000/health", timeout=5)
    print(f"✅ 后端服务正常: {response.status_code}")
except Exception as e:
    print(f"❌ 后端服务异常: {e}")
    exit(1)

print("\n等待观察调度器任务...")
print("如果调度器正常，应该看到:")
print("  1. 市场数据采集 (每30秒)")
print("  2. 策略执行 (每12分钟)")
print("\n请查看后端日志 tail -f /Users/uniteyoo/Documents/AutoMoney/.pids/backend.log")
print("\n监控数据库中的最新执行记录...")

import psycopg2
import datetime

conn = psycopg2.connect(
    host="localhost",
    database="automoney",
    user="uniteyoo",
    password=None
)

cur = conn.cursor()

# 记录当前时间和最后执行时间
cur.execute("""
    SELECT MAX(execution_time) as last_exec, NOW() as now
    FROM strategy_executions
    WHERE portfolio_id = '867ca89a-2100-401a-bf31-8fcb6862f1ee'
""")
last_exec, now = cur.fetchone()

print(f"\n当前时间: {now}")
print(f"上次执行: {last_exec}")
if last_exec:
    time_diff = now - last_exec
    print(f"距离上次执行: {time_diff}")

print("\n✅ 系统状态检查完成")
print("建议: 等待12分钟，然后再次查询数据库确认是否有新执行记录")

cur.close()
conn.close()
