#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
建築限界シミュレーター v5.0
簡素化版 - 高さによる必要離れ判定のみ
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
import math
from typing import List, Tuple, Dict, Any

class ClearanceModelV5Simple:
    """建築限界モデル v5 - 簡素化版"""
    
    def __init__(self):
        """初期化"""
        self.rail_gauge = 1067  # 軌間 (mm)
        
        # 高さ区分の定義（Excelシートより）
        self.height_ranges = [
            (0, 375),      # B15
            (375, 920),    # B16
            (920, 3156),   # B17
            (3156, 3823),  # B18
            (3823, 5190),  # B19
            (5190, float('inf'))  # B20
        ]
    
    def calculate_required_clearance(self, height: float, cant_mm: float, curve_radius_m: float) -> float:
        """
        高さに基づく必要離れの計算（OIRANシミュレーター準拠）
        
        Args:
            height: レールレベルからの高さ (mm)
            cant_mm: カント値 (mm)
            curve_radius_m: 曲線半径 (m)
            
        Returns:
            必要離れ距離 (mm)
        """
        # カント角度の計算
        t = math.atan(cant_mm / self.rail_gauge) if cant_mm != 0 else 0
        
        # 曲線拡幅量の計算
        w = 0
        if curve_radius_m > 0 and curve_radius_m < 3000:
            w = min(100, 1500.0 / curve_radius_m)
        
        # 高さによる必要離れの計算
        if height < 0:
            return float('inf')  # 負の高さは無効
        elif height < 375:  # B15
            base_clearance = 1225 + height
        elif height < 920:  # B16
            base_clearance = 1575
        elif height < 3156:  # B17
            base_clearance = 1900
        elif height < 3823:  # B18
            # 円弧部分の計算
            discriminant = 2150**2 - (height - 2150)**2
            if discriminant < 0:
                base_clearance = 0
            else:
                base_clearance = math.sqrt(discriminant)
        elif height < 5190:  # B19
            base_clearance = 1350
        else:  # B20 (5190mm以上)
            # 上部円弧部分の計算
            discriminant = 1800**2 - (height - 4000)**2
            if discriminant < 0:
                base_clearance = 0
            else:
                base_clearance = math.sqrt(discriminant)
        
        # カント補正と拡幅を加算
        required_clearance = base_clearance + w + height * math.sin(t)
        
        return required_clearance
    
    def check_interference(self, distance: float, height: float, cant_mm: float, curve_radius_m: float) -> Dict[str, Any]:
        """
        設備位置の支障判定
        
        Args:
            distance: レール中心からの距離 (mm)
            height: レールレベルからの高さ (mm)
            cant_mm: カント値 (mm)
            curve_radius_m: 曲線半径 (m)
            
        Returns:
            判定結果の辞書
        """
        abs_distance = abs(distance)
        required_clearance = self.calculate_required_clearance(height, cant_mm, curve_radius_m)
        
        # 支障判定
        is_interference = abs_distance < required_clearance
        
        # 余裕または支障量の計算
        if is_interference:
            margin = abs_distance - required_clearance  # 負の値（支障量）
        else:
            margin = abs_distance - required_clearance  # 正の値（余裕）
        
        return {
            "is_interference": is_interference,
            "required_clearance": required_clearance,
            "actual_distance": abs_distance,
            "margin": margin,
            "height_range": self._get_height_range_name(height)
        }
    
    def _get_height_range_name(self, height: float) -> str:
        """高さ区分の名称を返す"""
        if height < 375:
            return "0～375mm"
        elif height < 920:
            return "375～920mm"
        elif height < 3156:
            return "920～3156mm"
        elif height < 3823:
            return "3156～3823mm"
        elif height < 5190:
            return "3823～5190mm"
        else:
            return "5190mm以上"
    
    def create_clearance_polygon(self, cant_mm: float, curve_radius_m: float) -> List[Tuple[float, float]]:
        """
        建築限界の輪郭座標を生成（表示用）
        """
        points = []
        
        # 高さごとに必要離れを計算して輪郭を作成
        heights = [0, 25, 375, 920, 3156, 3823, 4300, 5190, 5700]
        
        # 右側の輪郭
        for h in heights:
            clearance = self.calculate_required_clearance(h, cant_mm, curve_radius_m)
            points.append((clearance, h))
        
        # 左側の輪郭（対称）
        for h in reversed(heights[:-1]):
            clearance = self.calculate_required_clearance(h, cant_mm, curve_radius_m)
            points.append((-clearance, h))
        
        # 閉じる
        points.append(points[0])
        
        return points

