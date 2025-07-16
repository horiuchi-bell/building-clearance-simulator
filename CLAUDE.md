# Claude Code プロジェクト設定

## プロジェクト情報
- プロジェクト名: outlook-スケジュール調整
- 作成日: 2025-07-13
- 説明: Outlookのスケジュール調整機能を開発するプロジェクト

## 開発環境
- プラットフォーム: Linux
- OS: Linux 5.15.153.1-microsoft-standard-WSL2 (WSL2)

## 🌏 日本語対応設定
**重要：必ず日本語でユーザーとやり取りを行う**

### ユーザー情報
- エンジニア以外の方向けの設定
- 専門用語は使わず、分かりやすい日本語で説明する
- システム設定は重要な変更の場合のみ許可を求める

### 🔤 日本語フォント設定
**重要: 文字化け防止のため、すべてのアプリケーションで日本語フォントを適切に設定する**

#### OS別推奨フォント
- **Windows**: Meiryo UI, Yu Gothic UI, MS Gothic
- **macOS**: Hiragino Sans, Hiragino Kaku Gothic Pro
- **Linux/WSL**: Noto Sans CJK JP, Takao Gothic, IPAexGothic

#### tkinterアプリケーションでの実装方針
1. **動的フォント検出**: システムで利用可能な日本語フォントを自動検出
2. **フォールバック機能**: 日本語フォントが見つからない場合の代替設定
3. **全ウィジェット対応**: Label, Text, Listbox等すべてに日本語フォント適用
4. **サイズ調整**: 読みやすさを考慮したフォントサイズ設定

#### フォント設定コード例
```python
def setup_japanese_font(self):
    system = platform.system()
    if system == "Windows":
        self.default_font = ("Meiryo UI", 9)
    elif system == "Darwin":
        self.default_font = ("Hiragino Sans", 12)
    else:  # Linux/WSL
        # 利用可能な日本語フォントを検出して設定
        import tkinter.font as tkFont
        japanese_fonts = ["Noto Sans CJK JP", "Takao Gothic", "IPAexGothic"]
        # 詳細実装は個別ファイル参照
```

### 作業方針
1. **自動化**: Pythonなどの必要なツールは自動でインストール
2. **説明**: コードの内容は分かりやすく簡潔に説明
3. **安全性**: PC全体に影響する変更は事前に日本語で詳しく説明
4. **記録**: すべての作業を履歴として保存
5. **日本語対応**: すべてのGUIアプリケーションで文字化け防止措置を実装

## 🔍 アプリ・マクロ開発の要件定義プロセス
**重要：詳細な要件定義なしには作業を開始しない**

### 開発前の必須確認事項
1. **目的・背景**: なぜこのアプリ・マクロが必要か？
2. **対象ユーザー**: 誰が使うのか？（本人のみ/チーム/一般ユーザー）
3. **使用環境**: どこで使うのか？（個人PC/社内システム/クラウド）
4. **データ**: どんなデータを扱うのか？（ファイル形式/サイズ/機密性）
5. **機能要件**: 具体的に何をしたいのか？
6. **非機能要件**: 
   - 性能（処理時間・データ量の上限）
   - セキュリティ（認証・権限・暗号化の必要性）
   - 保守性（更新頻度・メンテナンス担当者）

### 詳細ヒアリングのアプローチ
- **不明な点は必ず質問**: 「一般的に〜だと思いますが」という推測で進めない
- **具体例を求める**: 「例えば、どのようなデータですか？」
- **制約を確認**: 「使えないツールや制限はありますか？」
- **成功基準を明確化**: 「どうなったら完成ですか？」

### エラー処理・デバッグ設計
- **エラーログ出力**: 問題発生時の調査用
- **入力値検証**: 不正なデータでの処理防止
- **例外処理**: 予期しない状況への対処
- **デバッグ情報**: 動作状況の可視化
- **バックアップ機能**: データ消失防止

### 📋 一般的な考慮事項チェックリスト
開発前に以下の項目を確認し、不明な点は必ずユーザーに質問する：

#### データ関連
- [ ] 入力データの形式・サイズ・文字コード
- [ ] データの保存場所・バックアップの必要性
- [ ] 個人情報・機密情報の取り扱い
- [ ] 複数人での同時利用の可能性

#### 操作・UI関連
- [ ] 操作の複雑さ（初心者でも使えるか）
- [ ] 処理時間（長時間処理の進捗表示）
- [ ] 処理の取り消し・やり直し機能
- [ ] 設定の保存・復元機能

#### 運用・保守関連
- [ ] 定期的な更新・メンテナンスの必要性
- [ ] 他のシステム・ソフトとの連携
- [ ] バージョンアップ時の互換性
- [ ] 担当者変更時の引き継ぎ方法

