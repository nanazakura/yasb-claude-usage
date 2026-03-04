# yasb-claude-usage

[YASB (Yet Another Status Bar)](https://github.com/amnweb/yasb) 向けの Claude Code API 使用量ウィジェットです。

Claude Code をどれくらい使っているか（5時間/7日間の制限に対する消費量）を、Windows のステータスバー「YASB」にリアルタイムで表示します。

![widget example](https://img.shields.io/badge/YASB-Claude_42%25-76946a?style=flat-square)
*↑ こんな感じでバーに表示されます*

## これは何？

Claude Code（Pro / Max プラン）には使用量の上限があります。このウィジェットを入れると、YASB のバー上に現在の消費率がパーセントで常時表示されるようになります。マウスを乗せると、プログレスバー付きの詳細が見れます。

## 必要なもの

- **YASB** がインストール済みであること（[公式サイト](https://github.com/amnweb/yasb)）
- **Python 3.10 以上**（Windows に入っていれば OK。追加ライブラリは不要）
- **Claude Code** のサブスクリプション（Pro / Max プラン）で、一度でもログイン済みであること

## セットアップ手順

### ステップ 1: ダウンロード

好きな場所にクローン（ダウンロード）します。

```bash
git clone https://github.com/nanazakura/yasb-claude-usage.git
```

git を使っていない場合は、GitHub ページの緑色の「Code」ボタン → 「Download ZIP」でもOKです。

### ステップ 2: 動作確認

まずスクリプト単体で動くか確認しましょう。コマンドプロンプトまたは PowerShell で:

```bash
cd ダウンロードした場所/yasb-claude-usage
python claude_usage.py
```

こんな感じの JSON が出力されれば成功です:

```json
{"text": "42%", "five_pct": 42, "seven_pct": 15, ...}
```

エラーが出る場合:
- `python` が見つからない → Python がインストールされていないか、PATH に入っていません
- 認証エラー → Claude Code に一度もログインしていない可能性があります。`claude` コマンドを実行してログインしてください

### ステップ 3: YASB の設定ファイルを編集

YASB の設定ファイル `config.yaml` を開きます。場所は通常 `%USERPROFILE%\.config\yasb\config.yaml` です。

#### 3-1. ウィジェット定義を追加

`widgets:` セクションの中に、以下を追加してください:

```yaml
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
        run_cmd: "python ここにフルパスを入れる/claude_usage.py"
        run_interval: 120000
        return_format: "json"
      callbacks:
        on_left: "toggle_label"
        on_right: "exec"
```

**重要:** `run_cmd` のパスは、ステップ 1 でダウンロードした場所に合わせて書き換えてください。例:

```
run_cmd: "python C:/Tools/yasb-claude-usage/claude_usage.py"
```

スラッシュは `/`（スラッシュ）を使ってください。`\` だと動かないことがあります。

#### 3-2. バーに配置

同じ `config.yaml` の中にある、バーの `widgets:` セクション（`left` / `center` / `right` のいずれか）に `"claude_usage"` を追加します:

```yaml
bars:
  my-bar:
    widgets:
      center: ["clock", "claude_usage"]
```

### ステップ 4: スタイル（任意）

見た目を調整したい場合は `styles.css` に以下を追加できます:

```css
.claude-usage-widget {
  padding: 0 8px;
}
.claude-usage-widget .widget-content .label {
  font-size: 13px;
}
```

### ステップ 5: YASB を再起動

`config.yaml` で `watch_config: true` にしていれば自動で反映されます。されない場合は YASB を再起動してください。

## 使い方

- **左クリック**: 表示の切り替え（パーセントだけ ↔ 5h/7d の両方表示）
- **右クリック**: データを即時更新（通常は2分おきに自動更新）
- **マウスオーバー**: プログレスバー付きの詳細ポップアップ

## 表示される情報

| 項目 | 意味 |
|------|------|
| 5-hour session | 直近5時間の使用率。これが 80% を超えると制限が近い |
| 7-day rolling | 7日間の累積使用率 |
| 7-day Sonnet | 7日間の Sonnet モデル使用率 |
| Extra credits | 追加クレジット（有効な場合のみ表示） |

## うまく動かないとき

- **バーに何も表示されない**: `run_cmd` のパスが間違っている可能性が高いです。ステップ 2 の動作確認をやり直してみてください
- **`??` と表示される**: API へのアクセスに失敗しています。ネットワーク接続と Claude Code のログイン状態を確認してください
- **数値が更新されない**: 2分間のキャッシュがあります。右クリックで即時更新できます

## キャッシュについて

API への負荷を減らすため、取得したデータは `%TEMP%\claude_usage_cache.json` に2分間キャッシュされます。右クリックで強制更新できます。
