#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
OIRANエクセルの実際の計算式解析
極座標変換とカント回転の関係を調査
"""

import math

def main():
    print("=== OIRANエクセルの実際の計算式解析 ===")
    
    # エクセルから抽出したデータ
    excel_data = [
        (2110, 0, 0),
        (3335, 0, 0), 
        (3685, 350, 0.09469557520921408),
        (3685, 920, 0.24465937833567034),
        (4010, 920, 0.22552357091684352),
    ]
    
    print("AA列(x), AB列(y), X列(φ rad)の関係分析:")
    print()
    
    # カント50mmの場合を想定
    cant_mm = 50
    cant_angle = math.atan(cant_mm / 1067)
    print(f"カント角度: {cant_angle:.6f} rad")
    
    print()
    print("各点の解析:")
    
    for i, (x, y, phi) in enumerate(excel_data):
        print(f"点{i+1}: AA={x}, AB={y}, φ={phi:.6f}")
        
        # 元座標からの極座標計算
        r = math.sqrt(x**2 + y**2)
        if x != 0:
            theta_calc = math.atan(y/x) if x > 0 else math.atan(y/x) + math.pi
        else:
            theta_calc = math.pi/2 if y > 0 else -math.pi/2
        
        print(f"  極座標: r={r:.2f}, θ計算値={theta_calc:.6f}")
        print(f"  X列φ値: {phi:.6f}")
        
        if abs(phi) > 0.001:  # 0でない場合
            # φとθの関係を調べる
            diff = abs(phi - theta_calc)
            print(f"  差異: {diff:.6f}")
            
            # カント角度との関係を調べる
            if abs(phi - cant_angle) < 0.1:
                print(f"  → カント角度に近い値")
    
    print()
    print("=== カント50mm時の1225mm地点の推定計算 ===")
    
    # 1225mm地点（建築限界最底辺）の場合
    x_1225 = 1225
    y_0 = 0
    
    # 極座標変換
    r_1225 = math.sqrt(x_1225**2 + y_0**2)
    print(f"1225mm地点の極座標: r={r_1225}, θ=0")
    
    # カント回転後の座標
    x_rotated = r_1225 * math.cos(cant_angle)
    y_rotated = r_1225 * math.sin(cant_angle)
    
    print(f"カント回転後: x={x_rotated:.4f}, y={y_rotated:.4f}")
    print(f"y成分（浮き上がり量）: {y_rotated:.4f} mm")
    
    # 実測値との比較
    expected = 31.5960
    error = abs(y_rotated - expected)
    print(f"OIRANエクセル実測値: {expected:.4f} mm")
    print(f"誤差: {error:.4f} mm ({error/expected*100:.2f}%)")
    
    if error < 1.0:
        print("✅ 単純な極座標回転で説明可能")
    else:
        print("❌ 追加の補正が必要")
    
    print()
    print("=== より詳細な角度分析 ===")
    
    # 3685, 350の点での角度解析
    x, y, phi = 3685, 350, 0.09469557520921408
    print(f"点(3685, 350)の角度分析:")
    print(f"  atan(y/x) = atan(350/3685) = {math.atan(350/3685):.6f}")
    print(f"  X列φ値: {phi:.6f}")
    print(f"  カント角度: {cant_angle:.6f}")
    
    # 角度の関係を調べる
    base_angle = math.atan(350/3685)
    print(f"  基本角度: {base_angle:.6f}")
    print(f"  φ - 基本角度: {phi - base_angle:.6f}")
    print(f"  φ / カント角度: {phi / cant_angle:.6f}")
    
    if abs(phi - cant_angle) < 0.001:
        print("  → φはカント角度そのもの")
    elif abs(phi - base_angle) < 0.001:
        print("  → φは基本角度そのもの")
    else:
        print("  → φは別の計算式による")
    
    print()
    print("=== 重要な発見 ===")
    
    # φがカント角度と一致するかチェック
    phi_350 = 0.09469557520921408
    ratio = phi_350 / cant_angle
    print(f"点(3685, 350)のφ値: {phi_350:.6f}")
    print(f"カント角度: {cant_angle:.6f}")
    print(f"比率: {ratio:.6f}")
    
    if abs(ratio - 1.0) < 0.02:
        print("✅ φ値はカント角度とほぼ一致！")
        print("推定される計算式:")
        print("1. 建築限界の各点で、高さに応じたカント角度を適用")
        print("2. 極座標回転: x' = r*cos(cant_angle), y' = r*sin(cant_angle)")
        print("3. この結果が実測値31.5960mmと一致する")
    
    print()
    print("=== 最終検証 ===")
    
    # 1225mm地点での最終検証
    final_lift = 1225 * math.sin(cant_angle)
    print(f"最終浮き上がり量計算: 1225 * sin({cant_angle:.6f}) = {final_lift:.4f} mm")
    print(f"OIRANエクセル実測値: 31.5960 mm")
    print(f"最終誤差: {abs(final_lift - 31.5960):.4f} mm")
    
    if abs(final_lift - 31.5960) < 0.1:
        print("🎉 OIRANエクセルの実際の計算式を発見！")
        print("計算式: 浮き上がり量 = X距離 * sin(カント角度)")
        print("この単純な式がOIRANエクセルの実際の計算方式")
    else:
        print("⚠️  さらなる解析が必要")

if __name__ == "__main__":
    main()