#### セキュリティ関連
- [ ] パスワード・認証の必要性
- [ ] ファイルの暗号化・アクセス制限
- [ ] ログの記録・監査の必要性
- [ ] 外部サービスとの通信

## 📁 プロジェクト管理ルール
- 新しいプロジェクトフォルダごとにこの設定をコピー
- 過去のやり取りを記録して次回参照可能にする
- 修正・訂正時は間違いを削除し、正しい結果のみ残す
- GitHub連携での保管に対応

## 🔑 GitHub設定とAPI管理
**重要：機密情報の安全な管理**

### 設定ファイル構成
```
my-project/
├── github_config.json      # 上位フォルダ（全プロジェクト共通）
└── outlook-スケジュール調整/
    ├── project_config.json  # プロジェクト固有設定
    └── CLAUDE.md           # このファイル
```

### 設定ファイルの読み込み
```python
import json
import os

def load_github_config():
    """GitHub設定を読み込む"""
    # 上位フォルダの共通設定
    parent_config_path = "../github_config.json"
    if os.path.exists(parent_config_path):
        with open(parent_config_path, 'r', encoding='utf-8') as f:
            parent_config = json.load(f)
    
    # プロジェクト固有設定
    project_config_path = "project_config.json"
    if os.path.exists(project_config_path):
        with open(project_config_path, 'r', encoding='utf-8') as f:
            project_config = json.load(f)
    
    return parent_config, project_config

def get_github_token():
    """GitHub Personal Access Tokenを取得"""
    parent_config, _ = load_github_config()
    return parent_config.get('github', {}).get('personal_access_token')

def get_github_user():
    """GitHubユーザー情報を取得"""
    parent_config, _ = load_github_config()
    github_info = parent_config.get('github', {})
    return {
        'username': github_info.get('username'),
        'email': github_info.get('email')
    }
```

### Gitコマンドでの自動設定
```bash
# 設定ファイルから自動読み込み
python -c "
import json
with open('../github_config.json', 'r') as f:
    config = json.load(f)
    github = config['github']
    git = config['git']
    
import subprocess
subprocess.run(['git', 'config', 'user.name', git['user_name']])
subprocess.run(['git', 'config', 'user.email', git['user_email']])
subprocess.run(['git', 'remote', 'set-url', 'origin', f'https://{github[\"personal_access_token\"]}@github.com/{github[\"username\"]}/{github[\"repositories\"][\"outlook_scheduler\"][\"name\"]}.git'])
"
```

### セキュリティ対策
- **設定ファイルは.gitignoreで除外**
- **Personal Access Tokenは最小権限（repo）のみ**
- **定期的なトークンの更新**
- **本番環境では環境変数を使用**

## 利用可能なコマンド

### Python環境
```bash
source venv/bin/activate    # 仮想環境を有効化
python script.py           # Pythonスクリプト実行
pip list                   # インストール済みパッケージ一覧
```

### ビルド
```bash
# プロジェクト固有のビルドコマンドが決まったらここに記載
```

### テスト
```bash
source venv/bin/activate && pytest  # Pythonテスト実行
```

### リント・コード品質
```bash
source venv/bin/activate && black .     # コード整形
source venv/bin/activate && flake8 .    # コード品質チェック
source venv/bin/activate && isort .     # import文整理
```

### 開発ツール
```bash
source venv/bin/activate && jupyter lab  # Jupyter Lab起動
source venv/bin/activate && ipython      # IPython起動
```

### Office・PDF処理
```bash
source venv/bin/activate && python office_test.py  # テストファイル実行
# Excel: openpyxl, xlsxwriter, xlrd
# Word: python-docx  
# PowerPoint: python-pptx
# PDF: PyPDF2, pdfplumber, reportlab, pymupdf
```

## プロジェクト構造
```
outlook-スケジュール調整/
├── CLAUDE.md (このファイル - 基本設定)
├── project_history.md (プロジェクト履歴)
├── venv/ (Python仮想環境)
│   ├── bin/activate (仮想環境有効化スクリプト)
│   └── lib/python3.12/site-packages/ (インストール済みライブラリ)
└── (今後のファイル)
    ├── outlook_scheduler.py (メインスクリプト)
    ├── config/ (設定ファイル)
    └── docs/ (ドキュメント)
```

## ⚠️ 重要な設定変更について
システム全体に影響を与える可能性がある作業を行う場合は、以下の形式で事前にお知らせします：

**🚨 重要：システム設定変更の可能性**
- 変更内容：（具体的な説明）
- 影響範囲：（どの部分に影響するか）
- 理由：（なぜ必要か）
- 許可をお願いします：はい/いいえ

## 注意事項
- このプロジェクトは新規作成されたため、まだ具体的な設定がありません
- 必要に応じて自動的にファイルや設定を追加します
- 開発が進むにつれて、このファイルを自動更新します