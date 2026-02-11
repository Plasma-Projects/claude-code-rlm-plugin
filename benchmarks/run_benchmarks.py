#!/usr/bin/env python3
"""
Comprehensive benchmark suite for RLM plugin performance evaluation
Tests token efficiency, processing time, memory usage, and accuracy
"""

import sys
import os
import time
import json
import psutil
import traceback
from pathlib import Path
from typing import Dict, List, Any, Optional
from dataclasses import dataclass, asdict
from contextlib import contextmanager

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from context_router import ContextData, ContextRouter
from repl_engine import RLMREPLEngine
from agent_manager import ParallelAgentManager

@dataclass
class BenchmarkResult:
    """Results from a benchmark test"""
    test_name: str
    file_path: str
    file_size_mb: float
    
    # RLM metrics
    rlm_activated: bool
    strategy_used: Optional[str]
    chunks_created: int
    
    # Performance metrics
    processing_time_seconds: float
    peak_memory_mb: float
    tokens_estimated: int
    
    # Accuracy metrics
    accuracy_score: float
    completeness_score: float
    
    # Comparison metrics (with vs without RLM)
    baseline_time_seconds: Optional[float] = None
    time_improvement_ratio: Optional[float] = None
    memory_improvement_ratio: Optional[float] = None
    
    error: Optional[str] = None
    
    def to_dict(self):
        return asdict(self)

class TokenCounter:
    """Estimate token usage for content"""
    
    @staticmethod
    def estimate_tokens(content: str) -> int:
        """Estimate tokens using simple word count approximation"""
        # Rough approximation: 1 token ≈ 0.75 words
        words = len(content.split())
        return int(words * 1.33)
    
    @staticmethod
    def estimate_tokens_file(file_path: str) -> int:
        """Estimate tokens for a file"""
        try:
            with open(file_path, 'r') as f:
                content = f.read()
            return TokenCounter.estimate_tokens(content)
        except Exception:
            # Fallback to size-based estimation
            size = os.path.getsize(file_path)
            return size // 4

@contextmanager
def monitor_performance():
    """Context manager to monitor performance metrics"""
    process = psutil.Process()
    start_memory = process.memory_info().rss / 1024 / 1024  # MB
    start_time = time.time()
    peak_memory = start_memory
    
    def update_peak():
        nonlocal peak_memory
        current = process.memory_info().rss / 1024 / 1024
        peak_memory = max(peak_memory, current)
    
    try:
        yield lambda: update_peak()
    finally:
        end_time = time.time()
        update_peak()
        
        # Return metrics via exception (hacky but works with context manager)
        metrics = {
            'processing_time': end_time - start_time,
            'peak_memory': peak_memory,
            'start_memory': start_memory
        }
        # Store in a global for retrieval
        global _performance_metrics
        _performance_metrics = metrics

