"""集成测试 - 动量策略端到端测试"""

import pytest
import asyncio
from unittest.mock import Mock, AsyncMock, patch
from decimal import Decimal

from app.services.data_collectors.momentum_data_service import MomentumDataService
from app.agents.regime_filter_agent import RegimeFilterAgent
from app.agents.ta_momentum_agent import TAMomentumAgent
from app.decision_agents.momentum_regime_decision import MomentumRegimeDecision, OCOOrder
from app.services.trading.oco_order_manager import OCOOrderManager


class TestMomentumDataService:
    """测试数据采集服务"""
    
    @pytest.mark.asyncio
    async def test_data_collection_structure(self):
        """测试数据采集返回的结构"""
        service = MomentumDataService()
        
        # Mock API调用  
        with patch.object(service.binance_spot, 'get_ohlcv', new_callable=AsyncMock) as mock_ohlcv, \
             patch.object(service.binance_spot, 'get_current_price', new_callable=AsyncMock) as mock_price, \
             patch.object(service.binance_futures, 'get_funding_rate', new_callable=AsyncMock) as mock_fr, \
             patch.object(service.binance_futures, 'get_open_interest', new_callable=AsyncMock) as mock_oi, \
             patch.object(service.binance_futures, 'get_futures_premium', new_callable=AsyncMock) as mock_premium:
            
            # 设置mock返回值
            mock_ohlcv.return_value = [[1699900000000, 43000, 43100, 42900, 43050, 100] for _ in range(100)]
            mock_price.return_value = {"price": 43050.0, "change_24h": 2.5}
            mock_fr.return_value = {"current_funding_rate": 0.0001, "next_funding_time": "2025-11-13T16:00:00"}
            mock_oi.return_value = {"open_interest": 1000000, "change_24h": 5.2}
            mock_premium.return_value = {"premium_rate": 0.5, "spot_price": 43000, "futures_price": 43215}
            
            data = await service.collect_all_data()
            
            # 验证数据结构
            assert "macro" in data
            assert "sentiment" in data
            assert "assets" in data
            assert "onchain" in data
            
            # 验证资产数据
            assert "BTC" in data["assets"]
            assert "ETH" in data["assets"]
            assert "SOL" in data["assets"]
            
            # 验证BTC数据字段
            btc_data = data["assets"]["BTC"]
            assert "current_price" in btc_data
            assert "ohlcv_15m" in btc_data
            assert "ohlcv_60m" in btc_data


class TestRegimeFilterAgent:
    """测试市场制度过滤器"""
    
    @pytest.mark.asyncio
    async def test_regime_score_calculation(self):
        """测试Regime Score计算"""
        agent = RegimeFilterAgent()
        
        # 构造测试数据
        market_data = {
            "macro": {
                "dxy": 105.0,
                "fed_rate": 4.5,
            },
            "sentiment": {
                "fear_greed_value": 45,
                "fear_greed_classification": "Neutral"
            },
            "assets": {
                "BTC": {
                    "funding_rate": 0.0002,
                    "open_interest_change_24h": 3.5,
                    "futures_premium": 0.3
                }
            },
            "onchain": {
                "btc_mvrv_zscore": 1.5
            }
        }
        
        # Mock LLM调用
        with patch('app.services.llm.manager.llm_manager.chat_for_agent', new_callable=AsyncMock) as mock_llm:
            mock_llm.return_value = Mock(content='{"regime_score": 55.0, "regime_classification": "NEUTRAL", "confidence": 0.75, "reasoning": "Test", "component_scores": {}, "key_factors": [], "risk_level": "MEDIUM", "recommended_multiplier": 1.0}')
            
            result = await agent.analyze(market_data)
            
            # 验证输出
            assert "regime_score" in result
            assert 0 <= result["regime_score"] <= 100
            assert "regime_classification" in result
            assert "confidence" in result
            assert "recommended_multiplier" in result
            assert 0.3 <= result["recommended_multiplier"] <= 1.6


