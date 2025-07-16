#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
建築限界測定システム - テスト版
コマンドライン対話形式でテスト
"""

from building_limit_calculator import BuildingLimitCalculator
import matplotlib.pyplot as plt
import matplotlib.patches as patches
import numpy as np

def interactive_test():
    """対話式テスト"""
    print("=== 建築限界測定システム テスト版 ===")
    print("OIRANシュミレーターと同等の計算を実行します\n")
    
    # 計算器初期化
    calc = BuildingLimitCalculator("直流")
    
    while True:
        print("\n--- パラメータ入力 ---")
        
        try:
            # パラメータ入力
            radius = float(input("曲線半径 (m) [デフォルト: 160]: ") or "160")
            cant = float(input("カント (mm) [デフォルト: 105]: ") or "105")
            distance = float(input("測定離れ (mm) [デフォルト: 2110]: ") or "2110")
            height = float(input("測定高さ (mm) [デフォルト: 3150]: ") or "3150")
            
            print(f"\n入力値:")
            print(f"  曲線半径: {radius}m")
            print(f"  カント: {cant}mm")
            print(f"  測定離れ: {distance}mm")
            print(f"  測定高さ: {height}mm")
            
            # 計算実行
            result = calc.check_clearance(distance, height, radius, cant)
            
            # 結果表示
            print(f"\n=== 計算結果 ===")
            print(f"判定: {result['status']}")
            print(f"最小距離: {result['min_distance']:.1f}mm")
            print(f"拡大幅: {result['expansion_width']:.1f}mm")
            print(f"カント角度: {np.degrees(result['cant_angle']):.2f}°")
            print(f"スラック: {result['slack']}mm")
            print(f"測定ポイント: ({distance}, {height})")
            print(f"最近接点: ({result['nearest_point'][0]:.1f}, {result['nearest_point'][1]:.1f})")
            
            # グラフ保存
            save_graph = input("\nグラフを画像ファイルに保存しますか？ (y/N): ").lower()
            if save_graph == 'y':
                create_and_save_graph(calc, radius, cant, distance, height, result)
            
            # 座標データ表示
            show_coords = input("変形後の建築限界座標を表示しますか？ (y/N): ").lower()
            if show_coords == 'y':
                coords = result['transformed_coordinates']
                print(f"\n=== 変形後建築限界座標 ({len(coords)}点) ===")
                for i, (x, y) in enumerate(coords[:20]):  # 最初の20点
                    print(f"  {i+1:2d}: ({x:8.1f}, {y:8.1f})")
                if len(coords) > 20:
                    print(f"  ... 他 {len(coords) - 20} 点")
            
            # 継続確認
            continue_test = input("\n別のパラメータでテストしますか？ (Y/n): ").lower()
            if continue_test == 'n':
                break
                
        except ValueError:
            print("数値を正しく入力してください")
        except KeyboardInterrupt:
            print("\nテストを終了します")
            break
        except Exception as e:
            print(f"エラー: {e}")

def create_and_save_graph(calc, radius, cant, distance, height, result):
    """グラフ作成・保存"""
    try:
        coords = result['transformed_coordinates']
        
        plt.figure(figsize=(12, 8))
        
        # 建築限界描画
        x_coords = [x for x, y in coords]
        y_coords = [y for x, y in coords]
        
        plt.plot(x_coords + [x_coords[0]], y_coords + [y_coords[0]], 
                'b-', linewidth=2, label='建築限界')
        plt.fill(x_coords, y_coords, alpha=0.2, color='lightblue')
        
        # 軌道中心線
        plt.axvline(x=0, color='black', linestyle='--', alpha=0.5, label='軌道中心')
        
        # レール位置
        plt.axhline(y=0, color='brown', linewidth=3, alpha=0.7, label='レール面')
        
        # 測定ポイント
        color = 'red' if result['status'] == '支障' else 'green'
        plt.plot(distance, height, 'x', color=color, markersize=15, markeredgewidth=4, 
                label=f'測定点 ({result["status"]})')
        
        # 情報テキスト
        info_text = f"""パラメータ:
曲線半径: {radius}m
カント: {cant}mm
拡大幅: {result['expansion_width']:.1f}mm
カント角度: {np.degrees(result['cant_angle']):.2f}°
スラック: {result['slack']}mm

判定: {result['status']}
最小距離: {result['min_distance']:.1f}mm"""
        
        plt.text(0.02, 0.98, info_text, transform=plt.gca().transAxes, 
                verticalalignment='top', fontsize=10,
                bbox=dict(boxstyle='round', facecolor='wheat', alpha=0.8))
        
        # グリッドと軸設定
        plt.grid(True, alpha=0.3)
        plt.xlabel('軌道中心からの距離 (mm)')
        plt.ylabel('レール踏面からの高さ (mm)')
        plt.title(f'建築限界測定結果 - R{radius}m C{cant}mm')
        plt.legend()
        
        # 縦横比を等しく
        plt.gca().set_aspect('equal', adjustable='box')
        
        # 表示範囲調整
        margin = 300
        x_min, x_max = min(x_coords) - margin, max(x_coords) + margin
        y_min, y_max = min(y_coords) - margin, max(y_coords) + margin
        
        # 測定点も含める
        x_min = min(x_min, distance - margin)
        x_max = max(x_max, distance + margin)
        y_min = min(y_min, height - margin)
        y_max = max(y_max, height + margin)
        
        plt.xlim(x_min, x_max)
        plt.ylim(y_min, y_max)
        
        # 保存
        filename = f"建築限界図_R{radius}m_C{cant}mm.png"
        plt.tight_layout()
        plt.savefig(filename, dpi=300, bbox_inches='tight')
        print(f"グラフを保存しました: {filename}")
        plt.close()
        
    except Exception as e:
        print(f"グラフ保存エラー: {e}")

def run_preset_tests():
    """プリセットテスト実行"""
    print("\n=== プリセットテスト実行 ===")
    
    calc = BuildingLimitCalculator("直流")
    
    test_cases = [
        {"name": "OIRANデフォルト", "radius": 160, "cant": 105, "distance": 2110, "height": 3150},
        {"name": "急曲線", "radius": 200, "cant": 100, "distance": 1800, "height": 2500},
        {"name": "緩曲線", "radius": 800, "cant": 30, "distance": 2200, "height": 3500},
        {"name": "直線", "radius": 9999, "cant": 0, "distance": 1900, "height": 3000},
    ]
    
    for case in test_cases:
        print(f"\n--- {case['name']} ---")
        result = calc.check_clearance(case['distance'], case['height'], case['radius'], case['cant'])
        
        print(f"R{case['radius']}m C{case['cant']}mm 測定点({case['distance']}, {case['height']})")
        print(f"判定: {result['status']} (最小距離: {result['min_distance']:.1f}mm)")
        print(f"拡大幅: {result['expansion_width']:.1f}mm カント角度: {np.degrees(result['cant_angle']):.2f}°")

if __name__ == "__main__":
    print("建築限界測定システム - コマンドライン版")
    print("1: 対話式テスト")
    print("2: プリセットテスト")
    
    choice = input("選択してください (1/2): ").strip()
    
    if choice == "1":
        interactive_test()
    elif choice == "2":
        run_preset_tests()
    else:
        print("1または2を選択してください")
    
    print("\nテスト完了")