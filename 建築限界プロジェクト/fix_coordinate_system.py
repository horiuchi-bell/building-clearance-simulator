#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
座標系の矛盾を解決するための修正案
"""

import math
import numpy as np
from typing import List, Tuple

class CoordinateSystemFixer:
    """座標系修正器"""
    
    def __init__(self):
        self.rail_gauge = 1067
    
    def coordinate_transform_to_rail_center(self, measurement_distance: float, measurement_height: float, 
                                          cant_mm: float) -> Tuple[float, float]:
        """レールセンター座標変換"""
        if cant_mm == 0:
            return measurement_distance, measurement_height
        
        cant_angle = math.atan(cant_mm / self.rail_gauge)
        x_coord = measurement_distance - measurement_height * math.sin(cant_angle)
        y_coord = measurement_height * math.cos(cant_angle)
        
        return x_coord, y_coord
    
    def coordinate_transform_to_display(self, measurement_distance: float, measurement_height: float, 
                                      cant_mm: float) -> Tuple[float, float]:
        """表示座標変換（カント変形考慮）"""
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
    
    def test_coordinate_fix(self, measurement_distance: float, measurement_height: float, cant_mm: float):
        """座標系修正テスト"""
        print("=== 座標系修正テスト ===")
        print(f"入力: 離れ{measurement_distance}mm, 高さ{measurement_height}mm, カント{cant_mm}mm")
        print()
        
        # 従来の表示座標
        old_display_x = -abs(measurement_distance) if measurement_distance > 0 else abs(measurement_distance)
        old_display_y = measurement_height
        print(f"1. 従来の表示座標: ({old_display_x}, {old_display_y})")
        
        # レールセンター座標
        rail_x, rail_y = self.coordinate_transform_to_rail_center(measurement_distance, measurement_height, cant_mm)
        print(f"2. レールセンター座標: ({rail_x:.1f}, {rail_y:.1f})")
        
        # 修正された表示座標
        new_display_x, new_display_y = self.coordinate_transform_to_display(measurement_distance, measurement_height, cant_mm)
        print(f"3. 修正後表示座標: ({new_display_x:.1f}, {new_display_y:.1f})")
        print()
        
        # その高さでの建築限界値
        clearance_limit = self.get_clearance_at_height(rail_y)
        is_inside_rail = abs(rail_x) < clearance_limit
        print(f"4. レールセンター座標系:")
        print(f"   高さ{rail_y:.1f}mmでの建築限界値: {clearance_limit:.1f}mm")
        print(f"   建築限界内側判定: {'はい' if is_inside_rail else 'いいえ'}")
        print()
        
        # 修正後の表示座標での建築限界モデル作成
        model_points = self.create_consistent_clearance_model(cant_mm)
        
        # 測定点近辺の建築限界座標検索
        near_points = []
        for i, (mx, my) in enumerate(model_points):
            if abs(my - new_display_y) <= 10:  # ±10mm範囲
                distance = math.sqrt((new_display_x - mx)**2 + (new_display_y - my)**2)
                near_points.append((i, mx, my, distance))
        
        near_points.sort(key=lambda p: p[3])
        
        print(f"5. 修正後表示座標での建築限界モデル:")
        if near_points:
            closest = near_points[0]
            print(f"   最近建築限界点: ({closest[1]:.1f}, {closest[2]:.1f})")
            print(f"   測定点との距離: {closest[3]:.1f}mm")
            
            is_inside_display = abs(new_display_x) < abs(closest[1])
            print(f"   表示座標系での内側判定: {'はい' if is_inside_display else 'いいえ'}")
            
            if is_inside_rail == is_inside_display:
                print("   ✅ レールセンター座標系と表示座標系が一致")
                return True
            else:
                print("   ❌ まだ矛盾があります")
                return False
        else:
            print("   近辺に建築限界点が見つかりません")
            return False
    
    def get_clearance_at_height(self, height: float) -> float:
        """指定高さでの建築限界値"""
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
    
    def create_consistent_clearance_model(self, cant_mm: float) -> List[Tuple[float, float]]:
        """一貫性のある建築限界モデル作成"""
        points = []
        
        # 基本建築限界形状
        points.append((1225, 0))
        points.append((1225, 25))
        
        # 25mm→375mm
        for h in np.linspace(25, 375, 20):
            x = 1225 + (h - 25) * (1575 - 1225) / (375 - 25)
            points.append((x, h))
        
        points.append((1575, 920))
        points.append((1900, 920))
        points.append((1900, 3156))
        
        # 円弧部分 (3156mm→3823mm)
        for h in np.linspace(3156, 3823, 200):
            discriminant = 2150**2 - (h - 2150)**2
            if discriminant >= 0:
                x = math.sqrt(discriminant)
                points.append((x, h))
        
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
            
            for i in range(50):
                angle = start_angle + (end_angle - start_angle) * i / 49
                x = center_x + radius * math.cos(angle)
                y = center_y + radius * math.sin(angle)
                
                if abs(x) <= 1350 and y <= 5700 and y >= 4000:
                    points.append((x, y))
        
        points.append((1350, 5700))
        points.append((-1350, 5700))
        
        # 左側（対称）
        right_points = [(x, y) for x, y in points if x > 0]
        right_points.reverse()
        
        for x, y in right_points[1:-1]:
            points.append((-x, y))
        
        points.append((1225, 0))
        
        # カント変形適用
        if cant_mm != 0:
            coords = np.array(points)
            cant_angle = math.atan(cant_mm / self.rail_gauge)
            cos_a, sin_a = math.cos(cant_angle), math.sin(cant_angle)
            rotation_matrix = np.array([[cos_a, -sin_a], [sin_a, cos_a]])
            coords = coords @ rotation_matrix.T
            points = coords.tolist()
        
        return points

def main():
    """メイン修正テスト"""
    fixer = CoordinateSystemFixer()
    
    # 問題のケース
    distance = 1950
    height = 3560
    cant = 100
    
    result = fixer.test_coordinate_fix(distance, height, cant)
    
    print()
    print("=== 修正案の評価 ===")
    if result:
        print("✅ 座標系の矛盾が解決されました")
        print("   この修正をアプリケーションに適用します")
    else:
        print("❌ まだ問題が残っています")
        print("   別のアプローチが必要です")

if __name__ == "__main__":
    main()