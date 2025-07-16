#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
建築限界測定アプリ - PC版GUI 修正版
正確な建築限界表示と計算
"""

import tkinter as tk
from tkinter import ttk, messagebox
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
from matplotlib.figure import Figure
import matplotlib.patches as patches
import numpy as np
from building_limit_calculator_fixed import BuildingLimitCalculatorFixed

# 日本語フォント設定
plt.rcParams['font.family'] = ['DejaVu Sans', 'SimHei', 'Noto Sans CJK JP']

class BuildingLimitGUIFixed:
    """建築限界測定GUI - 修正版"""
    
    def __init__(self, root):
        self.root = root
        self.root.title("建築限界測定システム - 修正版")
        self.root.geometry("1400x900")
        
        # 計算器の初期化
        self.calculator = BuildingLimitCalculatorFixed("直流")
        
        self.setup_ui()
        self.update_display()
    
    def setup_ui(self):
        """UI設定"""
        # メインフレーム
        main_frame = ttk.Frame(self.root, padding="10")
        main_frame.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        
        # 左側：入力フォーム
        input_frame = ttk.LabelFrame(main_frame, text="入力パラメータ", padding="10")
        input_frame.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S), padx=(0, 10))
        
        # 曲線半径入力
        ttk.Label(input_frame, text="曲線半径 (m):").grid(row=0, column=0, sticky=tk.W, pady=5)
        self.radius_var = tk.StringVar(value="160")
        ttk.Entry(input_frame, textvariable=self.radius_var, width=15).grid(row=0, column=1, sticky=tk.W, pady=5)
        
        # カント入力
        ttk.Label(input_frame, text="カント (mm):").grid(row=1, column=0, sticky=tk.W, pady=5)
        self.cant_var = tk.StringVar(value="105")
        ttk.Entry(input_frame, textvariable=self.cant_var, width=15).grid(row=1, column=1, sticky=tk.W, pady=5)
        
        # 測定離れ入力
        ttk.Label(input_frame, text="測定離れ (mm):").grid(row=2, column=0, sticky=tk.W, pady=5)
        self.distance_var = tk.StringVar(value="2110")
        ttk.Entry(input_frame, textvariable=self.distance_var, width=15).grid(row=2, column=1, sticky=tk.W, pady=5)
        
        # 測定高さ入力
        ttk.Label(input_frame, text="測定高さ (mm):").grid(row=3, column=0, sticky=tk.W, pady=5)
        self.height_var = tk.StringVar(value="3150")
        ttk.Entry(input_frame, textvariable=self.height_var, width=15).grid(row=3, column=1, sticky=tk.W, pady=5)
        
        # 電化方式選択
        ttk.Label(input_frame, text="電化方式:").grid(row=4, column=0, sticky=tk.W, pady=5)
        self.electrification_var = tk.StringVar(value="直流")
        electrification_combo = ttk.Combobox(input_frame, textvariable=self.electrification_var, 
                                           values=["直流", "交流", "非電化"], state="readonly", width=12)
        electrification_combo.grid(row=4, column=1, sticky=tk.W, pady=5)
        
        # 計算ボタン
        ttk.Button(input_frame, text="計算実行", command=self.calculate).grid(row=5, column=0, columnspan=2, pady=20)
        
        # 結果表示エリア
        result_frame = ttk.LabelFrame(input_frame, text="判定結果", padding="10")
        result_frame.grid(row=6, column=0, columnspan=2, sticky=(tk.W, tk.E), pady=10)
        
        self.result_text = tk.Text(result_frame, height=12, width=45, font=("Consolas", 9))
        self.result_text.grid(row=0, column=0, sticky=(tk.W, tk.E))
        
        # スクロールバー
        scrollbar = ttk.Scrollbar(result_frame, orient="vertical", command=self.result_text.yview)
        scrollbar.grid(row=0, column=1, sticky=(tk.N, tk.S))
        self.result_text.configure(yscrollcommand=scrollbar.set)
        
        # 右側：グラフ表示
        graph_frame = ttk.LabelFrame(main_frame, text="建築限界表示", padding="10")
        graph_frame.grid(row=0, column=1, sticky=(tk.W, tk.E, tk.N, tk.S))
        
        # Matplotlib図の作成
        self.fig = Figure(figsize=(10, 8), dpi=100)
        self.ax = self.fig.add_subplot(111)
        
        self.canvas = FigureCanvasTkAgg(self.fig, master=graph_frame)
        self.canvas.get_tk_widget().grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        
        # グリッド設定
        self.root.columnconfigure(0, weight=1)
        self.root.rowconfigure(0, weight=1)
        main_frame.columnconfigure(1, weight=1)
        main_frame.rowconfigure(0, weight=1)
        graph_frame.columnconfigure(0, weight=1)
        graph_frame.rowconfigure(0, weight=1)
        
        # イベントバインド
        for var in [self.radius_var, self.cant_var, self.distance_var, self.height_var]:
            var.trace('w', lambda *args: self.update_display())
        self.electrification_var.trace('w', lambda *args: self.change_electrification())
    
    def change_electrification(self):
        """電化方式変更"""
        try:
            self.calculator = BuildingLimitCalculatorFixed(self.electrification_var.get())
            self.update_display()
        except Exception as e:
            messagebox.showerror("エラー", f"電化方式変更エラー: {e}")
    
    def calculate(self):
        """計算実行"""
        try:
            radius = float(self.radius_var.get())
            cant = float(self.cant_var.get())
            distance = float(self.distance_var.get())
            height = float(self.height_var.get())
            
            result = self.calculator.check_clearance(distance, height, radius, cant)
            
            # 結果表示
            result_text = f"""=== 判定結果 ===
