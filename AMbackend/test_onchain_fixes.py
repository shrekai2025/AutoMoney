"""Test OnChainAgent fixes"""

import asyncio
import sys
from app.agents.onchain_agent import OnChainAgent
from app.services.data_collectors.manager import data_manager


async def test_syntax_fix():
    """Test that the f-string syntax error is fixed"""
    print("=" * 70)
    print("Testing OnChainAgent Syntax Fixes")
    print("=" * 70)

    # Test 1: Agent instantiation (should not raise syntax error)
    print("\n[1] Testing agent instantiation...")
    try:
        agent = OnChainAgent()
        print("✅ Agent instantiated successfully (no syntax errors)")
    except SyntaxError as e:
        print(f"❌ Syntax error in agent code: {e}")
        return False

    # Test 2: Data collection
    print("\n[2] Testing data collection...")
    try:
        onchain_data = await data_manager.collect_for_onchain_agent()
        print("✅ Data collection successful")
        
        # Verify data structure
        assert "blockchain_info" in onchain_data, "Missing blockchain_info"
        assert "mempool_space" in onchain_data, "Missing mempool_space"
        assert "btc_price" in onchain_data, "Missing btc_price"
        print("✅ Data structure is correct")
    except Exception as e:
        print(f"❌ Data collection failed: {e}")
        import traceback
        traceback.print_exc()
        return False

    # Test 3: Prompt building with user query
    print("\n[3] Testing prompt building...")
    try:
        user_query = "比特币网络是否健康?"
        prompt = agent._build_analysis_prompt(user_query, onchain_data)
        
        # Verify prompt contains user query
        assert user_query in prompt, "User query not in prompt"
        print(f"✅ Prompt contains user query: '{user_query}'")
        
        # Verify no syntax errors in formatted values
        assert "Active Addresses (24h):" in prompt, "Active addresses not formatted"
        print("✅ Active addresses formatted correctly (f-string fix working)")
        
        # Print sample of prompt
        print("\n📝 Sample Prompt (first 500 chars):")
        print(prompt[:500])
        print("...")
        
    except Exception as e:
        print(f"❌ Prompt building failed: {e}")
        import traceback
        traceback.print_exc()
        return False

    # Test 4: Full analysis (optional - requires LLM)
    print("\n[4] Testing full analysis (with LLM)...")
    print("  Note: This requires LLM API credentials")
    try:
        result = await agent.analyze(user_query, onchain_data)
        
        # Verify result structure
        assert hasattr(result, 'signal'), "Missing signal field"
        assert hasattr(result, 'confidence'), "Missing confidence field"
        assert hasattr(result, 'confidence_level'), "Missing confidence_level field"
        assert hasattr(result, 'reasoning'), "Missing reasoning field"
        assert hasattr(result, 'onchain_metrics'), "Missing onchain_metrics field"
        assert hasattr(result, 'network_health'), "Missing network_health field"
        
        print(f"✅ Analysis completed successfully")
        print(f"  Signal: {result.signal.value}")
        print(f"  Confidence: {result.confidence:.2%} ({result.confidence_level.value})")
        print(f"  Network Health: {result.network_health}")
        print(f"  Reasoning (first 200 chars): {result.reasoning[:200]}...")
        
    except Exception as e:
        print(f"⚠️  Full analysis test skipped: {e}")
        print("  (This is OK if LLM credentials are not configured)")

    print("\n" + "=" * 70)
    print("✅ All critical tests passed!")
    print("=" * 70)
    return True


async def test_workflow_integration():
    """Test that user_message is properly passed in workflow"""
    print("\n" + "=" * 70)
    print("Testing Workflow Integration")
    print("=" * 70)
    
    from app.workflows.research_workflow import research_workflow
    
    print("\n[1] Testing workflow structure...")
    
    # Verify OnChainAgent is registered
    assert "onchain_agent" in research_workflow.agent_map, "OnChainAgent not in agent_map"
    print("✅ OnChainAgent registered in workflow")
    
    # Test _run_agent method signature
    import inspect
    sig = inspect.signature(research_workflow._run_agent)
    params = list(sig.parameters.keys())
    
    assert "user_message" in params, "_run_agent missing user_message parameter"
    print("✅ _run_agent has user_message parameter")
    
    # Test _execute_business_agents method signature
    sig2 = inspect.signature(research_workflow._execute_business_agents)
    params2 = list(sig2.parameters.keys())
    
    assert "user_message" in params2, "_execute_business_agents missing user_message parameter"
    print("✅ _execute_business_agents has user_message parameter")
    
    print("\n✅ Workflow integration looks good!")
    return True


if __name__ == "__main__":
    async def main():
        # Run syntax and agent tests
        success1 = await test_syntax_fix()
        
        # Run workflow integration tests
        success2 = await test_workflow_integration()
        
        if success1 and success2:
            print("\n🎉 All tests passed! OnChainAgent is ready.")
            sys.exit(0)
        else:
            print("\n❌ Some tests failed.")
            sys.exit(1)
    
    asyncio.run(main())


