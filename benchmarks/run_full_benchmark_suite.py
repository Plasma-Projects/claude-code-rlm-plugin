#!/usr/bin/env python3
"""
Complete benchmark suite runner for RLM plugin
Orchestrates all tests and generates comprehensive reports
"""

import sys
import time
import json
import subprocess
from pathlib import Path
from typing import Dict, List, Any

def run_command(command: List[str], description: str) -> Dict[str, Any]:
    """Run a command and capture results"""
    print(f"🔧 {description}...")
    
    start_time = time.time()
    try:
        result = subprocess.run(
            command,
            cwd=Path(__file__).parent,
            capture_output=True,
            text=True,
            timeout=300  # 5 minute timeout
        )
        
        end_time = time.time()
        
        return {
            'command': ' '.join(command),
            'description': description,
            'success': result.returncode == 0,
            'duration': end_time - start_time,
            'stdout': result.stdout,
            'stderr': result.stderr,
            'returncode': result.returncode
        }
        
    except subprocess.TimeoutExpired:
        return {
            'command': ' '.join(command),
            'description': description,
            'success': False,
            'duration': 300,
            'stdout': '',
            'stderr': 'Command timed out after 5 minutes',
            'returncode': -1
        }
    except Exception as e:
        return {
            'command': ' '.join(command),
            'description': description,
            'success': False,
            'duration': 0,
            'stdout': '',
            'stderr': str(e),
            'returncode': -1
        }

def check_dependencies():
    """Check if required dependencies are available"""
    print("🔍 Checking dependencies...")
    
    required_packages = ['psutil', 'numpy']
    missing_packages = []
    
    for package in required_packages:
        try:
            __import__(package)
            print(f"   ✅ {package}")
        except ImportError:
            missing_packages.append(package)
            print(f"   ❌ {package} (missing)")
    
    optional_packages = ['matplotlib']
    for package in optional_packages:
        try:
            __import__(package)
            print(f"   ✅ {package} (optional)")
        except ImportError:
            print(f"   ⚠️  {package} (optional, visualizations disabled)")
    
    if missing_packages:
        print(f"\n❌ Missing required packages: {', '.join(missing_packages)}")
        print("Install with: pip install " + " ".join(missing_packages))
        return False
    
    return True

def generate_test_data() -> Dict[str, Any]:
    """Generate test data"""
    return run_command(
        [sys.executable, "generate_test_data.py"],
        "Generating test datasets"
    )

def run_basic_tests() -> Dict[str, Any]:
    """Run basic functionality tests"""
    return run_command(
        [sys.executable, "../test_plugin.py"],
        "Running basic functionality tests"
    )

def run_edge_case_tests() -> Dict[str, Any]:
    """Run edge case tests"""
    return run_command(
        [sys.executable, "edge_case_tests.py"],
        "Running edge case tests"
    )

def run_performance_benchmarks() -> Dict[str, Any]:
    """Run performance benchmarks"""
    return run_command(
        [sys.executable, "run_benchmarks.py"],
        "Running performance benchmarks"
    )

def run_token_efficiency_analysis() -> Dict[str, Any]:
    """Run token efficiency analysis"""
    return run_command(
        [sys.executable, "token_efficiency_analyzer.py"],
        "Running token efficiency analysis"
    )

def collect_results() -> Dict[str, Any]:
    """Collect and consolidate all results"""
    results = {}
    
    # Collect JSON results from individual tests
    result_files = {
        'benchmarks': 'benchmark_results.json',
        'token_analysis': 'token_efficiency_analysis.json'
    }
    
    for key, filename in result_files.items():
        file_path = Path(__file__).parent / filename
        if file_path.exists():
            try:
                with open(file_path) as f:
                    results[key] = json.load(f)
            except Exception as e:
                results[key] = {'error': f'Failed to load {filename}: {e}'}
        else:
            results[key] = {'error': f'{filename} not found'}
    
    return results