状態: {result['status']}
測定高さでの必要離れ: {result['required_clearance']:.1f}mm
限界余裕値: {result['clearance_margin']:.1f}mm
最小距離: {result['min_distance']:.1f}mm

=== 入力パラメータ ===
曲線半径: {radius}m
カント: {cant}mm
測定離れ: {distance}mm  
測定高さ: {height}mm
電化方式: {self.electrification_var.get()}

=== 計算結果 ===
拡大幅: {result['expansion_width']:.1f}mm
カント角度: {np.degrees(result['cant_angle']):.2f}°
スラック: {result['slack']}mm

=== 座標情報 ===
測定ポイント: ({distance}, {height})
最近接点: ({result['nearest_point'][0]:.1f}, {result['nearest_point'][1]:.1f})
基準建築限界座標数: {len(result['basic_coordinates'])}
変形後建築限界座標数: {len(result['transformed_coordinates'])}

=== OIRANシュミレーター対応項目 ===
・曲線半径とカント: B11, D11セル対応
・測定離れと測定高さ: B14, D14セル対応  
・測定高さでの必要離れ: D18セル対応
・限界余裕値: 新規計算項目
"""
            
            self.result_text.delete(1.0, tk.END)
            self.result_text.insert(1.0, result_text)
            
            # 判定結果に応じて色分け
            if result['status'] == "支障":
                self.result_text.tag_add("warning", "2.4", "2.6")
                self.result_text.tag_config("warning", foreground="red", font=("Consolas", 10, "bold"))
            else:
                self.result_text.tag_add("safe", "2.4", "2.6")
                self.result_text.tag_config("safe", foreground="green", font=("Consolas", 10, "bold"))
            
            self.update_display()
            
        except ValueError as e:
            messagebox.showerror("入力エラー", "数値を正しく入力してください")
        except Exception as e:
            messagebox.showerror("計算エラー", f"計算中にエラーが発生しました: {e}")
    
    def update_display(self):
        """表示更新"""
        try:
            radius = float(self.radius_var.get()) if self.radius_var.get() else 160
            cant = float(self.cant_var.get()) if self.cant_var.get() else 105
            distance = float(self.distance_var.get()) if self.distance_var.get() else 2110
            height = float(self.height_var.get()) if self.height_var.get() else 3150
            
            # 表示データ取得
            display_data = self.calculator.get_display_data(radius, cant)
            basic_coords = display_data['basic_coordinates']
            transformed_coords = display_data['transformed_coordinates']
            
            # グラフクリア
            self.ax.clear()
            
            # 建築限界描画
            if basic_coords and transformed_coords:
                # 基準建築限界（実線）
                basic_x = [x for x, y in basic_coords]
                basic_y = [y for x, y in basic_coords]
                self.ax.plot(basic_x, basic_y, 'b-', linewidth=2, label='基準建築限界（実線）')
                self.ax.fill(basic_x, basic_y, alpha=0.1, color='blue')
                
                # 変形後建築限界（点線）
                trans_x = [x for x, y in transformed_coords]
                trans_y = [y for x, y in transformed_coords]
                self.ax.plot(trans_x, trans_y, 'r--', linewidth=2, label='変形後建築限界（点線）')
                self.ax.fill(trans_x, trans_y, alpha=0.1, color='red')
                
                # 軌道中心線
                y_min, y_max = self.ax.get_ylim()
                self.ax.axvline(x=0, color='black', linestyle='-', alpha=0.7, linewidth=1, label='軌道中心線')
                
                # レール位置
                self.ax.axhline(y=0, color='brown', linewidth=4, alpha=0.8, label='レール面')
                
                # 測定ポイント（×印）
                self.ax.plot(distance, height, 'kx', markersize=15, markeredgewidth=4, label='測定点')
                
                # 測定高さでの水平線
                self.ax.axhline(y=height, color='gray', linestyle=':', alpha=0.5, label=f'測定高さ({height}mm)')
                
                # 情報テキスト
                info_text = f"""パラメータ:
R={radius}m, C={cant}mm
拡大幅: {display_data['expansion_width']:.1f}mm
カント角度: {display_data['cant_angle_deg']:.2f}°
スラック: {display_data['slack']}mm
電化方式: {display_data['electrification_type']}"""
                
                self.ax.text(0.02, 0.98, info_text, transform=self.ax.transAxes, 
                           verticalalignment='top', fontsize=9,
                           bbox=dict(boxstyle='round', facecolor='wheat', alpha=0.9))
                
                # グリッド設定
                self.ax.grid(True, alpha=0.3)
                self.ax.set_xlabel('軌道中心からの距離 (mm)', fontsize=10)
                self.ax.set_ylabel('レール踏面からの高さ (mm)', fontsize=10)
                self.ax.set_title(f'建築限界図 - {self.electrification_var.get()} (R{radius}m C{cant}mm)', fontsize=12)
                self.ax.legend(fontsize=9)
                
                # 縦横比調整
                self.ax.set_aspect('equal', adjustable='box')
                
                # 表示範囲設定
                margin = 500
                all_x = basic_x + trans_x + [distance]
                all_y = basic_y + trans_y + [height]
                
                x_min, x_max = min(all_x) - margin, max(all_x) + margin
                y_min, y_max = min(all_y) - margin, max(all_y) + margin
                
                # 下部を-200mmから表示
                y_min = max(y_min, -200)
                
                self.ax.set_xlim(x_min, x_max)
                self.ax.set_ylim(y_min, y_max)
            
            self.canvas.draw()
            
        except ValueError:
            pass  # 入力中の無効な値は無視
        except Exception as e:
            print(f"表示更新エラー: {e}")

def main():
    """メイン関数"""
    root = tk.Tk()
    app = BuildingLimitGUIFixed(root)
    root.mainloop()

if __name__ == "__main__":
    main()