class ClearanceAppV5Simple:
    """建築限界アプリ v5 - 簡素化版"""
    
    def __init__(self):
        """アプリケーション初期化"""
        self.root = tk.Tk()
        self.root.title("建築限界シミュレーター v5.0 - 簡素化版")
        
        # ウィンドウサイズ設定
        screen_width = self.root.winfo_screenwidth()
        screen_height = self.root.winfo_screenheight()
        
        window_width = int(screen_width * 0.9)
        window_height = int(screen_height * 0.9)
        
        x = (screen_width - window_width) // 2
        y = (screen_height - window_height) // 2
        
        self.root.geometry(f"{window_width}x{window_height}+{x}+{y}")
        self.root.minsize(1200, 800)
        
        # 日本語フォント設定
        self.setup_japanese_font()
        
        # 建築限界モデル初期化
        self.clearance_model = ClearanceModelV5Simple()
        
        # UI変数初期化
        self.cant_var = tk.DoubleVar(value=0.0)
        self.radius_var = tk.DoubleVar(value=0.0)
        self.equipment_distance_var = tk.DoubleVar(value=0.0)
        self.equipment_height_var = tk.DoubleVar(value=1000.0)
        self.equipment_name_var = tk.StringVar(value="測定設備")
        
        # UI構築
        self.create_ui()
        
        # 初期表示更新
        self.update_display()
    
    def setup_japanese_font(self):
        """日本語フォント設定"""
        system = platform.system()
        
        font_candidates = []
        
        if system == "Windows":
            font_candidates = [("Yu Gothic UI", 10), ("Meiryo UI", 10), ("MS Gothic", 10)]
        elif system == "Darwin":
            font_candidates = [("Hiragino Sans", 12), ("Hiragino Kaku Gothic Pro", 12)]
        else:  # Linux/WSL
            font_candidates = [
                ("Noto Sans CJK JP", 10), ("Takao Gothic", 10), 
                ("IPAexGothic", 10), ("DejaVu Sans", 10)
            ]
        
        self.default_font = None
        self.title_font = None
        
        for font_name, size in font_candidates:
            try:
                test_font = tkFont.Font(family=font_name, size=size)
                test_font.actual()
                
                self.default_font = (font_name, size)
                self.title_font = (font_name, size + 2, "bold")
                self.font_family = font_name
                
                print(f"✅ 日本語フォント設定: {font_name}")
                break
            except:
                continue
        
        if not self.default_font:
            self.default_font = ("Arial", 10)
            self.title_font = ("Arial", 12, "bold")
            self.font_family = "Arial"
        
        # matplotlib設定
        try:
            plt.rcParams['font.family'] = self.font_family
            plt.rcParams['axes.unicode_minus'] = False
        except:
            plt.rcParams['font.family'] = 'DejaVu Sans'
    
    def create_ui(self):
        """UI作成"""
        main_frame = ttk.Frame(self.root)
        main_frame.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        
        # 左パネル（コントロール）
        self.create_control_panel(main_frame)
        
        # 右パネル（グラフ）
        self.create_graph_panel(main_frame)
    
    def create_control_panel(self, parent):
        """コントロールパネル作成"""
        left_panel = ttk.Frame(parent, width=400)
        left_panel.pack(side=tk.LEFT, fill=tk.Y, padx=(0, 5))
        left_panel.pack_propagate(False)
        
        # タイトル
        title_label = tk.Label(left_panel, text="建築限界シミュレーター v5", 
                              font=self.title_font, fg="navy")
        title_label.pack(pady=(10, 5))
        
        subtitle_label = tk.Label(left_panel, text="簡素化版 - 高さ判定のみ", 
                                font=self.default_font, fg="darkgreen")
        subtitle_label.pack(pady=(0, 10))
        
        # 設備位置セクション
        self.create_equipment_section(left_panel)
        
        # カント設定セクション
        self.create_cant_section(left_panel)
        
        # 曲線半径設定セクション
        self.create_curve_section(left_panel)
        
        # 判定結果セクション
        self.create_result_section(left_panel)
        
        # 操作ボタンセクション
        self.create_button_section(left_panel)
    
    def create_equipment_section(self, parent):
        """設備位置測定セクション"""
        equipment_group = ttk.LabelFrame(parent, text="📍 設備位置測定")
        equipment_group.pack(fill=tk.X, pady=5, padx=5)
        
        inner_frame = ttk.Frame(equipment_group)
        inner_frame.pack(fill=tk.X, padx=10, pady=10)
        
        # 設備名
        tk.Label(inner_frame, text="設備名:", font=self.default_font).pack(anchor=tk.W)
        ttk.Entry(inner_frame, textvariable=self.equipment_name_var, 
                 font=self.default_font, width=30).pack(fill=tk.X, pady=(2, 8))
        
        # 距離入力
        tk.Label(inner_frame, text="レール中心からの距離 (mm):", 
                font=self.default_font).pack(anchor=tk.W, pady=(5,0))
        
        distance_frame = ttk.Frame(inner_frame)
        distance_frame.pack(fill=tk.X, pady=2)
        
        ttk.Spinbox(distance_frame, from_=-3000, to=3000, increment=10,
                   textvariable=self.equipment_distance_var, width=15,
                   command=self.update_display).pack(side=tk.LEFT)
        
        tk.Label(distance_frame, text="(左:負, 右:正)", 
                font=(self.font_family, 8), foreground="gray").pack(side=tk.LEFT, padx=(5,0))
        
        # 高さ入力
        tk.Label(inner_frame, text="レールレベルからの高さ (mm):", 
                font=self.default_font).pack(anchor=tk.W, pady=(8,0))
        
        height_frame = ttk.Frame(inner_frame)
        height_frame.pack(fill=tk.X, pady=2)
        
        ttk.Spinbox(height_frame, from_=0, to=6000, increment=50,
                   textvariable=self.equipment_height_var, width=15,
                   command=self.update_display).pack(side=tk.LEFT)
        
        tk.Label(height_frame, text="(レール面=0)", 
                font=(self.font_family, 8), foreground="gray").pack(side=tk.LEFT, padx=(5,0))
    
    def create_cant_section(self, parent):
        """カント設定セクション"""
        cant_group = ttk.LabelFrame(parent, text="⚖️ カント設定")
        cant_group.pack(fill=tk.X, pady=5, padx=5)
        
        inner_frame = ttk.Frame(cant_group)
        inner_frame.pack(fill=tk.X, padx=10, pady=10)
        
        tk.Label(inner_frame, text="カント値 (mm):", font=self.default_font).pack(anchor=tk.W)
        
        ttk.Spinbox(inner_frame, from_=-200, to=200, increment=5,
                   textvariable=self.cant_var, width=20,
                   command=self.update_display).pack(fill=tk.X, pady=2)
    
    def create_curve_section(self, parent):
        """曲線半径設定セクション"""
        curve_group = ttk.LabelFrame(parent, text="🔄 曲線半径設定")
        curve_group.pack(fill=tk.X, pady=5, padx=5)
        
        inner_frame = ttk.Frame(curve_group)
        inner_frame.pack(fill=tk.X, padx=10, pady=10)
        
        tk.Label(inner_frame, text="曲線半径 (m):", font=self.default_font).pack(anchor=tk.W)
        
        ttk.Spinbox(inner_frame, from_=0, to=2000, increment=50,
                   textvariable=self.radius_var, width=20,
                   command=self.update_display).pack(fill=tk.X, pady=2)
    
    def create_result_section(self, parent):
        """判定結果セクション"""
        result_group = ttk.LabelFrame(parent, text="📊 判定結果")
        result_group.pack(fill=tk.X, pady=5, padx=5)
        
        inner_frame = ttk.Frame(result_group)
        inner_frame.pack(fill=tk.X, padx=10, pady=10)
        
        # 支障判定
        self.interference_label = tk.Label(inner_frame, text="判定: 計算中...", 
                                         font=self.title_font, fg="black")
        self.interference_label.pack(pady=5)
        
        # 高さ区分
        self.height_range_label = tk.Label(inner_frame, text="高さ区分: -", 
                                         font=self.default_font, fg="blue")
        self.height_range_label.pack(pady=2)
        
        # 必要離れ
        self.required_clearance_label = tk.Label(inner_frame, text="必要離れ: - mm", 
                                               font=self.default_font, fg="darkblue")
        self.required_clearance_label.pack(pady=2)
        
        # 余裕/支障量
        self.margin_label = tk.Label(inner_frame, text="余裕: - mm", 
                                   font=self.default_font, fg="black")
        self.margin_label.pack(pady=2)
        
        # 詳細情報
        detail_frame = ttk.LabelFrame(inner_frame, text="計算詳細")
        detail_frame.pack(fill=tk.X, pady=(10, 0))
        
        self.detail_text = tk.Text(detail_frame, height=8, width=35, 
                                 font=(self.font_family, 9), state=tk.DISABLED,
                                 wrap=tk.WORD)
        self.detail_text.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
    
    def create_button_section(self, parent):
        """操作ボタンセクション"""
        button_frame = ttk.Frame(parent)
        button_frame.pack(fill=tk.X, pady=10, padx=5)
        
        ttk.Button(button_frame, text="🔄 リセット", 
                  command=self.reset_values).pack(fill=tk.X, pady=2)
        
        ttk.Button(button_frame, text="💾 設定保存", 
                  command=self.save_settings).pack(fill=tk.X, pady=2)
    
    def create_graph_panel(self, parent):
        """グラフパネル作成"""
        graph_frame = ttk.LabelFrame(parent, text="🏗️ 建築限界表示")
        graph_frame.pack(side=tk.RIGHT, fill=tk.BOTH, expand=True, padx=(5, 0))
        
        self.fig = Figure(figsize=(10, 8), dpi=100)
        self.ax = self.fig.add_subplot(111)
        
        self.ax.set_xlabel('レール中心からの距離 (mm)', fontsize=12)
        self.ax.set_ylabel('レールレベルからの高さ (mm)', fontsize=12)
        self.ax.set_title('建築限界断面図 v5（簡素化版）', fontsize=14, pad=15)
        self.ax.grid(True, alpha=0.3)
        self.ax.set_aspect('equal')
        
        self.canvas = FigureCanvasTkAgg(self.fig, graph_frame)
        self.canvas.get_tk_widget().pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
    
    def update_display(self):
        """表示更新"""
        # 値の取得
        cant_value = self.cant_var.get()
        curve_radius = self.radius_var.get()
        equipment_x = self.equipment_distance_var.get()
        equipment_y = self.equipment_height_var.get()
        equipment_name = self.equipment_name_var.get()
        
        # 支障判定
        result = self.clearance_model.check_interference(
            equipment_x, equipment_y, cant_value, curve_radius
        )
        
        # UI更新
        self.update_result_display(result, equipment_x, equipment_y)
        
        # グラフ更新
        self.update_graph(cant_value, curve_radius, equipment_x, equipment_y, 
                         equipment_name, result)
    
    def update_result_display(self, result: Dict[str, Any], equipment_x: float, equipment_y: float):
        """判定結果表示更新"""
        # 支障判定
        if result["is_interference"]:
            self.interference_label.config(text="判定: ❌ 支障", fg="red")
            margin_text = f"支障量: {abs(result['margin']):.0f} mm"
            margin_color = "red"
        else:
            self.interference_label.config(text="判定: ✅ 安全", fg="green")
            margin_text = f"余裕: {result['margin']:.0f} mm"
            margin_color = "green"
        
        # その他の表示
        self.height_range_label.config(text=f"高さ区分: {result['height_range']}")
        self.required_clearance_label.config(text=f"必要離れ: {result['required_clearance']:.0f} mm")
        self.margin_label.config(text=margin_text, fg=margin_color)
        
        # 詳細情報
        self.detail_text.config(state=tk.NORMAL)
        self.detail_text.delete(1.0, tk.END)
        
        cant_value = self.cant_var.get()
        curve_radius = self.radius_var.get()
        
        detail_info = f"""【測定値】
距離: {equipment_x:.0f} mm（絶対値: {abs(equipment_x):.0f} mm）
高さ: {equipment_y:.0f} mm

【条件】
カント: {cant_value:.0f} mm
曲線半径: {curve_radius:.0f} m
曲線拡幅: {min(100, 1500/curve_radius) if curve_radius > 0 else 0:.1f} mm

【計算結果】
高さ区分: {result['height_range']}
必要離れ: {result['required_clearance']:.0f} mm
実際の距離: {result['actual_distance']:.0f} mm
{margin_text}

【判定基準】
実際の距離 < 必要離れ → 支障
実際の距離 ≥ 必要離れ → 安全"""
        
        self.detail_text.insert(1.0, detail_info)
        self.detail_text.config(state=tk.DISABLED)
    
    def update_graph(self, cant_value: float, curve_radius: float,
                    equipment_x: float, equipment_y: float, equipment_name: str,
                    result: Dict[str, Any]):
        """グラフ更新"""
        self.ax.clear()
        
        # 建築限界の輪郭を生成
        clearance_points = self.clearance_model.create_clearance_polygon(cant_value, curve_radius)
        
        if clearance_points:
            x_coords = [p[0] for p in clearance_points]
            y_coords = [p[1] for p in clearance_points]
            
            # 建築限界を描画
            clearance_color = 'red' if result["is_interference"] else 'blue'
            clearance_alpha = 0.5 if result["is_interference"] else 0.3
            
            self.ax.plot(x_coords, y_coords, color=clearance_color, linewidth=3, 
                        label='建築限界', alpha=0.8)
            self.ax.fill(x_coords, y_coords, color=clearance_color, alpha=clearance_alpha)
        
        # レール表示
        self.ax.axhline(y=0, color='black', linewidth=4, alpha=0.8, label='レール面')
        self.ax.axvline(x=0, color='gray', linewidth=2, linestyle=':', alpha=0.6, label='レール中心')
        
        # レール位置
        rail_positions = [-533.5, 533.5]
        for pos in rail_positions:
            self.ax.axvline(x=pos, color='brown', linewidth=3, alpha=0.7)
        
        # 設備位置表示
        equipment_color = 'red' if result["is_interference"] else 'green'
        equipment_marker = 'X' if result["is_interference"] else 'o'
        
        self.ax.scatter([equipment_x], [equipment_y], 
                       color=equipment_color, s=100, 
                       marker=equipment_marker, 
                       label=f'{equipment_name}', 
                       edgecolors='black', linewidth=1.5, zorder=10)
        
        # 設備名ラベル
        label_offset_x = 300 if equipment_x >= 0 else -300
        label_offset_y = 300
        self.ax.annotate(f'{equipment_name}\n({equipment_x:.0f}, {equipment_y:.0f})', 
                        xy=(equipment_x, equipment_y),
                        xytext=(equipment_x + label_offset_x, equipment_y + label_offset_y),
                        fontsize=10, ha='center',
                        bbox=dict(boxstyle='round,pad=0.4', facecolor='white', alpha=0.9),
                        arrowprops=dict(arrowstyle='->', color='black', alpha=0.8))
        
        # 必要離れラインを表示
        req_clearance = result["required_clearance"]
        self.ax.axvline(x=req_clearance, color='orange', linewidth=2, linestyle='--', 
                       alpha=0.7, label=f'必要離れ ({req_clearance:.0f}mm)')
        self.ax.axvline(x=-req_clearance, color='orange', linewidth=2, linestyle='--', 
                       alpha=0.7)
        
        # 情報表示
        info_texts = []
        if cant_value != 0:
            angle_deg = np.degrees(np.arctan(cant_value / 1067))
            info_texts.append(f'カント: {cant_value}mm (傾斜: {angle_deg:.2f}°)')
        
        if curve_radius > 0:
            widening = min(100, 1500.0 / curve_radius)
            info_texts.append(f'曲線半径: {curve_radius}m (拡幅: {widening:.1f}mm)')
        
        if info_texts:
            info_text = '\n'.join(info_texts)
            self.ax.text(0.02, 0.98, info_text, transform=self.ax.transAxes,
                        fontsize=11, verticalalignment='top',
                        bbox=dict(boxstyle='round', facecolor='lightyellow', alpha=0.9))
        
        # 軸設定
        self.ax.set_xlabel('レール中心からの距離 (mm)', fontsize=12)
        self.ax.set_ylabel('レールレベルからの高さ (mm)', fontsize=12)
        
        title_color = 'red' if result["is_interference"] else 'green'
        status_text = '【支障】' if result["is_interference"] else '【正常】'
        self.ax.set_title(f'建築限界断面図 v5 簡素化版 {status_text}', 
                         fontsize=14, pad=15, color=title_color)
        
        self.ax.grid(True, alpha=0.3)
        self.ax.legend(loc='upper right', fontsize=10)
        
        # 範囲設定
        margin = 500
        x_max = max(max(abs(equipment_x), req_clearance) + margin, 2500)
        y_max = max(equipment_y + margin, 6000)
        
        self.ax.set_xlim(-x_max, x_max)
        self.ax.set_ylim(-200, y_max)
        self.ax.set_aspect('equal')
        
        self.canvas.draw()
    
    def reset_values(self):
        """値をリセット"""
        self.cant_var.set(0.0)
        self.radius_var.set(0.0)
        self.equipment_distance_var.set(0.0)
        self.equipment_height_var.set(1000.0)
        self.equipment_name_var.set("測定設備")
        self.update_display()
    
    def save_settings(self):
        """設定保存"""
        try:
            settings = {
                "version": "5.0_simple",
                "cant": self.cant_var.get(),
                "curve_radius": self.radius_var.get(),
                "equipment_distance": self.equipment_distance_var.get(),
                "equipment_height": self.equipment_height_var.get(),
                "equipment_name": self.equipment_name_var.get()
            }
            
            with open("clearance_settings_v5_simple.json", 'w', encoding='utf-8') as f:
                json.dump(settings, f, ensure_ascii=False, indent=2)
            
            messagebox.showinfo("保存完了", "設定をv5簡素化版形式で保存しました。")
        except Exception as e:
            messagebox.showerror("保存エラー", f"設定保存に失敗しました: {e}")
    
    def run(self):
        """アプリケーション実行"""
        print("🚀 建築限界シミュレーター v5.0 簡素化版を起動...")
        try:
            self.root.mainloop()
        except KeyboardInterrupt:
            print("\n👋 アプリケーション終了")
        except Exception as e:
            print(f"❌ 実行エラー: {e}")
            messagebox.showerror("実行エラー", f"アプリケーションエラー: {e}")

def main():
    """メイン実行"""
    print("🏗️ 建築限界シミュレーター v5.0（簡素化版）初期化中...")
    
    try:
        app = ClearanceAppV5Simple()
        app.run()
    except Exception as e:
        print(f"❌ 初期化エラー: {e}")
        messagebox.showerror("初期化エラー", f"アプリケーション初期化失敗:\n{e}")

if __name__ == "__main__":
    main()