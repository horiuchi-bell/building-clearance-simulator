#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
特定ケースの詳細確認テスト
離れ1950、高さ3560、カント100での計算検証
"""

import math
import numpy as np
from typing import List, Tuple, Dict, Any

class DetailedTestCalculator:
    """詳細テスト用計算器"""
    
    def __init__(self):
        self.rail_gauge = 1067
        self.original_clearance_data = self._create_original_clearance_data()
    
    def _create_original_clearance_data(self) -> List[Tuple[float, float]]:
        clearance_data = []
        heights = np.linspace(0, 5700, 1775)
        
        for height in heights:
            if height < 25:
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
        if cant_mm == 0:
            return measurement_distance, measurement_height
        
        cant_angle = math.atan(cant_mm / self.rail_gauge)
        x_coord = measurement_distance - measurement_height * math.sin(cant_angle)
        y_coord = measurement_height * math.cos(cant_angle)
        
        return x_coord, y_coord
    
    def calculate_ag2_excel_method(self, measurement_distance: float, measurement_height: float,
                                  cant_mm: float, curve_radius_m: float) -> float:
        rail_x, rail_y = self.coordinate_transform_to_rail_center(measurement_distance, measurement_height, cant_mm)
        
        min_distance = float('inf')
        
        for clearance_x, clearance_y in self.original_clearance_data:
            dx = rail_x - clearance_x
            dy = rail_y - clearance_y
            distance = math.sqrt(dx**2 + dy**2)
            
            if distance < min_distance:
                min_distance = distance
        
        return min_distance
    
    def _get_clearance_at_height(self, height):
        """指定高さでの建築限界値を取得"""
        if height < 25:
            return 1225
        elif height < 375:
            return 1225 + (height - 25) * (1575 - 1225) / (375 - 25)
        elif height < 920:
            return 1575
        elif height < 3156:
            return 1900
        elif height < 3823:
            discriminant = 2150**2 - (height - 2150)**2
            if discriminant < 0:
                return 0
            else:
                return math.sqrt(discriminant)
        elif height < 5190:
            return 1350
        else:
            discriminant = 1800**2 - (height - 4000)**2
            if discriminant < 0:
                return 0
            else:
                return math.sqrt(discriminant)
    
    def _is_point_inside_building_clearance(self, x: float, y: float) -> bool:
        clearance_limit = self._get_clearance_at_height(y)
        return abs(x) < clearance_limit
    
    def create_accurate_clearance_model(self) -> List[Tuple[float, float]]:
        """正確な建築限界モデル作成"""
        points = []
        
        # 右側の輪郭を定義
        points.append((1225, 0))      # レールレベルから開始
        points.append((1225, 25))     # 25mmまで
        points.append((1575, 375))    # 375mmまで斜めの直線
        points.append((1575, 920))    # 920mmまで
        points.append((1900, 920))    # 920mmから最大幅
        points.append((1900, 3156))   # 3156mmまで
        
        # 円弧部分 (3156mm→3823mm) - より細かく
        for h in np.linspace(3156, 3823, 50):
            discriminant = 2150**2 - (h - 2150)**2
            if discriminant >= 0:
                x = math.sqrt(discriminant)
                points.append((x, h))
        
        # 3823mm以降
        points.append((1350, 3823))
        points.append((1350, 4300))
        
        # 上部円弧
        center_x, center_y, radius = 0, 4000, 1800
        x_boundary = 1350
        
        discriminant = radius**2 - x_boundary**2
        if discriminant >= 0:
            y_intersect = center_y + math.sqrt(discriminant)
            start_angle = math.atan2(y_intersect - center_y, x_boundary - center_x)
            end_angle = math.pi / 2
            
            for i in range(20):
                angle = start_angle + (end_angle - start_angle) * i / 19
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
    
    def transform_clearance_model(self, points: List[Tuple[float, float]], cant_mm: float) -> List[Tuple[float, float]]:
        """建築限界モデル変形"""
        if not points or cant_mm == 0:
            return points
        
        coords = np.array(points)
        
        # カント変形
        angle_rad = np.arctan(cant_mm / self.rail_gauge)
        cos_a, sin_a = np.cos(angle_rad), np.sin(angle_rad)
        rotation_matrix = np.array([[cos_a, -sin_a], [sin_a, cos_a]])
        coords = coords @ rotation_matrix.T
        
        return coords.tolist()

def test_specific_case():
    """特定ケースの詳細テスト"""
    print("=== 特定ケーステスト ===")
    print("離れ1950、高さ3560、カント100での計算検証")
    print()
    
    calculator = DetailedTestCalculator()
    
    # テスト条件
    distance = 1950
    height = 3560
    cant = 100
    radius = 0
    
    print(f"テスト条件:")
    print(f"・測定離れ: {distance} mm")
    print(f"・測定高さ: {height} mm") 
    print(f"・カント: {cant} mm")
    print(f"・曲線半径: {radius} m")
    print()
    
    # 座標変換
    rail_x, rail_y = calculator.coordinate_transform_to_rail_center(distance, height, cant)
    print(f"レールセンター座標: ({rail_x:.1f}, {rail_y:.1f})")
    
    # その高さでの建築限界値
    clearance_limit = calculator._get_clearance_at_height(rail_y)
    print(f"高さ{rail_y:.1f}mmでの建築限界値: {clearance_limit:.1f} mm")
    
    # 建築限界内外判定
    is_inside = calculator._is_point_inside_building_clearance(rail_x, rail_y)
    print(f"建築限界内側判定: {'はい' if is_inside else 'いいえ'}")
    
    # AG2計算
    ag2 = calculator.calculate_ag2_excel_method(distance, height, cant, radius)
    print(f"AG2距離: {ag2:.1f} mm")
    
    # 限界余裕計算
    if ag2 < 5:
        corrected_margin = 0
        correction_method = "AG2 < 5: 結果 = 0"
    elif ag2 < 13:
        corrected_margin = math.sqrt(ag2**2 - 25)
        correction_method = f"5 ≤ AG2 < 13: 結果 = √({ag2:.1f}² - 25) = {corrected_margin:.1f}"
    else:
        corrected_margin = ag2
        correction_method = f"AG2 ≥ 13: 結果 = AG2 = {ag2:.1f}"
    
    final_margin = math.ceil(corrected_margin)
    is_interference = is_inside or ag2 < 5 or corrected_margin <= 0 or final_margin <= 0
    
    print(f"補正前限界余裕: {corrected_margin:.1f} mm")
    print(f"最終限界余裕: {final_margin} mm")
    print(f"判定: {'❌ 建築限界抵触' if is_interference else '✅ 建築限界適合'}")
    print()
    
    # 建築限界モデルの精度確認
    print("=== 建築限界モデル精度確認 ===")
    base_model = calculator.create_accurate_clearance_model()
    transformed_model = calculator.transform_clearance_model(base_model, cant)
    
    # 測定点の表示座標（V9形式）
    if distance > 0:
        display_x = -abs(distance)
    else:
        display_x = abs(distance)
    
    print(f"測定点表示座標: ({display_x}, {height})")
    
    # 変形後建築限界で測定点近辺の座標を確認
    print("\n変形後建築限界の測定点近辺座標:")
    for i, (x, y) in enumerate(transformed_model):
        if abs(y - height) < 50:  # 測定高さ±50mm範囲
            distance_to_measurement = math.sqrt((display_x - x)**2 + (height - y)**2)
            print(f"  座標{i}: ({x:.1f}, {y:.1f}), 測定点からの距離: {distance_to_measurement:.1f}mm")
    
    print()
    print("=== 期待結果との比較 ===")
    print("期待: ギリギリ支障、限界支障量15mm")
    print(f"実際: {'支障' if is_interference else '適合'}, 限界余裕{final_margin}mm")
    
    if final_margin != 15:
        print("⚠️  期待値と異なります。建築限界モデルまたは計算に問題がある可能性があります。")
    else:
        print("✅ 期待値と一致")

if __name__ == "__main__":
    test_specific_case()