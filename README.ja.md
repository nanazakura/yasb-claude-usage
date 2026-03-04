# yasb-claude-usage

[YASB (Yet Another Status Bar)](https://github.com/amnweb/yasb) 向けの Claude Code API 使用量ウィジェット。

Claude Code のセッション使用量（5時間、7日間、Sonnet）を YASB バー上にリアルタイム表示します。CustomWidget の仕組みを利用しており、ネイティブウィジェットの開発は不要です。

## 必要要件

- Python 3.10+
- 外部ライブラリ不要（標準ライブラリのみ）
- Claude Code サブスクリプション（OAuth 認証情報が `~/.claude/.credentials.json` に必要）

## セットアップ

### 1. クローン

```bash
git clone https://github.com/nanazakura/yasb-claude-usage.git
```

### 2. YASB 設定 (`config.yaml`)

CustomWidget をウィジェット定義に追加:

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
        run_interval: 120000  # 2分 (ms)
        return_format: "json"
      callbacks:
        on_left: "toggle_label"
        on_right: "exec"
```

バーの任意の位置に `claude_usage` を追加:

```yaml
bars:
  my-bar:
    widgets:
      left: [...]
      center: [...]
      right: ["claude_usage", ...]
```

### 3. YASB スタイル (`styles.css`)

```css
.claude-usage-widget {
  padding: 0 8px;
}
.claude-usage-widget .widget-content .label {
  font-size: 13px;
}
```

## 出力フォーマット

スクリプトは以下のフィールドを持つ JSON オブジェクトを出力します:

| フィールド | 例 | 説明 |
|-----------|-----|------|
| `text` | `"42%"` | 5時間使用率（メイン表示） |
| `five_pct` | `42` | 5時間セッション使用率 % |
| `seven_pct` | `15` | 7日間ローリング使用率 % |
| `sonnet_pct` | `8` | 7日間 Sonnet 使用率 % |
| `five_reset` | `"2h30m"` | 5時間リセットまでの時間 |
| `seven_reset` | `"3d12h"` | 7日間リセットまでの時間 |
| `sonnet_reset` | `"5d08h"` | Sonnet リセットまでの時間 |
| `status` | `"low"` | `low` (<50%), `medium` (50-79%), `high` (>=80%) |
| `tooltip` | `"Claude Code Usage\n..."` | プログレスバー付き詳細テキスト |

## 使い方

```bash
# 通常実行（2分間のキャッシュ使用）
python claude_usage.py

# キャッシュを無視して最新データを取得
python claude_usage.py --force
```

## キャッシュ

使用量データは `%TEMP%\claude_usage_cache.json` に2分間キャッシュされます。上記設定でウィジェットを右クリックすると強制更新できます。
