# 建築限界シミュレーター V10 Perfect UI

## 概要
建築限界シミュレーター V10 Perfect UIは、V9の優れたUIデザインとV10のExcel完全再現計算エンジンを統合したアプリケーションです。

## 主要ファイル

### メインアプリケーション
- `clearance_app_v10_perfect_ui.py` - 最終版アプリケーション（V9 UI + V10計算エンジン）

### テストファイル
- `test_specific_case.py` - 特定ケース（離れ1950、高さ3560、カント100）の詳細テスト
- `test_final_app.py` - アプリケーション最終動作テスト
- `final_integration_test.py` - 最終統合テスト
- `test_measurement_point_fix.py` - 測定点表示位置の修正確認
- `verify_app_final.py` - アプリケーション最終確認

### 分析・検証ファイル
- `analyze_precision_difference.py` - 計算精度差異の分析
- `verify_model_display_problem.py` - モデル表示問題の検証
- `fix_coordinate_system.py` - 座標系修正案
- `test_coordinate_fix_applied.py` - 座標系修正適用後のテスト

## 主な機能と修正内容

### 2025-07-29の修正
1. **ROUNDUP/ROUNDDOWN処理**
   - 支障時：ROUNDUP（math.ceil）
   - 非支障時：ROUNDDOWN（math.floor）

2. **表示の簡潔化**
   - 最短距離表記を削除
   - 限界余裕/限界支障のみ表示

3. **座標系の矛盾解決**
   - 測定点の表示座標もカント変形を適用（後に修正）
   - レールセンター座標系と表示座標系の一致

4. **測定点表示位置の修正**
   - カントを設定しても測定点は移動しない
   - 入力座標をそのまま表示

## 実行方法
```bash
python3 clearance_app_v10_perfect_ui.py
```

## 注意事項
- tkinterが必要（GUI環境）
- Python 3.6以上推奨

## 今後の課題
- 建築限界数値データ方線シートの分析
- カント時のモデル表示位置（0レベルから浮く問題）の調査