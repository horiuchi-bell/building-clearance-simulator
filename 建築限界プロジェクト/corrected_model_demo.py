#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
修正版建築限界モデル - デモ・検証プログラム
正確な寸法に基づく建築限界形状の確認
"""

import matplotlib.pyplot as plt
import numpy as np
import math
from typing import List, Tuple

class CorrectedBuildingClearanceModel:
    """修正版建築限界モデル"""
    
    def __init__(self):
        """初期化"""
        self.rail_gauge = 1067  # 軌間 (mm)
        
    def create_clearance_shape(self) -> List[Tuple[float, float]]:
        """
        修正された正確な建築限界形状を作成
        ユーザー指定の寸法に基づく
        """
        points = []
        
        print("🏗️ 修正版建築限界モデルを作成中...")
        print("📐 適用寸法:")
        print("  - レールレベルから25mmまでの高さ = 1225mm")
        print("  - 高さ375～920mmまで = 1575mm")
        print("  - 高さ920～3200mm = 1900mm")
        print("  - 高さ3200mm～4300mmまでを滑らかな曲線で結ぶ")
        print("  - 上部架線限界: 縦方向1350mm, 最大高さ5700mm")
        print("  - 円弧処理: 中心(0,4000), 半径1800mm")
        
        # 右側の輪郭を作成（下から上へ）
        
        # 1. レールレベルから25mmまでの高さ = 1225mm
        points.append((1225, 0))     # レール面
        points.append((1225, 25))    # 25mmまで
        
        # 25mmから375mmまでの遷移（直線）
        points.append((1225, 375))   # 375mmまで直線
        
        # 2. 高さ375～920mmまで = 1575mm
        points.append((1575, 375))   # 375mmから拡張開始
        points.append((1575, 920))   # 920mmまで
        
        # 3. 高さ920～3200mm = 1900mm
        points.append((1900, 920))   # 920mmから最大幅
        points.append((1900, 3200))  # 3200mmまで
        
        # 4. 高さ3200mm～レール中心の高さ4300mmまでを滑らかな曲線で結ぶ
        curve_points = self._create_smooth_curve(1900, 3200, 1350, 4300, 15)
        points.extend(curve_points)
        
        # 5. 上部の架線に対する建築限界範囲（縦方向）
        points.append((1350, 4300))  # 縦方向範囲への接続点
        
        # 6. 上部架線範囲での円弧処理
        arc_points = self._create_overhead_arc_boundary()
        points.extend(arc_points)
        
        # 7. 最上部まで
        # 円弧の終点から最上部へ
        if arc_points:
            last_arc_point = arc_points[-1]
            if last_arc_point[1] < 5700:
                points.append((last_arc_point[0], 5700))  # 最大高さまで
        else:
            points.append((1350, 5700))  # 最大高さ
        
        # 上部（右から左へ）
        points.append((-1350, 5700))  # 最上部左端
        
        # 左側（上から下、右側と対称）
        right_points = [(x, y) for x, y in points if x > 0]
        right_points.reverse()  # 上から下の順番に
        
        for x, y in right_points[1:-1]:  # 最初と最後の点は除く
            points.append((-x, y))
        
        # 形状を閉じる
        points.append((1225, 0))
        
        print(f"✅ 修正版建築限界形状完成: {len(points)}点")
        self._print_shape_analysis(points)
        
        return points
    
    def _create_smooth_curve(self, x1: float, y1: float, x2: float, y2: float, num_points: int) -> List[Tuple[float, float]]:
        """滑らかな曲線を作成（3次ベジエ曲線）"""
        points = []
        
        print(f"🔄 滑らかな曲線を作成: ({x1},{y1}) → ({x2},{y2})")
        
        for i in range(1, num_points + 1):
            t = i / num_points
            
            # 制御点を設定（滑らかな曲線用）
            cp1_x, cp1_y = x1 - (x1 - x2) * 0.1, y1 + (y2 - y1) * 0.3
            cp2_x, cp2_y = x2 + (x1 - x2) * 0.1, y1 + (y2 - y1) * 0.7
            
            # 3次ベジエ曲線の計算
            x = (1-t)**3 * x1 + 3*(1-t)**2*t * cp1_x + 3*(1-t)*t**2 * cp2_x + t**3 * x2
            y = (1-t)**3 * y1 + 3*(1-t)**2*t * cp1_y + 3*(1-t)*t**2 * cp2_y + t**3 * y2
            
            points.append((x, y))
        
        return points
    
    def _create_overhead_arc_boundary(self) -> List[Tuple[float, float]]:
        """架線部分の円弧境界を作成"""
        points = []
        
        # 円の中心: (0, 4000), 半径: 1800mm
        center_x, center_y = 0, 4000
        radius = 1800
        
        print(f"⭕ 円弧境界作成: 中心({center_x},{center_y}), 半径{radius}mm")
        
        # 縦方向範囲 x=1350 との交点を求める
        x_boundary = 1350
        
        # 円の方程式: (x-0)² + (y-4000)² = 1800²
        # x = 1350 での y を求める
        discriminant = radius**2 - x_boundary**2
        
        if discriminant >= 0:
            y_intersect_upper = center_y + math.sqrt(discriminant)
            y_intersect_lower = center_y - math.sqrt(discriminant)
            
            print(f"  交点: x={x_boundary}, y={y_intersect_lower:.1f}～{y_intersect_upper:.1f}")
            
            # 上側の交点から円弧を描く
            start_angle = math.atan2(y_intersect_upper - center_y, x_boundary - center_x)
            end_angle = math.pi / 2  # 90度（真上）
            
            num_arc_points = 20
            for i in range(num_arc_points):
                angle = start_angle + (end_angle - start_angle) * i / (num_arc_points - 1)
                x = center_x + radius * math.cos(angle)
                y = center_y + radius * math.sin(angle)
                
                # 範囲内の点のみ追加
                if abs(x) <= 1350 and y <= 5700 and y >= 4000:
                    points.append((x, y))
                    
            print(f"  円弧点数: {len(points)}")
        
        return points
    
    def _print_shape_analysis(self, points: List[Tuple[float, float]]):
        """形状解析結果を表示"""
        if not points:
            return
        
        x_coords = [p[0] for p in points]
        y_coords = [p[1] for p in points]
        
        print("\\n📊 建築限界形状解析結果:")
        print(f"  - 座標点数: {len(points)}")
        print(f"  - 全幅: {max(x_coords) - min(x_coords):.0f}mm")
        print(f"  - 最大高さ: {max(y_coords):.0f}mm")
        print(f"  - 左端: {min(x_coords):.0f}mm")
        print(f"  - 右端: {max(x_coords):.0f}mm")
        
        # 主要高さでの幅を表示
        key_heights = [25, 375, 920, 3200, 4300, 5700]
        print("\\n📏 主要高さでの片側幅:")
        
        for height in key_heights:
            width = self._get_clearance_width_at_height(height, points)
            if width:
                print(f"  - 高さ{height:4.0f}mm: 片側{width:6.0f}mm (全幅{width*2:6.0f}mm)")
    
    def _get_clearance_width_at_height(self, height: float, 
                                      points: List[Tuple[float, float]]) -> float:
        """指定高さでの建築限界の片側幅を取得"""
        right_points = [(x, y) for x, y in points if x > 0]
        
        if not right_points:
            return None
        
        right_points.sort(key=lambda p: p[1])
        
        for i in range(len(right_points) - 1):
            y1, x1 = right_points[i][1], right_points[i][0]
            y2, x2 = right_points[i + 1][1], right_points[i + 1][0]
            
            if y1 <= height <= y2:
                if y2 == y1:
                    return x1
                ratio = (height - y1) / (y2 - y1)
                width = x1 + ratio * (x2 - x1)
                return width
        
        return None
    
    def validate_point_in_clearance(self, x: float, y: float, 
                                   clearance_points: List[Tuple[float, float]]) -> bool:
        """点が建築限界内にあるかチェック"""
        if not clearance_points or y < 0:
            return False
        
        clearance_width = self._get_clearance_width_at_height(y, clearance_points)
        
        if clearance_width is None:
            return False
        
        return abs(x) <= clearance_width
    
    def transform_clearance(self, points: List[Tuple[float, float]],
                           cant_mm: float, curve_radius_m: float) -> List[Tuple[float, float]]:
        """カント・曲線半径による建築限界の変形"""
        if not points:
            return []
        
        coords = np.array(points)
        
        # カント変換
        if cant_mm != 0:
            angle_rad = np.arctan(cant_mm / self.rail_gauge)
            
            cos_a = np.cos(angle_rad)
            sin_a = np.sin(angle_rad)
            
            rotation_matrix = np.array([
                [cos_a, -sin_a],
                [sin_a, cos_a]
            ])
            
            coords = coords @ rotation_matrix.T
        
        # 曲線拡幅
        if curve_radius_m > 0 and curve_radius_m < 3000:
            widening_factor = min(100, 1500.0 / curve_radius_m)
            coords[:, 0] = coords[:, 0] + np.sign(coords[:, 0]) * widening_factor
        
        return coords.tolist()

def create_comparison_visualization():
    """修正前後の比較可視化"""
    model = CorrectedBuildingClearanceModel()
    corrected_shape = model.create_clearance_shape()
    
    # プロット作成
    plt.figure(figsize=(16, 12))
    
    # 修正版建築限界をプロット
    if corrected_shape:
        coords = np.array(corrected_shape)
        x_coords = coords[:, 0]
        y_coords = coords[:, 1]
        
        plt.subplot(2, 2, 1)
        plt.plot(x_coords, y_coords, 'blue', linewidth=3, label='修正版建築限界')
        plt.fill(x_coords, y_coords, color='lightblue', alpha=0.4)
        plt.axhline(y=0, color='black', linewidth=3, alpha=0.7, label='レール面')
        plt.axvline(x=0, color='gray', linewidth=2, linestyle=':', alpha=0.6, label='レール中心')
        plt.axvline(x=-533.5, color='brown', linewidth=2, alpha=0.6)
        plt.axvline(x=533.5, color='brown', linewidth=2, alpha=0.6)
        
        plt.title('修正版建築限界モデル', fontsize=14)
        plt.xlabel('レール中心からの距離 (mm)')
        plt.ylabel('レールレベルからの高さ (mm)')
        plt.grid(True, alpha=0.3)
        plt.legend()
        plt.axis('equal')
        plt.xlim(-3000, 3000)
        plt.ylim(-500, 6000)
        
        # 主要寸法の注釈
        plt.annotate('1225mm', xy=(1225, 25/2), xytext=(1500, 200),
                    arrowprops=dict(arrowstyle='->', color='red'),
                    fontsize=10, color='red')
        plt.annotate('1575mm', xy=(1575, 650), xytext=(2000, 650),
                    arrowprops=dict(arrowstyle='->', color='red'),
                    fontsize=10, color='red')
        plt.annotate('1900mm', xy=(1900, 2000), xytext=(2200, 2000),
                    arrowprops=dict(arrowstyle='->', color='red'),
                    fontsize=10, color='red')
        plt.annotate('1350mm', xy=(1350, 5000), xytext=(1600, 5200),
                    arrowprops=dict(arrowstyle='->', color='red'),
                    fontsize=10, color='red')
    
    # カント変形例
    plt.subplot(2, 2, 2)
    cant_140 = model.transform_clearance(corrected_shape, 140, 0)
    if cant_140:
        coords_cant = np.array(cant_140)
        plt.plot(coords_cant[:, 0], coords_cant[:, 1], 'red', linewidth=3, label='カント140mm')
        plt.fill(coords_cant[:, 0], coords_cant[:, 1], color='lightcoral', alpha=0.4)
    
    plt.axhline(y=0, color='black', linewidth=3, alpha=0.7)
    plt.axvline(x=0, color='gray', linewidth=2, linestyle=':', alpha=0.6)
    plt.title('カント140mm適用時', fontsize=14)
    plt.xlabel('レール中心からの距離 (mm)')
    plt.ylabel('レールレベルからの高さ (mm)')
    plt.grid(True, alpha=0.3)
    plt.legend()
    plt.axis('equal')
    plt.xlim(-3000, 3000)
    plt.ylim(-500, 6000)
    
    # 曲線拡幅例
    plt.subplot(2, 2, 3)
    curve_300 = model.transform_clearance(corrected_shape, 0, 300)
    if curve_300:
        coords_curve = np.array(curve_300)
        plt.plot(coords_curve[:, 0], coords_curve[:, 1], 'green', linewidth=3, label='曲線R=300m')
        plt.fill(coords_curve[:, 0], coords_curve[:, 1], color='lightgreen', alpha=0.4)
    
    plt.axhline(y=0, color='black', linewidth=3, alpha=0.7)
    plt.axvline(x=0, color='gray', linewidth=2, linestyle=':', alpha=0.6)
    plt.title('曲線半径300m適用時', fontsize=14)
    plt.xlabel('レール中心からの距離 (mm)')
    plt.ylabel('レールレベルからの高さ (mm)')
    plt.grid(True, alpha=0.3)
    plt.legend()
    plt.axis('equal')
    plt.xlim(-3000, 3000)
    plt.ylim(-500, 6000)
    
    # 複合変形例
    plt.subplot(2, 2, 4)
    combined = model.transform_clearance(corrected_shape, 140, 300)
    if combined:
        coords_combined = np.array(combined)
        plt.plot(coords_combined[:, 0], coords_combined[:, 1], 'purple', linewidth=3, label='カント140mm + R=300m')
        plt.fill(coords_combined[:, 0], coords_combined[:, 1], color='plum', alpha=0.4)
    
    # 設備位置例
    test_equipment = [
        ("信号機", -2000, 3000),
        ("標識", -1800, 2000),
        ("架線柱", 1500, 4500),
        ("中央設備", 0, 2500)
    ]
    
    for name, x, y in test_equipment:
        is_safe = model.validate_point_in_clearance(x, y, combined)
        color = 'green' if is_safe else 'red'
        marker = 'o' if is_safe else 'X'
        plt.scatter([x], [y], color=color, s=150, marker=marker, 
                   edgecolors='black', linewidth=2, label=f'{name}')
    
    plt.axhline(y=0, color='black', linewidth=3, alpha=0.7)
    plt.axvline(x=0, color='gray', linewidth=2, linestyle=':', alpha=0.6)
    plt.title('複合変形 + 設備判定例', fontsize=14)
    plt.xlabel('レール中心からの距離 (mm)')
    plt.ylabel('レールレベルからの高さ (mm)')
    plt.grid(True, alpha=0.3)
    plt.legend(fontsize=9)
    plt.axis('equal')
    plt.xlim(-3000, 3000)
    plt.ylim(-500, 6000)
    
    plt.tight_layout()
    plt.savefig('corrected_clearance_model.png', dpi=150, bbox_inches='tight')
    plt.close()
    
    print("\\n💾 可視化プロットを保存: corrected_clearance_model.png")

def test_equipment_validation():
    """設備判定テスト"""
    print("\\n🧪 設備判定テストを実行...")
    
    model = CorrectedBuildingClearanceModel()
    base_shape = model.create_clearance_shape()
    
    # テストケース
    test_cases = [
        {"name": "基本形状", "cant": 0, "radius": 0},
        {"name": "カント140mm", "cant": 140, "radius": 0},
        {"name": "曲線R=300m", "cant": 0, "radius": 300},
        {"name": "複合変形", "cant": 140, "radius": 300},
    ]
    
    test_equipment = [
        ("信号機", -2000, 3000),
        ("標識", -1800, 2000),
        ("架線柱", 1500, 4500),
        ("中央設備", 0, 2500),
        ("境界設備", 1350, 4000),
    ]
    
    print("\\n📋 設備判定結果:")
    print("条件".ljust(12) + " | " + "".join([f"{name:8s}" for name, _, _ in test_equipment]))
    print("-" * 60)
    
    for case in test_cases:
        transformed = model.transform_clearance(base_shape, case["cant"], case["radius"])
        
        results = []
        for name, x, y in test_equipment:
            is_safe = model.validate_point_in_clearance(x, y, transformed)
            results.append("✅" if is_safe else "❌")
        
        result_str = " | ".join([f"{r:8s}" for r in results])
        print(f"{case['name']:12s} | {result_str}")
    
def main():
    """メイン実行"""
    print("🎯 修正版建築限界モデル - デモ・検証プログラム")
    print("=" * 60)
    
    # モデル作成と解析
    model = CorrectedBuildingClearanceModel()
    corrected_shape = model.create_clearance_shape()
    
    # 設備判定テスト
    test_equipment_validation()
    
    # 可視化作成
    create_comparison_visualization()
    
    print("\\n" + "=" * 60)
    print("✅ 修正版建築限界モデルの検証完了!")
    print("\\n📁 生成ファイル:")
    print("  - corrected_clearance_model.png (可視化プロット)")
    
    print("\\n🎯 修正内容:")
    print("  ✅ ウィンドウサイズ: 画面の90%に自動調整")
    print("  ✅ 日本語フォント: 複数候補から自動選択")
    print("  ✅ 判定開始ボタン: 明示的な判定実行")
    print("  ✅ 正確な寸法: ユーザー指定寸法に完全準拠")
    print("    - レール面～25mm: 1225mm")
    print("    - 375～920mm: 1575mm")
    print("    - 920～3200mm: 1900mm")
    print("    - 3200～4300mm: 滑らかな曲線")
    print("    - 上部架線限界: 1350mm, 最大5700mm")
    print("    - 円弧処理: 中心(0,4000), 半径1800mm")
    
    print("\\n💡 GUI版では以下の機能が動作:")
    print("  - 適切なウィンドウサイズとスクロール")
    print("  - 日本語文字化け解消")
    print("  - 判定開始ボタンによる明示的判定")
    print("  - 修正された建築限界寸法")
    print("  - 設備位置の×マーク表示")
    print("  - リアルタイム支障・安全判定")

if __name__ == "__main__":
    main()