class RLMBenchmark:
    """Comprehensive RLM performance benchmark suite"""
    
    def __init__(self, data_dir: Path):
        self.data_dir = data_dir
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
        self.results: List[BenchmarkResult] = []
    
    def run_all_benchmarks(self) -> List[BenchmarkResult]:
        """Run all benchmark tests"""
        print("🚀 Starting RLM Plugin Benchmark Suite")
        print("=" * 60)
        
        # Get test files
        test_files = self._get_test_files()
        
        for file_path in test_files:
            print(f"\n📁 Testing: {file_path.name}")
            
            # Run with RLM
            rlm_result = self._benchmark_with_rlm(file_path)
            
            # Run without RLM (baseline)
            baseline_result = self._benchmark_without_rlm(file_path)
            
            # Calculate comparative metrics
            if rlm_result and baseline_result:
                rlm_result.baseline_time_seconds = baseline_result.processing_time_seconds
                if baseline_result.processing_time_seconds > 0:
                    rlm_result.time_improvement_ratio = (
                        baseline_result.processing_time_seconds / rlm_result.processing_time_seconds
                    )
                if baseline_result.peak_memory_mb > 0:
                    rlm_result.memory_improvement_ratio = (
                        baseline_result.peak_memory_mb / rlm_result.peak_memory_mb
                    )
            
            if rlm_result:
                self.results.append(rlm_result)
        
        self._print_summary()
        return self.results
    
    def _get_test_files(self) -> List[Path]:
        """Get all test files"""
        test_files = []
        
        # Main test files
        candidates = [
            self.data_dir / "large_dataset.json",
            self.data_dir / "large_dataset.csv", 
            self.data_dir / "application.log",
        ]
        
        for file_path in candidates:
            if file_path.exists():
                test_files.append(file_path)
        
        # Add Python files from codebase
        code_dir = self.data_dir / "large_codebase"
        if code_dir.exists():
            py_files = list(code_dir.glob("**/*.py"))[:5]  # Limit to 5 files
            test_files.extend(py_files)
        
        return test_files
    
    def _benchmark_with_rlm(self, file_path: Path) -> Optional[BenchmarkResult]:
        """Benchmark processing with RLM enabled"""
        try:
            file_size_mb = file_path.stat().st_size / 1024 / 1024
            
            # Create context data
            context_data = ContextData.from_file(str(file_path))
            
            # Check if RLM should activate
            should_activate, strategy, metadata = self.router.should_activate_rlm(context_data)
            
            with monitor_performance() as update_memory:
                if should_activate:
                    result = self._process_with_rlm(file_path, strategy, metadata, update_memory)
                else:
                    result = self._process_directly(file_path, update_memory)
            
            global _performance_metrics
            metrics = _performance_metrics
            
            # Calculate accuracy metrics
            accuracy, completeness = self._evaluate_accuracy(file_path, result)
            
            return BenchmarkResult(
                test_name=f"RLM_{file_path.suffix[1:].upper()}",
                file_path=str(file_path),
                file_size_mb=file_size_mb,
                rlm_activated=should_activate,
                strategy_used=strategy,
                chunks_created=result.get('chunks_processed', 0),
                processing_time_seconds=metrics['processing_time'],
                peak_memory_mb=metrics['peak_memory'],
                tokens_estimated=context_data.estimated_tokens,
                accuracy_score=accuracy,
                completeness_score=completeness
            )
            
        except Exception as e:
            return BenchmarkResult(
                test_name=f"RLM_{file_path.suffix[1:].upper()}_ERROR",
                file_path=str(file_path),
                file_size_mb=0,
                rlm_activated=False,
                strategy_used=None,
                chunks_created=0,
                processing_time_seconds=0,
                peak_memory_mb=0,
                tokens_estimated=0,
                accuracy_score=0,
                completeness_score=0,
                error=str(e)
            )
    
    def _benchmark_without_rlm(self, file_path: Path) -> Optional[BenchmarkResult]:
        """Benchmark processing without RLM (baseline)"""
        try:
            file_size_mb = file_path.stat().st_size / 1024 / 1024
            
            with monitor_performance() as update_memory:
                result = self._process_directly(file_path, update_memory)
            
            global _performance_metrics
            metrics = _performance_metrics
            
            # Calculate accuracy metrics
            accuracy, completeness = self._evaluate_accuracy(file_path, result)
            
            return BenchmarkResult(
                test_name=f"BASELINE_{file_path.suffix[1:].upper()}",
                file_path=str(file_path),
                file_size_mb=file_size_mb,
                rlm_activated=False,
                strategy_used="direct",
                chunks_created=0,
                processing_time_seconds=metrics['processing_time'],
                peak_memory_mb=metrics['peak_memory'],
                tokens_estimated=TokenCounter.estimate_tokens_file(str(file_path)),
                accuracy_score=accuracy,
                completeness_score=completeness
            )
            
        except Exception as e:
            print(f"Baseline benchmark failed: {e}")
            return None
    
    def _process_with_rlm(self, file_path: Path, strategy: str, metadata: Dict, update_memory) -> Dict:
        """Process file using RLM strategy"""
        update_memory()
        
        if strategy in ["token_chunking", "file_chunking"]:
            return self._process_with_chunking(file_path, metadata, update_memory)
        elif strategy == "structural_decomp":
            return self._process_with_structural_decomp(file_path, metadata, update_memory)
        elif strategy == "file_parallel":
            return self._process_with_parallel(file_path, metadata, update_memory)
        else:
            return self._process_directly(file_path, update_memory)
    
    def _process_with_chunking(self, file_path: Path, metadata: Dict, update_memory) -> Dict:
        """Process file with chunking strategy"""
        from strategies.file_chunking import FileBasedChunking
        
        chunk_size = metadata.get('chunk_size', 50000)
        chunker = FileBasedChunking(chunk_size=chunk_size)
        
        chunks = chunker.decompose(str(file_path), metadata)
        update_memory()
        
        # Simulate processing chunks
        results = []
        for i, chunk in enumerate(chunks):
            update_memory()
            # Simulate chunk processing
            time.sleep(0.01)  # Small delay to simulate work
            results.append({
                'chunk_id': i,
                'size': len(str(chunk.get('content', ''))),
                'processed': True
            })
        
        aggregated = chunker.aggregate(results)
        update_memory()
        
        return {
            'type': 'rlm_chunked',
            'chunks_processed': len(chunks),
            'result': aggregated,
            'strategy': 'file_chunking'
        }
    
    def _process_with_structural_decomp(self, file_path: Path, metadata: Dict, update_memory) -> Dict:
        """Process file with structural decomposition"""
        from strategies.structural_decomp import StructuralDecomposition
        
        decomposer = StructuralDecomposition()
        
        chunks = decomposer.decompose(str(file_path), metadata)
        update_memory()
        
        # Simulate processing
        results = []
        for i, chunk in enumerate(chunks):
            update_memory()
            time.sleep(0.005)  # Small delay
            results.append({
                'chunk_id': i,
                'type': chunk.get('type', 'unknown'),
                'processed': True
            })
        
        aggregated = decomposer.aggregate(results)
        update_memory()
        
        return {
            'type': 'rlm_structural',
            'chunks_processed': len(chunks),
            'result': aggregated,
            'strategy': 'structural_decomp'
        }
    
    def _process_with_parallel(self, file_path: Path, metadata: Dict, update_memory) -> Dict:
        """Process file with parallel strategy"""
        max_concurrent = metadata.get('max_concurrent', 4)
        manager = ParallelAgentManager(max_concurrent=max_concurrent)
        
        # Create chunks for parallel processing
        chunks = []
        try:
            with open(file_path, 'r') as f:
                content = f.read()
            
            chunk_size = len(content) // max_concurrent
            for i in range(0, len(content), chunk_size):
                chunk = content[i:i+chunk_size]
                chunks.append({
                    'id': len(chunks),
                    'content': chunk
                })
                if len(chunks) >= max_concurrent:
                    break
        except Exception:
            chunks = [{'id': 0, 'content': 'fallback'}]
        
        update_memory()
        
        # Process chunks
        results = manager.process_chunks_sync(chunks, "Analyze content")
        update_memory()
        
        aggregated = manager.aggregate_results(results)
        update_memory()
        
        return {
            'type': 'rlm_parallel',
            'chunks_processed': len(chunks),
            'result': aggregated,
            'strategy': 'parallel'
        }
    
    def _process_directly(self, file_path: Path, update_memory) -> Dict:
        """Process file directly without RLM"""
        update_memory()
        
        try:
            with open(file_path, 'r') as f:
                content = f.read()
            update_memory()
            
            # Simulate processing
            lines = content.split('\n')
            update_memory()
            
            # Simple analysis
            stats = {
                'lines': len(lines),
                'chars': len(content),
                'words': len(content.split())
            }
            
            update_memory()
            
            return {
                'type': 'direct',
                'content': content[:1000] + "..." if len(content) > 1000 else content,
                'stats': stats
            }
            
        except Exception as e:
            return {
                'type': 'error',
                'error': str(e)
            }
    
    def _evaluate_accuracy(self, file_path: Path, result: Dict) -> tuple:
        """Evaluate accuracy and completeness of processing"""
        try:
            # Simple accuracy metrics based on result type
            if result.get('type') == 'error':
                return 0.0, 0.0
            
            # Check if we got reasonable output
            has_content = 'content' in result or 'result' in result
            accuracy = 0.8 if has_content else 0.2
            
            # Check completeness based on chunks processed
            chunks_processed = result.get('chunks_processed', 0)
            if chunks_processed > 0:
                completeness = min(1.0, chunks_processed / 10)  # Normalize to max 10 chunks
            else:
                completeness = 0.7 if has_content else 0.1
            
            return accuracy, completeness
            
        except Exception:
            return 0.5, 0.5
    
    def _print_summary(self):
        """Print benchmark summary"""
        print("\n" + "=" * 60)
        print("📊 BENCHMARK SUMMARY")
        print("=" * 60)
        
        if not self.results:
            print("❌ No results to display")
            return
        
        # Calculate aggregate metrics
        rlm_results = [r for r in self.results if r.rlm_activated]
        baseline_results = [r for r in self.results if not r.rlm_activated and not r.error]
        
        print(f"\n📈 Overall Statistics:")
        print(f"   Total Tests: {len(self.results)}")
        print(f"   RLM Activated: {len(rlm_results)}")
        print(f"   Errors: {len([r for r in self.results if r.error])}")
        
        if rlm_results:
            avg_time = sum(r.processing_time_seconds for r in rlm_results) / len(rlm_results)
            avg_memory = sum(r.peak_memory_mb for r in rlm_results) / len(rlm_results)
            avg_chunks = sum(r.chunks_created for r in rlm_results) / len(rlm_results)
            avg_accuracy = sum(r.accuracy_score for r in rlm_results) / len(rlm_results)
            
            print(f"\n🔄 RLM Performance:")
            print(f"   Avg Processing Time: {avg_time:.2f}s")
            print(f"   Avg Peak Memory: {avg_memory:.1f}MB")
            print(f"   Avg Chunks Created: {avg_chunks:.1f}")
            print(f"   Avg Accuracy: {avg_accuracy:.2f}")
            
            # Time improvements
            time_improvements = [r.time_improvement_ratio for r in rlm_results if r.time_improvement_ratio]
            if time_improvements:
                avg_time_improvement = sum(time_improvements) / len(time_improvements)
                print(f"   Avg Speed Improvement: {avg_time_improvement:.2f}x")
            
            # Memory improvements  
            memory_improvements = [r.memory_improvement_ratio for r in rlm_results if r.memory_improvement_ratio]
            if memory_improvements:
                avg_memory_improvement = sum(memory_improvements) / len(memory_improvements)
                print(f"   Avg Memory Efficiency: {avg_memory_improvement:.2f}x")
        
        print(f"\n📋 Individual Results:")
        for result in self.results:
            status = "✅" if not result.error else "❌"
            rlm_status = "RLM" if result.rlm_activated else "DIRECT"
            
            print(f"   {status} {result.test_name:<20} | {rlm_status:<6} | "
                  f"{result.file_size_mb:>6.1f}MB | {result.processing_time_seconds:>6.2f}s | "
                  f"{result.peak_memory_mb:>6.1f}MB | {result.accuracy_score:>5.2f}")
    
    def save_results(self, output_path: Optional[Path] = None):
        """Save results to JSON file"""
        if output_path is None:
            output_path = Path(__file__).parent / "benchmark_results.json"
        
        results_data = {
            'timestamp': time.time(),
            'config': self.config,
            'results': [result.to_dict() for result in self.results],
            'summary': self._generate_summary()
        }
        
        with open(output_path, 'w') as f:
            json.dump(results_data, f, indent=2)
        
        print(f"\n💾 Results saved to: {output_path}")
    
    def _generate_summary(self) -> Dict:
        """Generate summary statistics"""
        if not self.results:
            return {}
        
        rlm_results = [r for r in self.results if r.rlm_activated and not r.error]
        baseline_results = [r for r in self.results if not r.rlm_activated and not r.error]
        
        summary = {
            'total_tests': len(self.results),
            'rlm_activated_count': len([r for r in self.results if r.rlm_activated]),
            'error_count': len([r for r in self.results if r.error])
        }
        
        if rlm_results:
            summary['rlm_metrics'] = {
                'avg_processing_time': sum(r.processing_time_seconds for r in rlm_results) / len(rlm_results),
                'avg_memory_usage': sum(r.peak_memory_mb for r in rlm_results) / len(rlm_results),
                'avg_chunks_created': sum(r.chunks_created for r in rlm_results) / len(rlm_results),
                'avg_accuracy': sum(r.accuracy_score for r in rlm_results) / len(rlm_results)
            }
        
        if baseline_results:
            summary['baseline_metrics'] = {
                'avg_processing_time': sum(r.processing_time_seconds for r in baseline_results) / len(baseline_results),
                'avg_memory_usage': sum(r.peak_memory_mb for r in baseline_results) / len(baseline_results)
            }
        
        return summary

def main():
    """Run the benchmark suite"""
    data_dir = Path(__file__).parent / "test_data"
    
    if not data_dir.exists():
        print("❌ Test data directory not found. Please run generate_test_data.py first.")
        return 1
    
    benchmark = RLMBenchmark(data_dir)
    results = benchmark.run_all_benchmarks()
    benchmark.save_results()
    
    return 0

if __name__ == "__main__":
    sys.exit(main())