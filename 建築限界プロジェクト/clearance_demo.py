#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
建築限界シミュレーター - コマンドライン デモ版
正確な寸法に基づく建築限界モデルの機能確認
"""

import matplotlib.pyplot as plt
import numpy as np
from accurate_clearance_model import AccurateClearanceModel
import json

class ClearanceDemo:
    def __init__(self):
        """デモ初期化"""
        self.model = AccurateClearanceModel()
        self.base_clearance = self.model.create_simplified_clearance_shape()
        
        print("🏗️ 建築限界シミュレーター デモ版")
        print("=" * 50)
        
    def demonstrate_basic_functionality(self):
        """基本機能のデモンストレーション"""
        print("\\n📐 基本建築限界モデル:")
        print(f"  - 座標点数: {len(self.base_clearance)}")
        
        # 基本形状の主要寸法を表示
        if self.base_clearance:
            x_coords = [p[0] for p in self.base_clearance]
            y_coords = [p[1] for p in self.base_clearance]
            
            print(f"  - 全幅: {max(x_coords) - min(x_coords):.0f}mm")
            print(f"  - 最大高さ: {max(y_coords):.0f}mm")
            print(f"  - 左端: {min(x_coords):.0f}mm")
            print(f"  - 右端: {max(x_coords):.0f}mm")
    
    def demonstrate_cant_transformation(self):
        """カント変形のデモンストレーション"""
        print("\\n⚖️ カント変形デモ:")
        
        test_cant_values = [0, 100, 140, -80]
        
        for cant in test_cant_values:
            transformed = self.model.transform_clearance_for_cant_and_curve(
                self.base_clearance, cant, 0
            )
            
            angle_deg = np.degrees(np.arctan(cant / 1067)) if cant != 0 else 0
            
            print(f"  - カント {cant:4.0f}mm: 傾斜角 {angle_deg:6.2f}°, 座標数 {len(transformed)}")
    
    def demonstrate_curve_widening(self):
        """曲線拡幅のデモンストレーション"""
        print("\\n🔄 曲線拡幅デモ:")
        
        test_radii = [0, 300, 600, 1200, 2000]
        
        for radius in test_radii:
            transformed = self.model.transform_clearance_for_cant_and_curve(
                self.base_clearance, 0, radius
            )
            
            # 拡幅量を概算
            if radius > 0 and radius < 3000:
                widening = min(100, 1500.0 / radius)
            else:
                widening = 0
            
            curve_type = "直線" if radius == 0 else f"R={radius}m"
            print(f"  - {curve_type:8s}: 拡幅量 {widening:5.1f}mm, 座標数 {len(transformed)}")
    
    def demonstrate_equipment_measurement(self):
        """設備測定機能のデモンストレーション"""
        print("\\n📍 設備位置測定デモ:")
        
        # テスト用設備位置
        test_equipment = [
            ("信号機", -2000, 3000),
            ("標識", -1800, 2000),
            ("架線柱", -3000, 4000),
            ("中央設備", 0, 2000),
            ("支障設備", 1200, 2600),  # 建築限界外
        ]
        
        print("\\n  設備名     |  位置(mm)    | 高さ(mm) | 判定")
        print("  " + "-" * 45)
        
        for name, x, y in test_equipment:
            is_safe = self.model.validate_point_in_clearance(x, y, self.base_clearance)
            status = "✅ 安全" if is_safe else "❌ 支障"
            print(f"  {name:10s} | {x:8.0f}   | {y:6.0f}  | {status}")
    
    def demonstrate_combined_scenario(self):
        """複合シナリオのデモンストレーション"""
        print("\\n🎯 複合シナリオデモ:")
        print("  シナリオ: カント140mm + 曲線半径300m の条件での設備判定")
        
        cant = 140
        radius = 300
        
        # 変形後の建築限界
        transformed_clearance = self.model.transform_clearance_for_cant_and_curve(
            self.base_clearance, cant, radius
        )
        
        angle_deg = np.degrees(np.arctan(cant / 1067))
        widening = min(100, 1500.0 / radius) if radius > 0 else 0
        
        print(f"  - カント傾斜角: {angle_deg:.2f}°")
        print(f"  - 曲線拡幅: {widening:.1f}mm")
        
        # 設備判定
        test_positions = [
            ("信号機A", -2000, 3000),
            ("信号機B", -1500, 2500),
            ("架線設備", 1000, 4000),
        ]
        
        print("\\n  変形後の設備判定:")
        for name, x, y in test_positions:
            is_safe = self.model.validate_point_in_clearance(x, y, transformed_clearance)
            status = "✅ 安全" if is_safe else "❌ 支障"
            print(f"    {name}: {status}")
    
    def generate_sample_data(self):
        """サンプルデータ生成"""
        print("\\n💾 サンプルデータ生成:")
        
        # 複数のテストケースを生成
        test_cases = []
        
        scenarios = [
            {"name": "直線_傾きなし", "cant": 0, "radius": 0},
            {"name": "直線_カント140", "cant": 140, "radius": 0},
            {"name": "曲線_R300", "cant": 0, "radius": 300},
            {"name": "曲線_カント140_R300", "cant": 140, "radius": 300},
        ]
        
        for scenario in scenarios:
            cant = scenario["cant"]
            radius = scenario["radius"]
            
            # 変形された建築限界
            transformed = self.model.transform_clearance_for_cant_and_curve(
                self.base_clearance, cant, radius
            )
            
            # 設備測定例
            equipment_tests = [
                {"name": "信号機", "x": -2000, "y": 3000},
                {"name": "標識", "x": -1800, "y": 2000},
                {"name": "架線柱", "x": 1500, "y": 4200},
            ]
            
            scenario_data = {
                "scenario": scenario["name"],
                "conditions": {"cant_mm": cant, "curve_radius_m": radius},
                "clearance_coordinates": transformed,
                "equipment_tests": []
            }
            
            for equipment in equipment_tests:
                is_safe = self.model.validate_point_in_clearance(
                    equipment["x"], equipment["y"], transformed
                )
                
                equipment["safe"] = is_safe
                scenario_data["equipment_tests"].append(equipment)
            
            test_cases.append(scenario_data)
        
        # JSONファイルに保存
        with open("clearance_demo_data.json", 'w', encoding='utf-8') as f:
            json.dump(test_cases, f, ensure_ascii=False, indent=2)
        
        print(f"  ✅ {len(test_cases)}件のテストケースを 'clearance_demo_data.json' に保存")
    
    def create_visualization_plot(self):
        """可視化プロット作成（保存用）"""
        print("\\n📊 可視化プロット作成:")
        
        try:
            # matplotlib日本語フォント設定
            plt.rcParams['font.family'] = 'DejaVu Sans'
            plt.rcParams['axes.unicode_minus'] = False
            
            fig, axes = plt.subplots(2, 2, figsize=(16, 12))
            fig.suptitle('Building Clearance Simulation Demo', fontsize=16)
            
            scenarios = [
                ("Normal (Cant=0, R=inf)", 0, 0),
                ("Cant 140mm", 140, 0),  
                ("Curve R=300m", 0, 300),
                ("Cant 140mm + R=300m", 140, 300),
            ]
            
            for idx, (title, cant, radius) in enumerate(scenarios):
                ax = axes[idx // 2, idx % 2]
                
                # 変形された建築限界
                transformed = self.model.transform_clearance_for_cant_and_curve(
                    self.base_clearance, cant, radius
                )
                
                if transformed:
                    coords = np.array(transformed)
                    x_coords = coords[:, 0]
                    y_coords = coords[:, 1]
                    
                    # 建築限界描画
                    ax.plot(x_coords, y_coords, 'blue', linewidth=2, label='Building Clearance')
                    ax.fill(x_coords, y_coords, color='lightblue', alpha=0.3)
                    
                    # レール表示
                    ax.axhline(y=0, color='black', linewidth=3, alpha=0.7, label='Rail Level')
                    ax.axvline(x=0, color='gray', linewidth=1, linestyle=':', alpha=0.5)
                    ax.axvline(x=-533.5, color='brown', linewidth=2, alpha=0.6)
                    ax.axvline(x=533.5, color='brown', linewidth=2, alpha=0.6)
                    
                    # テスト設備位置
                    test_equipment = [
                        ("Signal", -2000, 3000),
                        ("Sign", -1800, 2000),
                        ("Pole", 1500, 4200),
                    ]
                    
                    for name, x, y in test_equipment:
                        is_safe = self.model.validate_point_in_clearance(x, y, transformed)
                        color = 'green' if is_safe else 'red'
                        marker = 'o' if is_safe else 'X'
                        ax.scatter([x], [y], color=color, s=100, marker=marker, 
                                 edgecolors='black', linewidth=1, label=f'{name}', zorder=10)
                
                ax.set_title(title)
                ax.set_xlabel('Distance from Rail Center (mm)')
                ax.set_ylabel('Height from Rail Level (mm)')
                ax.grid(True, alpha=0.3)
                ax.set_aspect('equal')
                ax.legend(fontsize=8)
                
                # 軸範囲設定
                ax.set_xlim(-3500, 3500)
                ax.set_ylim(-500, 5000)
            
            plt.tight_layout()
            plt.savefig('clearance_simulation_demo.png', dpi=150, bbox_inches='tight')
            plt.close()
            
            print("  ✅ 可視化プロットを 'clearance_simulation_demo.png' に保存")
            
        except Exception as e:
            print(f"  ❌ プロット作成エラー: {e}")
    
    def run_full_demo(self):
        """完全デモ実行"""
        print("\\n🚀 建築限界シミュレーター 完全デモを開始...")
        
        # 各機能のデモ
        self.demonstrate_basic_functionality()
        self.demonstrate_cant_transformation()
        self.demonstrate_curve_widening()
        self.demonstrate_equipment_measurement()
        self.demonstrate_combined_scenario()
        
        # データとグラフ生成
        self.generate_sample_data()
        self.create_visualization_plot()
        
        print("\\n" + "=" * 50)
        print("✅ デモンストレーション完了!")
        print("\\n📁 生成されたファイル:")
        print("  - clearance_demo_data.json (テストケースデータ)")
        print("  - clearance_simulation_demo.png (可視化プロット)")
        
        print("\\n🎯 アプリケーション機能概要:")
        print("  1. ✅ 正確な建築限界モデル（寸法図準拠）")
        print("  2. ✅ カント値による傾き変形")
        print("  3. ✅ 曲線半径による拡幅変形")
        print("  4. ✅ 設備位置測定・判定機能")
        print("  5. ✅ 支障・安全判定")
        print("  6. ✅ 複合条件対応")
        
        print("\\n💡 実際のGUIアプリケーションでは:")
        print("  - リアルタイムな視覚表示")
        print("  - 対話的なパラメータ調整")
        print("  - 設備位置の×マーク表示")
        print("  - 詳細な余裕距離計算")
        print("  - 設定の保存・読み込み")

def main():
    """メイン実行"""
    demo = ClearanceDemo()
    demo.run_full_demo()

if __name__ == "__main__":
    main()