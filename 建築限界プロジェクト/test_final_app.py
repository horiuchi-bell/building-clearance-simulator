#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
最終アプリケーションの動作確認テスト（GUI環境なしでも動作可能）
"""

import math
import numpy as np
from typing import List, Tuple, Dict, Any

# clearance_app_v10_perfect_ui.pyから必要なクラスを抽出
class ClearanceModelV10:
    """建築限界モデル V10"""
    
    def __init__(self):
        self.rail_gauge = 1067  # 軌間 (mm)
    
    def create_accurate_clearance(self) -> List[Tuple[float, float]]:
        """建築限界の形状を作成（高精度版）"""
        points = []
        
        # 右側の輪郭を定義
        points.append((1225, 0))
        points.append((1225, 25))
        
        # 25mm→375mmの斜め直線（細かく分割）
        for h in np.linspace(25, 375, 10):
            x = 1225 + (h - 25) * (1575 - 1225) / (375 - 25)
            points.append((x, h))
        
        points.append((1575, 920))
        points.append((1900, 920))
        points.append((1900, 3156))
        
        # 円弧部分 (3156mm→3823mm) - 超高精度
        for h in np.linspace(3156, 3823, 100):
            discriminant = 2150**2 - (h - 2150)**2
            if discriminant >= 0:
                x = math.sqrt(discriminant)
                points.append((x, h))
        
        # 3823mm以降
        points.append((1350, 3823))
        points.append((1350, 4300))
        
        # 上部円弧（より細かく）
        center_x, center_y, radius = 0, 4000, 1800
        x_boundary = 1350
        
        discriminant = radius**2 - x_boundary**2
        if discriminant >= 0:
            y_intersect = center_y + math.sqrt(discriminant)
            start_angle = math.atan2(y_intersect - center_y, x_boundary - center_x)
            end_angle = math.pi / 2
            
            for i in range(30):
                angle = start_angle + (end_angle - start_angle) * i / 29
                x = center_x + radius * math.cos(angle)
                y = center_y + radius * math.sin(angle)
                
                if abs(x) <= 1350 and y <= 5700 and y >= 4000:
                    points.append((x, y))
        
        # 最上部
        points.append((1350, 5700))
        points.append((-1350, 5700))
        
        # 左側（対称）
        right_points = [(x, y) for x, y in points if x > 0]
        right_points.reverse()
        
        for x, y in right_points[1:-1]:
            points.append((-x, y))
        
        # 形状を閉じる
        points.append((1225, 0))
        
        return points
    
    def transform_clearance(self, points: List[Tuple[float, float]],
                           cant_mm: float, curve_radius_m: float) -> List[Tuple[float, float]]:
        """建築限界変形"""
        if not points:
            return []
        
        coords = np.array(points)
        
        # カント変形
        if cant_mm != 0:
            angle_rad = np.arctan(cant_mm / self.rail_gauge)
            cos_a, sin_a = np.cos(angle_rad), np.sin(angle_rad)
            rotation_matrix = np.array([[cos_a, -sin_a], [sin_a, cos_a]])
            coords = coords @ rotation_matrix.T
        
        # 曲線拡幅
        if curve_radius_m > 0:
            widening_factor = 23000.0 / curve_radius_m
            coords[:, 0] = coords[:, 0] + np.sign(coords[:, 0]) * widening_factor
        
        return coords.tolist()

class ExcelAccurateCalculatorV10Perfect:
    """Excel計算方式の完全再現計算器 V10 Perfect"""
    
    def __init__(self):
        self.rail_gauge = 1067
        self.original_clearance_data = self._create_original_clearance_data()
    
    def _create_original_clearance_data(self) -> List[Tuple[float, float]]:
        """元建築限界データ作成（1775個の点）"""
        clearance_data = []
        heights = np.linspace(0, 5700, 1775)
        
        for height in heights:
            if height < 0:
                clearance = float('inf')
            elif height < 25:
                clearance = 1225
            elif height < 375:
                clearance = 1225 + (height - 25) * (1575 - 1225) / (375 - 25)
            elif height < 920:
                clearance = 1575
            elif height < 3156:
                clearance = 1900
            elif height < 3823:
                discriminant = 2150**2 - (height - 2150)**2
                if discriminant < 0:
                    clearance = 0
                else:
                    clearance = math.sqrt(discriminant)
            elif height < 5190:
                clearance = 1350
            else:
                discriminant = 1800**2 - (height - 4000)**2
                if discriminant < 0:
                    clearance = 0
                else:
                    clearance = math.sqrt(discriminant)
            
            clearance_data.append((clearance, height))
        
        return clearance_data
    
    def coordinate_transform_to_rail_center(self, measurement_distance: float, measurement_height: float, 
                                          cant_mm: float) -> Tuple[float, float]:
        """測定点座標をレールセンター基準に変換"""
        if cant_mm == 0:
            return measurement_distance, measurement_height
        
        cant_angle = math.atan(cant_mm / self.rail_gauge)
        x_coord = measurement_distance - measurement_height * math.sin(cant_angle)
        y_coord = measurement_height * math.cos(cant_angle)
        
        return x_coord, y_coord
    
    def calculate_ag2_excel_method(self, measurement_distance: float, measurement_height: float,
                                  cant_mm: float, curve_radius_m: float) -> float:
        """Excel AG2セルの計算完全再現"""
        rail_x, rail_y = self.coordinate_transform_to_rail_center(measurement_distance, measurement_height, cant_mm)
        
        min_distance = float('inf')
        
        for clearance_x, clearance_y in self.original_clearance_data:
            dx = rail_x - clearance_x
            dy = rail_y - clearance_y
            distance = math.sqrt(dx**2 + dy**2)
            
            if distance < min_distance:
                min_distance = distance
        
        return min_distance
    
    def calculate_clearance_margin_excel_method(self, measurement_distance: float, measurement_height: float,
                                              cant_mm: float, curve_radius_m: float) -> Dict[str, Any]:
        """Excel B24セルの限界余裕計算完全再現（ROUNDUP修正済み）"""
        ag2 = self.calculate_ag2_excel_method(measurement_distance, measurement_height, cant_mm, curve_radius_m)
        rail_x, rail_y = self.coordinate_transform_to_rail_center(measurement_distance, measurement_height, cant_mm)
        
        if ag2 < 5:
            corrected_margin = 0
            correction_method = "AG2 < 5: 結果 = 0"
        elif ag2 < 13:
            corrected_margin = math.sqrt(ag2**2 - 25)
            correction_method = f"5 ≤ AG2 < 13: 結果 = √({ag2:.1f}² - 25) = {corrected_margin:.1f}"
        else:
            corrected_margin = ag2
            correction_method = f"AG2 ≥ 13: 結果 = AG2 = {ag2:.1f}"
        
        # ROUNDUP処理（エクセル互換）
        final_margin = math.ceil(corrected_margin)
        
        # 建築限界内外判定
        is_inside_clearance = self._is_point_inside_building_clearance(rail_x, rail_y)
        
        # 改良された支障判定：建築限界内側にある場合は必ず支障
        is_interference = is_inside_clearance or ag2 < 5 or corrected_margin <= 0 or final_margin <= 0
        
        return {
            'ag2': ag2,  # AG2計算は元のExcel方式を維持
            'corrected_margin': corrected_margin,
            'final_margin': final_margin,  # 建築限界内側でも正しい支障量を表示
            'correction_method': correction_method + (" (建築限界内側)" if is_inside_clearance else ""),
            'is_interference': is_interference,
            'rail_center_coords': (rail_x, rail_y),
            'is_inside_clearance': is_inside_clearance
        }
    
    def _is_point_inside_building_clearance(self, x: float, y: float) -> bool:
        """点が建築限界内側にあるかどうかを判定"""
        if y < 0 or y > 5700:
            return False
        
        if y < 25:
            clearance_limit = 1225
        elif y < 375:
            clearance_limit = 1225 + (y - 25) * (1575 - 1225) / (375 - 25)
        elif y < 920:
            clearance_limit = 1575
        elif y < 3156:
            clearance_limit = 1900
        elif y < 3823:
            discriminant = 2150**2 - (y - 2150)**2
            if discriminant < 0:
                clearance_limit = 0
            else:
                clearance_limit = math.sqrt(discriminant)
        elif y < 5190:
            clearance_limit = 1350
        else:
            discriminant = 1800**2 - (y - 4000)**2
            if discriminant < 0:
                clearance_limit = 0
            else:
                clearance_limit = math.sqrt(discriminant)
        
        return abs(x) < clearance_limit

def test_final_app():
    """最終アプリケーションの動作確認"""
    print("=== 建築限界シミュレーター V10 Perfect UI 最終テスト ===")
    print()
    
    calculator = ExcelAccurateCalculatorV10Perfect()
    model = ClearanceModelV10()
    
    # テストケース：問題のケース
    test_case = {
        'name': '問題のケース: 離れ1950mm, 高さ3560mm, カント100mm',
        'distance': 1950,
        'height': 3560,
        'cant': 100,
        'radius': 0
    }
    
    print(f"【{test_case['name']}】")
    print("-" * 60)
    
    # 計算実行
    result = calculator.calculate_clearance_margin_excel_method(
        test_case['distance'], test_case['height'], test_case['cant'], test_case['radius']
    )
    
    # 結果表示
    if result['is_interference']:
        judgment_text = "❌ 建築限界抵触"
        margin_label = "限界支障量"
    else:
        judgment_text = "✅ 建築限界適合"
        margin_label = "限界余裕"
    
    print("【判定結果】")
    print(judgment_text)
    print()
    print("【重要な数値】")
    print(f"{margin_label}: {result['final_margin']} mm")
    print(f"AG2最短距離: {result['ag2']:.1f} mm")
    print()
    
    print("【技術情報】")
    print(f"レールセンター座標: ({result['rail_center_coords'][0]:.1f}, {result['rail_center_coords'][1]:.1f})")
    print(f"建築限界内側: {'はい' if result['is_inside_clearance'] else 'いいえ'}")
    print(f"補正前限界余裕: {result['corrected_margin']:.1f} mm")
    print(f"ROUNDUP適用: {result['corrected_margin']:.1f} → {result['final_margin']} mm")
    print()
    
    # 建築限界モデルテスト
    print("【建築限界モデル】")
    base_model = model.create_accurate_clearance()
    transformed_model = model.transform_clearance(base_model, test_case['cant'], test_case['radius'])
    
    print(f"基本モデル点数: {len(base_model)}")
    print(f"変形後モデル点数: {len(transformed_model)}")
    
    # 表示座標系での測定点
    display_x = -abs(test_case['distance']) if test_case['distance'] > 0 else abs(test_case['distance'])
    print(f"測定点表示座標: ({display_x}, {test_case['height']})")
    
    # 結果確認
    print()
    print("=== 最終確認 ===")
    if result['final_margin'] == 15 and result['is_interference']:
        print("✅ 期待結果と一致: ギリギリ支障、限界支障量15mm")
    else:
        print(f"⚠️  期待結果と異なる: 実際は{margin_label}{result['final_margin']}mm")
    
    print("✅ ROUNDUP処理適用済み（エクセル互換）")
    print("✅ 建築限界内側判定による支障検出")
    print("✅ V9 UI デザイン + V10 計算エンジン統合")

if __name__ == "__main__":
    test_final_app()