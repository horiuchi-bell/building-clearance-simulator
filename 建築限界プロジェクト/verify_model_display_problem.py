#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
支障時の赤丸がモデル外側に表示される問題の詳細検証
"""

import math
import numpy as np
from typing import List, Tuple, Dict, Any

class ModelDisplayProblemVerifier:
    """モデル表示問題の検証器"""
    
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
    
    def get_clearance_at_height_exact(self, height: float) -> float:
        """指定高さでの建築限界値（正確な計算）"""
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
    
    def create_ultra_precise_clearance_model(self, cant_mm: float) -> List[Tuple[float, float]]:
        """超高精度建築限界モデル作成"""
        points = []
        
        # 右側の輪郭を定義（超高精度）
        points.append((1225, 0))
        points.append((1225, 25))
        
        # 25mm→375mmの斜め直線（超細かく分割）
        for h in np.linspace(25, 375, 50):
            x = 1225 + (h - 25) * (1575 - 1225) / (375 - 25)
            points.append((x, h))
        
        points.append((1575, 920))
        points.append((1900, 920))
        points.append((1900, 3156))
        
        # 円弧部分 (3156mm→3823mm) - 極超高精度
        for h in np.linspace(3156, 3823, 500):  # 500分割
            discriminant = 2150**2 - (h - 2150)**2
            if discriminant >= 0:
                x = math.sqrt(discriminant)
                points.append((x, h))
        
        points.append((1350, 3823))
        points.append((1350, 4300))
        
        # 上部円弧（超高精度）
        center_x, center_y, radius = 0, 4000, 1800
        x_boundary = 1350
        
        discriminant = radius**2 - x_boundary**2
        if discriminant >= 0:
            y_intersect = center_y + math.sqrt(discriminant)
            start_angle = math.atan2(y_intersect - center_y, x_boundary - center_x)
            end_angle = math.pi / 2
            
            for i in range(100):  # 100分割
                angle = start_angle + (end_angle - start_angle) * i / 99
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
        
        # カント変形（詳細検証）
        if cant_mm != 0:
            print(f"カント変形詳細:")
            cant_angle_rad = math.atan(cant_mm / self.rail_gauge)
            cant_angle_deg = math.degrees(cant_angle_rad)
            print(f"・カント角度: {cant_angle_rad:.8f} rad = {cant_angle_deg:.6f}°")
            
            coords = np.array(points)
            cos_a, sin_a = math.cos(cant_angle_rad), math.sin(cant_angle_rad)
            rotation_matrix = np.array([[cos_a, -sin_a], [sin_a, cos_a]])
            
            print(f"・回転行列:")
            print(f"  [[{cos_a:.8f}, {-sin_a:.8f}]")
            print(f"   [{sin_a:.8f}, {cos_a:.8f}]]")
            
            coords = coords @ rotation_matrix.T
            points = coords.tolist()
        
        return points
    
    def verify_measurement_point_position(self, measurement_distance: float, measurement_height: float, cant_mm: float):
        """測定点位置の詳細検証"""
        print("=== 測定点位置詳細検証 ===")
        print(f"入力: 離れ{measurement_distance}mm, 高さ{measurement_height}mm, カント{cant_mm}mm")
        print()
        
        # レールセンター座標変換
        rail_x, rail_y = self.coordinate_transform_to_rail_center(measurement_distance, measurement_height, cant_mm)
        print(f"1. レールセンター座標変換:")
        print(f"   入力座標: ({measurement_distance}, {measurement_height})")
        print(f"   レール座標: ({rail_x:.6f}, {rail_y:.6f})")
        print()
        
        # その高さでの建築限界値
        clearance_limit = self.get_clearance_at_height_exact(rail_y)
        print(f"2. 建築限界値計算:")
        print(f"   高さ{rail_y:.3f}mmでの建築限界値: {clearance_limit:.6f}mm")
        print(f"   測定点の絶対X座標: {abs(rail_x):.6f}mm")
        print(f"   建築限界内側判定: {'はい' if abs(rail_x) < clearance_limit else 'いいえ'}")
        print(f"   建築限界からの距離: {abs(rail_x) - clearance_limit:.6f}mm")
        print()
        
        # 表示座標系（V9形式）
        if measurement_distance > 0:
            display_x = -abs(measurement_distance)
        else:
            display_x = abs(measurement_distance)
        display_y = measurement_height
        
        print(f"3. 表示座標系:")
        print(f"   測定点表示座標: ({display_x}, {display_y})")
        print()
        
        # 超高精度建築限界モデル作成
        print(f"4. 建築限界モデル作成:")
        model_points = self.create_ultra_precise_clearance_model(cant_mm)
        print(f"   モデル点数: {len(model_points)}")
        print()
        
        # 測定点近辺のモデル座標検索
        print(f"5. 測定点近辺のモデル座標分析:")
        near_points = []
        
        for i, (mx, my) in enumerate(model_points):
            # 測定点の高さ±5mm範囲で検索
            if abs(my - display_y) <= 5:
                distance_to_measurement = math.sqrt((display_x - mx)**2 + (display_y - my)**2)
                near_points.append((i, mx, my, distance_to_measurement))
        
        # 距離でソート
        near_points.sort(key=lambda p: p[3])
        
        print(f"   測定点高さ±5mm範囲の建築限界座標:")
        for idx, (i, mx, my, dist) in enumerate(near_points[:10]):  # 最も近い10点
            print(f"     {idx+1:2d}. 座標{i:3d}: ({mx:8.1f}, {my:6.1f}), 距離: {dist:6.1f}mm")
        
        if near_points:
            closest_point = near_points[0]
            print(f"   最近点: 座標{closest_point[0]} ({closest_point[1]:.1f}, {closest_point[2]:.1f})")
            print()
            
            # 表示判定
            print(f"6. 表示判定:")
            if abs(display_x) < abs(closest_point[1]):
                print(f"   測定点X座標の絶対値: {abs(display_x)} < 最近建築限界X座標の絶対値: {abs(closest_point[1])}")
                print("   → 測定点は建築限界内側に表示されます ✅")
            else:
                print(f"   測定点X座標の絶対値: {abs(display_x)} > 最近建築限界X座標の絶対値: {abs(closest_point[1])}")
                print("   → 測定点は建築限界外側に表示されます ⚠️")
        
        print()
        print("7. レールセンター座標系 vs 表示座標系の整合性:")
        print(f"   レール座標系での内側判定: {'内側' if abs(rail_x) < clearance_limit else '外側'}")
        print(f"   表示座標系での見え方: {'内側' if near_points and abs(display_x) < abs(near_points[0][1]) else '外側'}")
        
        if (abs(rail_x) < clearance_limit) != (near_points and abs(display_x) < abs(near_points[0][1])):
            print("   ⚠️ 座標系間で矛盾があります！")
            return False
        else:
            print("   ✅ 座標系間で一致しています")
            return True

def main():
    """メイン検証実行"""
    verifier = ModelDisplayProblemVerifier()
    
    # 問題のケース
    print("【問題のケース検証】")
    print("=" * 80)
    
    distance = 1950
    height = 3560
    cant = 100
    
    result = verifier.verify_measurement_point_position(distance, height, cant)
    
    print()
    print("=" * 80)
    print("【検証結果】")
    if result:
        print("✅ モデル表示は正確です")
    else:
        print("❌ モデル表示に問題があります")
        print("   - 建築限界モデルの精度を向上させる必要があります")
        print("   - または座標変換ロジックに問題があります")

if __name__ == "__main__":
    main()