class TestTAMomentumAgent:
    """测试技术动量分析Agent"""
    
    @pytest.mark.asyncio
    async def test_technical_analysis(self):
        """测试技术分析"""
        agent = TAMomentumAgent()
        
        # 构造测试数据（模拟上涨趋势）
        prices = [42000 + i * 50 for i in range(100)]  # 上涨趋势
        ohlcv = [[i, p-20, p+30, p-25, p, 100] for i, p in enumerate(prices)]
        
        market_data = {
            "assets": {
                "BTC": {
                    "current_price": 47000.0,
                    "price_change_24h": 5.0,
                    "ohlcv_15m": ohlcv,
                    "ohlcv_60m": ohlcv,
                    "funding_rate": 0.0001
                },
                "ETH": {
                    "current_price": 2500.0,
                    "price_change_24h": 3.0,
                    "ohlcv_15m": ohlcv[:80],
                    "ohlcv_60m": ohlcv[:80],
                    "funding_rate": 0.0001
                },
                "SOL": {
                    "current_price": 50.0,
                    "price_change_24h": 1.0,
                    "ohlcv_15m": ohlcv[:60],
                    "ohlcv_60m": ohlcv[:60],
                    "funding_rate": 0.0001
                }
            }
        }
        
        # Mock LLM调用
        with patch('app.services.llm.manager.llm_manager.chat_for_agent', new_callable=AsyncMock) as mock_llm:
            mock_llm.return_value = Mock(content='''{
                "asset_analyses": {
                    "BTC": {
                        "signal": "LONG",
                        "signal_strength": 0.8,
                        "confidence": 0.75,
                        "entry_price": 47000.0,
                        "stop_loss_distance_atr": 2.0,
                        "take_profit_rr": 2.5,
                        "reasoning": "Strong uptrend",
                        "technical_scores": {"trend": 0.8, "momentum": 0.9, "timing": 0.7, "risk": 0.6},
                        "timeframe_alignment": 0.85
                    },
                    "ETH": {"signal": "NEUTRAL", "signal_strength": 0.3, "confidence": 0.5},
                    "SOL": {"signal": "NEUTRAL", "signal_strength": 0.2, "confidence": 0.4}
                },
                "best_opportunity": {
                    "asset": "BTC",
                    "signal": "LONG",
                    "signal_strength": 0.8,
                    "confidence": 0.75,
                    "reasoning": "BTC shows strongest momentum"
                },
                "overall_momentum_strength": 0.6,
                "market_trend": "UPTREND",
                "reasoning": "BTC leading the market higher"
            }''')
            
            result = await agent.analyze(market_data)
            
            # 验证输出
            assert "asset_analyses" in result
            assert "BTC" in result["asset_analyses"]
            assert "best_opportunity" in result
            assert result["best_opportunity"] is not None
            assert result["best_opportunity"]["asset"] == "BTC"


class TestMomentumRegimeDecision:
    """测试决策引擎"""
    
    def test_oco_order_validation(self):
        """测试OCO订单验证"""
        # 测试有效的做多订单
        oco_long = OCOOrder(
            asset="BTC",
            side="LONG",
            entry_price=43000.0,
            entry_amount=0.1,
            stop_loss_price=42000.0,  # 低于入场价
            take_profit_price=45000.0,  # 高于入场价
            leverage=3.0
        )
        
        is_valid, errors = oco_long.validate()
        assert is_valid, f"Valid LONG order failed validation: {errors}"
        
        # 测试有效的做空订单
        oco_short = OCOOrder(
            asset="BTC",
            side="SHORT",
            entry_price=43000.0,
            entry_amount=0.1,
            stop_loss_price=44000.0,  # 高于入场价
            take_profit_price=41000.0,  # 低于入场价
            leverage=3.0
        )
        
        is_valid, errors = oco_short.validate()
        assert is_valid, f"Valid SHORT order failed validation: {errors}"
        
        # 测试无效订单：做多但止损高于入场价
        oco_invalid = OCOOrder(
            asset="BTC",
            side="LONG",
            entry_price=43000.0,
            entry_amount=0.1,
            stop_loss_price=44000.0,  # 错误：高于入场价
            take_profit_price=45000.0,
            leverage=3.0
        )
        
        is_valid, errors = oco_invalid.validate()
        assert not is_valid
        assert len(errors) > 0
    
    def test_regime_multiplier_calculation(self):
        """测试Regime乘数计算"""
        decision_engine = MomentumRegimeDecision()
        
        # 测试不同Regime Score的乘数
        test_cases = [
            (10, 0.3),   # 极度危险
            (25, 0.45),  # 危险边缘
            (50, 0.8),   # 中性
            (75, 1.15),  # 健康
            (90, 1.5),   # 极度健康
        ]
        
        for regime_score, expected_range_min in test_cases:
            multiplier = decision_engine._calculate_regime_multiplier(regime_score)
            assert 0.3 <= multiplier <= 1.6, f"Multiplier {multiplier} out of range for score {regime_score}"
            assert multiplier >= expected_range_min - 0.1, f"Multiplier {multiplier} too low for score {regime_score}"
    
    def test_extreme_counter_trend_filter(self):
        """测试极端逆势过滤"""
        decision_engine = MomentumRegimeDecision()
        
        # 极低Regime Score + 做多信号 = 应该被拒绝
        ta_decision_buy = {
            "signal": "BUY",
            "asset": "BTC",
            "signal_strength": 0.8
        }
        
        is_extreme = decision_engine._is_extreme_counter_trend(
            ta_decision_buy,
            regime_score=20.0,
            params={"extreme_regime_threshold": 25.0}
        )
        
        assert is_extreme, "Extreme counter-trend should be detected"
        
        # 正常Regime Score + 做多信号 = 不应被拒绝
        is_extreme = decision_engine._is_extreme_counter_trend(
            ta_decision_buy,
            regime_score=50.0,
            params={"extreme_regime_threshold": 25.0}
        )
        
        assert not is_extreme, "Normal trend should not be filtered"


