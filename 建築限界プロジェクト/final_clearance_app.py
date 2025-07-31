#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
建築限界シミュレーター - 最終版
正確な寸法に基づく建築限界モデル + 設備位置測定機能
"""

import tkinter as tk
from tkinter import ttk, messagebox
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
from matplotlib.figure import Figure
import numpy as np
import platform
import tkinter.font as tkFont
from typing import List, Tuple, Dict, Any
from accurate_clearance_model import AccurateClearanceModel

class FinalClearanceApp:
    def __init__(self):
        """アプリケーション初期化"""
        self.root = tk.Tk()
        self.root.title("建築限界シミュレーター - 設備位置測定対応版")
        self.root.geometry("1600x1000")
        
        # 日本語フォント設定
        self.setup_japanese_font()
        
        # 建築限界モデル初期化
        self.clearance_model = AccurateClearanceModel()
        self.base_clearance = self.clearance_model.create_simplified_clearance_shape()
        
        # UI変数初期化
        self.cant_var = tk.DoubleVar(value=0.0)
        self.radius_var = tk.DoubleVar(value=0.0)
        
        # 設備位置測定値変数
        self.equipment_distance_var = tk.DoubleVar(value=0.0)  # レール中心からの距離(mm)
        self.equipment_height_var = tk.DoubleVar(value=1000.0)  # レールレベルからの高さ(mm)
        self.equipment_name_var = tk.StringVar(value="測定設備")
        
        # UI構築
        self.create_ui()
        
        # 初期表示更新
        self.update_display()
    
    def setup_japanese_font(self):
        """日本語フォント設定"""
        system = platform.system()
        
        if system == "Windows":
            self.font_family = "Meiryo UI"
            self.default_font = ("Meiryo UI", 9)
            self.title_font = ("Meiryo UI", 12, "bold")
        elif system == "Darwin":
            self.font_family = "Hiragino Sans"
            self.default_font = ("Hiragino Sans", 12)
            self.title_font = ("Hiragino Sans", 14, "bold")
        else:  # Linux/WSL
            japanese_fonts = ["Noto Sans CJK JP", "Takao Gothic", "IPAexGothic"]
            self.font_family = "DejaVu Sans"
            
            for font_name in japanese_fonts:
                try:
                    test_font = tkFont.Font(family=font_name, size=10)
                    self.font_family = font_name
                    break
                except:
                    continue
            
            self.default_font = (self.font_family, 10)
            self.title_font = (self.font_family, 12, "bold")
        
        # matplotlib設定
        try:
            plt.rcParams['font.family'] = self.font_family
            plt.rcParams['axes.unicode_minus'] = False
        except:
            plt.rcParams['font.family'] = 'DejaVu Sans'
        
        print(f"✅ フォント設定完了: {self.font_family}")
    
    def create_ui(self):
        """UI作成"""
        # メインフレーム
        main_frame = ttk.Frame(self.root)
        main_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        # 左パネル（設定）
        self.create_control_panel(main_frame)
        
        # 右パネル（グラフ）
        self.create_graph_panel(main_frame)
    
    def create_control_panel(self, parent):
        """コントロールパネル作成"""
        control_frame = ttk.Frame(parent)
        control_frame.pack(side=tk.LEFT, fill=tk.Y, padx=(0, 15))
        
        # タイトル
        title_label = tk.Label(control_frame, text="建築限界シミュレーター", 
                              font=self.title_font, fg="navy")
        title_label.pack(pady=(0, 20))
        
        # 設備位置測定セクション
        self.create_equipment_section(control_frame)
        
        # カント設定セクション
        self.create_cant_section(control_frame)
        
        # 曲線半径設定セクション
        self.create_curve_section(control_frame)
        
        # 判定結果セクション
        self.create_result_section(control_frame)
        
        # 統計情報セクション
        self.create_stats_section(control_frame)
        
        # 操作ボタンセクション
        self.create_button_section(control_frame)
    
    def create_equipment_section(self, parent):
        """設備位置測定セクション"""
        equipment_group = ttk.LabelFrame(parent, text="📍 設備位置測定", padding=15)
        equipment_group.pack(fill=tk.X, pady=10)
        
        # 設備名入力
        ttk.Label(equipment_group, text="設備名:", font=self.default_font).pack(anchor=tk.W)
        equipment_name_entry = ttk.Entry(equipment_group, textvariable=self.equipment_name_var, 
                                        font=self.default_font, width=20)
        equipment_name_entry.pack(fill=tk.X, pady=5)
        
        # レール中心からの距離入力
        ttk.Label(equipment_group, text="レール中心からの距離 (mm):", 
                 font=self.default_font).pack(anchor=tk.W, pady=(10,0))
        distance_frame = ttk.Frame(equipment_group)
        distance_frame.pack(fill=tk.X, pady=5)
        
        distance_spin = ttk.Spinbox(distance_frame, from_=-3000, to=3000, increment=10,
                                   textvariable=self.equipment_distance_var, width=15,
                                   command=self.on_equipment_change)
        distance_spin.pack(side=tk.LEFT)
        
        ttk.Label(distance_frame, text="（左側: 負値, 右側: 正値）", 
                 font=(self.font_family, 8), foreground="gray").pack(side=tk.LEFT, padx=(10,0))
        
        # レールレベルからの高さ入力
        ttk.Label(equipment_group, text="レールレベルからの高さ (mm):", 
                 font=self.default_font).pack(anchor=tk.W, pady=(10,0))
        height_frame = ttk.Frame(equipment_group)
        height_frame.pack(fill=tk.X, pady=5)
        
        height_spin = ttk.Spinbox(height_frame, from_=0, to=5000, increment=50,
                                 textvariable=self.equipment_height_var, width=15,
                                 command=self.on_equipment_change)
        height_spin.pack(side=tk.LEFT)
        
        ttk.Label(height_frame, text="（レール面=0mm）", 
                 font=(self.font_family, 8), foreground="gray").pack(side=tk.LEFT, padx=(10,0))
        
        # 測定値プリセット
        preset_frame = ttk.Frame(equipment_group)
        preset_frame.pack(fill=tk.X, pady=(10,0))
        
        ttk.Label(preset_frame, text="プリセット:", font=self.default_font).pack(anchor=tk.W)
        
        presets = [
            ("信号機", -2000, 3000),
            ("標識", -1800, 2000),
            ("架線柱", -3000, 4000),
            ("中央", 0, 2000)
        ]
        
        preset_buttons_frame = ttk.Frame(preset_frame)
        preset_buttons_frame.pack(fill=tk.X, pady=5)
        
        for i, (name, dist, height) in enumerate(presets):
            btn = ttk.Button(preset_buttons_frame, text=name, width=8,
                           command=lambda d=dist, h=height: self.set_equipment_position(d, h))
            btn.grid(row=i//2, column=i%2, padx=2, pady=2, sticky="ew")
        
        preset_buttons_frame.columnconfigure(0, weight=1)
        preset_buttons_frame.columnconfigure(1, weight=1)
    
    def create_cant_section(self, parent):
        """カント設定セクション"""
        cant_group = ttk.LabelFrame(parent, text="⚖️ カント設定", padding=15)
        cant_group.pack(fill=tk.X, pady=10)
        
        ttk.Label(cant_group, text="カント値 (mm):", font=self.default_font).pack(anchor=tk.W)
        cant_spin = ttk.Spinbox(cant_group, from_=-200, to=200, increment=5,
                               textvariable=self.cant_var, width=20,
                               command=self.on_parameter_change)
        cant_spin.pack(fill=tk.X, pady=5)
        
        # カントプリセット
        cant_preset_frame = ttk.Frame(cant_group)
        cant_preset_frame.pack(fill=tk.X, pady=5)
        
        cant_presets = [("0", 0), ("100", 100), ("140", 140), ("-80", -80)]
        for i, (text, value) in enumerate(cant_presets):
            btn = ttk.Button(cant_preset_frame, text=text, width=8,
                           command=lambda v=value: self.set_cant(v))
            btn.grid(row=0, column=i, padx=2, sticky="ew")
        
        for i in range(4):
            cant_preset_frame.columnconfigure(i, weight=1)
    
    def create_curve_section(self, parent):
        """曲線半径設定セクション"""
        curve_group = ttk.LabelFrame(parent, text="🔄 曲線半径設定", padding=15)
        curve_group.pack(fill=tk.X, pady=10)
        
        ttk.Label(curve_group, text="曲線半径 (m):", font=self.default_font).pack(anchor=tk.W)
        radius_spin = ttk.Spinbox(curve_group, from_=0, to=2000, increment=50,
                                 textvariable=self.radius_var, width=20,
                                 command=self.on_parameter_change)
        radius_spin.pack(fill=tk.X, pady=5)
        
        # 曲線半径プリセット
        radius_preset_frame = ttk.Frame(curve_group)
        radius_preset_frame.pack(fill=tk.X, pady=5)
        
        radius_presets = [("直線", 0), ("急曲線", 300), ("標準", 600), ("緩曲線", 1200)]
        for i, (text, value) in enumerate(radius_presets):
            btn = ttk.Button(radius_preset_frame, text=text, width=8,
                           command=lambda v=value: self.set_radius(v))
            btn.grid(row=0, column=i, padx=2, sticky="ew")
        
        for i in range(4):
            radius_preset_frame.columnconfigure(i, weight=1)
    
    def create_result_section(self, parent):
        """判定結果セクション"""
        result_group = ttk.LabelFrame(parent, text="📊 判定結果", padding=15)
        result_group.pack(fill=tk.X, pady=10)
        
        self.clearance_rank_label = tk.Label(result_group, text="建築限界ランク: E", 
                                           font=self.title_font, fg="green")
        self.clearance_rank_label.pack()
        
        self.equipment_status_label = tk.Label(result_group, text="設備状態: 限界内", 
                                             font=self.default_font, fg="blue")
        self.equipment_status_label.pack(pady=5)
        
        self.distance_info_label = tk.Label(result_group, text="余裕距離: ---", 
                                           font=self.default_font, fg="black")
        self.distance_info_label.pack()
    
    def create_stats_section(self, parent):
        """統計情報セクション"""
        stats_group = ttk.LabelFrame(parent, text="📈 詳細情報", padding=15)
        stats_group.pack(fill=tk.X, pady=10)
        
        self.stats_text = tk.Text(stats_group, height=8, width=30, 
                                 font=(self.font_family, 9), state=tk.DISABLED)
        self.stats_text.pack(fill=tk.BOTH, expand=True)
    
    def create_button_section(self, parent):
        """操作ボタンセクション"""
        button_frame = ttk.Frame(parent)
        button_frame.pack(fill=tk.X, pady=20)
        
        ttk.Button(button_frame, text="🔄 表示更新", 
                  command=self.update_display).pack(fill=tk.X, pady=3)
        
        ttk.Button(button_frame, text="🔄 リセット", 
                  command=self.reset_all_values).pack(fill=tk.X, pady=3)
        
        ttk.Button(button_frame, text="💾 設定保存", 
                  command=self.save_settings).pack(fill=tk.X, pady=3)
    
    def create_graph_panel(self, parent):
        """グラフパネル作成"""
        graph_frame = ttk.LabelFrame(parent, text="🏗️ 建築限界表示", padding=15)
        graph_frame.pack(side=tk.RIGHT, fill=tk.BOTH, expand=True)
        
        # matplotlib図作成
        self.fig = Figure(figsize=(14, 12), dpi=100)
        self.ax = self.fig.add_subplot(111)
        
        # 基本設定
        self.ax.set_xlabel('レール中心からの距離 (mm)', fontsize=14)
        self.ax.set_ylabel('レールレベルからの高さ (mm)', fontsize=14)
        self.ax.set_title('建築限界断面図（在来・一般・片線用）', fontsize=16, pad=20)
        self.ax.grid(True, alpha=0.3)
        self.ax.set_aspect('equal')
        
        # tkinterに埋め込み
        self.canvas = FigureCanvasTkAgg(self.fig, graph_frame)
        self.canvas.get_tk_widget().pack(fill=tk.BOTH, expand=True)
    
    def set_equipment_position(self, distance: float, height: float):
        """設備位置プリセット設定"""
        self.equipment_distance_var.set(distance)
        self.equipment_height_var.set(height)
        self.update_display()
    
    def set_cant(self, value: float):
        """カント値設定"""
        self.cant_var.set(value)
        self.update_display()
    
    def set_radius(self, value: float):
        """曲線半径設定"""
        self.radius_var.set(value)
        self.update_display()
    
    def reset_all_values(self):
        """全値リセット"""
        self.cant_var.set(0.0)
        self.radius_var.set(0.0)
        self.equipment_distance_var.set(0.0)
        self.equipment_height_var.set(1000.0)
        self.equipment_name_var.set("測定設備")
        self.update_display()
    
    def on_parameter_change(self):
        """パラメータ変更イベント"""
        if hasattr(self, 'update_timer'):
            self.root.after_cancel(self.update_timer)
        self.update_timer = self.root.after(300, self.update_display)
    
    def on_equipment_change(self):
        """設備位置変更イベント"""
        if hasattr(self, 'equipment_timer'):
            self.root.after_cancel(self.equipment_timer)
        self.equipment_timer = self.root.after(100, self.update_display)
    
    def update_display(self):
        """表示更新"""
        # 現在の値を取得
        cant_value = self.cant_var.get()
        curve_radius = self.radius_var.get()
        equipment_x = self.equipment_distance_var.get()
        equipment_y = self.equipment_height_var.get()
        equipment_name = self.equipment_name_var.get()
        
        # 建築限界を変形
        transformed_clearance = self.clearance_model.transform_clearance_for_cant_and_curve(
            self.base_clearance, cant_value, curve_radius
        )
        
        # 設備位置の支障判定
        equipment_in_clearance = self.clearance_model.validate_point_in_clearance(
            equipment_x, equipment_y, transformed_clearance
        )
        
        # 建築限界ランク判定
        clearance_rank, clearance_status, rank_color = self.determine_clearance_rank(cant_value, curve_radius)
        
        # グラフ更新
        self.update_graph(transformed_clearance, cant_value, curve_radius, 
                         equipment_x, equipment_y, equipment_name, equipment_in_clearance)
        
        # UI更新
        self.update_ui_status(clearance_rank, clearance_status, rank_color,
                             equipment_x, equipment_y, equipment_name, equipment_in_clearance,
                             cant_value, curve_radius)
    
    def determine_clearance_rank(self, cant_value: float, curve_radius: float) -> Tuple[str, str, str]:
        """建築限界ランク判定"""
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
    
    def update_graph(self, clearance_coords: List[Tuple[float, float]], 
                    cant_value: float, curve_radius: float,
                    equipment_x: float, equipment_y: float, equipment_name: str,
                    equipment_safe: bool):
        """グラフ更新"""
        self.ax.clear()
        
        if not clearance_coords:
            self.ax.text(0, 0, 'データなし', ha='center', va='center', fontsize=16)
            self.canvas.draw()
            return
        
        # 建築限界描画
        coords = np.array(clearance_coords)
        x_coords = coords[:, 0]
        y_coords = coords[:, 1]
        
        clearance_color = 'blue' if equipment_safe else 'red'
        clearance_alpha = 0.3 if equipment_safe else 0.5
        
        self.ax.plot(x_coords, y_coords, color=clearance_color, linewidth=3, 
                    label='建築限界', alpha=0.8)
        self.ax.fill(x_coords, y_coords, color=clearance_color, alpha=clearance_alpha)
        
        # レール表示
        self.ax.axhline(y=0, color='black', linewidth=4, alpha=0.8, label='レール面')
        self.ax.axvline(x=0, color='gray', linewidth=2, linestyle=':', alpha=0.6, label='レール中心')
        
        # レール位置
        rail_positions = [-533.5, 533.5]  # 軌間1067mmの半分
        for pos in rail_positions:
            self.ax.axvline(x=pos, color='brown', linewidth=3, alpha=0.7)
        
        # 設備位置表示
        equipment_color = 'green' if equipment_safe else 'red'
        equipment_marker = 'o' if equipment_safe else 'X'
        marker_size = 12 if equipment_safe else 15
        
        self.ax.scatter([equipment_x], [equipment_y], 
                       color=equipment_color, s=marker_size**2, 
                       marker=equipment_marker, 
                       label=f'{equipment_name}', 
                       edgecolors='black', linewidth=2, zorder=10)
        
        # 設備名ラベル
        label_offset_x = 200 if equipment_x >= 0 else -200
        label_offset_y = 200
        self.ax.annotate(f'{equipment_name}\\n({equipment_x:.0f}, {equipment_y:.0f})', 
                        xy=(equipment_x, equipment_y),
                        xytext=(equipment_x + label_offset_x, equipment_y + label_offset_y),
                        fontsize=11, ha='center',
                        bbox=dict(boxstyle='round,pad=0.3', facecolor='white', alpha=0.8),
                        arrowprops=dict(arrowstyle='->', color='black', alpha=0.7))
        
        # 情報表示
        info_texts = []
        if cant_value != 0:
            angle_deg = np.degrees(np.arctan(cant_value / 1067))
            info_texts.append(f'カント: {cant_value}mm (傾斜: {angle_deg:.2f}°)')
        
        if curve_radius > 0:
            info_texts.append(f'曲線半径: {curve_radius}m')
        
        if info_texts:
            info_text = '\\n'.join(info_texts)
            self.ax.text(0.02, 0.98, info_text, transform=self.ax.transAxes,
                        fontsize=12, verticalalignment='top',
                        bbox=dict(boxstyle='round', facecolor='lightyellow', alpha=0.9))
        
        # 軸設定
        self.ax.set_xlabel('レール中心からの距離 (mm)', fontsize=14)
        self.ax.set_ylabel('レールレベルからの高さ (mm)', fontsize=14)
        
        title_color = 'red' if not equipment_safe else 'green'
        status_text = '【支障】' if not equipment_safe else '【正常】'
        self.ax.set_title(f'建築限界断面図 {status_text}', 
                         fontsize=16, pad=20, color=title_color)
        
        self.ax.grid(True, alpha=0.3)
        self.ax.legend(loc='upper right', fontsize=11)
        
        # 範囲設定
        margin = 800
        x_min = min(min(x_coords), equipment_x) - margin
        x_max = max(max(x_coords), equipment_x) + margin
        y_min = -200
        y_max = max(max(y_coords), equipment_y) + margin
        
        self.ax.set_xlim(x_min, x_max)
        self.ax.set_ylim(y_min, y_max)
        self.ax.set_aspect('equal')
        
        self.canvas.draw()
    
    def update_ui_status(self, clearance_rank: str, clearance_status: str, rank_color: str,
                        equipment_x: float, equipment_y: float, equipment_name: str, 
                        equipment_safe: bool, cant_value: float, curve_radius: float):
        """UI状態更新"""
        # ランク表示
        self.clearance_rank_label.config(text=f"建築限界ランク: {clearance_rank}", fg=rank_color)
        
        # 設備状態
        equipment_status = "✅ 限界内" if equipment_safe else "❌ 支障"
        equipment_color = "green" if equipment_safe else "red"
        self.equipment_status_label.config(text=f"設備状態: {equipment_status}", fg=equipment_color)
        
        # 余裕距離計算（簡略化）
        if equipment_safe:
            # 建築限界境界までの余裕距離を概算
            clearance_width = 1000  # 概算値
            margin_distance = clearance_width - abs(equipment_x)
            self.distance_info_label.config(text=f"余裕距離: 約{margin_distance:.0f}mm", fg="blue")
        else:
            self.distance_info_label.config(text="余裕距離: 支障", fg="red")
        
        # 統計情報更新
        self.update_stats_display(equipment_x, equipment_y, equipment_name, equipment_safe,
                                 cant_value, curve_radius, clearance_rank)
    
    def update_stats_display(self, equipment_x: float, equipment_y: float, equipment_name: str,
                           equipment_safe: bool, cant_value: float, curve_radius: float,
                           clearance_rank: str):
        """統計情報表示更新"""
        self.stats_text.config(state=tk.NORMAL)
        self.stats_text.delete(1.0, tk.END)
        
        angle_deg = np.degrees(np.arctan(cant_value / 1067)) if cant_value != 0 else 0
        
        stats_info = f"""【設備情報】
