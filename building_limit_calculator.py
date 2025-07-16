#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
建築限界計算システム - 完全版
OIRANシュミレーターと同等の機能を実装
"""

import json
import math
from typing import List, Tuple, Dict, Optional

class BuildingLimitCalculator:
    """建築限界計算システム"""
    
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
        """基本建築限界データを読み込み"""
        try:
            with open("building_limit_data.json", "r", encoding="utf-8") as f:
                data = json.load(f)
            
            # 電化方式に応じて基本データを選択
            sheet_map = {
                "直流": "建築限界数値データ 　直流",
                "交流": "建築限界数値データ 交流",
                "非電化": "建築限界数値データ 　非電化"
            }
            
            sheet_name = sheet_map.get(self.electrification_type, "建築限界数値データ 　直流")
            self.basic_coordinates = data[sheet_name]["coordinates"]
            
        except FileNotFoundError:
            # デフォルトの建築限界データ（簡略版）
            self.basic_coordinates = [
                (0, 0), (1225, 0), (1575, 350), (1575, 920), (1900, 920),
                (1900, 3156), (1884, 3186), (1815, 3302), (1739, 3414),
                (1657, 3520), (1568, 3620), (1474, 3713), (1375, 3800),
                (1272, 3879), (1166, 3952), (1058, 4017), (947, 4075),
                (835, 4126), (722, 4169), (608, 4206), (494, 4236),
                (379, 4259), (264, 4275), (149, 4284), (34, 4287),
                (-81, 4283), (-196, 4273), (-310, 4256), (-424, 4233),
                (-537, 4203), (-649, 4167), (-759, 4125), (-867, 4076),
                (-973, 4021), (-1076, 3960), (-1176, 3893), (-1273, 3820),
                (-1366, 3741), (-1455, 3657), (-1540, 3568), (-1620, 3474),
                (-1695, 3376), (-1764, 3274), (-1827, 3168), (-1884, 3058),
                (-1935, 2945), (-1979, 2828), (-2016, 2709), (-2046, 2587),
                (-2069, 2463), (-2085, 2337), (-2093, 2210), (-2095, 2081),
                (-2089, 1952), (-2076, 1822), (-2055, 1693), (-2027, 1564),
                (-1992, 1436), (-1950, 1309), (-1900, 1184), (-1900, 920),
                (-1575, 920), (-1575, 350), (-1225, 0), (0, 0)
            ]
    
    def calculate_expansion_width(self, radius: float) -> float:
        """
        曲線による拡大幅計算
        
        Args:
            radius: 曲線半径（m）
            
        Returns:
            拡大幅（mm）
        """
        if radius == 0:
            return 0
        return 23100 / radius
    
    def calculate_upper_expansion_width(self, radius: float) -> float:
        """
        上部限界拡大幅計算
        
        Args:
            radius: 曲線半径（m）
            
        Returns:
            上部拡大幅（mm）
        """
        if radius == 0:
            return 0
        return 11550 / radius
    
    def calculate_cant_angle(self, cant: float) -> float:
        """
        カント角度計算
        
        Args:
            cant: カント（mm）
            
        Returns:
            カント角度（rad）
        """
        if cant < 0:
            return math.atan(cant / self.gauge) + 2 * math.pi
        return math.atan(cant / self.gauge)
    
    def calculate_slack(self, radius: float) -> float:
        """
        スラック量計算
        
        Args:
            radius: 曲線半径（m）
            
        Returns:
            スラック量（mm）
        """
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
        カントによる変位量計算
        
        Args:
            x: X座標（mm）
            y: Y座標（mm）
            cant: カント（mm）
            
        Returns:
            変位後の座標（Li, Hi）
        """
        cant_angle = self.calculate_cant_angle(cant)
        
        # カントによる傾斜変位計算
        Li = x - (y - y * math.cos(cant_angle))
        Hi = y - (x * math.cos(cant_angle) - y * math.sin(cant_angle))
        
        return Li, Hi
    
    def calculate_transformed_coordinates(self, radius: float, cant: float) -> List[Tuple[float, float]]:
        """
        変形後の建築限界座標計算
        
        Args:
            radius: 曲線半径（m）
            cant: カント（mm）
            
        Returns:
            変形後の座標リスト
        """
        expansion_width = self.calculate_expansion_width(radius)
        slack = self.calculate_slack(radius)
        cant_angle = self.calculate_cant_angle(cant)
        
        transformed_coords = []
        
        for x, y in self.basic_coordinates:
            # 曲線による拡大
            expanded_x = x - expansion_width if x > 0 else x + expansion_width
            expanded_y = y
            
            # カントによる変位
            Li, Hi = self.calculate_displacement(expanded_x, expanded_y, cant)
            
            # スラック考慮
            if expanded_x > 0:
                final_x = slack / 2 + expansion_width + Li
            else:
                final_x = -(slack / 2 + expansion_width) + Li
            
            final_y = Hi
            
            transformed_coords.append((final_x, final_y))
        
        return transformed_coords
    
    def check_clearance(self, measurement_distance: float, measurement_height: float,
                       radius: float, cant: float) -> Dict[str, any]:
        """
        建築限界判定
        
        Args:
            measurement_distance: 測定離れ（軌道中心からの距離）（mm）
            measurement_height: 測定高さ（レール踏面からの高さ）（mm）
            radius: 曲線半径（m）
            cant: カント（mm）
            
        Returns:
            判定結果辞書
        """
        transformed_coords = self.calculate_transformed_coordinates(radius, cant)
        
        # 測定点が建築限界内かチェック
        is_within_limit = self._point_in_polygon(measurement_distance, measurement_height, transformed_coords)
        
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
            "is_within_limit": is_within_limit,
            "status": "支障" if is_within_limit else "安全",
            "min_distance": min_distance,
            "nearest_point": nearest_point,
            "transformed_coordinates": transformed_coords,
            "measurement_point": (measurement_distance, measurement_height),
            "expansion_width": self.calculate_expansion_width(radius),
            "cant_angle": self.calculate_cant_angle(cant),
            "slack": self.calculate_slack(radius)
        }
        
        return result
    
    def _point_in_polygon(self, x: float, y: float, polygon: List[Tuple[float, float]]) -> bool:
        """
        点が多角形内部にあるかチェック（レイキャスト法）
        
        Args:
            x: 点のX座標
            y: 点のY座標
            polygon: 多角形の頂点座標リスト
            
        Returns:
            内部にある場合True
        """
        n = len(polygon)
        inside = False
        
        p1x, p1y = polygon[0]
        for i in range(1, n + 1):
            p2x, p2y = polygon[i % n]
            if y > min(p1y, p2y):
                if y <= max(p1y, p2y):
                    if x <= max(p1x, p2x):
                        if p1y != p2y:
                            xinters = (y - p1y) * (p2x - p1x) / (p2y - p1y) + p1x
                        if p1x == p2x or x <= xinters:
                            inside = not inside
            p1x, p1y = p2x, p2y
        
        return inside
    
    def get_display_data(self, radius: float, cant: float) -> Dict[str, any]:
        """
        表示用データ取得
        
        Args:
            radius: 曲線半径（m）
            cant: カント（mm）
            
        Returns:
            表示用データ
        """
        transformed_coords = self.calculate_transformed_coordinates(radius, cant)
        
        # 座標の範囲を計算
        x_coords = [x for x, y in transformed_coords]
        y_coords = [y for x, y in transformed_coords]
        
        return {
            "coordinates": transformed_coords,
            "x_range": (min(x_coords), max(x_coords)),
            "y_range": (min(y_coords), max(y_coords)),
            "expansion_width": self.calculate_expansion_width(radius),
            "cant_angle_deg": math.degrees(self.calculate_cant_angle(cant)),
            "slack": self.calculate_slack(radius),
            "electrification_type": self.electrification_type
        }

