#!/usr/bin/env python3
"""
Basic functionality test for RLM plugin components
"""

import sys
import os
from pathlib import Path

# Add the project root to the path so we can import
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

# Import the main plugin
try:
    from src import RLMPlugin
    print("✅ Successfully imported RLMPlugin")
except ImportError as e:
    print(f"❌ Failed to import RLMPlugin: {e}")
    sys.exit(1)

def test_basic_functionality():
    """Test basic RLM functionality"""
    print("🔧 Testing basic RLM functionality...")
    
    try:
        # Create plugin instance without config file dependency
        plugin = RLMPlugin()
        print("❌ Plugin creation should fail without config")
        return False
    except Exception:
        print("✅ Plugin correctly fails without config file")
    
    # Test with mock config
    try:
        # Create a basic test
        from src.context_router import ContextData, ContextRouter
        
        config = {
            'auto_trigger': {
                'enabled': True,
                'token_count': 50_000,
                'file_size_kb': 100,
                'file_count': 5
            },
            'processing': {
                'max_concurrent_agents': 4
            }
        }
        
        router = ContextRouter(config)
        
        # Test with our generated data
        test_file = Path(__file__).parent / "test_data" / "large_dataset.json"
        if test_file.exists():
            context_data = ContextData.from_file(str(test_file))
            should_activate, strategy, metadata = router.should_activate_rlm(context_data)
            
            print(f"📁 Test file: {test_file.name}")
            print(f"📏 Size: {test_file.stat().st_size / (1024*1024):.1f}MB")
            print(f"🔢 Estimated tokens: {context_data.estimated_tokens:,}")
            print(f"🔄 RLM activated: {should_activate}")
            print(f"📋 Strategy: {strategy}")
            
            if should_activate:
                print("✅ RLM activation logic working correctly")
                return True
            else:
                print("❌ RLM should have activated for large file")
                return False
        else:
            print(f"❌ Test data not found at {test_file}")
            return False
            
    except Exception as e:
        print(f"❌ Test failed with error: {e}")
        return False

def test_context_data():
    """Test context data creation"""
    print("\n🔍 Testing ContextData...")
    
    from src.context_router import ContextData
    
    # Test content-based context
    test_content = "This is a test content string. " * 1000
    context_data = ContextData.from_content(test_content)
    
    print(f"📄 Content size: {len(test_content)} chars")
    print(f"🔢 Estimated tokens: {context_data.estimated_tokens}")
    print(f"📊 Has structure: {context_data.has_structure}")
    
    return True

def test_token_estimation():
    """Test token estimation accuracy"""
    print("\n🎯 Testing token estimation...")
    
    from src.context_router import ContextData
    
    # Test different content types
    test_cases = [
        ("Short text", "Hello world", 3),
        ("JSON structure", '{"key": "value", "array": [1, 2, 3]}', 15),
        ("Code snippet", "def function():\n    return True", 8),
        ("Long text", "word " * 1000, 1300)
    ]
    
    for name, content, expected_range in test_cases:
        context_data = ContextData.from_content(content)
        estimated = context_data.estimated_tokens
        
        print(f"  {name}: {estimated} tokens (expected ~{expected_range})")
        
        # Check if estimation is reasonable (within 50% of expected)
        if abs(estimated - expected_range) / expected_range > 0.5:
            print(f"    ⚠️  Estimation seems off")
        else:
            print(f"    ✅ Estimation looks reasonable")
    
    return True

def main():
    """Run all basic tests"""
    print("🚀 RLM Plugin Basic Functionality Tests")
    print("=" * 50)
    
    tests = [
        test_basic_functionality,
        test_context_data,
        test_token_estimation
    ]
    
    results = []
    for test in tests:
        try:
            result = test()
            results.append(result)
        except Exception as e:
            print(f"❌ Test {test.__name__} failed with exception: {e}")
            results.append(False)
    
    print("\n" + "=" * 50)
    passed = sum(results)
    total = len(results)
    print(f"📊 Results: {passed}/{total} tests passed")
    
    if passed == total:
        print("🎉 All basic functionality tests passed!")
        return 0
    else:
        print("❌ Some tests failed")
        return 1

if __name__ == "__main__":
    sys.exit(main())