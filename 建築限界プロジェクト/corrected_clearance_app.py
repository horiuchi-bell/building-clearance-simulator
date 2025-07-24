#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
建築限界シミュレーター - 修正版
正確な寸法・ウィンドウサイズ・日本語対応・判定ボタン付き
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

class AccurateBuildingClearanceModel:
    """正確な寸法に基づく建築限界モデル"""
    
    def __init__(self):
        """初期化"""
        self.rail_gauge = 1067  # 軌間 (mm)
        
    def create_clearance_shape(self) -> List[Tuple[float, float]]:
        """
        修正された正確な建築限界形状を作成
        """
        points = []
        
        # 右側の輪郭を作成（下から上へ）
        
        # 1. レールレベルから25mmまでの高さ = 1225mm
        points.append((1225, 0))     # レール面
        points.append((1225, 25))    # 25mmまで
        
        # 2. 高さ375～920mmまで = 1575mm
        points.append((1575, 375))   # 375mmから拡張開始
        points.append((1575, 920))   # 920mmまで
        
        # 3. 高さ920～3200mm = 1900mm
        points.append((1900, 920))   # 920mmから最大幅
        points.append((1900, 3200))  # 3200mmまで
        
        # 4. 高さ3200mm～レール中心の高さ4300mmまでを滑らかな曲線で結ぶ
        # 曲線部分を複数点で近似
        curve_points = self._create_smooth_curve(1900, 3200, 1350, 4300, 20)
        points.extend(curve_points)
        
        # 5. 上部の架線に対する建築限界範囲（縦方向）
        points.append((1350, 4300))  # 縦方向範囲
        
        # 6. 上部架線範囲での円弧処理
        # レール中心の高さ4000mmの箇所から半径1800mmで円を描く
        arc_points = self._create_overhead_arc_boundary()
        points.extend(arc_points)
        
        # 7. 最上部まで
        points.append((1350, 5700))  # 最大高さ
        
        # 上部（右から左へ）
        points.append((-1350, 5700))  # 最上部左端
        
        # 左側（上から下、右側と対称）
        # 右側の点を左右反転して追加
        right_points = [(x, y) for x, y in points if x > 0]
        right_points.reverse()  # 上から下の順番に
        
        for x, y in right_points[1:-1]:  # 最初と最後の点は除く
            points.append((-x, y))
        
        # 形状を閉じる
        points.append((1225, 0))
        
        print(f"✅ 修正された建築限界形状を作成: {len(points)}点")
        return points
    
    def _create_smooth_curve(self, x1: float, y1: float, x2: float, y2: float, num_points: int) -> List[Tuple[float, float]]:
        """滑らかな曲線を作成"""
        points = []
        
        # 3次ベジエ曲線で滑らかに接続
        for i in range(1, num_points + 1):
            t = i / num_points
            
            # 制御点を設定（滑らかな曲線用）
            cp1_x, cp1_y = x1, y1 + (y2 - y1) * 0.3
            cp2_x, cp2_y = x2, y1 + (y2 - y1) * 0.7
            
            # ベジエ曲線の計算
            x = (1-t)**3 * x1 + 3*(1-t)**2*t * cp1_x + 3*(1-t)*t**2 * cp2_x + t**3 * x2
            y = (1-t)**3 * y1 + 3*(1-t)**2*t * cp1_y + 3*(1-t)*t**2 * cp2_y + t**3 * y2
            
            points.append((x, y))
        
        return points
    
    def _create_overhead_arc_boundary(self) -> List[Tuple[float, float]]:
        """架線部分の円弧境界を作成"""
        points = []
        
        # 円の中心: (0, 4000), 半径: 1800mm
        center_x, center_y = 0, 4000
        radius = 1800
        
        # 縦方向範囲 x=1350 との交点を求める
        x_boundary = 1350
        
        # 円の方程式: (x-0)² + (y-4000)² = 1800²
        # x = 1350 での y を求める
        discriminant = radius**2 - x_boundary**2
        
        if discriminant >= 0:
            y_intersect = center_y + math.sqrt(discriminant)
            
            # 交点から上部まで円弧を描く
            start_angle = math.atan2(y_intersect - center_y, x_boundary - center_x)
            end_angle = math.pi / 2  # 90度
            
            num_arc_points = 15
            for i in range(num_arc_points):
                angle = start_angle + (end_angle - start_angle) * i / (num_arc_points - 1)
                x = center_x + radius * math.cos(angle)
                y = center_y + radius * math.sin(angle)
                
                # 範囲内の点のみ追加
                if abs(x) <= 1350 and y <= 5700:
                    points.append((x, y))
        
        return points
    
    def validate_point_in_clearance(self, x: float, y: float, 
                                   clearance_points: List[Tuple[float, float]]) -> bool:
        """点が建築限界内にあるかチェック"""
        if not clearance_points or y < 0:
            return False
        
        clearance_width = self._get_clearance_width_at_height(y, clearance_points)
        
        if clearance_width is None:
            return False
        
        return abs(x) <= clearance_width
    
    def _get_clearance_width_at_height(self, height: float, 
                                      points: List[Tuple[float, float]]) -> float:
        """指定高さでの建築限界の片側幅を取得"""
        right_points = [(x, y) for x, y in points if x > 0]
        
        if not right_points:
            return None
        
        right_points.sort(key=lambda p: p[1])
        
        for i in range(len(right_points) - 1):
            y1, x1 = right_points[i][1], right_points[i][0]
            y2, x2 = right_points[i + 1][1], right_points[i + 1][0]
            
            if y1 <= height <= y2:
                if y2 == y1:
                    return x1
                ratio = (height - y1) / (y2 - y1)
                width = x1 + ratio * (x2 - x1)
                return width
        
        return None
    
    def transform_clearance(self, points: List[Tuple[float, float]],
                           cant_mm: float, curve_radius_m: float) -> List[Tuple[float, float]]:
        """カント・曲線半径による建築限界の変形"""
        if not points:
            return []
        
        coords = np.array(points)
        
        # カント変換
        if cant_mm != 0:
            angle_rad = np.arctan(cant_mm / self.rail_gauge)
            
            cos_a = np.cos(angle_rad)
            sin_a = np.sin(angle_rad)
            
            rotation_matrix = np.array([
                [cos_a, -sin_a],
                [sin_a, cos_a]
            ])
            
            coords = coords @ rotation_matrix.T
        
        # 曲線拡幅
        if curve_radius_m > 0 and curve_radius_m < 3000:
            widening_factor = min(100, 1500.0 / curve_radius_m)
            coords[:, 0] = coords[:, 0] + np.sign(coords[:, 0]) * widening_factor
        
        return coords.tolist()