def generate_comprehensive_report(test_results: List[Dict[str, Any]], collected_results: Dict[str, Any]):
    """Generate comprehensive benchmark report"""
    
    print("\n" + "=" * 80)
    print("🎯 COMPREHENSIVE RLM PLUGIN BENCHMARK REPORT")
    print("=" * 80)
    
    # Test execution summary
    print(f"\n📋 Test Execution Summary:")
    total_tests = len(test_results)
    successful_tests = len([r for r in test_results if r['success']])
    total_duration = sum(r['duration'] for r in test_results)
    
    print(f"   Total Tests Run: {total_tests}")
    print(f"   Successful Tests: {successful_tests}")
    print(f"   Failed Tests: {total_tests - successful_tests}")
    print(f"   Total Duration: {total_duration:.2f}s")
    print(f"   Success Rate: {successful_tests/total_tests*100:.1f}%")
    
    # Individual test results
    print(f"\n📊 Individual Test Results:")
    for result in test_results:
        status = "✅" if result['success'] else "❌"
        print(f"   {status} {result['description']:<40} | {result['duration']:>6.2f}s")
        
        if not result['success']:
            print(f"      Error: {result['stderr'][:100]}...")
    
    # Performance metrics (if available)
    if 'benchmarks' in collected_results and 'summary' in collected_results['benchmarks']:
        summary = collected_results['benchmarks']['summary']
        print(f"\n⚡ Performance Summary:")
        print(f"   Total Files Tested: {summary.get('total_tests', 'N/A')}")
        print(f"   RLM Activations: {summary.get('rlm_activated_count', 'N/A')}")
        print(f"   Error Count: {summary.get('error_count', 'N/A')}")
        
        if 'rlm_metrics' in summary:
            rlm = summary['rlm_metrics']
            print(f"   Avg Processing Time: {rlm.get('avg_processing_time', 'N/A'):.2f}s")
            print(f"   Avg Memory Usage: {rlm.get('avg_memory_usage', 'N/A'):.1f}MB")
            print(f"   Avg Chunks Created: {rlm.get('avg_chunks_created', 'N/A'):.1f}")
            print(f"   Avg Accuracy: {rlm.get('avg_accuracy', 'N/A'):.2f}")
    
    # Token efficiency metrics (if available)
    if 'token_analysis' in collected_results and 'report' in collected_results['token_analysis']:
        report = collected_results['token_analysis']['report']
        
        if 'efficiency_metrics' in report:
            metrics = report['efficiency_metrics']
            print(f"\n🎯 Token Efficiency Summary:")
            print(f"   Avg Token Reduction: {metrics.get('avg_token_reduction_ratio', 'N/A'):.2f}x")
            print(f"   Avg Chunk Efficiency: {metrics.get('avg_chunk_efficiency_score', 'N/A'):.2f}")
            print(f"   Avg Context Utilization: {metrics.get('avg_context_window_utilization', 'N/A'):.1%}")
            print(f"   Total Wasted Tokens: {metrics.get('total_wasted_tokens', 'N/A'):,}")
            print(f"   Total Overhead Tokens: {metrics.get('total_overhead_tokens', 'N/A'):,}")
    
    # Recommendations
    print(f"\n💡 Recommendations:")
    
    if successful_tests < total_tests:
        print("   🔧 Fix failing tests before production deployment")
    
    # Performance recommendations
    if 'benchmarks' in collected_results:
        try:
            results = collected_results['benchmarks']['results']
            large_files = [r for r in results if r.get('file_size_mb', 0) > 1]
            
            if large_files:
                avg_time = sum(r.get('processing_time_seconds', 0) for r in large_files) / len(large_files)
                if avg_time > 5:
                    print(f"   ⚡ Consider optimizing large file processing (avg {avg_time:.1f}s)")
            
            errors = [r for r in results if r.get('error')]
            if errors:
                print(f"   🐛 Address {len(errors)} processing errors")
                
        except (KeyError, TypeError):
            pass
    
    # Token efficiency recommendations
    if 'token_analysis' in collected_results:
        try:
            report = collected_results['token_analysis']['report']
            metrics = report.get('efficiency_metrics', {})
            
            utilization = metrics.get('avg_context_window_utilization', 0)
            if utilization < 0.7:
                print(f"   📊 Low context utilization ({utilization:.1%}) - consider larger chunk sizes")
            
            wasted = metrics.get('total_wasted_tokens', 0)
            if wasted > 100000:
                print(f"   🗑️  High token waste ({wasted:,}) - optimize chunking strategy")
                
        except (KeyError, TypeError):
            pass
    
    print(f"\n🎉 Benchmark suite completed successfully!")
    
    # Final score
    performance_score = (successful_tests / total_tests) * 100 if total_tests > 0 else 0
    print(f"\n🏆 Overall Score: {performance_score:.1f}/100")
    
    if performance_score >= 90:
        print("   🌟 Excellent! Plugin is ready for production")
    elif performance_score >= 70:
        print("   👍 Good! Minor improvements recommended")
    elif performance_score >= 50:
        print("   ⚠️  Fair! Several issues need attention")
    else:
        print("   ❌ Poor! Significant issues must be resolved")

def save_consolidated_report(test_results: List[Dict[str, Any]], collected_results: Dict[str, Any]):
    """Save consolidated benchmark report"""
    
    report_data = {
        'timestamp': time.time(),
        'test_execution': {
            'total_tests': len(test_results),
            'successful_tests': len([r for r in test_results if r['success']]),
            'total_duration': sum(r['duration'] for r in test_results),
            'individual_results': test_results
        },
        'collected_results': collected_results,
        'metadata': {
            'python_version': sys.version,
            'platform': sys.platform
        }
    }
    
    output_file = Path(__file__).parent / "comprehensive_benchmark_report.json"
    with open(output_file, 'w') as f:
        json.dump(report_data, f, indent=2)
    
    print(f"\n📄 Comprehensive report saved to: {output_file}")

def main():
    """Run the complete benchmark suite"""
    print("🚀 Starting Complete RLM Plugin Benchmark Suite")
    print("=" * 80)
    
    start_time = time.time()
    
    # Check dependencies
    if not check_dependencies():
        return 1
    
    # Run all tests
    test_results = []
    
    # Generate test data
    result = generate_test_data()
    test_results.append(result)
    
    if not result['success']:
        print("❌ Failed to generate test data. Cannot continue.")
        return 1
    
    # Run basic tests
    test_results.append(run_basic_tests())
    
    # Run edge case tests  
    test_results.append(run_edge_case_tests())
    
    # Run performance benchmarks
    test_results.append(run_performance_benchmarks())
    
    # Run token efficiency analysis
    test_results.append(run_token_efficiency_analysis())
    
    # Collect and consolidate results
    print("\n🔍 Collecting and consolidating results...")
    collected_results = collect_results()
    
    # Generate comprehensive report
    generate_comprehensive_report(test_results, collected_results)
    
    # Save consolidated report
    save_consolidated_report(test_results, collected_results)
    
    end_time = time.time()
    print(f"\n⏱️  Total benchmark suite duration: {end_time - start_time:.2f}s")
    
    # Return success if most tests passed
    successful_tests = len([r for r in test_results if r['success']])
    success_rate = successful_tests / len(test_results) if test_results else 0
    
    return 0 if success_rate >= 0.8 else 1

if __name__ == "__main__":
    sys.exit(main())