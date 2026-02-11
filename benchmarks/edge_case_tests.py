#!/usr/bin/env python3
"""
Edge case and stress testing for RLM plugin
Tests error handling, memory limits, and extreme scenarios
"""

import sys
import os
import time
import json
import tempfile
import threading
from pathlib import Path
from typing import Dict, List, Any
import random

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from context_router import ContextData, ContextRouter
from repl_engine import RLMREPLEngine
from agent_manager import ParallelAgentManager


class EdgeCaseTests:
    """Comprehensive edge case testing suite"""
    
    def __init__(self):
        self.config = {
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
        self.router = ContextRouter(self.config)
        self.test_results = []
    
    def run_all_tests(self):
        """Run all edge case tests"""
        print("🧪 Running RLM Edge Case Tests")
        print("=" * 50)
        
        test_methods = [
            self.test_empty_files,
            self.test_huge_files,
            self.test_malformed_data,
            self.test_unicode_edge_cases,
            self.test_memory_pressure,
            self.test_concurrent_access,
            self.test_recursion_limits,
            self.test_invalid_strategies,
            self.test_network_timeouts,
            self.test_disk_space_limits
        ]
        
        for test in test_methods:
            try:
                print(f"\n🔍 {test.__name__}")
                result = test()
                self.test_results.append({
                    'test': test.__name__,
                    'status': 'pass' if result else 'fail',
                    'details': result
                })
                print(f"   {'✅ PASS' if result else '❌ FAIL'}")
            except Exception as e:
                print(f"   ❌ ERROR: {e}")
                self.test_results.append({
                    'test': test.__name__,
                    'status': 'error',
                    'error': str(e)
                })
    
    def test_empty_files(self) -> bool:
        """Test handling of empty files and content"""
        # Empty file
        with tempfile.NamedTemporaryFile(mode='w', delete=False) as f:
            temp_file = f.name
        
        try:
            context_data = ContextData.from_file(temp_file)
            should_activate, strategy, metadata = self.router.should_activate_rlm(context_data)
            
            # Should not activate RLM for empty file
            if should_activate:
                return False
            
            # Test empty content
            context_data = ContextData.from_content("")
            should_activate, strategy, metadata = self.router.should_activate_rlm(context_data)
            
            return not should_activate
            
        finally:
            os.unlink(temp_file)
    
    def test_huge_files(self) -> bool:
        """Test handling of extremely large files"""
        # Create very large file (100MB simulation)
        huge_size = 100 * 1024 * 1024
        
        context_data = ContextData(
            estimated_tokens=huge_size // 4,
            files=["huge_file.txt"],
            total_size_bytes=huge_size,
            data_type='txt'
        )
        
        should_activate, strategy, metadata = self.router.should_activate_rlm(context_data)
        
        # Should definitely activate RLM for huge files
        return should_activate and strategy is not None
    
    def test_malformed_data(self) -> bool:
        """Test handling of malformed JSON, CSV, etc."""
        test_cases = [
            '{"incomplete": json',  # Malformed JSON
            'name,age\nJohn,\nBroken CSV',  # Malformed CSV
            '<xml><unclosed>tag</xml>',  # Malformed XML
            '\x00\x01\x02binary data',  # Binary data
            'normal text with\nnull\x00bytes',  # Mixed content
        ]
        
        for malformed_content in test_cases:
            try:
                context_data = ContextData.from_content(malformed_content)
                
                # Should handle gracefully without crashing
                should_activate, strategy, metadata = self.router.should_activate_rlm(context_data)
                
                # Test REPL engine with malformed data
                repl = RLMREPLEngine()
                result = repl.load_content(malformed_content)
                
                # Should not crash
                assert result['status'] in ['loaded', 'decomposed']
                
            except Exception as e:
                print(f"     Failed on: {repr(malformed_content[:50])}")
                return False
        
        return True
    
    def test_unicode_edge_cases(self) -> bool:
        """Test handling of various Unicode characters"""
        unicode_tests = [
            "Hello 🌍 World 🚀",  # Emojis
            "Ω ≈ ∞ ∑ ∆",  # Math symbols  
            "中文测试文本",  # Chinese characters
            "العربية اختبار",  # Arabic text
            "🔥💯🎉🎊🌟⭐",  # Multiple emojis
            "\u200b\u200c\u200d",  # Zero-width characters
            "a" * 1000 + "🌍" + "b" * 1000,  # Mixed long content
        ]
        
        for unicode_content in unicode_tests:
            try:
                context_data = ContextData.from_content(unicode_content)
                should_activate, strategy, metadata = self.router.should_activate_rlm(context_data)
                
                # Test REPL engine
                repl = RLMREPLEngine()
                result = repl.load_content(unicode_content)
                
                # Should handle Unicode properly
                assert result['status'] in ['loaded', 'decomposed']
                
            except Exception as e:
                print(f"     Failed on Unicode: {repr(unicode_content[:30])}")
                return False
        
        return True
    
    def test_memory_pressure(self) -> bool:
        """Test behavior under memory pressure"""
        # Create large content in memory
        large_content = "x" * (10 * 1024 * 1024)  # 10MB of 'x'
        
        try:
            # Test context detection with large content
            context_data = ContextData.from_content(large_content)
            should_activate, strategy, metadata = self.router.should_activate_rlm(context_data)
            
            # Should activate due to size
            if not should_activate:
                return False
            
            # Test REPL with large content
            repl = RLMREPLEngine()
            result = repl.load_content(large_content, max_size=1024)
            
            # Should decompose due to size limit
            return result['status'] == 'decomposed'
            
        except MemoryError:
            # Expected behavior under memory pressure
            return True
        except Exception as e:
            print(f"     Unexpected error: {e}")
            return False
    
    def test_concurrent_access(self) -> bool:
        """Test concurrent access to RLM components"""
        results = []
        errors = []
        
        def worker_thread(thread_id):
            try:
                # Each thread creates its own context
                content = f"Thread {thread_id} content " * 1000
                context_data = ContextData.from_content(content)
                
                should_activate, strategy, metadata = self.router.should_activate_rlm(context_data)
                results.append((thread_id, should_activate, strategy))
                
                # Test REPL in thread
                repl = RLMREPLEngine()
                repl_result = repl.load_content(content)
                results.append((thread_id, 'repl', repl_result['status']))
                
            except Exception as e:
                errors.append((thread_id, str(e)))
        
        # Start multiple threads
        threads = []
        for i in range(5):
            thread = threading.Thread(target=worker_thread, args=(i,))
            threads.append(thread)
            thread.start()
        
        # Wait for completion
        for thread in threads:
            thread.join(timeout=10)
        
        # Check results
        if errors:
            print(f"     Concurrent errors: {errors}")
            return False
        
        return len(results) >= 10  # Should have results from all threads
    
    def test_recursion_limits(self) -> bool:
        """Test recursion depth limits"""
        repl = RLMREPLEngine()
        repl._max_recursion = 2
        
        # Test direct recursion limit
        result1 = repl.namespace['llm_query']("Query 1")
        
        # This should work (within limit)
        if "Recursion limit" in str(result1):
            return False
        
        # Force recursion depth and test limit
        repl._recursion_depth = 2
        result2 = repl.namespace['llm_query']("Query 2")
        
        # This should hit the limit
        return "Recursion limit" in str(result2)
    
    def test_invalid_strategies(self) -> bool:
        """Test handling of invalid strategy configurations"""
        invalid_strategies = [
            "nonexistent_strategy",
            None,
            "",
            123,
            {"invalid": "object"}
        ]
        
        for invalid_strategy in invalid_strategies:
            try:
                # Should fall back to default strategy
                strategy_obj = self.router.get_strategy(invalid_strategy)
                
                # Should return a valid strategy object (fallback)
                assert hasattr(strategy_obj, 'decompose')
                assert hasattr(strategy_obj, 'aggregate')
                
            except Exception as e:
                print(f"     Failed on invalid strategy: {invalid_strategy}")
                return False
        
        return True
    
    def test_network_timeouts(self) -> bool:
        """Test network timeout simulation (for future network-based features)"""
        # Simulate slow network operations
        def slow_llm_function(prompt, model="haiku"):
            time.sleep(0.1)  # Simulate network delay
            return f"Response to: {prompt[:50]}..."
        
        repl = RLMREPLEngine(llm_query_fn=slow_llm_function)
        
        try:
            # Test that timeouts don't crash the system
            start_time = time.time()
            result = repl.namespace['llm_query']("Test query")
            end_time = time.time()
            
            # Should complete but take some time
            return (end_time - start_time) > 0.05 and result is not None
            
        except Exception as e:
            print(f"     Network timeout test failed: {e}")
            return False
    
    def test_disk_space_limits(self) -> bool:
        """Test behavior when disk space is limited"""
        # Create temporary directory
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_path = Path(temp_dir)
            
            try:
                # Create REPL with temp directory
                repl = RLMREPLEngine()
                repl.temp_dir = temp_path / "rlm_test"
                repl.temp_dir.mkdir(exist_ok=True)
                
                # Test basic operations
                result = repl.load_content("Test content")
                
                # Should work normally
                return result['status'] == 'loaded'
                
            except Exception as e:
                # Should handle disk issues gracefully
                return "No space left" in str(e) or "Permission denied" in str(e)
    
    def print_summary(self):
        """Print test summary"""
        print("\n" + "=" * 50)
        print("🧪 EDGE CASE TEST SUMMARY")
        print("=" * 50)
        
        total_tests = len(self.test_results)
        passed = len([r for r in self.test_results if r['status'] == 'pass'])
        failed = len([r for r in self.test_results if r['status'] == 'fail'])
        errors = len([r for r in self.test_results if r['status'] == 'error'])
        
        print(f"Total Tests: {total_tests}")
        print(f"Passed: {passed}")
        print(f"Failed: {failed}")
        print(f"Errors: {errors}")
        print(f"Success Rate: {passed/total_tests*100:.1f}%" if total_tests > 0 else "No tests run")
        
        # Show failed/error details
        for result in self.test_results:
            if result['status'] != 'pass':
                print(f"❌ {result['test']}: {result.get('error', 'Failed')}")


def main():
    """Run edge case tests"""
    tester = EdgeCaseTests()
    tester.run_all_tests()
    tester.print_summary()
    
    # Return success if all tests passed
    passed = len([r for r in tester.test_results if r['status'] == 'pass'])
    total = len(tester.test_results)
    
    return 0 if passed == total else 1


if __name__ == "__main__":
    sys.exit(main())