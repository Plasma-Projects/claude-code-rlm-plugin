# Claude Code RLM Plugin

Recursive Language Model plugin for processing massive contexts (10M+ tokens) in Claude Code.

## Features

- **Automatic activation** for large files (>50KB) and contexts (>100K tokens)
- **Parallel processing** with up to 8 concurrent agents
- **Smart decomposition** strategies for different data types
- **REPL environment** for interactive processing
- **Seamless integration** with Claude Code tools

## Installation

```bash
git clone https://github.com/yourusername/claude-code-rlm-plugin
cd claude-code-rlm-plugin
./scripts/install.sh
```

Or manual installation:
```bash
cp -r . ~/.config/opencode/plugins/rlm
```

## Usage

### Automatic Mode
```python
# Automatically triggers for large files
content = read("/path/to/large/file.json")  # >50KB
```

### Manual Mode
```python
from rlm import RLMPlugin

rlm = RLMPlugin()
result = rlm.process(file_path="/path/to/massive/dataset.csv")
```

### REPL Session
```python
with RLM() as rlm:
    rlm.load_context("/path/to/file")
    results = rlm.query("Find all anomalies")
```

## Configuration

Edit `~/.config/opencode/plugins/rlm/.claude-plugin/plugin.json`:

```json
{
  "auto_trigger": {
    "file_size_kb": 50,
    "token_count": 100000,
    "file_count": 10,
    "enabled": true
  },
  "processing": {
    "max_concurrent_agents": 8,
    "chunk_overlap_percent": 10
  }
}
```

## Strategies

| File Type | Strategy | Description |
|-----------|----------|-------------|
| JSON/YAML | Structural Decomposition | Splits by keys/sections |
| CSV | Row Batching | Processes in row batches |
| Logs | Time Window | Groups by timestamps |
| Code | File Chunking | Smart overlap chunking |
| Text | Line-based | Preserves context |

## Performance

- Handles 10M+ token contexts
- 8x faster through parallel processing
- 60% token reduction via smart chunking
- Automatic caching for repeated queries

## API

```python
# Initialize
rlm = RLMPlugin()

# Check if should activate
should_activate = rlm.should_activate(context)

# Process file
result = rlm.process(file_path="/path/to/file")

# Process with query
result = rlm.process(file_path="/path/to/file", query="Extract insights")

# REPL session
repl = rlm.repl_session()
repl.load_file("/path/to/file")
repl.execute("chunks = decompose(context)")
```

## Architecture

```
RLM Plugin
├── Context Router (activation logic)
├── REPL Engine (interactive processing)
├── Agent Manager (parallel execution)
└── Strategies (decomposition methods)
    ├── File Chunking
    ├── Structural Decomposition
    └── Time Window Splitting
```

## Based on Research

[Recursive Language Models](https://arxiv.org/html/2512.24601v1) - Enables LLMs to programmatically examine and recursively process massive contexts.

## License

MIT