設備名: {equipment_name}
水平位置: {equipment_x:.0f} mm
高さ位置: {equipment_y:.0f} mm
判定: {'✅ 安全' if equipment_safe else '❌ 支障'}

【軌道条件】
カント: {cant_value:.0f} mm
傾斜角: {angle_deg:.3f}°
曲線半径: {curve_radius:.0f} m
建築限界ランク: {clearance_rank}

【システム情報】
建築限界座標数: {len(self.base_clearance)}点
使用モデル: 正確寸法版
対応規格: 在来・一般・片線用

建築限界シミュレーター
設備位置測定対応版"""
        
        self.stats_text.insert(1.0, stats_info)
        self.stats_text.config(state=tk.DISABLED)
    
    def save_settings(self):
        """設定保存"""
        try:
            settings = {
                "cant": self.cant_var.get(),
                "curve_radius": self.radius_var.get(),
                "equipment_distance": self.equipment_distance_var.get(),
                "equipment_height": self.equipment_height_var.get(),
                "equipment_name": self.equipment_name_var.get()
            }
            
            import json
            with open("clearance_settings.json", 'w', encoding='utf-8') as f:
                json.dump(settings, f, ensure_ascii=False, indent=2)
            
            messagebox.showinfo("保存完了", "設定を保存しました。")
        except Exception as e:
            messagebox.showerror("保存エラー", f"設定保存に失敗しました: {e}")
    
    def run(self):
        """アプリケーション実行"""
        print("🚀 建築限界シミュレーター（設備測定対応版）を起動...")
        try:
            self.root.mainloop()
        except KeyboardInterrupt:
            print("\\n👋 アプリケーション終了")
        except Exception as e:
            print(f"❌ 実行エラー: {e}")
            messagebox.showerror("実行エラー", f"アプリケーションエラー: {e}")

def main():
    """メイン関数"""
    print("🏗️ 建築限界シミュレーター（最終版）初期化中...")
    
    try:
        app = FinalClearanceApp()
        app.run()
    except Exception as e:
        print(f"❌ 初期化エラー: {e}")
        messagebox.showerror("初期化エラー", f"アプリケーション初期化失敗:\\n{e}")

if __name__ == "__main__":
    main()