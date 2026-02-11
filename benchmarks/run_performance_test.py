#!/usr/bin/env python3
"""
Simple performance test for RLM components without full plugin dependency
"""

import sys
import time
import psutil
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

def test_rlm_performance():
    """Test RLM component performance"""
    print("🚀 RLM Performance Test")
    print("=" * 40)
    
    # Import components
    from src.context_router import ContextData, ContextRouter
    from src.strategies.file_chunking import FileBasedChunking
    from src.strategies.structural_decomp import StructuralDecomposition
    
    # Configuration
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
    
    # Test files
    test_files = [
        Path(__file__).parent / "test_data" / "large_dataset.json",
        Path(__file__).parent / "test_data" / "large_dataset.csv",
        Path(__file__).parent / "test_data" / "application.log"
    ]
    
    results = []
    
    for test_file in test_files:
        if not test_file.exists():
            print(f"❌ {test_file.name} not found")
            continue
            
        print(f"\n📁 Testing: {test_file.name}")
        
        # Get file info
        file_size = test_file.stat().st_size
        file_size_mb = file_size / (1024 * 1024)
        
        # Test context detection
        start_time = time.time()
        context_data = ContextData.from_file(str(test_file))
        should_activate, strategy, metadata = router.should_activate_rlm(context_data)
        detection_time = time.time() - start_time
        
        print(f"   📏 Size: {file_size_mb:.1f}MB")
        print(f"   🔢 Tokens: {context_data.estimated_tokens:,}")
        print(f"   🔄 RLM: {should_activate} ({'✅' if should_activate else '❌'})")
        print(f"   📋 Strategy: {strategy}")
        print(f"   ⏱️  Detection: {detection_time:.3f}s")
        
        if should_activate:
            # Test chunking performance
            start_time = time.time()
            process = psutil.Process()
            start_memory = process.memory_info().rss / 1024 / 1024  # MB
            
            try:
                if strategy in ["token_chunking", "file_chunking"]:
                    chunker = FileBasedChunking(chunk_size=50000)
                    chunks = chunker.decompose(str(test_file), metadata)
                elif strategy == "structural_decomp":
                    decomposer = StructuralDecomposition()
                    chunks = decomposer.decompose(str(test_file), metadata)
                else:
                    chunks = []
                
                end_time = time.time()
                end_memory = process.memory_info().rss / 1024 / 1024  # MB
                
                chunking_time = end_time - start_time
                memory_used = end_memory - start_memory
                
                print(f"   🔧 Chunks: {len(chunks)}")
                print(f"   ⏱️  Chunking: {chunking_time:.3f}s")
                print(f"   🧠 Memory: +{memory_used:.1f}MB")
                
                # Calculate efficiency
                if file_size > 0:
                    processing_rate = file_size_mb / chunking_time if chunking_time > 0 else 0
                    print(f"   📊 Rate: {processing_rate:.1f}MB/s")
                
                results.append({
                    'file': test_file.name,
                    'size_mb': file_size_mb,
                    'tokens': context_data.estimated_tokens,
                    'rlm_activated': should_activate,
                    'strategy': strategy,
                    'chunks': len(chunks),
                    'detection_time': detection_time,
                    'chunking_time': chunking_time,
                    'memory_mb': memory_used,
                    'rate_mbps': processing_rate
                })
                
            except Exception as e:
                print(f"   ❌ Chunking failed: {e}")
                results.append({
                    'file': test_file.name,
                    'size_mb': file_size_mb,
                    'tokens': context_data.estimated_tokens,
                    'rlm_activated': should_activate,
                    'strategy': strategy,
                    'error': str(e)
                })
        else:
            results.append({
                'file': test_file.name,
                'size_mb': file_size_mb,
                'tokens': context_data.estimated_tokens,
                'rlm_activated': should_activate,
                'detection_time': detection_time
            })
    
    # Summary
    print("\n" + "=" * 40)
    print("📊 PERFORMANCE SUMMARY")
    print("=" * 40)
    
    if results:
        successful_tests = [r for r in results if 'error' not in r]
        rlm_tests = [r for r in successful_tests if r.get('rlm_activated')]
        
        print(f"Tests completed: {len(results)}")
        print(f"Successful: {len(successful_tests)}")
        print(f"RLM activated: {len(rlm_tests)}")
        
        if rlm_tests:
            avg_chunking_time = sum(r.get('chunking_time', 0) for r in rlm_tests) / len(rlm_tests)
            avg_chunks = sum(r.get('chunks', 0) for r in rlm_tests) / len(rlm_tests)
            avg_rate = sum(r.get('rate_mbps', 0) for r in rlm_tests) / len(rlm_tests)
            
            print(f"Avg chunking time: {avg_chunking_time:.3f}s")
            print(f"Avg chunks created: {avg_chunks:.1f}")
            print(f"Avg processing rate: {avg_rate:.1f}MB/s")
        
        print("\nDetailed results:")
        for result in results:
            if 'error' in result:
                print(f"  ❌ {result['file']}: {result['error']}")
            else:
                rlm_status = "RLM" if result.get('rlm_activated') else "DIRECT"
                chunks = result.get('chunks', 0)
                rate = result.get('rate_mbps', 0)
                print(f"  ✅ {result['file']:<20} | {rlm_status:<6} | {chunks:>3} chunks | {rate:>6.1f}MB/s")
    
    return len([r for r in results if 'error' not in r])

if __name__ == "__main__":
    success_count = test_rlm_performance()
    print(f"\n🏆 {success_count} tests completed successfully")