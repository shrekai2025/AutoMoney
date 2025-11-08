"""测试前端API集成 - 模拟前端调用"""

import asyncio
import sys
sys.path.insert(0, '/Users/uniteyoo/Documents/AutoMoney/AMbackend')

import httpx
import json

BASE_URL = "http://localhost:8000"

async def test_frontend_api_integration():
    """测试前端API集成"""

    print("=" * 100)
    print("🧪 测试前端API集成")
    print("=" * 100)
    print()

    # 先登录获取token
    print("1️⃣ 登录获取token...")
    async with httpx.AsyncClient() as client:
        # 登录
        login_response = await client.post(
            f"{BASE_URL}/api/v1/auth/login",
            data={
                "username": "admin",
                "password": "admin123",
            }
        )

        if login_response.status_code != 200:
            print(f"❌ 登录失败: {login_response.status_code}")
            print(f"   响应: {login_response.text}")
            return

        token = login_response.json()["access_token"]
        print(f"✅ 登录成功，获取到token")
        print()

        # 设置请求头
        headers = {
            "Authorization": f"Bearer {token}",
            "Content-Type": "application/json",
        }

        # 2. 获取策略列表
        print("2️⃣ 获取Admin策略列表...")
        admin_response = await client.get(
            f"{BASE_URL}/api/v1/admin/strategies",
            headers=headers,
        )

        if admin_response.status_code != 200:
            print(f"❌ 获取策略列表失败: {admin_response.status_code}")
            print(f"   响应: {admin_response.text}")
            return

        strategies = admin_response.json()["strategies"]
        if not strategies:
            print("❌ 没有找到策略")
            return

        portfolio_id = strategies[0]["id"]
        print(f"✅ 找到策略: {strategies[0]['name']} (ID: {portfolio_id})")
        print()

        # 3. 获取当前阈值配置
        print("3️⃣ 获取策略详情（包含当前阈值）...")
        detail_response = await client.get(
            f"{BASE_URL}/api/v1/marketplace/{portfolio_id}",
            headers=headers,
        )

        if detail_response.status_code != 200:
            print(f"❌ 获取策略详情失败: {detail_response.status_code}")
            return

        detail = detail_response.json()
        print(f"✅ 当前阈值配置:")
        print(f"   Fear & Greed 熔断阈值: {detail.get('fg_circuit_breaker_threshold', 'N/A')}")
        print(f"   Fear & Greed 仓位调整阈值: {detail.get('fg_position_adjust_threshold', 'N/A')}")
        print(f"   买入阈值: {detail.get('buy_threshold', 'N/A')}")
        print(f"   部分减仓阈值: {detail.get('partial_sell_threshold', 'N/A')}")
        print(f"   全部清仓阈值: {detail.get('full_sell_threshold', 'N/A')}")
        print()

        # 4. 测试更新阈值（模拟前端PATCH请求）
        print("4️⃣ 更新交易阈值...")

        new_thresholds = {
            "fg_circuit_breaker_threshold": 18,
            "fg_position_adjust_threshold": 28,
            "buy_threshold": 52,
            "partial_sell_threshold": 51,
            "full_sell_threshold": 46,
        }

        # 构造查询参数
        params = {
            "fg_circuit_breaker_threshold": new_thresholds["fg_circuit_breaker_threshold"],
            "fg_position_adjust_threshold": new_thresholds["fg_position_adjust_threshold"],
            "buy_threshold": new_thresholds["buy_threshold"],
            "partial_sell_threshold": new_thresholds["partial_sell_threshold"],
            "full_sell_threshold": new_thresholds["full_sell_threshold"],
        }

        update_response = await client.patch(
            f"{BASE_URL}/api/v1/marketplace/{portfolio_id}/settings",
            headers=headers,
            params=params,
            json={},  # body为空，因为阈值通过query参数传递
        )

        if update_response.status_code != 200:
            print(f"❌ 更新失败: {update_response.status_code}")
            print(f"   响应: {update_response.text}")
            return

        update_result = update_response.json()
        print(f"✅ 更新成功！")
        print(f"   返回消息: {update_result.get('message', 'N/A')}")
        print(f"   更新的字段: {update_result.get('updated_fields', [])}")
        print()

        # 5. 验证更新
        print("5️⃣ 验证更新后的阈值...")
        verify_response = await client.get(
            f"{BASE_URL}/api/v1/marketplace/{portfolio_id}",
            headers=headers,
        )

        if verify_response.status_code != 200:
            print(f"❌ 验证失败: {verify_response.status_code}")
            return

        verify_detail = verify_response.json()

        all_correct = True
        for field, expected_value in new_thresholds.items():
            actual_value = verify_detail.get(field)
            if actual_value == expected_value:
                print(f"   ✅ {field}: {actual_value}")
            else:
                print(f"   ❌ {field}: {actual_value} (期望: {expected_value})")
                all_correct = False

        if all_correct:
            print("\n✅ 所有阈值更新验证通过！")
        else:
            print("\n❌ 部分阈值更新失败")

        print()

        # 6. 恢复默认值
        print("6️⃣ 恢复默认值...")
        default_params = {
            "fg_circuit_breaker_threshold": 20,
            "fg_position_adjust_threshold": 30,
            "buy_threshold": 50,
            "partial_sell_threshold": 50,
            "full_sell_threshold": 45,
        }

        restore_response = await client.patch(
            f"{BASE_URL}/api/v1/marketplace/{portfolio_id}/settings",
            headers=headers,
            params=default_params,
            json={},
        )

        if restore_response.status_code != 200:
            print(f"❌ 恢复失败: {restore_response.status_code}")
            return

        print("✅ 已恢复默认值")
        print()

        # 7. 测试边界值验证
        print("7️⃣ 测试边界值验证...")

        # 测试超出范围的值（应该被拒绝）
        invalid_params = {
            "buy_threshold": 150,  # 超过100
        }

        invalid_response = await client.patch(
            f"{BASE_URL}/api/v1/marketplace/{portfolio_id}/settings",
            headers=headers,
            params=invalid_params,
            json={},
        )

        if invalid_response.status_code == 422:  # Unprocessable Entity
            print(f"   ✅ 正确拒绝了超出范围的值 (buy_threshold=150)")
        else:
            print(f"   ❌ 应该拒绝超出范围的值，但状态码为: {invalid_response.status_code}")

        # 测试负值（应该被拒绝）
        negative_params = {
            "fg_circuit_breaker_threshold": -5,
        }

        negative_response = await client.patch(
            f"{BASE_URL}/api/v1/marketplace/{portfolio_id}/settings",
            headers=headers,
            params=negative_params,
            json={},
        )

        if negative_response.status_code == 422:
            print(f"   ✅ 正确拒绝了负值 (fg_circuit_breaker_threshold=-5)")
        else:
            print(f"   ❌ 应该拒绝负值，但状态码为: {negative_response.status_code}")

        print()

    print("=" * 100)
    print("🎉 前端API集成测试完成！")
    print("=" * 100)

if __name__ == "__main__":
    asyncio.run(test_frontend_api_integration())
