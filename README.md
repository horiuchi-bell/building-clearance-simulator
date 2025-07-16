# 建築限界測定システム

OIRANシュミレーターと同等の機能を持つ建築限界測定アプリケーション

## 概要

鉄道の建築限界を測量するための計算システムです。曲線半径とカントの影響を考慮した建築限界の計算と可視化を行います。

## 機能

- **曲線半径とカント入力**: B11, D11セル相当の入力機能
- **測定離れと測定高さ入力**: B14, D14セル相当の入力機能
- **建築限界グラフィック表示**: 基準限界（実線）と変形後限界（点線）
- **測定高さでの必要離れ計算**: D18セル相当の計算機能
- **限界余裕値計算**: 新規実装
- **支障判定**: 安全/支障の自動判定
- **電化方式対応**: 直流/交流/非電化

## ファイル構成

### メインファイル
- `building_limit_gui_fixed.py` - GUIアプリケーション（推奨）
- `building_limit_calculator_fixed.py` - 計算エンジン
- `building_limit_data.json` - 建築限界座標データ

### テスト・分析ファイル
- `building_limit_test.py` - コマンドライン版テストアプリ
- `analyze_oiran_excel.py` - OIRANシュミレーター分析スクリプト
- `extract_building_limit_data.py` - 建築限界データ抽出スクリプト
- `read_pdf.py` - PDF計算式抽出スクリプト

### 参考ファイル（従来版）
- `building_limit_gui.py` - 従来版GUIアプリ
- `building_limit_calculator.py` - 従来版計算エンジン

## 動作環境

- Python 3.8以上
- Windows 10/11, macOS, Linux

## インストール

1. リポジトリのクローン
```bash
git clone https://github.com/your-username/building-limit-system.git
cd building-limit-system
```

2. 仮想環境の作成
```bash
python -m venv venv
source venv/bin/activate  # Linux/macOS
# または
venv\\Scripts\\activate  # Windows
```

3. 依存関係のインストール
```bash
pip install -r requirements.txt
```

## 使用方法

### GUIアプリケーション
```bash
python building_limit_gui_fixed.py
```

### コマンドライン版
```bash
python building_limit_test.py
```

## 入力パラメータ

| 項目 | 単位 | 説明 | OIRANセル対応 |
|------|------|------|---------------|
| 曲線半径 | m | 線路の曲線半径 | B11 |
| カント | mm | レールの傾斜量 | D11 |
| 測定離れ | mm | 軌道中心からの水平距離 | B14 |
| 測定高さ | mm | レール踏面からの垂直距離 | D14 |

## 計算結果

| 項目 | 説明 | OIRANセル対応 |
|------|------|---------------|
| 測定高さでの必要離れ | その高さで建築限界に接触しない最小距離 | D18 |
| 限界余裕値 | 測定点と建築限界の余裕（正の値が安全） | 新規 |
| 判定 | 支障/安全の自動判定 | 新規 |

## 計算式

建築限界の計算は以下の式に基づいています：

### 拡大幅計算
- 一般限界: `W = 23100 / R` (mm)
- 上部限界: `W' = 11550 / R` (mm)

### カント変位計算
- `Li = li - [mi - mi×cos(tan⁻¹(C/g))]`
- `Hi = hi - [li×cos(tan⁻¹(C/g)) - mi×sin(tan⁻¹(C/g))]`

### スラック量
| 曲線半径(m) | スラック(mm) |
|-------------|--------------|
| 200未満 | 20 |
| 240未満 | 15 |
| 320未満 | 10 |
| 440以下 | 5 |
| 440超過 | 0 |

## 技術仕様

- **言語**: Python 3.8+
- **GUI**: tkinter, matplotlib
- **計算**: numpy
- **ファイル処理**: openpyxl, pdfplumber
- **基準**: JR東日本「土木施設実施基準」第8条

## 参考資料

- **基準文書**: 01_第１章_総則（24電SI信管第67号）.pdf（133-135ページ）
- **元データ**: OIRANシュミレーター（修正）20231215.xlsx
- **対象シート**: 限界余裕測定図 片線

## グラフィック表示

- **青い実線**: 基準建築限界（カント・曲線影響なし）
- **赤い点線**: 変形後建築限界（カント・曲線影響あり）
- **黒い×印**: 測定ポイント
- **茶色い太線**: レール面
- **黒い縦線**: 軌道中心線

## 使用例

```python
from building_limit_calculator_fixed import BuildingLimitCalculatorFixed

# 計算器の初期化
calc = BuildingLimitCalculatorFixed("直流")

# OIRANデフォルト値での計算
result = calc.check_clearance(
    measurement_distance=2110,  # 測定離れ(mm)
    measurement_height=3150,    # 測定高さ(mm)
    radius=160,                 # 曲線半径(m)
    cant=105                    # カント(mm)
)

print(f"判定: {result['status']}")
print(f"必要離れ: {result['required_clearance']:.1f}mm")
print(f"限界余裕値: {result['clearance_margin']:.1f}mm")
```

## ライセンス

MIT License

## 更新履歴

### v1.0.0 (2025-07-16)
- 初版リリース
- OIRANシュミレーター互換機能実装
- 建築限界計算ロジック実装
- GUI版・コマンドライン版作成

### v1.1.0 (2025-07-16)
- 計算精度向上
- 測定高さでの必要離れ計算実装
- 限界余裕値計算実装
- グラフィック表示改善（実線・点線対応）
- PDFの132ページ図形準拠

## 貢献

プルリクエストやイシューの報告を歓迎します。

## サポート

技術的な質問やバグ報告は、GitHubのIssuesページをご利用ください。