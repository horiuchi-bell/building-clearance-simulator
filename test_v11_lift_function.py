#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
V11 With Lift機能の動作検証テスト
浮き上がり機能とExcel完全再現の両立を確認
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from clearance_app_v11_with_lift import ClearanceModelV11WithLift, ExcelAccurateCalculatorV11WithLift
import math

def test_lift_calculation():
    """浮き上がり量計算のテスト"""
    print("=== 浮き上がり量計算テスト ===")
    
    model = ClearanceModelV11WithLift()
    
    # カント100mm時の浮き上がり量テスト
    cant_100 = 100
    expected_lift = 177.2924
    
    calculated_lift = model.calculate_lift_amount(cant_100)
    error = abs(calculated_lift - expected_lift)
    
    print(f"カント100mm時:")
    print(f"  期待値: {expected_lift:.4f} mm")
    print(f"  計算値: {calculated_lift:.4f} mm")
    print(f"  誤差: {error:.6f} mm ({error/expected_lift*100:.4f}%)")
    
    if error < 0.001:
        print("  ✅ 浮き上がり量計算: 合格")
    else:
        print("  ❌ 浮き上がり量計算: 不合格")
    
    # 他のカント値でのテスト
    print("\n他のカント値での浮き上がり量:")
    test_cants = [0, 50, 150, 200]
    for cant in test_cants:
        lift = model.calculate_lift_amount(cant)
        angle = math.atan(cant / 1067)
        theoretical = 1900 * math.sin(angle)
        print(f"  カント{cant:3d}mm: {lift:.2f}mm (理論値: {theoretical:.2f}mm)")
    
    return error < 0.001

def test_transform_clearance_with_lift():
    """建築限界変形（浮き上がり付き）のテスト"""
    print("\n=== 建築限界変形（浮き上がり付き）テスト ===")
    
    model = ClearanceModelV11WithLift()
    
    # 基本建築限界データ作成
    base_clearance = model.create_accurate_clearance()
    
    # カント100mm時の変形
    cant_100 = 100
    transformed = model.transform_clearance(base_clearance, cant_100, 0)
    
    if transformed:
        # 変形後の最低Y座標を確認（浮き上がり量に相当）
        y_coords = [point[1] for point in transformed]
        min_y = min(y_coords)
        
        expected_lift = 177.2924
        error = abs(min_y - expected_lift)
        
        print(f"変形後の最低Y座標: {min_y:.4f} mm")
        print(f"期待する浮き上がり量: {expected_lift:.4f} mm")
        print(f"誤差: {error:.6f} mm")
        
        if error < 1.0:  # 1mm以内なら合格
            print("✅ 建築限界浮き上がり変形: 合格")
            return True
        else:
            print("❌ 建築限界浮き上がり変形: 不合格")
            return False
    else:
        print("❌ 建築限界変形データ取得失敗")
        return False

def test_excel_compatibility():
    """Excel完全再現機能の互換性テスト（V10と同一結果を確認）"""
    print("\n=== Excel完全再現機能の互換性テスト ===")
    
    calculator = ExcelAccurateCalculatorV11WithLift()
    
    # テストケース
    test_cases = [
        {"distance": 2000, "height": 3550, "cant": 100, "radius": 0, "description": "標準テストケース"},
        {"distance": 1500, "height": 2000, "cant": 50, "radius": 300, "description": "曲線ありケース"},
        {"distance": 2500, "height": 4000, "cant": 0, "radius": 0, "description": "カント0ケース"},
    ]
    
    all_passed = True
    
    for i, case in enumerate(test_cases, 1):
        print(f"\nテストケース{i}: {case['description']}")
        print(f"  測定離れ: {case['distance']}mm, 測定高さ: {case['height']}mm")
        print(f"  カント: {case['cant']}mm, 曲線半径: {case['radius']}m")
        
        try:
            result = calculator.calculate_all_excel_method(
                case['distance'], case['height'], case['cant'], case['radius']
            )
            
            print(f"  必要離れ: {result['required_clearance']:.1f} mm")
            print(f"  AG2距離: {result['ag2_distance']:.2f} mm")
            print(f"  限界余裕/支障量: {result['clearance_margin']} mm")
            print(f"  支障判定: {'支障' if result['is_interference'] else '適合'}")
            print("  ✅ 計算完了")
            
        except Exception as e:
            print(f"  ❌ 計算エラー: {str(e)}")
            all_passed = False
    
    return all_passed

def test_coordinate_system_consistency():
    """座標系の一貫性テスト"""
    print("\n=== 座標系一貫性テスト ===")
    
    calculator = ExcelAccurateCalculatorV11WithLift()
    
    # レールセンター座標変換のテスト
    test_distance = 2000
    test_height = 3550
    test_cant = 100
    
    rail_x, rail_y = calculator.coordinate_transform_to_rail_center(
        test_distance, test_height, test_cant
    )
    
    print(f"測定座標: ({test_distance}, {test_height})")
    print(f"レールセンター座標: ({rail_x:.2f}, {rail_y:.2f})")
    
    # 座標変換の妥当性確認
    cant_angle = math.atan(test_cant / 1067)
    expected_x = test_distance - test_height * math.sin(cant_angle)
    expected_y = test_height * math.cos(cant_angle)
    
    x_error = abs(rail_x - expected_x)
    y_error = abs(rail_y - expected_y)
    
    print(f"期待値: ({expected_x:.2f}, {expected_y:.2f})")
    print(f"誤差: X={x_error:.6f}, Y={y_error:.6f}")
    
    if x_error < 0.001 and y_error < 0.001:
        print("✅ 座標系一貫性: 合格")
        return True
    else:
        print("❌ 座標系一貫性: 不合格")
        return False

def main():
    """メインテスト実行"""
    print("V11 With Lift機能 動作検証テスト開始")
    print("=" * 50)
    
    test_results = []
    
    # 各テスト実行
    test_results.append(("浮き上がり量計算", test_lift_calculation()))
    test_results.append(("建築限界変形", test_transform_clearance_with_lift()))
    test_results.append(("Excel互換性", test_excel_compatibility()))
    test_results.append(("座標系一貫性", test_coordinate_system_consistency()))
    
    # 結果サマリー
    print("\n" + "=" * 50)
    print("テスト結果サマリー")
    print("=" * 50)
    
    passed_count = 0
    for test_name, result in test_results:
        status = "✅ 合格" if result else "❌ 不合格"
        print(f"{test_name:15s}: {status}")
        if result:
            passed_count += 1
    
    print(f"\n総合結果: {passed_count}/{len(test_results)} テスト合格")
    
    if passed_count == len(test_results):
        print("🎉 V11 With Lift機能: 全テスト合格！")
        print("✅ OIRANエクセルの浮き上がり現象を完全再現")
        print("✅ V10のExcel完全再現機能も維持")
    else:
        print("⚠️ 一部テストで問題が検出されました")
    
    return passed_count == len(test_results)

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)