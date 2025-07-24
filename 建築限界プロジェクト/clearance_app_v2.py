#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
建築限界シミュレーター v2.0
改良版 - Excel解析結果を反映、GUI機能追加
"""

import tkinter as tk
from tkinter import ttk, messagebox
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
from matplotlib.figure import Figure
import numpy as np
import platform
import tkinter.font as tkFont
import json
from typing import List, Tuple, Dict, Any

class ClearanceModelV2:
    """建築限界モデル v2 - Excel解析反映版"""
    
    def __init__(self):
        self.rail_gauge = 1067  # 軌間 (mm)
        
    def create_excel_based_clearance(self) -> List[Tuple[float, float]]:
        """Excel解析結果に基づく建築限界形状"""
        # OIRANシミュレーター解析結果を反映
        points = [
            # 右側（下から上）
            (1225, 0), (1625, 200), (1625, 1000),
            (1000, 2600), (1350, 3200), (1350, 4650),
            # 上部
            (-1350, 4650),
            # 左側（上から下）
            (-1350, 3200), (-1000, 2600), (-1625, 1000),
            (-1625, 200), (-1225, 0), (1225, 0)
        ]
        return points
    
    def validate_point_in_clearance(self, x: float, y: float, 
                                   clearance_points: List[Tuple[float, float]]) -> bool:
        """点が建築限界内にあるかチェック"""
        if not clearance_points or y < 0:
            return False
        
        clearance_width = self._get_clearance_width_at_height(y, clearance_points)
        return clearance_width is not None and abs(x) <= clearance_width
    
    def _get_clearance_width_at_height(self, height: float, 
                                      points: List[Tuple[float, float]]) -> float:
        """指定高さでの建築限界幅取得"""
        right_points = [(x, y) for x, y in points if x > 0]
        right_points.sort(key=lambda p: p[1])
        
        for i in range(len(right_points) - 1):
            y1, x1 = right_points[i][1], right_points[i][0]
            y2, x2 = right_points[i + 1][1], right_points[i + 1][0]
            
            if y1 <= height <= y2:
                if y2 == y1:
                    return x1
                ratio = (height - y1) / (y2 - y1)
                return x1 + ratio * (x2 - x1)
        
        return None
    
    def transform_clearance(self, points: List[Tuple[float, float]],
                           cant_mm: float, curve_radius_m: float) -> List[Tuple[float, float]]:
        """カント・曲線半径による建築限界変形"""
        if not points:
            return []
        
        coords = np.array(points)
        
        # カント変形（Excel解析の三角関数を反映）
        if cant_mm != 0:
            angle_rad = np.arctan(cant_mm / self.rail_gauge)
            cos_a, sin_a = np.cos(angle_rad), np.sin(angle_rad)
            rotation_matrix = np.array([[cos_a, -sin_a], [sin_a, cos_a]])
            coords = coords @ rotation_matrix.T
        
        # 曲線拡幅
        if curve_radius_m > 0 and curve_radius_m < 3000:
            widening_factor = min(100, 1500.0 / curve_radius_m)
            coords[:, 0] = coords[:, 0] + np.sign(coords[:, 0]) * widening_factor
        
        return coords.tolist()

class ClearanceAppV2:
    """建築限界アプリ v2 - GUI機能付き"""
    
    def __init__(self):
        self.root = tk.Tk()
        self.root.title("建築限界シミュレーター v2.0")
        self.root.geometry("1200x800")
        
        self.setup_japanese_font()
        self.clearance_model = ClearanceModelV2()
        self.base_clearance = self.clearance_model.create_excel_based_clearance()
        
        # UI変数
        self.cant_var = tk.DoubleVar(value=0.0)
        self.radius_var = tk.DoubleVar(value=0.0)
        self.equipment_distance_var = tk.DoubleVar(value=0.0)
        self.equipment_height_var = tk.DoubleVar(value=1000.0)
        self.equipment_name_var = tk.StringVar(value="測定設備")
        
        self.create_ui()
        self.update_display()
    
    def setup_japanese_font(self):
        """日本語フォント設定"""
        system = platform.system()
        
        if system == "Windows":
            self.default_font = ("Meiryo UI", 9)
            self.title_font = ("Meiryo UI", 12, "bold")
        elif system == "Darwin":
            self.default_font = ("Hiragino Sans", 12)
            self.title_font = ("Hiragino Sans", 14, "bold")
        else:
            japanese_fonts = ["Noto Sans CJK JP", "Takao Gothic", "IPAexGothic"]
            self.default_font = ("DejaVu Sans", 10)
            self.title_font = ("DejaVu Sans", 12, "bold")
            
            for font_name in japanese_fonts:
                try:
                    tkFont.Font(family=font_name, size=10)
                    self.default_font = (font_name, 10)
                    self.title_font = (font_name, 12, "bold")
                    break
                except:
                    continue
        
        try:
            plt.rcParams['font.family'] = self.default_font[0]
            plt.rcParams['axes.unicode_minus'] = False
        except:
            plt.rcParams['font.family'] = 'DejaVu Sans'
    
    def create_ui(self):
        """UI作成"""
        main_frame = ttk.Frame(self.root)
        main_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        # 左パネル（コントロール）
        control_frame = ttk.Frame(main_frame)
        control_frame.pack(side=tk.LEFT, fill=tk.Y, padx=(0, 10))
        
        # タイトル
        title_label = tk.Label(control_frame, text="建築限界シミュレーター v2", 
                              font=self.title_font, fg="navy")
        title_label.pack(pady=(0, 20))
        
        self.create_equipment_section(control_frame)
        self.create_cant_section(control_frame)
        self.create_curve_section(control_frame)
        self.create_result_section(control_frame)
        self.create_button_section(control_frame)
        
        # 右パネル（グラフ）
        self.create_graph_panel(main_frame)
    
    def create_equipment_section(self, parent):
        """設備位置設定セクション"""
        equipment_group = ttk.LabelFrame(parent, text="設備位置測定", padding=10)
        equipment_group.pack(fill=tk.X, pady=10)
        
        ttk.Label(equipment_group, text="設備名:", font=self.default_font).pack(anchor=tk.W)
        ttk.Entry(equipment_group, textvariable=self.equipment_name_var, 
                 width=20).pack(fill=tk.X, pady=5)
        
        ttk.Label(equipment_group, text="レール中心からの距離 (mm):", 
                 font=self.default_font).pack(anchor=tk.W, pady=(10,0))
        ttk.Spinbox(equipment_group, from_=-3000, to=3000, increment=10,
                   textvariable=self.equipment_distance_var, width=20,
                   command=self.update_display).pack(fill=tk.X, pady=5)
        
        ttk.Label(equipment_group, text="レールレベルからの高さ (mm):", 
                 font=self.default_font).pack(anchor=tk.W, pady=(10,0))
        ttk.Spinbox(equipment_group, from_=0, to=5000, increment=50,
                   textvariable=self.equipment_height_var, width=20,
                   command=self.update_display).pack(fill=tk.X, pady=5)
    
    def create_cant_section(self, parent):
        """カント設定セクション"""
        cant_group = ttk.LabelFrame(parent, text="カント設定", padding=10)
        cant_group.pack(fill=tk.X, pady=10)
        
        ttk.Label(cant_group, text="カント値 (mm):", font=self.default_font).pack(anchor=tk.W)
        ttk.Spinbox(cant_group, from_=-200, to=200, increment=5,
                   textvariable=self.cant_var, width=20,
                   command=self.update_display).pack(fill=tk.X, pady=5)
    
    def create_curve_section(self, parent):
        """曲線半径設定セクション"""
        curve_group = ttk.LabelFrame(parent, text="曲線半径設定", padding=10)
        curve_group.pack(fill=tk.X, pady=10)
        
        ttk.Label(curve_group, text="曲線半径 (m):", font=self.default_font).pack(anchor=tk.W)
        ttk.Spinbox(curve_group, from_=0, to=2000, increment=50,
                   textvariable=self.radius_var, width=20,
                   command=self.update_display).pack(fill=tk.X, pady=5)
    
    def create_result_section(self, parent):
        """判定結果セクション"""
        result_group = ttk.LabelFrame(parent, text="判定結果", padding=10)
        result_group.pack(fill=tk.X, pady=10)
        
        self.rank_label = tk.Label(result_group, text="ランク: E", 
                                  font=self.title_font, fg="green")
        self.rank_label.pack()
        
        self.status_label = tk.Label(result_group, text="状態: 正常", 
                                    font=self.default_font, fg="blue")
        self.status_label.pack(pady=5)
    
    def create_button_section(self, parent):
        """ボタンセクション"""
        button_frame = ttk.Frame(parent)
        button_frame.pack(fill=tk.X, pady=20)
        
        ttk.Button(button_frame, text="表示更新", 
                  command=self.update_display).pack(fill=tk.X, pady=2)
        
        ttk.Button(button_frame, text="リセット", 
                  command=self.reset_values).pack(fill=tk.X, pady=2)
    
    def create_graph_panel(self, parent):
        """グラフパネル作成"""
        graph_frame = ttk.LabelFrame(parent, text="建築限界表示", padding=10)
        graph_frame.pack(side=tk.RIGHT, fill=tk.BOTH, expand=True)
        
        self.fig = Figure(figsize=(10, 8), dpi=100)
        self.ax = self.fig.add_subplot(111)
        
        self.ax.set_xlabel('レール中心からの距離 (mm)', fontsize=12)
        self.ax.set_ylabel('レールレベルからの高さ (mm)', fontsize=12)
        self.ax.set_title('建築限界断面図 v2', fontsize=14, pad=20)
        self.ax.grid(True, alpha=0.3)
        self.ax.set_aspect('equal')
        
        self.canvas = FigureCanvasTkAgg(self.fig, graph_frame)
        self.canvas.get_tk_widget().pack(fill=tk.BOTH, expand=True)
    
    def reset_values(self):
        """値リセット"""
        self.cant_var.set(0.0)
        self.radius_var.set(0.0)
        self.equipment_distance_var.set(0.0)
        self.equipment_height_var.set(1000.0)
        self.equipment_name_var.set("測定設備")
        self.update_display()
    
    def update_display(self):
        """表示更新"""
        cant_value = self.cant_var.get()
        curve_radius = self.radius_var.get()
        equipment_x = self.equipment_distance_var.get()
        equipment_y = self.equipment_height_var.get()
        equipment_name = self.equipment_name_var.get()
        
        # 建築限界変形
        transformed_clearance = self.clearance_model.transform_clearance(
            self.base_clearance, cant_value, curve_radius
        )
        
        # 設備判定
        equipment_safe = self.clearance_model.validate_point_in_clearance(
            equipment_x, equipment_y, transformed_clearance
        )
        
        # ランク判定
        rank, status, color = self.determine_rank(cant_value, curve_radius)
        
        # グラフ更新
        self.update_graph(transformed_clearance, cant_value, curve_radius,
                         equipment_x, equipment_y, equipment_name, equipment_safe)
        
        # UI更新
        self.rank_label.config(text=f"ランク: {rank}", fg=color)
        equipment_status = "✅ 限界内" if equipment_safe else "❌ 支障"
        equipment_color = "green" if equipment_safe else "red"
        self.status_label.config(text=f"設備状態: {equipment_status}", fg=equipment_color)
    
    def determine_rank(self, cant_value: float, curve_radius: float) -> tuple:
        """ランク判定"""
        abs_cant = abs(cant_value)
        
        if abs_cant > 150:
            return "A", "支障あり", "red"
        elif abs_cant > 100:
            return "B", "支障あり", "red"
        elif abs_cant > 50:
            return "D", "注意", "orange"
        elif abs_cant > 0:
            return "E", "正常", "green"
        else:
            return "E", "正常", "green"
    
    def update_graph(self, clearance_coords, cant_value, curve_radius,
                    equipment_x, equipment_y, equipment_name, equipment_safe):
        """グラフ更新"""
        self.ax.clear()
        
        if clearance_coords:
            coords = np.array(clearance_coords)
            x_coords, y_coords = coords[:, 0], coords[:, 1]
            
            color = 'blue' if equipment_safe else 'red'
            self.ax.plot(x_coords, y_coords, color=color, linewidth=3, label='建築限界')
            self.ax.fill(x_coords, y_coords, color=color, alpha=0.3)
            
            # レール表示
            self.ax.axhline(y=0, color='black', linewidth=4, alpha=0.8, label='レール面')
            self.ax.axvline(x=0, color='gray', linewidth=2, linestyle=':', alpha=0.6)
            
            # 設備位置表示
            equipment_color = 'green' if equipment_safe else 'red'
            marker = 'o' if equipment_safe else 'X'
            self.ax.scatter([equipment_x], [equipment_y], 
                           color=equipment_color, s=200, marker=marker,
                           edgecolors='black', linewidth=2, zorder=10,
                           label=equipment_name)
            
            # 情報表示
            if cant_value != 0 or curve_radius > 0:
                info_text = f'カント: {cant_value}mm\\n曲線半径: {curve_radius}m'
                self.ax.text(0.02, 0.98, info_text, transform=self.ax.transAxes,
                            fontsize=11, verticalalignment='top',
                            bbox=dict(boxstyle='round', facecolor='lightyellow', alpha=0.9))
        
        self.ax.set_xlabel('レール中心からの距離 (mm)', fontsize=12)
        self.ax.set_ylabel('レールレベルからの高さ (mm)', fontsize=12)
        
        title_color = 'red' if not equipment_safe else 'green'
        status_text = '【支障】' if not equipment_safe else '【正常】'
        self.ax.set_title(f'建築限界断面図 v2 {status_text}', 
                         fontsize=14, pad=20, color=title_color)
        
        self.ax.grid(True, alpha=0.3)
        self.ax.legend(loc='upper right')
        self.ax.set_aspect('equal')
        
        margin = 800
        if clearance_coords:
            coords = np.array(clearance_coords)
            x_min = min(min(coords[:, 0]), equipment_x) - margin
            x_max = max(max(coords[:, 0]), equipment_x) + margin
            y_min = -200
            y_max = max(max(coords[:, 1]), equipment_y) + margin
            
            self.ax.set_xlim(x_min, x_max)
            self.ax.set_ylim(y_min, y_max)
        
        self.canvas.draw()
    
    def run(self):
        """アプリケーション実行"""
        print("🚀 建築限界シミュレーター v2.0 を起動...")
        try:
            self.root.mainloop()
        except Exception as e:
            print(f"❌ エラー: {e}")

def main_v2():
    """v2 メイン実行"""
    try:
        app = ClearanceAppV2()
        app.run()
    except Exception as e:
        print(f"❌ 初期化エラー: {e}")

if __name__ == "__main__":
    main_v2()