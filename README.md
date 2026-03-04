# yasb-claude-usage

Claude Code API usage widget for [YASB (Yet Another Status Bar)](https://github.com/amnweb/yasb).

Displays real-time Claude Code session usage (5-hour, 7-day, Sonnet) on your YASB bar via the CustomWidget mechanism.

## Requirements

- Python 3.10+
- No external libraries required (stdlib only)
- Active Claude Code subscription with OAuth credentials at `~/.claude/.credentials.json`

## Setup

### 1. Clone

```bash
git clone https://github.com/nanazakura/yasb-claude-usage.git
```

### 2. YASB Config (`config.yaml`)

Add a CustomWidget to your YASB bar configuration:

```yaml
widgets:
  claude_usage:
    type: "yasb.custom.CustomWidget"
    options:
      label: "\uf4fc {data[text]}"
      label_alt: "\uf4fc 5h:{data[five_pct]}% 7d:{data[seven_pct]}%"
      label_max_length: 32
      class_name: "claude-usage-widget"
      tooltip: true
      tooltip_label: "{data[tooltip]}"
      exec_options:
        run_cmd: "python /path/to/yasb-claude-usage/claude_usage.py"
        run_interval: 120000  # 2 minutes (ms)
        return_format: "json"
      callbacks:
        on_left: "toggle_label"
        on_right: "exec"
```

Then add `claude_usage` to one of your bar rows:

```yaml
bars:
  my-bar:
    widgets:
      left: [...]
      center: [...]
      right: ["claude_usage", ...]
```

### 3. YASB Styles (`styles.css`)

```css
.claude-usage-widget {
  padding: 0 8px;
}
.claude-usage-widget .widget-content .label {
  font-size: 13px;
}
```

## Output Format

The script outputs a JSON object with these fields:

| Field | Example | Description |
|-------|---------|-------------|
| `text` | `"42%"` | 5-hour usage percentage (primary display) |
| `five_pct` | `42` | 5-hour session utilization % |
| `seven_pct` | `15` | 7-day rolling utilization % |
| `sonnet_pct` | `8` | 7-day Sonnet utilization % |
| `five_reset` | `"2h30m"` | Time until 5-hour reset |
| `seven_reset` | `"3d12h"` | Time until 7-day reset |
| `sonnet_reset` | `"5d08h"` | Time until Sonnet reset |
| `status` | `"low"` | `low` (<50%), `medium` (50-79%), `high` (>=80%) |
| `tooltip` | `"Claude Code Usage\n..."` | Multi-line plain-text tooltip with progress bars |

## Usage

```bash
# Normal (uses 2-minute cache)
python claude_usage.py

# Force refresh (bypass cache)
python claude_usage.py --force
```

## Cache

Usage data is cached at `%TEMP%\claude_usage_cache.json` for 2 minutes to avoid excessive API calls. Right-click the widget (with the config above) to force a refresh.
