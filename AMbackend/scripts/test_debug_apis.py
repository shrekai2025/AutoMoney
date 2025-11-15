#!/usr/bin/env python3
"""测试Debug相关API功能"""

import asyncio
import sys
from pathlib import Path

# 添加项目根目录到路径
sys.path.insert(0, str(Path(__file__).parent.parent))

from app.db.session import AsyncSessionLocal
from app.services.monitoring.error_tracker import error_tracker
from app.models.system_error import SystemError
from sqlalchemy import select


async def test_error_tracker():
    """测试错误追踪服务"""
    print("=" * 60)
    print("测试错误追踪服务")
    print("=" * 60)
    
    async with AsyncSessionLocal() as db:
        # 1. 测试获取错误摘要
        print("\n1. 测试获取错误摘要...")
        try:
            summary = await error_tracker.get_error_summary(db)
            print(f"✅ 错误摘要获取成功:")
            print(f"   - 总错误数: {summary.get('total_errors', 0)}")
            print(f"   - 未解决错误: {summary.get('unresolved_errors', 0)}")
            print(f"   - Critical: {summary.get('critical_count', 0)}")
            print(f"   - Error: {summary.get('error_count', 0)}")
            print(f"   - Warning: {summary.get('warning_count', 0)}")
        except Exception as e:
            print(f"❌ 获取错误摘要失败: {e}")
            import traceback
            traceback.print_exc()
        
        # 2. 测试获取最近错误
        print("\n2. 测试获取最近错误...")
        try:
            errors = await error_tracker.get_recent_errors(
                db=db,
                limit=10,
                unresolved_only=True,
            )
            print(f"✅ 获取最近错误成功: {len(errors)} 条")
            for i, error in enumerate(errors[:3], 1):
                print(f"   错误 {i}:")
                print(f"     - ID: {error.id}")
                print(f"     - 类型: {error.error_type}")
                print(f"     - 严重程度: {error.severity}")
                print(f"     - 组件: {error.component}")
                print(f"     - 消息: {error.error_message[:50]}...")
        except Exception as e:
            print(f"❌ 获取最近错误失败: {e}")
            import traceback
            traceback.print_exc()
        
        # 3. 测试数据库表结构
        print("\n3. 测试数据库表结构...")
        try:
            result = await db.execute(select(SystemError).limit(1))
            first_error = result.scalar_one_or_none()
            if first_error:
                print(f"✅ 表结构正常，示例字段:")
                print(f"   - id: {first_error.id}")
                print(f"   - error_type: {first_error.error_type}")
                print(f"   - severity: {first_error.severity}")
                print(f"   - component: {first_error.component}")
                print(f"   - is_resolved: {first_error.is_resolved}")
            else:
                print("ℹ️  表中暂无错误记录（这是正常的）")
        except Exception as e:
            print(f"❌ 表结构检查失败: {e}")
            import traceback
            traceback.print_exc()


async def test_log_file_parsing():
    """测试日志文件解析"""
    print("\n" + "=" * 60)
    print("测试日志文件解析")
    print("=" * 60)
    
    from app.api.v1.endpoints.admin import _parse_log_line
    
    test_lines = [
        "2025-11-14 10:00:00,123 INFO sqlalchemy.engine.Engine BEGIN (implicit)",
        "2025-11-14 10:00:01,456 ERROR app.services.data_collectors.manager: Failed to collect data",
        "2025-11-14 10:00:02,789 WARNING app.services.strategy.scheduler: Strategy execution delayed",
        "CRITICAL: System failure detected",
        "INFO: Server started",
    ]
    
    print("\n测试日志行解析:")
    for line in test_lines:
        entry = _parse_log_line(line)
        if entry:
            print(f"✅ 解析成功: {entry.level} - {entry.message[:50]}")
        else:
            print(f"⚠️  解析失败: {line[:50]}")


async def main():
    """主函数"""
    print("\n" + "=" * 60)
    print("Debug功能全面测试")
    print("=" * 60)
    
    await test_error_tracker()
    await test_log_file_parsing()
    
    print("\n" + "=" * 60)
    print("测试完成")
    print("=" * 60)


if __name__ == "__main__":
    asyncio.run(main())


