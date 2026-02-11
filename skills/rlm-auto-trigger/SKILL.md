# RLM Auto-Trigger Skill

## Trigger Conditions

This skill automatically activates the RLM (Recursive Language Model) plugin when:

1. **Large Files**: Reading files larger than 50KB
2. **High Token Count**: Processing content exceeding 100,000 estimated tokens
3. **Multiple Files**: Working with more than 10 files simultaneously
4. **Structured Data**: Processing large JSON, CSV, XML files over 100KB
5. **Log Analysis**: Analyzing log files larger than 50KB

## Activation Pattern

```python
# Automatic activation
content = read("/path/to/large/file.json")  # Auto-triggers if >50KB

# Manual override
with RLM() as rlm:
    result = rlm.process(file_path="/path/to/file")
```

## Configuration

Edit `~/.config/opencode/plugins/rlm/.claude-plugin/plugin.json`:

```json
{
  "auto_trigger": {
    "enabled": true,
    "file_size_kb": 50,
    "token_count": 100000,
    "file_count": 10
  }
}
```

## Disable Auto-Trigger

To disable automatic activation:

```python
# In code
os.environ['RLM_AUTO_TRIGGER'] = 'false'

# Or in config
"auto_trigger": {"enabled": false}
```