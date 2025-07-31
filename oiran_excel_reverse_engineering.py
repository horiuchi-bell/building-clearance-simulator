#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
OIRANエクセルの実際の計算式逆算解析
実測データから正確な計算式を逆算で発見
"""

import math
import numpy as np
from scipy.optimize import minimize

def load_measured_data():
    """OIRANエクセルから取得した実測データ"""
    # カント50mm時の実測データ
    data = [
        # (x_distance, y_height, measured_lift, description)
        (1225, 0, 31.5960, "建築限界最底辺"),
        (1575, 350, 14.8293, "中間点1"),
        (1575, 920, 14.2045, "中間点2"), 
        (1900, 0, 88.9371, "最大幅点"),
        (1900, 920, -1.0085, "最大幅上部")
    ]
    return data

def test_linear_coefficient_model(data):
    """線形係数モデルのテスト"""
    print("=== 線形係数モデルのテスト ===")
    
    cant_angle = math.atan(50 / 1067)
    
    # 線形回帰で係数を求める
    X = []
    y = []
    
    for x_dist, y_height, measured_lift, _ in data:
        # 特徴量: [x_distance, y_height, x*y交互作用項, 定数項]
        X.append([x_dist, y_height, x_dist * y_height, 1])
        # 目標値: measured_lift / (x_dist * sin(cant_angle))
        base_lift = x_dist * math.sin(cant_angle)
        if abs(base_lift) > 0.001:
            coefficient = measured_lift / base_lift
        else:
            coefficient = 0
        y.append(coefficient)
    
    X = np.array(X)
    y = np.array(y)
    
    # 最小二乗法で解く
    try:
        coeffs = np.linalg.lstsq(X, y, rcond=None)[0]
        
        print(f"線形回帰結果:")
        print(f"  X距離係数: {coeffs[0]:.8f}")
        print(f"  Y高さ係数: {coeffs[1]:.8f}")
        print(f"  交互作用係数: {coeffs[2]:.8f}")
        print(f"  定数項: {coeffs[3]:.6f}")
        
        # 検証
        print("\n検証結果:")
        total_error = 0
        for i, (x_dist, y_height, measured_lift, desc) in enumerate(data):
            predicted_coeff = coeffs[0]*x_dist + coeffs[1]*y_height + coeffs[2]*x_dist*y_height + coeffs[3]
            predicted_lift = x_dist * math.sin(cant_angle) * predicted_coeff
            error = abs(predicted_lift - measured_lift)
            error_pct = (error / abs(measured_lift)) * 100 if abs(measured_lift) > 0.001 else 0
            
            print(f"  {desc}: 予測={predicted_lift:.4f}, 実測={measured_lift:.4f}, 誤差={error:.4f}mm ({error_pct:.1f}%)")
            total_error += error
        
        avg_error = total_error / len(data)
        print(f"\n平均誤差: {avg_error:.4f} mm")
        
        return coeffs, avg_error
        
    except Exception as e:
        print(f"線形回帰エラー: {e}")
        return None, float('inf')

def test_piecewise_model(data):
    """区間別モデルのテスト"""
    print("=== 区間別モデルのテスト ===")
    
    cant_angle = math.atan(50 / 1067)
    
    # X距離別にグループ化
    x_groups = {}
    for x_dist, y_height, measured_lift, desc in data:
        if x_dist not in x_groups:
            x_groups[x_dist] = []
        x_groups[x_dist].append((y_height, measured_lift, desc))
    
    results = {}
    
    for x_dist, group_data in x_groups.items():
        print(f"\nX={x_dist}mm地点の分析:")
        
        if len(group_data) >= 2:
            # 高さ0での基本係数を推定
            y_heights = [item[0] for item in group_data]
            lifts = [item[1] for item in group_data]
            
            # 高さ0での値を線形補間で推定
            if 0 in y_heights:
                base_lift = lifts[y_heights.index(0)]
            else:
                # 線形補間
                y_sorted = sorted(zip(y_heights, lifts))
                y0, l0 = y_sorted[0]
                y1, l1 = y_sorted[1]
                base_lift = l0 + (l1 - l0) * (0 - y0) / (y1 - y0)
            
            base_coeff = base_lift / (x_dist * math.sin(cant_angle))
            print(f"  基本係数（高さ0推定）: {base_coeff:.6f}")
            
            # 高さ依存性を分析
            for y_height, measured_lift, desc in group_data:
                if y_height > 0:
                    actual_coeff = measured_lift / (x_dist * math.sin(cant_angle))
                    ratio = actual_coeff / base_coeff if abs(base_coeff) > 0.001 else 0
                    decay = (1 - ratio) / y_height if y_height > 0 else 0
                    
                    print(f"    高さ{y_height}mm: 係数={actual_coeff:.6f}, 比率={ratio:.6f}, 減衰={decay:.8f}")
            
            results[x_dist] = {
                'base_coefficient': base_coeff,
                'group_data': group_data
            }
    
    return results

def test_exponential_model(data):
    """指数関数モデルのテスト"""
    print("=== 指数関数モデルのテスト ===")
    
    cant_angle = math.atan(50 / 1067)
    
    def exponential_model(params, x_dist, y_height):
        """指数関数モデル: coeff = (a*x + b) * exp(-c*y)"""
        a, b, c = params
        base_coeff = a * x_dist + b
        height_factor = math.exp(-c * y_height)
        return base_coeff * height_factor
    
    def objective(params):
        """目的関数"""
        total_error = 0
        for x_dist, y_height, measured_lift, _ in data:
            predicted_coeff = exponential_model(params, x_dist, y_height)
            predicted_lift = x_dist * math.sin(cant_angle) * predicted_coeff
            error = (predicted_lift - measured_lift) ** 2
            total_error += error
        return total_error
    
    # 初期値
    initial_params = [0.0007, -0.26, 0.001]
    
    try:
        result = minimize(objective, initial_params, method='Nelder-Mead')
        
        if result.success:
            a, b, c = result.x
            print(f"指数関数モデル結果:")
            print(f"  係数 = ({a:.8f} × X距離 + {b:.6f}) × exp(-{c:.8f} × Y高さ)")
            
            # 検証
            print("\n検証結果:")
            total_error = 0
            for x_dist, y_height, measured_lift, desc in data:
                predicted_coeff = exponential_model(result.x, x_dist, y_height)
                predicted_lift = x_dist * math.sin(cant_angle) * predicted_coeff
                error = abs(predicted_lift - measured_lift)
                error_pct = (error / abs(measured_lift)) * 100 if abs(measured_lift) > 0.001 else 0
                
                print(f"  {desc}: 予測={predicted_lift:.4f}, 実測={measured_lift:.4f}, 誤差={error:.4f}mm ({error_pct:.1f}%)")
                total_error += error
            
            avg_error = total_error / len(data)
            print(f"\n平均誤差: {avg_error:.4f} mm")
            
            return result.x, avg_error
        else:
            print("指数関数モデル最適化失敗")
            return None, float('inf')
            
    except Exception as e:
        print(f"指数関数モデルエラー: {e}")
        return None, float('inf')

def analyze_data_patterns():
    """データパターンの詳細分析"""
    print("=== データパターンの詳細分析 ===")
    
    data = load_measured_data()
    cant_angle = math.atan(50 / 1067)
    
    print("実測データの特徴:")
    for x_dist, y_height, measured_lift, desc in data:
        simple_lift = x_dist * math.sin(cant_angle)
        coefficient = measured_lift / simple_lift if abs(simple_lift) > 0.001 else 0
        
        print(f"{desc}:")
        print(f"  座標: ({x_dist}, {y_height})")
        print(f"  単純回転: {simple_lift:.4f} mm")
        print(f"  実測値: {measured_lift:.4f} mm")
        print(f"  係数: {coefficient:.6f}")
        
        # 特異なパターンの検出
        if coefficient < 0:
            print(f"  ⚠️ 負の係数 - 特殊な計算が適用されている可能性")
        elif abs(coefficient - 1.0) < 0.01:
            print(f"  ✅ 単純回転とほぼ一致")
        elif coefficient < 0.5:
            print(f"  📉 大幅な減衰 - 高さまたは距離による補正")
        
        print()

def main():
    """メイン解析実行"""
    print("OIRANエクセル実際の計算式 逆算解析")
    print("=" * 60)
    
    data = load_measured_data()
    
    # データパターン分析
    analyze_data_patterns()
    print()
    
    # 各モデルのテスト
    models_results = []
    
    # 線形係数モデル
    linear_coeffs, linear_error = test_linear_coefficient_model(data)
    models_results.append(("線形係数モデル", linear_error))
    print()
    
    # 区間別モデル
    piecewise_results = test_piecewise_model(data)
    print()
    
    # 指数関数モデル
    exp_coeffs, exp_error = test_exponential_model(data)
    models_results.append(("指数関数モデル", exp_error))
    print()
    
    # 結果比較
    print("=== モデル性能比較 ===")
    models_results.sort(key=lambda x: x[1])
    
    for model_name, error in models_results:
        print(f"{model_name}: 平均誤差 {error:.4f} mm")
    
    best_model = models_results[0]
    print(f"\n最適モデル: {best_model[0]} (誤差: {best_model[1]:.4f} mm)")
    
    print()
    print("=== 結論 ===")
    print("OIRANエクセルの計算式は:")
    print("1. 単純な線形係数では不十分")
    print("2. X距離とY高さの複雑な相互作用がある")
    print("3. 負の値を含む特殊なケースが存在")
    print("4. 実際のExcel内部の計算式はより複雑な可能性")

if __name__ == "__main__":
    main()