class CorrectedClearanceApp:
    """修正版建築限界シミュレーター"""
    
    def __init__(self):
        """アプリケーション初期化"""
        self.root = tk.Tk()
        self.root.title("建築限界シミュレーター - 修正版")
        
        # ウィンドウサイズを適切に設定
        screen_width = self.root.winfo_screenwidth()
        screen_height = self.root.winfo_screenheight()
        
        # 画面の90%を使用
        window_width = int(screen_width * 0.9)
        window_height = int(screen_height * 0.9)
        
        # 中央配置
        x = (screen_width - window_width) // 2
        y = (screen_height - window_height) // 2
        
        self.root.geometry(f"{window_width}x{window_height}+{x}+{y}")
        self.root.minsize(1400, 900)  # 最小サイズ設定
        
        # 日本語フォント設定
        self.setup_japanese_font()
        
        # 建築限界モデル初期化
        self.clearance_model = AccurateBuildingClearanceModel()
        self.base_clearance = self.clearance_model.create_clearance_shape()
        
        # UI変数初期化
        self.cant_var = tk.DoubleVar(value=0.0)
        self.radius_var = tk.DoubleVar(value=0.0)
        
        # 設備位置測定値変数
        self.equipment_distance_var = tk.DoubleVar(value=0.0)
        self.equipment_height_var = tk.DoubleVar(value=1000.0)
        self.equipment_name_var = tk.StringVar(value="測定設備")
        
        # UI構築
        self.create_ui()
        
        # 初期表示更新
        self.update_display()
    
    def setup_japanese_font(self):
        """日本語フォント設定（改良版）"""
        system = platform.system()
        
        # フォント設定を試行錯誤で決定
        font_candidates = []
        
        if system == "Windows":
            font_candidates = [
                ("Yu Gothic UI", 10),
                ("Meiryo UI", 10), 
                ("MS Gothic", 10),
                ("Arial Unicode MS", 10)
            ]
        elif system == "Darwin":  # macOS
            font_candidates = [
                ("Hiragino Sans", 12),
                ("Hiragino Kaku Gothic Pro", 12),
                ("Arial Unicode MS", 12)
            ]
        else:  # Linux/WSL
            font_candidates = [
                ("Noto Sans CJK JP", 10),
                ("Takao Gothic", 10),
                ("IPAexGothic", 10),
                ("DejaVu Sans", 10),
                ("Liberation Sans", 10)
            ]
        
        # 利用可能なフォントを探す
        self.default_font = None
        self.title_font = None
        
        for font_name, size in font_candidates:
            try:
                test_font = tkFont.Font(family=font_name, size=size)
                # フォントが実際に使用可能かテスト
                test_font.actual()
                
                self.default_font = (font_name, size)
                self.title_font = (font_name, size + 2, "bold")
                self.font_family = font_name
                
                print(f"✅ 日本語フォント設定成功: {font_name}")
                break
            except Exception as e:
                print(f"⚠️ フォント '{font_name}' は利用できません: {e}")
                continue
        
        # フォールバック
        if not self.default_font:
            self.default_font = ("Arial", 10)
            self.title_font = ("Arial", 12, "bold")
            self.font_family = "Arial"
            print("⚠️ 日本語フォントが見つかりません。Arialを使用します。")
        
        # matplotlib日本語フォント設定
        try:
            plt.rcParams['font.family'] = self.font_family
            plt.rcParams['axes.unicode_minus'] = False
            print(f"✅ matplotlib日本語フォント設定: {self.font_family}")
        except:
            plt.rcParams['font.family'] = 'DejaVu Sans'
            print("⚠️ matplotlib日本語フォント設定失敗")
    
    def create_ui(self):
        """UI作成（改良版レイアウト）"""
        # メインフレーム
        main_frame = ttk.Frame(self.root)
        main_frame.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        
        # 左パネル（設定）- 幅を調整
        self.create_control_panel(main_frame)
        
        # 右パネル（グラフ）
        self.create_graph_panel(main_frame)
    
    def create_control_panel(self, parent):
        """コントロールパネル作成（幅調整版）"""
        # スクロール可能なフレームを作成
        canvas = tk.Canvas(parent, width=350)  # 固定幅
        scrollbar = ttk.Scrollbar(parent, orient="vertical", command=canvas.yview)
        scrollable_frame = ttk.Frame(canvas)
        
        scrollable_frame.bind(
            "<Configure>",
            lambda e: canvas.configure(scrollregion=canvas.bbox("all"))
        )
        
        canvas.create_window((0, 0), window=scrollable_frame, anchor="nw")
        canvas.configure(yscrollcommand=scrollbar.set)
        
        canvas.pack(side=tk.LEFT, fill=tk.Y, padx=(0, 5))
        scrollbar.pack(side=tk.LEFT, fill=tk.Y)
        
        # タイトル
        title_label = tk.Label(scrollable_frame, text="建築限界シミュレーター", 
                              font=self.title_font, fg="navy")
        title_label.pack(pady=(10, 15))
        
        # 各セクションを作成
        self.create_equipment_section(scrollable_frame)
        self.create_cant_section(scrollable_frame)
        self.create_curve_section(scrollable_frame)
        self.create_result_section(scrollable_frame)
        self.create_stats_section(scrollable_frame)
        self.create_button_section(scrollable_frame)
    
    def create_equipment_section(self, parent):
        """設備位置測定セクション"""
        equipment_group = ttk.LabelFrame(parent, text="📍 設備位置測定")
        equipment_group.pack(fill=tk.X, pady=5, padx=5)
        
        # 内部フレーム
        inner_frame = ttk.Frame(equipment_group)
        inner_frame.pack(fill=tk.X, padx=10, pady=10)
        
        # 設備名入力
        tk.Label(inner_frame, text="設備名:", font=self.default_font).pack(anchor=tk.W)
        equipment_name_entry = ttk.Entry(inner_frame, textvariable=self.equipment_name_var, 
                                        font=self.default_font, width=25)
        equipment_name_entry.pack(fill=tk.X, pady=(2, 8))
        
        # レール中心からの距離入力
        tk.Label(inner_frame, text="レール中心からの距離 (mm):", 
                font=self.default_font).pack(anchor=tk.W, pady=(5,0))
        
        distance_frame = ttk.Frame(inner_frame)
        distance_frame.pack(fill=tk.X, pady=2)
        
        distance_spin = ttk.Spinbox(distance_frame, from_=-3000, to=3000, increment=10,
                                   textvariable=self.equipment_distance_var, width=12,
                                   command=self.on_equipment_change)
        distance_spin.pack(side=tk.LEFT)
        
        tk.Label(distance_frame, text="(左:負, 右:正)", 
                font=(self.font_family, 8), foreground="gray").pack(side=tk.LEFT, padx=(5,0))
        
        # レールレベルからの高さ入力
        tk.Label(inner_frame, text="レールレベルからの高さ (mm):", 
                font=self.default_font).pack(anchor=tk.W, pady=(8,0))
        
        height_frame = ttk.Frame(inner_frame)
        height_frame.pack(fill=tk.X, pady=2)
        
        height_spin = ttk.Spinbox(height_frame, from_=0, to=6000, increment=50,
                                 textvariable=self.equipment_height_var, width=12,
                                 command=self.on_equipment_change)
        height_spin.pack(side=tk.LEFT)
        
        tk.Label(height_frame, text="(レール面=0)", 
                font=(self.font_family, 8), foreground="gray").pack(side=tk.LEFT, padx=(5,0))
        
        # プリセットボタン
        preset_frame = ttk.LabelFrame(inner_frame, text="プリセット")
        preset_frame.pack(fill=tk.X, pady=(10, 5))
        
        presets = [
            ("信号機", -2000, 3000),
            ("標識", -1800, 2000),
            ("架線柱", -2500, 4000),
            ("中央", 0, 2000)
        ]
        
        for i, (name, dist, height) in enumerate(presets):
            btn = ttk.Button(preset_frame, text=name, width=8,
                           command=lambda d=dist, h=height, n=name: self.set_equipment_position(d, h, n))
            btn.grid(row=i//2, column=i%2, padx=2, pady=2, sticky="ew")
        
        preset_frame.columnconfigure(0, weight=1)
        preset_frame.columnconfigure(1, weight=1)
    
    def create_cant_section(self, parent):
        """カント設定セクション"""
        cant_group = ttk.LabelFrame(parent, text="⚖️ カント設定")
        cant_group.pack(fill=tk.X, pady=5, padx=5)
        
        inner_frame = ttk.Frame(cant_group)
        inner_frame.pack(fill=tk.X, padx=10, pady=10)
        
        tk.Label(inner_frame, text="カント値 (mm):", font=self.default_font).pack(anchor=tk.W)
        cant_spin = ttk.Spinbox(inner_frame, from_=-200, to=200, increment=5,
                               textvariable=self.cant_var, width=25,
                               command=self.on_parameter_change)
        cant_spin.pack(fill=tk.X, pady=2)
        
        # カントプリセット
        preset_frame = ttk.Frame(inner_frame)
        preset_frame.pack(fill=tk.X, pady=(8, 0))
        
        cant_presets = [("0", 0), ("100", 100), ("140", 140), ("-80", -80)]
        for i, (text, value) in enumerate(cant_presets):
            btn = ttk.Button(preset_frame, text=text, width=6,
                           command=lambda v=value: self.set_cant(v))
            btn.grid(row=0, column=i, padx=1, sticky="ew")
        
        for i in range(4):
            preset_frame.columnconfigure(i, weight=1)
    
    def create_curve_section(self, parent):
        """曲線半径設定セクション"""
        curve_group = ttk.LabelFrame(parent, text="🔄 曲線半径設定")
        curve_group.pack(fill=tk.X, pady=5, padx=5)
        
        inner_frame = ttk.Frame(curve_group)
        inner_frame.pack(fill=tk.X, padx=10, pady=10)
        
        tk.Label(inner_frame, text="曲線半径 (m):", font=self.default_font).pack(anchor=tk.W)
        radius_spin = ttk.Spinbox(inner_frame, from_=0, to=2000, increment=50,
                                 textvariable=self.radius_var, width=25,
                                 command=self.on_parameter_change)
        radius_spin.pack(fill=tk.X, pady=2)
        
        # 半径プリセット
        preset_frame = ttk.Frame(inner_frame)
        preset_frame.pack(fill=tk.X, pady=(8, 0))
        
        radius_presets = [("直線", 0), ("急曲線", 300), ("標準", 600), ("緩曲線", 1200)]
        for i, (text, value) in enumerate(radius_presets):
            btn = ttk.Button(preset_frame, text=text, width=6,
                           command=lambda v=value: self.set_radius(v))
            btn.grid(row=0, column=i, padx=1, sticky="ew")
        
        for i in range(4):
            preset_frame.columnconfigure(i, weight=1)
    
    def create_result_section(self, parent):
        """判定結果セクション"""
        result_group = ttk.LabelFrame(parent, text="📊 判定結果")
        result_group.pack(fill=tk.X, pady=5, padx=5)
        
        inner_frame = ttk.Frame(result_group)
        inner_frame.pack(fill=tk.X, padx=10, pady=10)
        
        self.clearance_rank_label = tk.Label(inner_frame, text="建築限界ランク: E", 
                                           font=self.title_font, fg="green")
        self.clearance_rank_label.pack(pady=2)
        
        self.equipment_status_label = tk.Label(inner_frame, text="設備状態: 限界内", 
                                             font=self.default_font, fg="blue")
        self.equipment_status_label.pack(pady=2)
        
        self.distance_info_label = tk.Label(inner_frame, text="余裕距離: ---", 
                                           font=self.default_font, fg="black")
        self.distance_info_label.pack(pady=2)
    
    def create_stats_section(self, parent):
        """統計情報セクション"""
        stats_group = ttk.LabelFrame(parent, text="📈 詳細情報")
        stats_group.pack(fill=tk.X, pady=5, padx=5)
        
        inner_frame = ttk.Frame(stats_group)
        inner_frame.pack(fill=tk.X, padx=10, pady=10)
        
        self.stats_text = tk.Text(inner_frame, height=6, width=30, 
                                 font=(self.font_family, 9), state=tk.DISABLED,
                                 wrap=tk.WORD)
        self.stats_text.pack(fill=tk.BOTH, expand=True)
    
    def create_button_section(self, parent):
        """操作ボタンセクション"""
        button_frame = ttk.LabelFrame(parent, text="🔧 操作")
        button_frame.pack(fill=tk.X, pady=5, padx=5)
        
        inner_frame = ttk.Frame(button_frame)
        inner_frame.pack(fill=tk.X, padx=10, pady=10)
        
        # 判定開始ボタンを追加
        ttk.Button(inner_frame, text="🔍 判定開始", 
                  command=self.start_evaluation).pack(fill=tk.X, pady=2)
        
        ttk.Button(inner_frame, text="🔄 表示更新", 
                  command=self.update_display).pack(fill=tk.X, pady=2)
        
        ttk.Button(inner_frame, text="🔄 リセット", 
                  command=self.reset_all_values).pack(fill=tk.X, pady=2)
        
        ttk.Button(inner_frame, text="💾 設定保存", 
                  command=self.save_settings).pack(fill=tk.X, pady=2)
    
    def create_graph_panel(self, parent):
        """グラフパネル作成"""
        graph_frame = ttk.LabelFrame(parent, text="🏗️ 建築限界表示")
        graph_frame.pack(side=tk.RIGHT, fill=tk.BOTH, expand=True, padx=(5, 0))
        
        # matplotlib図作成
        self.fig = Figure(figsize=(12, 10), dpi=100)
        self.ax = self.fig.add_subplot(111)
        
        # 基本設定
        self.ax.set_xlabel('レール中心からの距離 (mm)', fontsize=12)
        self.ax.set_ylabel('レールレベルからの高さ (mm)', fontsize=12)
        self.ax.set_title('建築限界断面図（修正版・正確寸法）', fontsize=14, pad=15)
        self.ax.grid(True, alpha=0.3)
        self.ax.set_aspect('equal')
        
        # tkinterに埋め込み
        self.canvas = FigureCanvasTkAgg(self.fig, graph_frame)
        self.canvas.get_tk_widget().pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
    
    def set_equipment_position(self, distance: float, height: float, name: str = None):
        """設備位置プリセット設定"""
        self.equipment_distance_var.set(distance)
        self.equipment_height_var.set(height)
        if name:
            self.equipment_name_var.set(name)
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
    
    def start_evaluation(self):
        """判定開始ボタンの処理"""
        cant_value = self.cant_var.get()
        curve_radius = self.radius_var.get()
        equipment_x = self.equipment_distance_var.get()
        equipment_y = self.equipment_height_var.get()
        equipment_name = self.equipment_name_var.get()
        
        # 判定処理
        transformed_clearance = self.clearance_model.transform_clearance(
            self.base_clearance, cant_value, curve_radius
        )
        
        equipment_in_clearance = self.clearance_model.validate_point_in_clearance(
            equipment_x, equipment_y, transformed_clearance
        )
        
        # 結果をメッセージボックスで表示
        if equipment_in_clearance:
            result_msg = f"✅ 判定結果: 安全\\n\\n設備名: {equipment_name}\\n位置: ({equipment_x:.0f}, {equipment_y:.0f})\\n状態: 建築限界内\\n\\nカント: {cant_value}mm\\n曲線半径: {curve_radius}m"
            messagebox.showinfo("判定結果", result_msg)
        else:
            result_msg = f"❌ 判定結果: 支障\\n\\n設備名: {equipment_name}\\n位置: ({equipment_x:.0f}, {equipment_y:.0f})\\n状態: 建築限界外（支障）\\n\\nカント: {cant_value}mm\\n曲線半径: {curve_radius}m"
            messagebox.showwarning("判定結果", result_msg)
        
        # 表示も更新
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
        cant_value = self.cant_var.get()
        curve_radius = self.radius_var.get()
        equipment_x = self.equipment_distance_var.get()
        equipment_y = self.equipment_height_var.get()
        equipment_name = self.equipment_name_var.get()
        
        # 建築限界を変形
        transformed_clearance = self.clearance_model.transform_clearance(
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
        
        # 設備位置表示（×マーク）
        equipment_color = 'green' if equipment_safe else 'red'
        equipment_marker = 'o' if equipment_safe else 'X'
        marker_size = 15 if equipment_safe else 20
        
        self.ax.scatter([equipment_x], [equipment_y], 
                       color=equipment_color, s=marker_size**2, 
                       marker=equipment_marker, 
                       label=f'{equipment_name}', 
                       edgecolors='black', linewidth=2, zorder=10)
        
        # 設備名ラベル
        label_offset_x = 300 if equipment_x >= 0 else -300
        label_offset_y = 300
        self.ax.annotate(f'{equipment_name}\\n({equipment_x:.0f}, {equipment_y:.0f})', 
                        xy=(equipment_x, equipment_y),
                        xytext=(equipment_x + label_offset_x, equipment_y + label_offset_y),
                        fontsize=10, ha='center',
                        bbox=dict(boxstyle='round,pad=0.4', facecolor='white', alpha=0.9),
                        arrowprops=dict(arrowstyle='->', color='black', alpha=0.8))
        
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
                        fontsize=11, verticalalignment='top',
                        bbox=dict(boxstyle='round', facecolor='lightyellow', alpha=0.9))
        
        # 軸設定
        self.ax.set_xlabel('レール中心からの距離 (mm)', fontsize=12)
        self.ax.set_ylabel('レールレベルからの高さ (mm)', fontsize=12)
        
        title_color = 'red' if not equipment_safe else 'green'
        status_text = '【支障】' if not equipment_safe else '【正常】'
        self.ax.set_title(f'建築限界断面図（修正版） {status_text}', 
                         fontsize=14, pad=15, color=title_color)
        
        self.ax.grid(True, alpha=0.3)
        self.ax.legend(loc='upper right', fontsize=10)
        
        # 範囲設定（修正された寸法に対応）
        margin = 500
        x_min = min(min(x_coords), equipment_x) - margin
        x_max = max(max(x_coords), equipment_x) + margin
        y_min = -200
        y_max = max(max(y_coords), equipment_y, 5700) + margin
        
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
        
        # 余裕距離計算
        if equipment_safe:
            transformed_clearance = self.clearance_model.transform_clearance(
                self.base_clearance, cant_value, curve_radius)
            clearance_width = self.clearance_model._get_clearance_width_at_height(
                equipment_y, transformed_clearance)
            
            if clearance_width and clearance_width > abs(equipment_x):
                margin_distance = clearance_width - abs(equipment_x)
                self.distance_info_label.config(text=f"余裕距離: {margin_distance:.0f}mm", fg="blue")
            else:
                self.distance_info_label.config(text="余裕距離: 計算不可", fg="gray")
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
ランク: {clearance_rank}

【建築限界寸法】
最大高さ: 5700mm
最大幅: ±1900mm
座標点数: {len(self.base_clearance)}点

建築限界シミュレーター
修正版 - 正確寸法対応"""
        
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
            
            with open("clearance_settings.json", 'w', encoding='utf-8') as f:
                json.dump(settings, f, ensure_ascii=False, indent=2)
            
            messagebox.showinfo("保存完了", "設定を保存しました。")
        except Exception as e:
            messagebox.showerror("保存エラー", f"設定保存に失敗しました: {e}")
    
    def run(self):
        """アプリケーション実行"""
        print("🚀 建築限界シミュレーター（修正版）を起動...")
        try:
            self.root.mainloop()
        except KeyboardInterrupt:
            print("\\n👋 アプリケーション終了")
        except Exception as e:
            print(f"❌ 実行エラー: {e}")
            messagebox.showerror("実行エラー", f"アプリケーションエラー: {e}")

def main():
    """メイン関数"""
    print("🏗️ 建築限界シミュレーター（修正版）初期化中...")
    
    try:
        app = CorrectedClearanceApp()
        app.run()
    except Exception as e:
        print(f"❌ 初期化エラー: {e}")
        messagebox.showerror("初期化エラー", f"アプリケーション初期化失敗:\\n{e}")

if __name__ == "__main__":
    main()