class TestOCOOrderManager:
    """测试OCO订单管理器"""
    
    @pytest.mark.asyncio
    async def test_oco_stop_loss_trigger(self):
        """测试止损触发"""
        # 这里需要实际的数据库会话，暂时跳过
        # 在真实环境中需要使用test database
        pass
    
    @pytest.mark.asyncio
    async def test_oco_take_profit_trigger(self):
        """测试止盈触发"""
        # 这里需要实际的数据库会话，暂时跳过
        pass


class TestEndToEndStrategy:
    """端到端策略测试"""
    
    @pytest.mark.asyncio
    async def test_complete_strategy_execution(self):
        """测试完整策略执行流程"""
        # 1. 数据采集
        data_service = MomentumDataService()
        
        # 2. Agent分析
        regime_agent = RegimeFilterAgent()
        ta_agent = TAMomentumAgent()
        
        # 3. 决策引擎
        decision_engine = MomentumRegimeDecision()
        
        # Mock所有外部调用
        with patch.object(data_service.binance_spot, 'get_ohlcv', new_callable=AsyncMock) as mock_ohlcv, \
             patch.object(data_service.binance_spot, 'get_current_price', new_callable=AsyncMock) as mock_price, \
             patch('app.services.llm.manager.llm_manager.chat_for_agent', new_callable=AsyncMock) as mock_llm:
            
            # 设置mock数据
            prices = [43000 + i * 10 for i in range(100)]
            mock_ohlcv.return_value = [[i, p-5, p+10, p-8, p, 100] for i, p in enumerate(prices)]
            mock_price.return_value = {"price": 43950.0, "change_24h": 2.2}
            
            # Mock LLM响应
            llm_responses = [
                # RegimeFilterAgent响应
                Mock(content='{"regime_score": 65.0, "regime_classification": "HEALTHY", "confidence": 0.8, "reasoning": "Good market", "component_scores": {}, "key_factors": [], "risk_level": "LOW", "recommended_multiplier": 1.2}'),
                # TAMomentumAgent响应
                Mock(content='''{
                    "asset_analyses": {
                        "BTC": {
                            "signal": "LONG",
                            "signal_strength": 0.75,
                            "confidence": 0.8,
                            "entry_price": 43950.0,
                            "stop_loss_distance_atr": 2.0,
                            "take_profit_rr": 2.0,
                            "reasoning": "Strong momentum",
                            "technical_scores": {"trend": 0.8, "momentum": 0.85, "timing": 0.7, "risk": 0.65},
                            "key_levels": {"support": [43000, 42500], "resistance": [44500, 45000]},
                            "timeframe_alignment": 0.8
                        },
                        "ETH": {"signal": "NEUTRAL", "signal_strength": 0.4, "confidence": 0.5},
                        "SOL": {"signal": "NEUTRAL", "signal_strength": 0.3, "confidence": 0.4}
                    },
                    "best_opportunity": {
                        "asset": "BTC",
                        "signal": "LONG",
                        "signal_strength": 0.75,
                        "confidence": 0.8,
                        "reasoning": "Best momentum"
                    },
                    "overall_momentum_strength": 0.65,
                    "market_trend": "UPTREND",
                    "reasoning": "Market trending up"
                }''')
            ]
            
            mock_llm.side_effect = llm_responses
            
            # 执行策略流程
            # Step 1: 采集数据
            market_data = await data_service.collect_all_data()
            assert market_data is not None
            
            # Step 2: Regime分析
            regime_output = await regime_agent.analyze(market_data)
            assert regime_output["regime_score"] > 0
            
            # Step 3: TA分析
            ta_output = await ta_agent.analyze(market_data)
            assert ta_output["best_opportunity"] is not None
            
            # Step 4: 决策
            agent_outputs = {
                "regime_filter": regime_output,
                "ta_momentum": ta_output
            }
            
            decision = decision_engine.decide(
                agent_outputs=agent_outputs,
                market_data=market_data,
                instance_params={"portfolio_value": 10000.0},
                current_position=0.0
            )
            
            # 验证决策结果
            assert decision.should_execute
            assert decision.signal in ["LONG", "SHORT", "HOLD"]
            
            if decision.should_execute and decision.signal != "HOLD":
                # 验证OCO订单
                oco_order = decision.metadata.get("oco_order")
                assert oco_order is not None
                assert oco_order["stop_loss_price"] > 0
                assert oco_order["take_profit_price"] > 0
                assert oco_order["entry_amount"] > 0
                
                print(f"\n✅ 完整策略执行成功!")
                print(f"   信号: {decision.signal}")
                print(f"   资产: {oco_order['asset']}")
                print(f"   入场: {oco_order['entry_price']:.2f}")
                print(f"   止损: {oco_order['stop_loss_price']:.2f}")
                print(f"   止盈: {oco_order['take_profit_price']:.2f}")
                print(f"   数量: {oco_order['entry_amount']:.6f}")
                print(f"   Regime Score: {regime_output['regime_score']:.1f}")


if __name__ == "__main__":
    # 运行单个测试
    asyncio.run(TestEndToEndStrategy().test_complete_strategy_execution())

