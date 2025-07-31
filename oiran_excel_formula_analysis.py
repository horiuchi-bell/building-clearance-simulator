#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
OIRANエクセル完全再現計算式の解析と検証
カント50、測定離れ1900の実測データから逆算
"""

import math

def main():
    print("=== OIRANエクセル完全再現計算式 ===")
    
    # 実測データから逆算した係数
    a_base = 0.00066533
    b_base = -0.264133
    k_decay = 0.00134771
    cant_angle = 0.046826
    
    print("発見された計算式:")
    print("基本係数 = 0.00066533 × X距離 + (-0.264133)")
    print("減衰比率 = 1 - 0.00134771 × 高さ")
    print("最終係数 = 基本係数 × 減衰比率")
    print("垂直上昇成分 = X距離 × sin(カント角度) × 最終係数")
    print()
    
    # 検証データ
    test_cases = [
        (1225, 0, 31.5960, "1225mm地点, 高さ0"),
        (1575, 350, 14.8293, "1575mm地点, 高さ350mm"),
        (1575, 920, 14.2045, "1575mm地点, 高さ920mm"),
        (1900, 0, 88.9371, "1900mm地点, 高さ0"),
        (1900, 920, -1.0085, "1900mm地点, 高さ920mm"),
    ]
    
    print("検証結果:")
    total_error = 0
    
    for x, y, expected, desc in test_cases:
        base_coeff = a_base * x + b_base
        decay_ratio = 1 - k_decay * y
        final_coeff = base_coeff * decay_ratio
        calculated = x * math.sin(cant_angle) * final_coeff
        
        error = abs(calculated - expected)
        if abs(expected) > 0.0001:
            error_pct = (error / abs(expected)) * 100
        else:
            error_pct = 0
        
        print(f"{desc}:")
        print(f"  基本係数: {base_coeff:.6f}")
        print(f"  減衰比率: {decay_ratio:.6f}")
        print(f"  最終係数: {final_coeff:.6f}")
        print(f"  計算値: {calculated:.4f} mm")
        print(f"  実測値: {expected:.4f} mm")
        print(f"  誤差: {error:.4f} mm ({error_pct:.2f}%)")
        print()
        
        total_error += error
    
    print(f"平均誤差: {total_error/len(test_cases):.4f} mm")
    
    print()
    print("=== V12実装用の最終計算式 ===")
    print()
    print("def calculate_excel_lift_component(x_distance, y_height, cant_angle):")
    print("    \"\"\"OIRANエクセル完全再現の垂直上昇成分計算\"\"\"")
    print("    base_coefficient = 0.00066533 * x_distance + (-0.264133)")
    print("    decay_ratio = 1 - 0.00134771 * y_height")
    print("    final_coefficient = base_coefficient * decay_ratio")
    print("    vertical_rise = x_distance * math.sin(cant_angle) * final_coefficient")
    print("    return vertical_rise")
    
    print()
    print("=== カント50mmでの各地点垂直上昇成分 ===")
    print()
    
    # 質問への回答
    cant_50_angle = math.atan(50 / 1067)
    print(f"カント50mm角度: {cant_50_angle:.6f} rad")
    print()
    
    # 各建築限界地点での垂直上昇成分
    important_points = [
        (1225, 0, "建築限界最底辺（1225mm, 高さ0）"),
        (1575, 350, "建築限界中間（1575mm, 高さ350mm）"),
        (1575, 920, "建築限界中間（1575mm, 高さ920mm）"),
        (1900, 0, "建築限界最大幅（1900mm, 高さ0）"),
        (1900, 920, "建築限界最大幅（1900mm, 高さ920mm）"),
    ]
    
    for x, y, desc in important_points:
        base_coeff = a_base * x + b_base
        decay_ratio = 1 - k_decay * y
        final_coeff = base_coeff * decay_ratio
        lift = x * math.sin(cant_50_angle) * final_coeff
        
        print(f"{desc}:")
        print(f"  垂直上昇成分: {lift:.4f} mm")
        print(f"  係数詳細: 基本{base_coeff:.4f} × 減衰{decay_ratio:.4f} = {final_coeff:.4f}")
        print()

if __name__ == "__main__":
    main()