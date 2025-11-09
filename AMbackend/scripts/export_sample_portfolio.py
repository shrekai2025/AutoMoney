"""
导出示例策略数据
用于在远程服务器上创建测试策略
"""
import json

# 示例策略数据
sample_portfolios = [
    {
        "name": "稳健型BTC策略",
        "strategy_name": "Conservative BTC Strategy",
        "initial_balance": "10000.00000000",
        "current_balance": "10000.00000000",
        "total_value": "10000.00000000",
        "initial_btc_amount": "0.10000000",
        "is_active": True,
        "rebalance_period_minutes": 30,

        # Agent权重配置
        "agent_weights": {
            "macro": 0.40,
            "onchain": 0.40,
            "ta": 0.20
        },

        # 连续信号配置
        "consecutive_signal_threshold": 30,
        "acceleration_multiplier_min": 1.1,
        "acceleration_multiplier_max": 2.0,

        # 交易阈值配置
        "fg_circuit_breaker_threshold": 20,
        "fg_position_adjust_threshold": 30,
        "buy_threshold": 55.0,
        "partial_sell_threshold": 50.0,
        "full_sell_threshold": 45.0,
    },
    {
        "name": "激进型BTC策略",
        "strategy_name": "Aggressive BTC Strategy",
        "initial_balance": "10000.00000000",
        "current_balance": "10000.00000000",
        "total_value": "10000.00000000",
        "initial_btc_amount": "0.10000000",
        "is_active": False,
        "rebalance_period_minutes": 15,

        # Agent权重配置
        "agent_weights": {
            "macro": 0.25,
            "onchain": 0.50,
            "ta": 0.25
        },

        # 连续信号配置
        "consecutive_signal_threshold": 20,
        "acceleration_multiplier_min": 1.2,
        "acceleration_multiplier_max": 2.5,

        # 交易阈值配置
        "fg_circuit_breaker_threshold": 15,
        "fg_position_adjust_threshold": 25,
        "buy_threshold": 50.0,
        "partial_sell_threshold": 48.0,
        "full_sell_threshold": 42.0,
    },
]

if __name__ == "__main__":
    # 导出为JSON文件
    output_file = "sample_portfolios.json"
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(sample_portfolios, f, indent=2, ensure_ascii=False)

    print(f"✅ 示例策略数据已导出到: {output_file}")
    print(f"   共 {len(sample_portfolios)} 个策略")
