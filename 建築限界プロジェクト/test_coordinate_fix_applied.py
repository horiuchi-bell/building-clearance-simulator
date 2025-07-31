#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
座標系修正適用後のテスト
"""

import math
import numpy as np
from typing import List, Tuple, Dict, Any

# clearance_app_v10_perfect_ui.pyから必要なクラスを抽出（修正版）
class ClearanceModelV10Fixed:
    """建築限界モデル V10 修正版"""
    
    def __init__(self):
        self.rail_gauge = 1067
    
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

class ExcelAccurateCalculatorV10PerfectFixed:
    """Excel計算方式の完全再現計算器 V10 Perfect 修正版"""
    
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
    
    def _calculate_display_coordinates(self, measurement_distance: float, measurement_height: float, 
                                     cant_mm: float) -> Tuple[float, float]:
        """表示座標計算（カント変形考慮、座標系一致版）"""
        if cant_mm == 0:
            # カント0の場合は従来通り
            display_x = -abs(measurement_distance) if measurement_distance > 0 else abs(measurement_distance)
            return display_x, measurement_height
        
        # レールセンター座標を取得
        rail_x, rail_y = self.coordinate_transform_to_rail_center(measurement_distance, measurement_height, cant_mm)
        
        # レールセンター座標をカント変形して表示座標に変換
        cant_angle = math.atan(cant_mm / self.rail_gauge)
        cos_a, sin_a = math.cos(cant_angle), math.sin(cant_angle)
        
        # カント変形（建築限界モデルと同じ変形）
        display_x = rail_x * cos_a - rail_y * sin_a
        display_y = rail_x * sin_a + rail_y * cos_a
        
        # V9形式の表示（左側表示）
        if measurement_distance > 0:
            display_x = -abs(display_x)
        
        return display_x, display_y
    
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

def test_coordinate_fix_applied():
    """座標系修正適用後のテスト"""
    print("=== 座標系修正適用後のテスト ===")
    print()
    
    calculator = ExcelAccurateCalculatorV10PerfectFixed()
    model = ClearanceModelV10Fixed()
    
    # テストケース：問題のケース
    distance = 1950
    height = 3560
    cant = 100
    radius = 0
    
    print(f"【テスト条件】")
    print(f"離れ: {distance}mm, 高さ: {height}mm, カント: {cant}mm")
    print()
    
    # レールセンター座標変換
    rail_x, rail_y = calculator.coordinate_transform_to_rail_center(distance, height, cant)
    print(f"1. レールセンター座標: ({rail_x:.1f}, {rail_y:.1f})")
    
    # 建築限界内外判定
    is_inside_rail = calculator._is_point_inside_building_clearance(rail_x, rail_y)
    print(f"   建築限界内側判定: {'はい' if is_inside_rail else 'いいえ'}")
    print()
    
    # 修正された表示座標
    display_x, display_y = calculator._calculate_display_coordinates(distance, height, cant)
    print(f"2. 修正後表示座標: ({display_x:.1f}, {display_y:.1f})")
    print()
    
    # 建築限界モデル作成
    base_model = model.create_accurate_clearance()
    transformed_model = model.transform_clearance(base_model, cant, radius)
    
    print(f"3. 建築限界モデル: {len(transformed_model)}点")
    
    # 表示座標での最近点検索
    min_distance = float('inf')
    closest_point = None
    
    for mx, my in transformed_model:
        dx = display_x - mx
        dy = display_y - my
        distance_to_point = math.sqrt(dx**2 + dy**2)
        
        if distance_to_point < min_distance:
            min_distance = distance_to_point
            closest_point = (mx, my)
    
    if closest_point:
        print(f"   最近建築限界点: ({closest_point[0]:.1f}, {closest_point[1]:.1f})")
        print(f"   距離: {min_distance:.1f}mm")
        
        # 表示座標系での内外判定
        is_inside_display = abs(display_x) < abs(closest_point[0])
        print(f"   表示座標系での内側判定: {'はい' if is_inside_display else 'いいえ'}")
        print()
        
        # 座標系一致確認
        print(f"4. 座標系一致確認:")
        print(f"   レールセンター座標系: {'内側' if is_inside_rail else '外側'}")
        print(f"   表示座標系: {'内側' if is_inside_display else '外側'}")
        
        if is_inside_rail == is_inside_display:
            print("   ✅ 座標系が一致しています")
            return True
        else:
            print("   ❌ 座標系に矛盾があります")
            return False
    else:
        print("   最近点が見つかりません")
        return False

def main():
    """メインテスト実行"""
    result = test_coordinate_fix_applied()
    
    print()
    print("=== 最終結果 ===")
    if result:
        print("✅ 座標系修正が正常に適用されました")
        print("   支障時の赤丸が建築限界内側に正しく表示されます")
    else:
        print("❌ まだ問題が残っています")
        print("   さらなる修正が必要です")

if __name__ == "__main__":
    main()