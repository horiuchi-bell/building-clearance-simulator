#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
精度差異の詳細分析 - 14mm vs 15mmの差異原因調査
"""

import math
import numpy as np
from typing import List, Tuple, Dict, Any

class PrecisionAnalyzer:
    """精度差異分析器"""
    
    def __init__(self):
        self.rail_gauge = 1067
        self.original_clearance_data = self._create_original_clearance_data()
    
    def _create_original_clearance_data(self) -> List[Tuple[float, float]]:
        """元建築限界データ作成（1775個の点）"""
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
        """座標変換の詳細分析"""
        if cant_mm == 0:
            return measurement_distance, measurement_height
        
        cant_angle = math.atan(cant_mm / self.rail_gauge)
        x_coord = measurement_distance - measurement_height * math.sin(cant_angle)
        y_coord = measurement_height * math.cos(cant_angle)
        
        return x_coord, y_coord
    
    def get_clearance_at_height_precise(self, height: float) -> float:
        """指定高さでの建築限界値（高精度）"""
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
    
    def calculate_ag2_with_analysis(self, measurement_distance: float, measurement_height: float,
                                   cant_mm: float) -> Dict[str, Any]:
        """AG2計算の詳細分析"""
        # 座標変換
        rail_x, rail_y = self.coordinate_transform_to_rail_center(measurement_distance, measurement_height, cant_mm)
        
        # その高さでの建築限界値（連続関数）
        clearance_limit = self.get_clearance_at_height_precise(rail_y)
        
        # 建築限界からの水平距離
        horizontal_distance_to_limit = abs(rail_x) - clearance_limit
        
        # 離散点による最短距離計算
        min_distance = float('inf')
        closest_point = None
        
        for clearance_x, clearance_y in self.original_clearance_data:
            dx = rail_x - clearance_x
            dy = rail_y - clearance_y
            distance = math.sqrt(dx**2 + dy**2)
            
            if distance < min_distance:
                min_distance = distance
                closest_point = (clearance_x, clearance_y)
        
        # 理論的最短距離（連続関数）
        theoretical_distance = horizontal_distance_to_limit if horizontal_distance_to_limit > 0 else 0
        
        return {
            'rail_coords': (rail_x, rail_y),
            'clearance_limit_at_height': clearance_limit,
            'horizontal_distance_to_limit': horizontal_distance_to_limit,
            'discrete_min_distance': min_distance,
            'theoretical_distance': theoretical_distance,
            'closest_point': closest_point,
            'is_inside': horizontal_distance_to_limit < 0
        }
    
    def analyze_excel_vs_calculation(self, measurement_distance: float, measurement_height: float, cant_mm: float):
        """エクセルとの計算差異分析"""
        print("=== エクセルとの計算差異分析 ===")
        print(f"テスト条件: 離れ{measurement_distance}mm, 高さ{measurement_height}mm, カント{cant_mm}mm")
        print()
        
        analysis = self.calculate_ag2_with_analysis(measurement_distance, measurement_height, cant_mm)
        
        print("座標変換結果:")
        print(f"・レールセンター座標: ({analysis['rail_coords'][0]:.6f}, {analysis['rail_coords'][1]:.6f})")
        print()
        
        print("建築限界分析:")
        print(f"・その高さでの建築限界値: {analysis['clearance_limit_at_height']:.6f} mm")
        print(f"・水平距離: {analysis['horizontal_distance_to_limit']:.6f} mm")
        print(f"・建築限界内側: {'はい' if analysis['is_inside'] else 'いいえ'}")
        print()
        
        print("距離計算:")
        print(f"・離散点による最短距離: {analysis['discrete_min_distance']:.6f} mm")
        print(f"・理論的距離: {analysis['theoretical_distance']:.6f} mm")
        print(f"・最近点: ({analysis['closest_point'][0]:.3f}, {analysis['closest_point'][1]:.3f})")
        print()
        
        # エクセル係数による補正（カント補正の微調整）
        excel_kant_correction_factor = 0.097268  # エクセルで観測された係数
        theoretical_kant_correction_factor = math.sin(math.atan(cant_mm / self.rail_gauge))
        
        print("カント補正分析:")
        print(f"・理論的係数: {theoretical_kant_correction_factor:.6f}")
        print(f"・エクセル係数: {excel_kant_correction_factor:.6f}")
        print(f"・係数差異: {excel_kant_correction_factor - theoretical_kant_correction_factor:.6f}")
        print()
        
        # エクセル係数を使った再計算
        excel_x = measurement_distance - measurement_height * excel_kant_correction_factor
        excel_y = measurement_height * math.cos(math.atan(cant_mm / self.rail_gauge))
        
        print("エクセル係数での再計算:")
        print(f"・エクセル座標: ({excel_x:.6f}, {excel_y:.6f})")
        
        # エクセル座標での最短距離
        min_distance_excel = float('inf')
        for clearance_x, clearance_y in self.original_clearance_data:
            dx = excel_x - clearance_x
            dy = excel_y - clearance_y
            distance = math.sqrt(dx**2 + dy**2)
            if distance < min_distance_excel:
                min_distance_excel = distance
        
        print(f"・エクセル係数での最短距離: {min_distance_excel:.6f} mm")
        print()
        
        # 限界余裕計算
        if min_distance_excel < 5:
            excel_margin = 0
        elif min_distance_excel < 13:
            excel_margin = math.sqrt(min_distance_excel**2 - 25)
        else:
            excel_margin = min_distance_excel
        
        final_excel_margin = math.floor(excel_margin)
        
        print("最終結果:")
        print(f"・補正前限界余裕: {excel_margin:.6f} mm")
        print(f"・最終限界余裕: {final_excel_margin} mm")
        
        if final_excel_margin == 15:
            print("✅ エクセル係数で期待値15mmに一致")
        else:
            print(f"⚠️  エクセル係数でも{final_excel_margin}mm（期待15mm）")

def main():
    """メイン分析実行"""
    analyzer = PrecisionAnalyzer()
    
    # 問題のケース
    distance = 1950
    height = 3560
    cant = 100
    
    analyzer.analyze_excel_vs_calculation(distance, height, cant)

if __name__ == "__main__":
    main()