"""添加临时调试日志到signal_generator"""

import sys
sys.path.insert(0, '/Users/uniteyoo/Documents/AutoMoney/AMbackend')

# Read the signal_generator.py file
file_path = '/Users/uniteyoo/Documents/AutoMoney/AMbackend/app/services/decision/signal_generator.py'

with open(file_path, 'r') as f:
    content = f.read()

# Find the line where circuit breaker is checked (around line 228)
# Add logging before the check

insert_point = 'if fg_value < fg_circuit_breaker_threshold:'

if insert_point in content:
    # Insert debug logging
    debug_code = '''        # 🐛 DEBUG: Log threshold values
        import logging
        logger = logging.getLogger(__name__)
        logger.info(f"🐛 DEBUG - Circuit Breaker Check:")
        logger.info(f"  fg_value={fg_value}")
        logger.info(f"  fg_circuit_breaker_threshold={fg_circuit_breaker_threshold}")
        logger.info(f"  Will trigger: {fg_value < fg_circuit_breaker_threshold}")

        '''

    content = content.replace(insert_point, debug_code + insert_point)

    # Also add logging at the start of generate_signal
    insert_point_2 = '# 提取交易阈值参数'
    debug_code_2 = '''        # 🐛 DEBUG: Log portfolio_state
        import logging
        logger = logging.getLogger(__name__)
        logger.info(f"🐛 DEBUG - generate_signal called:")
        logger.info(f"  conviction_score={conviction_score}")
        logger.info(f"  portfolio_state keys: {list(portfolio_state.keys())}")
        logger.info(f"  portfolio_state values: {portfolio_state}")

        '''

    content = content.replace(insert_point_2, debug_code_2 + insert_point_2)

    # Write back
    with open(file_path, 'w') as f:
        f.write(content)

    print("✅ 已添加调试日志到 signal_generator.py")
    print()
    print("调试日志位置:")
    print("  1. generate_signal方法开始处 - 打印portfolio_state")
    print("  2. circuit breaker检查处 - 打印F&G值和阈值")
    print()
    print("请等待下一次策略执行（大约8分钟一次），然后查看日志：")
    print("  tail -f /tmp/automoney.log")
else:
    print("❌ 未找到插入点")
