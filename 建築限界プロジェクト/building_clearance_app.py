#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
建築限界シミュレーター - 完全版
カント・曲線半径に応じた建築限界モデルの視覚的表示アプリケーション
"""

import tkinter as tk
from tkinter import ttk, messagebox
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
from matplotlib.figure import Figure
import numpy as np
import json
import platform
import tkinter.font as tkFont
from typing import List, Tuple, Dict, Any

class BuildingClearanceApp:
    def __init__(self):
        """アプリケーションの初期化"""
        self.root = tk.Tk()
        self.root.title("建築限界シミュレーター - OIRAN対応版")
        self.root.geometry("1400x900")
        
        # 日本語フォント設定
        self.setup_japanese_font()
        
        # データの初期化
        self.base_coordinates = []
        self.current_coordinates = []
        
        # UI変数の初期化
        self.cant_var = tk.DoubleVar(value=0.0)
        self.radius_var = tk.DoubleVar(value=0.0)
        
        # データ読み込み
        self.load_data()
        
        # UI構築
        self.create_ui()
        
        # 初期表示
        self.update_display()
    
    def setup_japanese_font(self):
        """日本語フォント設定"""
        system = platform.system()
        
        if system == "Windows":
            self.font_family = "Meiryo UI"
            self.default_font = ("Meiryo UI", 9)
            self.title_font = ("Meiryo UI", 12, "bold")
        elif system == "Darwin":  # macOS
            self.font_family = "Hiragino Sans"
            self.default_font = ("Hiragino Sans", 12)
            self.title_font = ("Hiragino Sans", 14, "bold")
        else:  # Linux/WSL
            # 利用可能な日本語フォントを試行
            japanese_fonts = ["Noto Sans CJK JP", "Takao Gothic", "IPAexGothic"]
            self.font_family = "DejaVu Sans"  # デフォルト
            
            for font_name in japanese_fonts:
                try:
                    test_font = tkFont.Font(family=font_name, size=10)
                    self.font_family = font_name
                    break
                except:
                    continue
            
            self.default_font = (self.font_family, 10)
            self.title_font = (self.font_family, 12, "bold")
        
        # matplotlib日本語フォント設定
        try:
            plt.rcParams['font.family'] = self.font_family
            plt.rcParams['axes.unicode_minus'] = False
        except:
            plt.rcParams['font.family'] = 'DejaVu Sans'
        
        print(f"✅ フォント設定完了: {self.font_family}")
    
    def load_data(self):
        """建築限界データの読み込み"""
        try:
            with open("building_clearance_data.json", 'r', encoding='utf-8') as f:
                data = json.load(f)
            self.base_coordinates = data.get("base_shape", [])
            print(f"✅ データ読み込み完了: {len(self.base_coordinates)}点")
        except FileNotFoundError:
            print("⚠️ データファイル未検出。サンプルデータを生成します。")
            self.base_coordinates = self.generate_sample_data()
        except Exception as e:
            print(f"❌ データ読み込みエラー: {e}")
            self.base_coordinates = self.generate_sample_data()
    
    def generate_sample_data(self) -> List[Tuple[float, float]]:
        """サンプル建築限界データ生成"""
        points = []
        
        # 標準的な建築限界形状
        # 下部（レール面付近）
        points.extend([(-1372, 0), (-1372, 200), (-1067, 400)])
        
        # 左側面
        for y in range(400, 3200, 200):
            points.append((-1067, y))
        
        # 上部
        points.extend([(-1067, 3200), (-500, 3800), (0, 4000), (500, 3800), (1067, 3200)])
        
        # 右側面
        for y in range(3200, 400, -200):
            points.append((1067, y))
        
        # 下部右側
        points.extend([(1067, 400), (1372, 200), (1372, 0)])
        
        return points
    
    def create_ui(self):
        """UI作成"""
        # メインフレーム
        main_frame = ttk.Frame(self.root)
        main_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        # 左パネル（コントロール）
        self.create_control_panel(main_frame)
        
        # 右パネル（グラフ）
        self.create_graph_panel(main_frame)
    
    def create_control_panel(self, parent):
        """コントロールパネル作成"""
        control_frame = ttk.LabelFrame(parent, text="設定パネル", padding=20)
        control_frame.pack(side=tk.LEFT, fill=tk.Y, padx=(0, 10))
        
        # タイトル
        title_label = tk.Label(control_frame, text="建築限界シミュレーター", 
                              font=self.title_font, fg="navy")
        title_label.pack(pady=(0, 20))
        
        # カント設定
        cant_group = ttk.LabelFrame(control_frame, text="カント設定", padding=10)
        cant_group.pack(fill=tk.X, pady=10)
        
        ttk.Label(cant_group, text="カント値 (mm):", font=self.default_font).pack(anchor=tk.W)
        cant_spin = ttk.Spinbox(cant_group, from_=-200, to=200, increment=5,
                               textvariable=self.cant_var, width=15,
                               command=self.on_value_change)
        cant_spin.pack(fill=tk.X, pady=5)
        
        # カントプリセット
        cant_preset_frame = ttk.Frame(cant_group)
        cant_preset_frame.pack(fill=tk.X, pady=5)
        
        cant_presets = [("0", 0), ("100", 100), ("140", 140), ("-80", -80)]
        for i, (text, value) in enumerate(cant_presets):
            btn = ttk.Button(cant_preset_frame, text=text, width=6,
                           command=lambda v=value: self.set_cant(v))
            btn.grid(row=0, column=i, padx=2)
        
        # 曲線半径設定
        radius_group = ttk.LabelFrame(control_frame, text="曲線半径設定", padding=10)
        radius_group.pack(fill=tk.X, pady=10)
        
        ttk.Label(radius_group, text="曲線半径 (m):", font=self.default_font).pack(anchor=tk.W)
        radius_spin = ttk.Spinbox(radius_group, from_=0, to=2000, increment=50,
                                 textvariable=self.radius_var, width=15,
                                 command=self.on_value_change)
        radius_spin.pack(fill=tk.X, pady=5)
        
        # 半径プリセット
        radius_preset_frame = ttk.Frame(radius_group)
        radius_preset_frame.pack(fill=tk.X, pady=5)
        
        radius_presets = [("0", 0), ("300", 300), ("600", 600), ("1200", 1200)]
        for i, (text, value) in enumerate(radius_presets):
            btn = ttk.Button(radius_preset_frame, text=text, width=6,
                           command=lambda v=value: self.set_radius(v))
            btn.grid(row=0, column=i, padx=2)
        
        # 判定結果
        result_group = ttk.LabelFrame(control_frame, text="判定結果", padding=10)
        result_group.pack(fill=tk.X, pady=10)
        
        self.rank_label = tk.Label(result_group, text="ランク: E", 
                                  font=self.title_font, fg="green")
        self.rank_label.pack()
        
        self.status_label = tk.Label(result_group, text="状態: 正常", 
                                    font=self.default_font, fg="blue")
        self.status_label.pack()
        
        # 統計情報
        stats_group = ttk.LabelFrame(control_frame, text="統計情報", padding=10)
        stats_group.pack(fill=tk.X, pady=10)
        
        self.stats_text = tk.Text(stats_group, height=6, width=25, 
                                 font=self.default_font, state=tk.DISABLED)
        self.stats_text.pack(fill=tk.BOTH)
        
        # ボタン
        button_frame = ttk.Frame(control_frame)
        button_frame.pack(fill=tk.X, pady=20)
        
        ttk.Button(button_frame, text="表示更新", 
                  command=self.update_display).pack(fill=tk.X, pady=2)
        
        ttk.Button(button_frame, text="リセット", 
                  command=self.reset_values).pack(fill=tk.X, pady=2)
    
    def create_graph_panel(self, parent):
        """グラフパネル作成"""
        graph_frame = ttk.LabelFrame(parent, text="建築限界表示", padding=10)
        graph_frame.pack(side=tk.RIGHT, fill=tk.BOTH, expand=True)
        
        # matplotlib図作成
        self.fig = Figure(figsize=(12, 10), dpi=100)
        self.ax = self.fig.add_subplot(111)
        
        # 基本設定
        self.ax.set_xlabel('水平距離 (mm)', fontsize=12)
        self.ax.set_ylabel('高さ (mm)', fontsize=12)
        self.ax.set_title('建築限界断面図（在来・一般・片線用）', fontsize=14, pad=20)
        self.ax.grid(True, alpha=0.3)
        self.ax.set_aspect('equal')
        
        # tkinterに埋め込み
        self.canvas = FigureCanvasTkAgg(self.fig, graph_frame)
        self.canvas.get_tk_widget().pack(fill=tk.BOTH, expand=True)
    
    def set_cant(self, value):
        """カント値設定"""
        self.cant_var.set(value)
        self.update_display()
    
    def set_radius(self, value):
        """曲線半径設定"""
        self.radius_var.set(value)
        self.update_display()
    
    def reset_values(self):
        """値リセット"""
        self.cant_var.set(0.0)
        self.radius_var.set(0.0)
        self.update_display()
    
    def on_value_change(self):
        """値変更イベント"""
        if hasattr(self, 'update_timer'):
            self.root.after_cancel(self.update_timer)
        self.update_timer = self.root.after(500, self.update_display)
    
    def transform_coordinates(self, coordinates, cant_value, curve_radius):
        """座標変換"""
        if not coordinates:
            return []
        
        coords = np.array(coordinates)
        
        # カント変換
        if cant_value != 0:
            gauge = 1067  # 軌間(mm)
            angle_rad = np.arctan(cant_value / gauge)
            
            cos_a = np.cos(angle_rad)
            sin_a = np.sin(angle_rad)
            
            rotation_matrix = np.array([[cos_a, -sin_a], [sin_a, cos_a]])
            coords = coords @ rotation_matrix.T
        
        # 曲線拡幅
        if curve_radius > 0 and curve_radius < 2000:
            widening = max(0, 800.0 / curve_radius)
            coords[:, 0] = coords[:, 0] + np.sign(coords[:, 0]) * widening
        
        return coords.tolist()
    
    def determine_rank(self, cant_value, curve_radius):
        """ランク判定"""
        abs_cant = abs(cant_value)
        
        if abs_cant > 150:
            return "A", "支障", "red"
        elif abs_cant > 100:
            return "B", "支障", "red"
        elif abs_cant > 50:
            return "D", "注意", "orange"
        elif abs_cant > 0:
            return "E", "正常", "green"
        else:
            return "E", "正常", "green"
    
    def update_display(self):
        """表示更新"""
        cant_value = self.cant_var.get()
        curve_radius = self.radius_var.get()
        
        # 座標変換
        transformed_coords = self.transform_coordinates(
            self.base_coordinates, cant_value, curve_radius)
        
        # ランク判定
        rank, status, color = self.determine_rank(cant_value, curve_radius)
        
        # グラフ更新
        self.update_graph(transformed_coords, cant_value, curve_radius)
        
        # UI更新
        self.rank_label.config(text=f"ランク: {rank}", fg=color)
        self.status_label.config(text=f"状態: {status}", fg=color)
        
        # 統計情報更新
        self.update_stats(transformed_coords, cant_value, curve_radius, rank)
    
    def update_graph(self, coordinates, cant_value, curve_radius):
        """グラフ更新"""
        self.ax.clear()
        
        if not coordinates:
            self.ax.text(0, 0, 'データなし', ha='center', va='center', fontsize=16)
            self.canvas.draw()
            return
        
        coords = np.array(coordinates)
        x_coords = coords[:, 0]
        y_coords = coords[:, 1]
        
        # 建築限界描画
        self.ax.plot(x_coords, y_coords, 'b-', linewidth=3, label='建築限界')
        self.ax.fill(x_coords, y_coords, color='lightblue', alpha=0.4)
        
        # レール位置
        self.ax.axhline(y=0, color='black', linewidth=4, alpha=0.8, label='レール面')
        self.ax.axvline(x=-533.5, color='red', linewidth=2, linestyle='--', alpha=0.6)
        self.ax.axvline(x=533.5, color='red', linewidth=2, linestyle='--', alpha=0.6)
        
        # 情報表示
        if cant_value != 0:
            angle_deg = np.degrees(np.arctan(cant_value / 1067))
            info_text = f'カント: {cant_value}mm\\n傾斜角: {angle_deg:.2f}°'
            self.ax.text(0, -500, info_text, ha='center', va='top', fontsize=11,
                        bbox=dict(boxstyle='round', facecolor='wheat', alpha=0.9))
        
        if curve_radius > 0:
            self.ax.text(1000, 4200, f'曲線半径: {curve_radius}m', 
                        ha='left', va='top', fontsize=11,
                        bbox=dict(boxstyle='round', facecolor='lightgreen', alpha=0.9))
        
        # 軸設定
        self.ax.set_xlabel('水平距離 (mm)', fontsize=12)
        self.ax.set_ylabel('高さ (mm)', fontsize=12)
        self.ax.set_title(f'建築限界断面図 (カント: {cant_value}mm, 半径: {curve_radius}m)', 
                         fontsize=14, pad=20)
        self.ax.grid(True, alpha=0.3)
        self.ax.legend(loc='upper right')
        
        # 範囲設定
        if coordinates:
            margin = 600
            x_min, x_max = min(x_coords) - margin, max(x_coords) + margin
            y_min, y_max = min(y_coords) - margin, max(y_coords) + margin
            self.ax.set_xlim(x_min, x_max)
            self.ax.set_ylim(y_min, y_max)
        
        self.ax.set_aspect('equal')
        self.canvas.draw()
    
    def update_stats(self, coordinates, cant_value, curve_radius, rank):
        """統計情報更新"""
        self.stats_text.config(state=tk.NORMAL)
        self.stats_text.delete(1.0, tk.END)
        
        stats_info = f"""座標点数: {len(coordinates)}

入力値:
  カント: {cant_value} mm
  曲線半径: {curve_radius} m

判定:
  ランク: {rank}
  
傾斜角: {np.degrees(np.arctan(cant_value/1067)):.3f}°

建築限界プロジェクト
OIRANシミュレーター対応版"""
        
        self.stats_text.insert(1.0, stats_info)
        self.stats_text.config(state=tk.DISABLED)
    
    def run(self):
        """アプリケーション実行"""
        print("🚀 建築限界シミュレーターを起動...")
        try:
            self.root.mainloop()
        except KeyboardInterrupt:
            print("\\n👋 アプリケーション終了")
        except Exception as e:
            messagebox.showerror("エラー", f"実行エラー: {e}")

def main():
    """メイン関数"""
    print("🏗️ 建築限界シミュレーター初期化中...")
    
    try:
        app = BuildingClearanceApp()
        app.run()
    except Exception as e:
        print(f"❌ 初期化エラー: {e}")
        messagebox.showerror("初期化エラー", f"アプリケーション初期化失敗:\\n{e}")

if __name__ == "__main__":
    main()