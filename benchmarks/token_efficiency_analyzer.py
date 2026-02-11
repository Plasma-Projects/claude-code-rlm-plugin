#!/usr/bin/env python3
"""
Token efficiency analyzer for RLM plugin
Detailed analysis of token usage patterns and optimization effectiveness
"""

import sys
import json
import time
from pathlib import Path
from typing import Dict, List, Tuple, Optional
from dataclasses import dataclass, asdict
try:
    import matplotlib.pyplot as plt
    import numpy as np
    HAS_PLOTTING = True
except ImportError:
    HAS_PLOTTING = False

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.context_router import ContextData, ContextRouter


@dataclass
class TokenAnalysis:
    """Token usage analysis results"""
    file_path: str
    file_size_kb: float
    original_tokens: int
    
    # RLM analysis
    rlm_activated: bool
    strategy_used: Optional[str]
    chunks_created: int
    tokens_per_chunk: List[int]
    
    # Efficiency metrics
    token_reduction_ratio: float
    chunk_efficiency_score: float
    processing_overhead_tokens: int
    
    # Context window utilization
    context_window_utilization: float
    wasted_tokens: int
    optimal_chunk_size: int


class TokenEfficiencyAnalyzer:
    """Analyze token efficiency of RLM strategies"""
    
    def __init__(self, context_window_size: int = 200_000):
        self.context_window_size = context_window_size
        self.config = {
            'auto_trigger': {
                'enabled': True,
                'token_count': 50_000,
                'file_size_kb': 100,
                'file_count': 5
            }
        }
        self.router = ContextRouter(self.config)
        self.analyses: List[TokenAnalysis] = []
    
    def analyze_file(self, file_path: Path) -> TokenAnalysis:
        """Perform comprehensive token analysis on a file"""
        print(f"🔍 Analyzing: {file_path.name}")
        
        # Basic file metrics
        file_size_kb = file_path.stat().st_size / 1024
        original_tokens = self._estimate_tokens_file(file_path)
        
        # Create context data
        context_data = ContextData.from_file(str(file_path))
        
        # Check RLM activation
        should_activate, strategy, metadata = self.router.should_activate_rlm(context_data)
        
        if should_activate:
            # Analyze RLM chunking efficiency
            chunks_analysis = self._analyze_chunks(file_path, strategy, metadata)
            
            analysis = TokenAnalysis(
                file_path=str(file_path),
                file_size_kb=file_size_kb,
                original_tokens=original_tokens,
                rlm_activated=True,
                strategy_used=strategy,
                chunks_created=chunks_analysis['count'],
                tokens_per_chunk=chunks_analysis['token_distribution'],
                token_reduction_ratio=chunks_analysis['reduction_ratio'],
                chunk_efficiency_score=chunks_analysis['efficiency_score'],
                processing_overhead_tokens=chunks_analysis['overhead_tokens'],
                context_window_utilization=chunks_analysis['context_utilization'],
                wasted_tokens=chunks_analysis['wasted_tokens'],
                optimal_chunk_size=chunks_analysis['optimal_chunk_size']
            )
        else:
            # Direct processing analysis
            analysis = TokenAnalysis(
                file_path=str(file_path),
                file_size_kb=file_size_kb,
                original_tokens=original_tokens,
                rlm_activated=False,
                strategy_used="direct",
                chunks_created=1,
                tokens_per_chunk=[original_tokens],
                token_reduction_ratio=1.0,
                chunk_efficiency_score=1.0 if original_tokens <= self.context_window_size else 0.0,
                processing_overhead_tokens=0,
                context_window_utilization=min(1.0, original_tokens / self.context_window_size),
                wasted_tokens=max(0, self.context_window_size - original_tokens),
                optimal_chunk_size=original_tokens
            )
        
        self.analyses.append(analysis)
        return analysis
    
    def _estimate_tokens_file(self, file_path: Path) -> int:
        """Estimate tokens in a file"""
        try:
            with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                content = f.read()
            return self._estimate_tokens_content(content)
        except Exception:
            # Fallback to size-based estimation
            return file_path.stat().st_size // 4
    
    def _estimate_tokens_content(self, content: str) -> int:
        """Estimate tokens in content"""
        # More sophisticated token estimation
        words = content.split()
        
        # Account for punctuation, special characters
        punctuation_factor = 1.1
        
        # Account for code vs natural language
        if self._looks_like_code(content):
            # Code typically has more tokens per word
            code_factor = 1.4
        else:
            code_factor = 1.0
        
        # Base estimation: ~1.3 tokens per word
        estimated_tokens = len(words) * 1.3 * punctuation_factor * code_factor
        
        return int(estimated_tokens)
    
    def _looks_like_code(self, content: str) -> bool:
        """Detect if content looks like code"""
        code_indicators = [
            'def ', 'function ', 'class ', 'import ', 'from ',
            '{', '}', '()', '=>', '==', '!=', '&&', '||'
        ]
        
        indicator_count = sum(1 for indicator in code_indicators if indicator in content)
        return indicator_count >= 3
    
    def _analyze_chunks(self, file_path: Path, strategy: str, metadata: Dict) -> Dict:
        """Analyze chunking efficiency for a strategy"""
        # Get strategy object
        strategy_obj = self.router.get_strategy(strategy)
        
        # Create chunks
        try:
            chunks = strategy_obj.decompose(str(file_path), metadata)
        except Exception:
            # Fallback chunking
            chunks = self._create_fallback_chunks(file_path)
        
        # Analyze token distribution
        token_distribution = []
        total_chunk_tokens = 0
        
        for chunk in chunks:
            chunk_content = str(chunk.get('content', ''))
            chunk_tokens = self._estimate_tokens_content(chunk_content)
            token_distribution.append(chunk_tokens)
            total_chunk_tokens += chunk_tokens
        
        # Calculate efficiency metrics
        original_tokens = self._estimate_tokens_file(file_path)
        
        # Reduction ratio (how much we reduced token processing)
        if original_tokens > 0:
            reduction_ratio = total_chunk_tokens / original_tokens
        else:
            reduction_ratio = 1.0
        
        # Efficiency score (how well chunks fit context windows)
        efficiency_score = self._calculate_efficiency_score(token_distribution)
        
        # Overhead tokens (metadata, chunk headers, etc.)
        overhead_tokens = max(0, total_chunk_tokens - original_tokens)
        
        # Context window utilization
        avg_chunk_size = np.mean(token_distribution) if token_distribution else 0
        context_utilization = min(1.0, avg_chunk_size / self.context_window_size)
        
        # Wasted tokens (unused context window space)
        wasted_tokens = sum(max(0, self.context_window_size - tokens) 
                           for tokens in token_distribution)
        
        # Optimal chunk size analysis
        optimal_chunk_size = self._find_optimal_chunk_size(original_tokens)
        
        return {
            'count': len(chunks),
            'token_distribution': token_distribution,
            'reduction_ratio': reduction_ratio,
            'efficiency_score': efficiency_score,
            'overhead_tokens': overhead_tokens,
            'context_utilization': context_utilization,
            'wasted_tokens': wasted_tokens,
            'optimal_chunk_size': optimal_chunk_size
        }
    
    def _create_fallback_chunks(self, file_path: Path) -> List[Dict]:
        """Create simple fallback chunks"""
        try:
            with open(file_path, 'r') as f:
                content = f.read()
            
            chunk_size = 50_000  # characters
            chunks = []
            
            for i in range(0, len(content), chunk_size):
                chunk = content[i:i+chunk_size]
                chunks.append({
                    'content': chunk,
                    'id': len(chunks)
                })
            
            return chunks
        except Exception:
            return [{'content': 'fallback', 'id': 0}]
    
    def _calculate_efficiency_score(self, token_distribution: List[int]) -> float:
        """Calculate how efficiently chunks use available context window"""
        if not token_distribution:
            return 0.0
        
        total_score = 0
        for tokens in token_distribution:
            if tokens <= self.context_window_size:
                # Efficiency is how much of context window is used
                efficiency = tokens / self.context_window_size
                total_score += efficiency
            else:
                # Penalty for exceeding context window
                total_score += 0.1
        
        return total_score / len(token_distribution)
    
    def _find_optimal_chunk_size(self, total_tokens: int) -> int:
        """Find optimal chunk size for given total tokens"""
        if total_tokens <= self.context_window_size:
            return total_tokens
        
        # Find chunk size that minimizes waste while staying under limit
        target_utilization = 0.9  # Use 90% of context window
        optimal_size = int(self.context_window_size * target_utilization)
        
        return optimal_size
    
    def analyze_batch(self, file_paths: List[Path]) -> List[TokenAnalysis]:
        """Analyze multiple files"""
        print(f"🔬 Analyzing {len(file_paths)} files for token efficiency...")
        
        for file_path in file_paths:
            try:
                self.analyze_file(file_path)
            except Exception as e:
                print(f"   ❌ Error analyzing {file_path.name}: {e}")
        
        return self.analyses
    
    def generate_efficiency_report(self) -> Dict:
        """Generate comprehensive efficiency report"""
        if not self.analyses:
            return {"error": "No analyses available"}
        
        # Overall statistics
        total_files = len(self.analyses)
        rlm_activated_count = len([a for a in self.analyses if a.rlm_activated])
        
        # Token efficiency metrics
        avg_reduction_ratio = np.mean([a.token_reduction_ratio for a in self.analyses])
        avg_efficiency_score = np.mean([a.chunk_efficiency_score for a in self.analyses])
        avg_context_utilization = np.mean([a.context_window_utilization for a in self.analyses])
        
        total_wasted_tokens = sum(a.wasted_tokens for a in self.analyses)
        total_overhead_tokens = sum(a.processing_overhead_tokens for a in self.analyses)
        
        # RLM-specific metrics
        rlm_analyses = [a for a in self.analyses if a.rlm_activated]
        
        if rlm_analyses:
            avg_chunks_per_file = np.mean([a.chunks_created for a in rlm_analyses])
            strategies_used = list(set(a.strategy_used for a in rlm_analyses if a.strategy_used))
        else:
            avg_chunks_per_file = 0
            strategies_used = []
        
        # Size-based analysis
        size_buckets = {
            'small (< 100KB)': [a for a in self.analyses if a.file_size_kb < 100],
            'medium (100KB - 1MB)': [a for a in self.analyses if 100 <= a.file_size_kb < 1024],
            'large (> 1MB)': [a for a in self.analyses if a.file_size_kb >= 1024]
        }
        
        size_analysis = {}
        for bucket_name, bucket_analyses in size_buckets.items():
            if bucket_analyses:
                size_analysis[bucket_name] = {
                    'count': len(bucket_analyses),
                    'avg_efficiency': np.mean([a.chunk_efficiency_score for a in bucket_analyses]),
                    'avg_utilization': np.mean([a.context_window_utilization for a in bucket_analyses])
                }
        
        return {
            'summary': {
                'total_files': total_files,
                'rlm_activated': rlm_activated_count,
                'rlm_activation_rate': rlm_activated_count / total_files if total_files > 0 else 0
            },
            'efficiency_metrics': {
                'avg_token_reduction_ratio': avg_reduction_ratio,
                'avg_chunk_efficiency_score': avg_efficiency_score,
                'avg_context_window_utilization': avg_context_utilization,
                'total_wasted_tokens': total_wasted_tokens,
                'total_overhead_tokens': total_overhead_tokens
            },
            'rlm_metrics': {
                'avg_chunks_per_file': avg_chunks_per_file,
                'strategies_used': strategies_used
            },
            'size_analysis': size_analysis
        }
    
    def print_report(self):
        """Print detailed efficiency report"""
        report = self.generate_efficiency_report()
        
        if 'error' in report:
            print(f"❌ {report['error']}")
            return
        
        print("\n" + "=" * 60)
        print("📊 TOKEN EFFICIENCY ANALYSIS REPORT")
        print("=" * 60)
        
        # Summary
        summary = report['summary']
        print(f"\n📈 Summary:")
        print(f"   Files Analyzed: {summary['total_files']}")
        print(f"   RLM Activated: {summary['rlm_activated']}")
        print(f"   Activation Rate: {summary['rlm_activation_rate']:.1%}")
        
        # Efficiency metrics
        metrics = report['efficiency_metrics']
        print(f"\n⚡ Efficiency Metrics:")
        print(f"   Avg Token Reduction: {metrics['avg_token_reduction_ratio']:.2f}x")
        print(f"   Avg Chunk Efficiency: {metrics['avg_chunk_efficiency_score']:.2f}")
        print(f"   Avg Context Utilization: {metrics['avg_context_window_utilization']:.1%}")
        print(f"   Total Wasted Tokens: {metrics['total_wasted_tokens']:,}")
        print(f"   Total Overhead Tokens: {metrics['total_overhead_tokens']:,}")
        
        # RLM metrics
        rlm = report['rlm_metrics']
        print(f"\n🔄 RLM Metrics:")
        print(f"   Avg Chunks per File: {rlm['avg_chunks_per_file']:.1f}")
        print(f"   Strategies Used: {', '.join(rlm['strategies_used'])}")
        
        # Size analysis
        size_analysis = report['size_analysis']
        print(f"\n📏 Size-based Analysis:")
        for size_bucket, metrics in size_analysis.items():
            print(f"   {size_bucket}:")
            print(f"     Count: {metrics['count']}")
            print(f"     Avg Efficiency: {metrics['avg_efficiency']:.2f}")
            print(f"     Avg Utilization: {metrics['avg_utilization']:.1%}")
        
        # Individual file details
        print(f"\n📋 Individual File Analysis:")
        for analysis in self.analyses:
            rlm_status = "RLM" if analysis.rlm_activated else "DIRECT"
            print(f"   {Path(analysis.file_path).name:<25} | {rlm_status:<6} | "
                  f"{analysis.file_size_kb:>8.1f}KB | {analysis.original_tokens:>8,} tokens | "
                  f"Efficiency: {analysis.chunk_efficiency_score:.2f}")
    
    def save_analysis(self, output_path: Optional[Path] = None):
        """Save analysis results to JSON"""
        if output_path is None:
            output_path = Path(__file__).parent / "token_efficiency_analysis.json"
        
        data = {
            'timestamp': time.time(),
            'context_window_size': self.context_window_size,
            'config': self.config,
            'analyses': [asdict(analysis) for analysis in self.analyses],
            'report': self.generate_efficiency_report()
        }
        
        with open(output_path, 'w') as f:
            json.dump(data, f, indent=2)
        
        print(f"\n💾 Analysis saved to: {output_path}")
    
    def create_visualizations(self, output_dir: Optional[Path] = None):
        """Create visualization charts"""
        if output_dir is None:
            output_dir = Path(__file__).parent / "visualizations"
        
        output_dir.mkdir(exist_ok=True)
        
        if not self.analyses:
            print("❌ No data to visualize")
            return
        
        # Token distribution chart
        self._create_token_distribution_chart(output_dir)
        
        # Efficiency comparison chart
        self._create_efficiency_comparison_chart(output_dir)
        
        # Context utilization chart
        self._create_utilization_chart(output_dir)
        
        print(f"📊 Visualizations saved to: {output_dir}")
    
    def _create_token_distribution_chart(self, output_dir: Path):
        """Create token distribution visualization"""
        try:
            import matplotlib.pyplot as plt
            
            fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(15, 6))
            
            # Original tokens vs file size
            file_sizes = [a.file_size_kb for a in self.analyses]
            original_tokens = [a.original_tokens for a in self.analyses]
            colors = ['red' if a.rlm_activated else 'blue' for a in self.analyses]
            
            ax1.scatter(file_sizes, original_tokens, c=colors, alpha=0.7)
            ax1.set_xlabel('File Size (KB)')
            ax1.set_ylabel('Original Tokens')
            ax1.set_title('Token Count vs File Size')
            ax1.legend(['RLM Activated', 'Direct Processing'])
            
            # Chunk efficiency distribution
            rlm_analyses = [a for a in self.analyses if a.rlm_activated]
            if rlm_analyses:
                efficiencies = [a.chunk_efficiency_score for a in rlm_analyses]
                ax2.hist(efficiencies, bins=20, alpha=0.7, color='green')
                ax2.set_xlabel('Chunk Efficiency Score')
                ax2.set_ylabel('Frequency')
                ax2.set_title('RLM Chunk Efficiency Distribution')
            
            plt.tight_layout()
            plt.savefig(output_dir / 'token_distribution.png', dpi=300)
            plt.close()
            
        except ImportError:
            print("   ⚠️  matplotlib not available, skipping token distribution chart")
    
    def _create_efficiency_comparison_chart(self, output_dir: Path):
        """Create efficiency comparison chart"""
        try:
            import matplotlib.pyplot as plt
            
            rlm_analyses = [a for a in self.analyses if a.rlm_activated]
            direct_analyses = [a for a in self.analyses if not a.rlm_activated]
            
            if not rlm_analyses and not direct_analyses:
                return
            
            fig, ax = plt.subplots(figsize=(10, 6))
            
            # Compare efficiency scores
            if rlm_analyses:
                rlm_efficiencies = [a.chunk_efficiency_score for a in rlm_analyses]
                ax.bar(['RLM Processing'], [np.mean(rlm_efficiencies)], 
                      color='green', alpha=0.7, label='RLM')
            
            if direct_analyses:
                direct_efficiencies = [a.chunk_efficiency_score for a in direct_analyses]
                ax.bar(['Direct Processing'], [np.mean(direct_efficiencies)], 
                      color='blue', alpha=0.7, label='Direct')
            
            ax.set_ylabel('Average Efficiency Score')
            ax.set_title('Processing Efficiency Comparison')
            ax.legend()
            
            plt.tight_layout()
            plt.savefig(output_dir / 'efficiency_comparison.png', dpi=300)
            plt.close()
            
        except ImportError:
            print("   ⚠️  matplotlib not available, skipping efficiency comparison chart")
    
    def _create_utilization_chart(self, output_dir: Path):
        """Create context window utilization chart"""
        try:
            import matplotlib.pyplot as plt
            
            fig, ax = plt.subplots(figsize=(12, 6))
            
            # Context utilization vs file size
            file_sizes = [a.file_size_kb for a in self.analyses]
            utilizations = [a.context_window_utilization for a in self.analyses]
            colors = ['red' if a.rlm_activated else 'blue' for a in self.analyses]
            
            scatter = ax.scatter(file_sizes, utilizations, c=colors, alpha=0.7, s=50)
            ax.set_xlabel('File Size (KB)')
            ax.set_ylabel('Context Window Utilization')
            ax.set_title('Context Window Utilization vs File Size')
            ax.axhline(y=1.0, color='red', linestyle='--', alpha=0.5, label='100% Utilization')
            ax.legend(['RLM Activated', 'Direct Processing', '100% Utilization'])
            
            plt.tight_layout()
            plt.savefig(output_dir / 'context_utilization.png', dpi=300)
            plt.close()
            
        except ImportError:
            print("   ⚠️  matplotlib not available, skipping utilization chart")


def main():
    """Run token efficiency analysis"""
    data_dir = Path(__file__).parent / "test_data"
    
    if not data_dir.exists():
        print("❌ Test data directory not found. Please run generate_test_data.py first.")
        return 1
    
    # Get test files
    test_files = []
    for pattern in ["*.json", "*.csv", "*.log", "*.py"]:
        test_files.extend(data_dir.glob(pattern))
        test_files.extend(data_dir.glob(f"**/{pattern}"))
    
    if not test_files:
        print("❌ No test files found.")
        return 1
    
    # Run analysis
    analyzer = TokenEfficiencyAnalyzer()
    analyzer.analyze_batch(test_files)
    analyzer.print_report()
    analyzer.save_analysis()
    analyzer.create_visualizations()
    
    return 0


if __name__ == "__main__":
    sys.exit(main())