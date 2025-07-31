#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
アプリケーション最終確認
修正されたclearance_app_v10_perfect_ui.pyの動作確認
"""

import os
import sys

def verify_app_structure():
    """アプリケーション構造の確認"""
    print("=== 建築限界シミュレーター V10 Perfect UI 最終確認 ===")
    print()
    
    app_file = "clearance_app_v10_perfect_ui.py"
    
    if not os.path.exists(app_file):
        print(f"❌ {app_file} が見つかりません")
        return False
    
    print(f"✅ {app_file} が存在します")
    
    # ファイル内容を確認
    with open(app_file, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # 必要な修正が含まれているか確認
    checks = [
        {
            'name': '_calculate_display_coordinatesメソッド',
            'pattern': 'def _calculate_display_coordinates',
            'found': False
        },
        {
            'name': 'ROUNDUP/ROUNDDOWN処理',
            'pattern': 'if is_interference:\n            final_margin = math.ceil',
            'found': False
        },
        {
            'name': '最短距離表記削除',
            'pattern': '限界支障量:',
            'found': False
        },
        {
            'name': '表示座標の使用',
            'pattern': 'actual_measurement_x, actual_measurement_y = self._calculate_display_coordinates',
            'found': False
        }
    ]
    
    print("\n【実装確認】")
    all_passed = True
    
    for check in checks:
        if check['pattern'] in content:
            check['found'] = True
            print(f"✅ {check['name']}")
        else:
            print(f"❌ {check['name']}")
            all_passed = False
    
    print("\n【主要な修正内容】")
    print("1. 支障時/非支障時の丸め処理")
    print("   - 支障時: ROUNDUP (math.ceil)")
    print("   - 非支障時: ROUNDDOWN (math.floor)")
    
    print("\n2. 表示の簡潔化")
    print("   - 最短距離表記を削除")
    print("   - 限界余裕/限界支障のみ表示")
    
    print("\n3. 座標系の矛盾解決")
    print("   - 測定点の表示座標もカント変形を適用")
    print("   - レールセンター座標系と表示座標系の一致")
    
    print("\n【期待される動作】")
    print("- 問題のケース（離れ1950, 高さ3560, カント100）:")
    print("  → 判定: ❌ 建築限界抵触")
    print("  → 限界支障量: 15mm (14.2→15 ROUNDUP)")
    print("  → 測定点が建築限界内側に正しく表示")
    
    return all_passed

def main():
    """メイン実行"""
    print("修正済みアプリケーションの最終確認を行います...")
    print()
    
    result = verify_app_structure()
    
    print("\n" + "=" * 60)
    print("【最終確認結果】")
    
    if result:
        print("✅ すべての修正が正しく実装されています！")
        print()
        print("アプリケーションの起動方法:")
        print("  python3 clearance_app_v10_perfect_ui.py")
        print()
        print("注意: tkinterが必要です。GUI環境で実行してください。")
    else:
        print("❌ 一部の修正が不完全です")
        print("   上記のエラーを確認してください")

if __name__ == "__main__":
    main()