#!/usr/bin/env python3
"""
Validation script to ensure all benchmark components are working
"""

import sys
from pathlib import Path

def validate_files():
    """Validate all required files exist"""
    print("🔍 Validating benchmark suite files...")
    
    required_files = [
        "generate_test_data.py",
        "run_benchmarks.py", 
        "token_efficiency_analyzer.py",
        "edge_case_tests.py",
        "run_full_benchmark_suite.py",
        "test_basic_functionality.py",
        "run_performance_test.py",
        "README.md",
        "BENCHMARK_SUMMARY.md"
    ]
    
    missing_files = []
    for file in required_files:
        if not Path(file).exists():
            missing_files.append(file)
    
    if missing_files:
        print(f"❌ Missing files: {missing_files}")
        return False
    
    print(f"✅ All {len(required_files)} benchmark files present")
    return True

def validate_test_data():
    """Validate test data was generated correctly"""
    print("\n🔍 Validating test data...")
    
    data_dir = Path("test_data")
    if not data_dir.exists():
        print("❌ test_data directory not found")
        return False
    
    required_data = [
        ("large_dataset.json", 1024 * 1024),  # > 1MB
        ("large_dataset.csv", 1024 * 1024),   # > 1MB  
        ("application.log", 1024 * 1024),     # > 1MB
        ("large_codebase", 0)                 # Directory
    ]
    
    for name, min_size in required_data:
        path = data_dir / name
        if not path.exists():
            print(f"❌ Missing test data: {name}")
            return False
        
        if path.is_file():
            size = path.stat().st_size
            if size < min_size:
                print(f"❌ {name} too small: {size} bytes")
                return False
            print(f"✅ {name}: {size / (1024*1024):.1f}MB")
        else:
            file_count = len(list(path.glob("**/*.py")))
            print(f"✅ {name}: {file_count} Python files")
    
    return True

def validate_dependencies():
    """Validate required dependencies are available"""
    print("\n🔍 Validating dependencies...")
    
    required_packages = ['psutil', 'numpy']
    optional_packages = ['matplotlib']
    
    missing_required = []
    missing_optional = []
    
    for package in required_packages:
        try:
            __import__(package)
            print(f"✅ {package}")
        except ImportError:
            missing_required.append(package)
            print(f"❌ {package} (required)")
    
    for package in optional_packages:
        try:
            __import__(package)
            print(f"✅ {package} (optional)")
        except ImportError:
            missing_optional.append(package)
            print(f"⚠️  {package} (optional)")
    
    if missing_required:
        print(f"\n❌ Missing required packages: {missing_required}")
        print(f"Install with: pip install {' '.join(missing_required)}")
        return False
    
    if missing_optional:
        print(f"\n⚠️  Missing optional packages: {missing_optional}")
        print(f"Install with: pip install {' '.join(missing_optional)}")
    
    return True

def validate_imports():
    """Validate core RLM components can be imported"""
    print("\n🔍 Validating RLM imports...")
    
    # Add project root to path
    project_root = Path(__file__).parent.parent
    sys.path.insert(0, str(project_root))
    
    try:
        from src.context_router import ContextData, ContextRouter
        print("✅ context_router")
        
        from src.strategies.file_chunking import FileBasedChunking  
        print("✅ file_chunking")
        
        from src.strategies.structural_decomp import StructuralDecomposition
        print("✅ structural_decomp")
        
        from src.repl_engine import RLMREPLEngine
        print("✅ repl_engine")
        
        return True
        
    except ImportError as e:
        print(f"❌ Import failed: {e}")
        return False

def validate_basic_functionality():
    """Quick test of core functionality"""
    print("\n🔍 Validating basic functionality...")
    
    try:
        from src.context_router import ContextData, ContextRouter
        
        # Test configuration
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
        print("✅ ContextRouter created")
        
        # Test with real data
        test_file = Path("test_data/large_dataset.json")
        if test_file.exists():
            context_data = ContextData.from_file(str(test_file))
            should_activate, strategy, metadata = router.should_activate_rlm(context_data)
            
            if should_activate:
                print(f"✅ RLM activation: {strategy}")
                return True
            else:
                print("❌ RLM should have activated for large file")
                return False
        else:
            print("❌ Test file not found")
            return False
            
    except Exception as e:
        print(f"❌ Functionality test failed: {e}")
        return False

def main():
    """Run all validation checks"""
    print("🚀 RLM Benchmark Suite Validation")
    print("=" * 50)
    
    checks = [
        ("Files", validate_files),
        ("Test Data", validate_test_data), 
        ("Dependencies", validate_dependencies),
        ("Imports", validate_imports),
        ("Functionality", validate_basic_functionality)
    ]
    
    results = []
    for name, check_func in checks:
        try:
            result = check_func()
            results.append(result)
        except Exception as e:
            print(f"❌ {name} validation failed: {e}")
            results.append(False)
    
    print("\n" + "=" * 50)
    print("📊 VALIDATION SUMMARY")
    print("=" * 50)
    
    passed = sum(results)
    total = len(results)
    
    for i, (name, result) in enumerate(zip([c[0] for c in checks], results)):
        status = "✅" if result else "❌"
        print(f"{status} {name}")
    
    print(f"\n📈 Overall: {passed}/{total} checks passed")
    
    if passed == total:
        print("🎉 Benchmark suite is fully functional!")
        print("\n🚀 Ready to run:")
        print("   python run_performance_test.py")
        print("   python run_full_benchmark_suite.py")
        return 0
    else:
        print("❌ Some validation checks failed")
        print("Please fix the issues above before running benchmarks")
        return 1

if __name__ == "__main__":
    sys.exit(main())