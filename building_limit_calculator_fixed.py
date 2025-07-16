#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
建築限界計算システム - 修正版
正確な計算式とグラフィック表示を実装
"""

import json
import math
from typing import List, Tuple, Dict, Optional

class BuildingLimitCalculatorFixed:
    """建築限界計算システム - 修正版"""
    
    def __init__(self, electrification_type: str = "直流"):
        """
        初期化
        
        Args:
            electrification_type: 電化方式 ("直流", "交流", "非電化")
        """
        self.electrification_type = electrification_type
        self.gauge = 1067  # 軌間（mm）
        self.load_basic_building_limit_data()
    
    def load_basic_building_limit_data(self):
        """基本建築限界データを読み込み（標準建築限界）"""
        # 基準となる建築限界座標（実線部分）
        # 直流・非電化用の標準建築限界
        self.basic_coordinates = [
            # 下部から時計回り
            (-1225, 0), (-1575, 350), (-1575, 920), (-1900, 920),
            (-1900, 1900), (-1900, 2150), (-1366.5, 3156), (-1366.5, 5190.6),
            (-1041.5, 5190.6), (-691.5, 5190.6), (-375.0, 5190.6), (-25.0, 5190.6),
            (0, 5190.6), (25.0, 5190.6), (375.0, 5190.6), (691.5, 5190.6),
            (1041.5, 5190.6), (1366.5, 5190.6), (1366.5, 3156), (1900, 2150),
            (1900, 1900), (1900, 920), (1575, 920), (1575, 350), (1225, 0),
            (0, 0), (-1225, 0)  # 閉じる
        ]
        
        # 電化方式による上部高さ調整
        if self.electrification_type == "交流":
            # 交流の場合は上部限界が高い
            self.basic_coordinates = [
                (x, y if y < 5000 else y + 1000) for x, y in self.basic_coordinates
            ]
    
    def calculate_expansion_width(self, radius: float) -> float:
        """曲線による拡大幅計算"""
        if radius == 0 or radius > 10000:
            return 0
        return 23100 / radius
    
    def calculate_upper_expansion_width(self, radius: float) -> float:
        """上部限界拡大幅計算"""
        if radius == 0 or radius > 10000:
            return 0
        return 11550 / radius
    
    def calculate_cant_angle(self, cant: float) -> float:
        """カント角度計算"""
        if cant < 0:
            return math.atan(cant / self.gauge) + 2 * math.pi
        return math.atan(cant / self.gauge)
    
    def calculate_slack(self, radius: float) -> float:
        """スラック量計算"""
        if radius < 200:
            return 20
        elif radius < 240:
            return 15
        elif radius < 320:
            return 10
        elif radius <= 440:
            return 5
        else:
            return 0
    
    def calculate_displacement(self, x: float, y: float, cant: float) -> Tuple[float, float]:
        """
        カントによる変位量計算（正確な計算式）
        Li = li - [mi - mi*cos(tan^-1(C/g))]
        Hi = hi - [li*cos(tan^-1(C/g)) - mi*sin(tan^-1(C/g))]
        """
        if cant == 0:
            return x, y
            
        cant_angle = self.calculate_cant_angle(cant)
        cos_angle = math.cos(cant_angle)
        sin_angle = math.sin(cant_angle)
        
        # 変位計算
        Li = x - (y - y * cos_angle)
        Hi = y - (x * cos_angle - y * sin_angle)
        
        return Li, Hi
    
    def calculate_transformed_coordinates(self, radius: float, cant: float) -> Tuple[List[Tuple[float, float]], List[Tuple[float, float]]]:
        """
        変形後の建築限界座標計算
        Returns: (基準建築限界座標, 変形後建築限界座標)
        """
        expansion_width = self.calculate_expansion_width(radius)
        slack = self.calculate_slack(radius)
        
        # 基準建築限界（実線）
        basic_coords = self.basic_coordinates.copy()
        
        # 変形後建築限界（点線）
        transformed_coords = []
        
        for x, y in self.basic_coordinates:
            # 曲線による拡大
            if x > 0:
                expanded_x = x + expansion_width
            elif x < 0:
                expanded_x = x - expansion_width
            else:
                expanded_x = x
            
            expanded_y = y
            
            # カントによる変位
            Li, Hi = self.calculate_displacement(expanded_x, expanded_y, cant)
            
            # スラック考慮（曲線内側の拡大）
            if x > 0:
                final_x = Li + slack / 2
            elif x < 0:
                final_x = Li - slack / 2
            else:
                final_x = Li
            
            final_y = Hi
            
            transformed_coords.append((final_x, final_y))
        
        return basic_coords, transformed_coords
    
    def calculate_required_clearance_at_height(self, height: float, radius: float, cant: float) -> float:
        """測定高さでの必要離れ計算"""
        basic_coords, transformed_coords = self.calculate_transformed_coordinates(radius, cant)
        
        # 指定高さでの建築限界幅を求める
        min_x = float('inf')
        
        for i in range(len(transformed_coords) - 1):
            x1, y1 = transformed_coords[i]
            x2, y2 = transformed_coords[i + 1]
            
            # 高さがy1とy2の間にある場合
            if min(y1, y2) <= height <= max(y1, y2) and y1 != y2:
                # 線形補間でX座標を求める
                t = (height - y1) / (y2 - y1)
                x_at_height = x1 + t * (x2 - x1)
                
                # 右側（正の側）の建築限界を求める
                if x_at_height > 0:
                    min_x = min(min_x, x_at_height)
        
        return min_x if min_x != float('inf') else 0
    
    def calculate_clearance_margin(self, measurement_distance: float, measurement_height: float,
                                 radius: float, cant: float) -> float:
        """限界余裕値計算"""
        required_clearance = self.calculate_required_clearance_at_height(measurement_height, radius, cant)
        
        if measurement_distance >= 0:
            # 右側（正の側）の場合
            margin = measurement_distance - required_clearance
        else:
            # 左側（負の側）の場合
            margin = abs(measurement_distance) - abs(required_clearance)
        
        return margin
    
    def check_clearance(self, measurement_distance: float, measurement_height: float,
                       radius: float, cant: float) -> Dict[str, any]:
        """建築限界判定"""
        basic_coords, transformed_coords = self.calculate_transformed_coordinates(radius, cant)
        
        # 測定高さでの必要離れ
        required_clearance = self.calculate_required_clearance_at_height(measurement_height, radius, cant)
        
        # 限界余裕値
        clearance_margin = self.calculate_clearance_margin(measurement_distance, measurement_height, radius, cant)
        
        # 支障判定
        is_interference = clearance_margin < 0
        
        # 最近接点との距離計算
        min_distance = float('inf')
        nearest_point = None
        
        for x, y in transformed_coords:
            distance = math.sqrt((x - measurement_distance)**2 + (y - measurement_height)**2)
            if distance < min_distance:
                min_distance = distance
                nearest_point = (x, y)
        
        # 判定結果
        result = {
            "is_interference": is_interference,
            "status": "支障" if is_interference else "安全",
            "min_distance": min_distance,
            "nearest_point": nearest_point,
            "basic_coordinates": basic_coords,
            "transformed_coordinates": transformed_coords,
            "measurement_point": (measurement_distance, measurement_height),
            "expansion_width": self.calculate_expansion_width(radius),
            "cant_angle": self.calculate_cant_angle(cant),
            "slack": self.calculate_slack(radius),
            "required_clearance": required_clearance,
            "clearance_margin": clearance_margin
        }
        
        return result
    
    def get_display_data(self, radius: float, cant: float) -> Dict[str, any]:
        """表示用データ取得"""
        basic_coords, transformed_coords = self.calculate_transformed_coordinates(radius, cant)
        
        # 座標の範囲を計算
        all_coords = basic_coords + transformed_coords
        x_coords = [x for x, y in all_coords]
        y_coords = [y for x, y in all_coords]
        
        return {
            "basic_coordinates": basic_coords,
            "transformed_coordinates": transformed_coords,
            "x_range": (min(x_coords), max(x_coords)),
            "y_range": (min(y_coords), max(y_coords)),
            "expansion_width": self.calculate_expansion_width(radius),
            "cant_angle_deg": math.degrees(self.calculate_cant_angle(cant)),
            "slack": self.calculate_slack(radius),
            "electrification_type": self.electrification_type
        }

# テスト実行
if __name__ == "__main__":
    print("=== 建築限界計算システム 修正版 テスト ===")
    
    # 計算器の初期化
    calc = BuildingLimitCalculatorFixed("直流")
    
    # OIRANシュミレーターのデフォルト値でテスト
    radius = 160
    cant = 105
    distance = 2110
    height = 3150
    
    print(f"パラメータ:")
    print(f"  曲線半径: {radius}m")
    print(f"  カント: {cant}mm")
    print(f"  測定離れ: {distance}mm")
    print(f"  測定高さ: {height}mm")
    
    result = calc.check_clearance(distance, height, radius, cant)
    
    print(f"\n計算結果:")
    print(f"  判定: {result['status']}")
    print(f"  測定高さでの必要離れ: {result['required_clearance']:.1f}mm")
    print(f"  限界余裕値: {result['clearance_margin']:.1f}mm")
    print(f"  最小距離: {result['min_distance']:.1f}mm")
    print(f"  拡大幅: {result['expansion_width']:.1f}mm")
    print(f"  カント角度: {math.degrees(result['cant_angle']):.2f}°")
    print(f"  スラック: {result['slack']}mm")
    
    # 座標数確認
    print(f"\n座標情報:")
    print(f"  基準建築限界座標数: {len(result['basic_coordinates'])}")
    print(f"  変形後建築限界座標数: {len(result['transformed_coordinates'])}")