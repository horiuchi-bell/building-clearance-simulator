#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
正確な建築限界モデル作成クラス
寸法図に基づいた建築限界形状の生成
"""

import numpy as np
from typing import List, Tuple

class AccurateClearanceModel:
    def __init__(self):
        """正確な建築限界モデルの初期化"""
        self.rail_gauge = 1067  # 軌間 (mm)
        self.rail_center_to_edge = self.rail_gauge / 2  # レール中心から外側レールまで
        
    def create_accurate_clearance_shape(self) -> List[Tuple[float, float]]:
        """
        寸法図に基づいた正確な建築限界形状を作成
        備考２の単純直線部分を基本とする
        
        Returns:
            List[Tuple[float, float]]: (x, y) 座標のリスト (mm単位)
        """
        points = []
        
        # 寸法図から読み取った主要寸法（レール中心からの距離、mm）
        # 高さ別の片側寸法（右側、左側は対称）
        clearance_data = [
            # (高さ, 片側寸法)
            (4650, 1350),  # 最上部
            (4000, 1350),  # 上部直線部
            (3200, 1350),  # 上部から中央部への変化点
            (2600, 1000),  # 中央部最小幅
            (2100, 1000),  # 中央部
            (1500, 1350),  # 中央から下部への拡張開始
            (1000, 1625),  # 下部拡張部
            (600,  1625),  # 下部
            (200,  1625),  # レール面近く
            (0,    1225),  # レール面（軌道中心から軌道端まで）
        ]
        
        # 右側の輪郭を作成（下から上へ）
        for height, half_width in clearance_data:
            points.append((half_width, height))
        
        # 上部の輪郭を作成（右から左へ）
        # 最上部は平坦
        top_height = clearance_data[0][0]
        top_width = clearance_data[0][1]
        points.append((-top_width, top_height))
        
        # 左側の輪郭を作成（上から下へ）
        for height, half_width in reversed(clearance_data[1:]):
            points.append((-half_width, height))
        
        # 形状を閉じる（最初の点に戻る）
        if points:
            points.append(points[0])
        
        print(f"✅ 正確な建築限界形状を作成: {len(points)}点")
        self._print_shape_info(points)
        
        return points
    
    def _print_shape_info(self, points: List[Tuple[float, float]]):
        """形状情報を表示"""
        if not points:
            return
        
        x_coords = [p[0] for p in points]
        y_coords = [p[1] for p in points]
        
        print(f"📐 建築限界寸法情報:")
        print(f"  - 全幅: {max(x_coords) - min(x_coords):.0f}mm")
        print(f"  - 最大高さ: {max(y_coords):.0f}mm")
        print(f"  - 左端: {min(x_coords):.0f}mm")
        print(f"  - 右端: {max(x_coords):.0f}mm")
    
    def create_simplified_clearance_shape(self) -> List[Tuple[float, float]]:
        """
        簡略化された建築限界形状（備考２の直線部分のみ）
        
        Returns:
            List[Tuple[float, float]]: 簡略化された座標リスト
        """
        # より単純な直線のみの形状
        simplified_points = [
            # 右側（下から上）
            (1225, 0),     # レール面右端
            (1625, 200),   # 下部右端
            (1625, 1000),  # 下部上端
            (1000, 2600),  # 中央部最小幅
            (1350, 3200),  # 上部下端
            (1350, 4650),  # 最上部右端
            
            # 上部（右から左）
            (-1350, 4650), # 最上部左端
            
            # 左側（上から下）
            (-1350, 3200), # 上部下端
            (-1000, 2600), # 中央部最小幅  
            (-1625, 1000), # 下部上端
            (-1625, 200),  # 下部左端
            (-1225, 0),    # レール面左端
            
            # 下部（左から右、レール面）
            (1225, 0),     # 形状を閉じる
        ]
        
        print(f"✅ 簡略化建築限界形状を作成: {len(simplified_points)}点")
        return simplified_points
    
    def validate_point_in_clearance(self, x: float, y: float, 
                                   clearance_points: List[Tuple[float, float]]) -> bool:
        """
        指定された点が建築限界内にあるかチェック
        
        Args:
            x, y: チェックする点の座標 (mm)
            clearance_points: 建築限界の座標リスト
            
        Returns:
            bool: True if 建築限界内, False if 建築限界外（支障）
        """
        if not clearance_points or y < 0:
            return False
        
        # 同じ高さでの建築限界幅を取得
        clearance_width = self._get_clearance_width_at_height(y, clearance_points)
        
        if clearance_width is None:
            return False
        
        # 中心からの距離が建築限界幅以内かチェック
        return abs(x) <= clearance_width
    
    def _get_clearance_width_at_height(self, height: float, 
                                      points: List[Tuple[float, float]]) -> float:
        """
        指定高さでの建築限界の片側幅を取得
        
        Args:
            height: 高さ (mm)
            points: 建築限界座標リスト
            
        Returns:
            float: 片側幅 (mm)、該当なしの場合はNone
        """
        # 右側の点のみを抽出（x > 0）
        right_points = [(x, y) for x, y in points if x > 0]
        
        if not right_points:
            return None
        
        # 高さでソート
        right_points.sort(key=lambda p: p[1])
        
        # 指定高さでの幅を線形補間で求める
        for i in range(len(right_points) - 1):
            y1, x1 = right_points[i][1], right_points[i][0]
            y2, x2 = right_points[i + 1][1], right_points[i + 1][0]
            
            if y1 <= height <= y2:
                if y2 == y1:
                    return x1
                # 線形補間
                ratio = (height - y1) / (y2 - y1)
                width = x1 + ratio * (x2 - x1)
                return width
        
        return None
    
    def transform_clearance_for_cant_and_curve(self, 
                                              points: List[Tuple[float, float]],
                                              cant_mm: float, 
                                              curve_radius_m: float) -> List[Tuple[float, float]]:
        """
        カント・曲線半径による建築限界の変形
        
        Args:
            points: 基本建築限界座標
            cant_mm: カント値 (mm)
            curve_radius_m: 曲線半径 (m)
            
        Returns:
            List[Tuple[float, float]]: 変形後の座標リスト
        """
        if not points:
            return []
        
        coords = np.array(points)
        
        # カント変換
        if cant_mm != 0:
            angle_rad = np.arctan(cant_mm / self.rail_gauge)
            
            # 回転行列
            cos_a = np.cos(angle_rad)
            sin_a = np.sin(angle_rad)
            
            rotation_matrix = np.array([
                [cos_a, -sin_a],
                [sin_a, cos_a]
            ])
            
            coords = coords @ rotation_matrix.T
        
        # 曲線拡幅
        if curve_radius_m > 0 and curve_radius_m < 3000:
            # 曲線での拡幅計算（実際の鉄道基準に近似）
            widening_factor = min(100, 1500.0 / curve_radius_m)  # 最大100mm拡幅
            
            # X座標のみ拡幅（レール側を広げる）
            coords[:, 0] = coords[:, 0] + np.sign(coords[:, 0]) * widening_factor
        
        return coords.tolist()

def main():
    """テスト実行"""
    print("🏗️ 正確な建築限界モデルをテスト中...")
    
    model = AccurateClearanceModel()
    
    # 正確な形状を作成
    accurate_shape = model.create_accurate_clearance_shape()
    
    # 簡略化形状を作成
    simplified_shape = model.create_simplified_clearance_shape()
    
    # テスト点での判定
    test_points = [
        (0, 2000),      # 中央、高さ2m
        (800, 2600),    # 中央部幅内
        (1200, 2600),   # 中央部幅外（支障）
        (1500, 1000),   # 下部幅内
        (1700, 1000),   # 下部幅外（支障）
    ]
    
    print("\\n🧪 建築限界判定テスト:")
    for x, y in test_points:
        result = model.validate_point_in_clearance(x, y, simplified_shape)
        status = "✅ 限界内" if result else "❌ 支障"
        print(f"  位置({x:4.0f}, {y:4.0f}): {status}")
    
    # カント・曲線変形テスト
    print("\\n🔄 変形テスト:")
    transformed = model.transform_clearance_for_cant_and_curve(
        simplified_shape, cant_mm=140, curve_radius_m=300
    )
    print(f"  変形後座標数: {len(transformed)}")
    
    print("\\n✅ 建築限界モデルテスト完了")

if __name__ == "__main__":
    main()