# テスト実行
if __name__ == "__main__":
    print("=== 建築限界計算システム テスト ===")
    
    # 計算器の初期化
    calc = BuildingLimitCalculator("直流")
    
    # テストケース
    test_cases = [
        {"radius": 160, "cant": 105, "distance": 2110, "height": 3150},
        {"radius": 300, "cant": 45, "distance": 1500, "height": 2000},
        {"radius": 500, "cant": 60, "distance": 2000, "height": 3000},
    ]
    
    for i, case in enumerate(test_cases):
        print(f"\n=== テストケース {i+1} ===")
        print(f"曲線半径: {case['radius']}m")
        print(f"カント: {case['cant']}mm")
        print(f"測定離れ: {case['distance']}mm")
        print(f"測定高さ: {case['height']}mm")
        
        result = calc.check_clearance(case['distance'], case['height'], case['radius'], case['cant'])
        
        print(f"判定: {result['status']}")
        print(f"最小距離: {result['min_distance']:.1f}mm")
        print(f"拡大幅: {result['expansion_width']:.1f}mm")
        print(f"カント角度: {math.degrees(result['cant_angle']):.2f}°")
        print(f"スラック: {result['slack']}mm")
        
        # 表示データの取得
        display_data = calc.get_display_data(case['radius'], case['cant'])
        print(f"座標数: {len(display_data['coordinates'])}")
        print(f"X範囲: {display_data['x_range'][0]:.1f} ～ {display_data['x_range'][1]:.1f}")
        print(f"Y範囲: {display_data['y_range'][0]:.1f} ～ {display_data['y_range'][1]:.1f}")