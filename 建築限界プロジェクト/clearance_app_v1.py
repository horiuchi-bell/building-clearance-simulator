#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
建築限界シミュレーター v1.0
基本版 - 初期実装
"""

import matplotlib.pyplot as plt
import numpy as np
from typing import List, Tuple

class ClearanceModelV1:
    """建築限界モデル v1 - 基本版"""
    
    def __init__(self):
        self.rail_gauge = 1067  # 軌間 (mm)
        
    def create_basic_clearance(self) -> List[Tuple[float, float]]:
        """基本的な建築限界形状を作成"""
        points = [
            # 右側（下から上）
            (1225, 0), (1372, 200), (1067, 400),
            (1067, 3000), (500, 3800), (0, 4000),
            # 左側（対称）
            (-500, 3800), (-1067, 3000), (-1067, 400),
            (-1372, 200), (-1225, 0), (1225, 0)
        ]
        return points
    
    def transform_basic(self, points: List[Tuple[float, float]], 
                       cant: float, radius: float) -> List[Tuple[float, float]]:
        """基本的な変形処理"""
        if not points:
            return []
        
        coords = np.array(points)
        
        # カント変形
        if cant != 0:
            angle = np.arctan(cant / self.rail_gauge)
            cos_a, sin_a = np.cos(angle), np.sin(angle)
            rotation = np.array([[cos_a, -sin_a], [sin_a, cos_a]])
            coords = coords @ rotation.T
        
        return coords.tolist()

def main_v1():
    """v1 メイン実行"""
    print("🚀 建築限界シミュレーター v1.0 - 基本版")
    model = ClearanceModelV1()
    shape = model.create_basic_clearance()
    print(f"✅ 基本形状作成完了: {len(shape)}点")

if __name__ == "__main__":
    main_v1()