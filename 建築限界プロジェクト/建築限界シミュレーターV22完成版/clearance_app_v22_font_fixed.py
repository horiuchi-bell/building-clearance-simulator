#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
建築限界シミュレーター v22 文字化け修正版
V21の曲線拡幅修正を維持し、Matplotlibの文字化けを解消
- Matplotlib日本語フォント設定を追加
- システム環境に応じた適切なフォント選択
- 文字化け完全解消
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
import matplotlib.font_manager as fm

class ClearanceModelV22:
    """建築限界モデル v22 - 文字化け修正版"""
    
    def __init__(self):
        """初期化"""
        self.rail_gauge = 1067  # 軌間 (mm)
        
    def calculate_base_clearance_at_height(self, height: float) -> float:
        """高さに対する基本建築限界離れ"""
        if height < 0:
            return float('inf')
        elif height < 25:
            return 1225
        elif height < 375:
            return 1225 + (height - 25) * (1575 - 1225) / (375 - 25)
        elif height < 920:
            return 1575
        elif height < 3156:
            return 1900
        elif height < 3823:
            discriminant = 2150**2 - (height - 2150)**2
            if discriminant < 0:
                return 0
            return math.sqrt(discriminant)
        elif height < 5190:
            return 1350
        else:
            discriminant = 1800**2 - (height - 4000)**2
            if discriminant < 0:
                return 0
            return math.sqrt(discriminant)
    
    def calculate_cant_correction(self, height: float, cant_mm: float) -> float:
        """カント補正量計算"""
        if cant_mm == 0:
            return 0
        cant_angle = math.atan(cant_mm / self.rail_gauge)
        return height * math.sin(cant_angle)
    
    def calculate_curve_widening(self, curve_radius_m: float) -> float:
        """曲線拡幅量計算"""
        if curve_radius_m == 0:
            return 0
        return 23000.0 / curve_radius_m
    
    def calculate_required_clearance(self, height: float, cant_mm: float = 0, curve_radius_m: float = 0) -> float:
        """必要離れ計算"""
        base_clearance = self.calculate_base_clearance_at_height(height)
        cant_correction = self.calculate_cant_correction(height, cant_mm)
        curve_widening = self.calculate_curve_widening(curve_radius_m)
        required_clearance = base_clearance + cant_correction + curve_widening
        return required_clearance
    
    def create_accurate_clearance(self) -> List[Tuple[float, float]]:
        """建築限界の形状を作成（高精度版）"""
        points = []
        
        # 右側の輪郭を定義
        points.append((1225, 0))      # レールレベルから開始
        points.append((1225, 25))     # 25mmまで
        
        # 25mm→375mmの斜め直線（細かく分割）
        for h in np.linspace(25, 375, 10):
            x = 1225 + (h - 25) * (1575 - 1225) / (375 - 25)
            points.append((x, h))
        
        points.append((1575, 920))    # 920mmまで
        points.append((1900, 920))    # 920mmから最大幅
        points.append((1900, 3156))   # 3156mmまで
        
        # 円弧部分 (3156mm→3823mm) - 超高精度
        for h in np.linspace(3156, 3823, 100):
            discriminant = 2150**2 - (h - 2150)**2
            if discriminant >= 0:
                x = math.sqrt(discriminant)
                points.append((x, h))
        
        # 3823mm以降
        points.append((1350, 3823))
        points.append((1350, 4300))
        
        # 上部円弧（より細かく）
        center_x, center_y, radius = 0, 4000, 1800
        x_boundary = 1350
        
        discriminant = radius**2 - x_boundary**2
        if discriminant >= 0:
            y_intersect = center_y + math.sqrt(discriminant)
            start_angle = math.atan2(y_intersect - center_y, x_boundary - center_x)
            end_angle = math.pi / 2
            
            for i in range(30):
                angle = start_angle + (end_angle - start_angle) * i / 29
                x = center_x + radius * math.cos(angle)
                y = center_y + radius * math.sin(angle)
                
                if abs(x) <= 1350 and y <= 5700 and y >= 4000:
                    points.append((x, y))
        
        # 最上部
        points.append((1350, 5700))
        points.append((-1350, 5700))
        
        # 左側（対称）
        right_points = [(x, y) for x, y in points if x > 0]
        right_points.reverse()
        
        for x, y in right_points[1:-1]:
            points.append((-x, y))
        
        # 形状を閉じる
        points.append((1225, 0))
        
        return points
    
    def transform_clearance_excel_display_method(self, points: List[Tuple[float, float]],
                                               cant_mm: float, curve_radius_m: float, 
                                               measurement_distance: float) -> List[Tuple[float, float]]:
        """
        建築限界変形（Excel表示データ計算シート片線のAA,AB列方式）
        V20修正: Excel座標系(測定点原点) → アプリ座標系(レール中心原点)への変換
        """
        if not points:
            return []
        
        transformed_coords = []
        
        # 拡幅量計算
        if curve_radius_m > 0:
            widening = self.calculate_curve_widening(curve_radius_m)
        else:
            widening = 0
        
        # カント角度計算
        cant_angle = math.atan(cant_mm / self.rail_gauge) if cant_mm != 0 else 0
        
        for x_base, y_base in points:
            # Step 1: 基本建築限界座標 (A,B)
            a_coord = x_base
            b_coord = y_base
            
            # Step 2: 拡幅建築限界座標 (L,M) - 拡幅量を加算
            if a_coord != 0:
                l_coord = a_coord + widening if a_coord > 0 else a_coord - widening
            else:
                l_coord = 0
            m_coord = b_coord
            
            # Step 3: 移動建築限界座標 (O,P) - 測定離れを加算
            o_coord = l_coord + measurement_distance
            p_coord = m_coord
            
            # Step 4: 極座標変換 (R,S,T)
            r_coord = math.sqrt(o_coord**2 + p_coord**2)
            
            # S列: 角度計算
            if o_coord == 0 and p_coord == 0:
                s_coord = 0
            elif o_coord == 0 and p_coord > 0:
                s_coord = math.pi / 2
            elif o_coord == 0 and p_coord < 0:
                s_coord = -math.pi / 2
            else:
                s_coord = math.atan(p_coord / o_coord)
            
            # T列: 象限補正
            if o_coord >= 0 and p_coord >= 0:
                t_coord = s_coord
            elif o_coord < 0 and p_coord >= 0:
                t_coord = s_coord + math.pi
            elif o_coord < 0 and p_coord < 0:
                t_coord = s_coord + math.pi
            else:  # o_coord >= 0 and p_coord < 0
                t_coord = s_coord + 2 * math.pi
            
            # Step 5: カント回転 (W,X)
            w_coord = r_coord  # W列 = R列（距離はそのまま）
            x_coord = t_coord + cant_angle  # X列 = T列 + カント角度
            
            # 2πを超えた場合の処理
            if x_coord >= 2 * math.pi:
                x_coord = x_coord % (2 * math.pi)
            
            # Step 6: 最終座標 (AA,AB) - Excel式: AA=W*COS(X), AB=W*SIN(X)
            excel_aa_coord = w_coord * math.cos(x_coord)
            excel_ab_coord = w_coord * math.sin(x_coord)
            
            # V20新機能: 座標系変換（測定点原点 → レール中心原点）
            app_x_coord = excel_aa_coord - measurement_distance
            app_y_coord = excel_ab_coord
            
            transformed_coords.append((app_x_coord, app_y_coord))
        
        return transformed_coords

class ExcelAccurateCalculatorV22:
    """Excel計算方式の完全再現計算器 V22 - 文字化け修正版"""
    
    def __init__(self):
        """初期化"""
        self.rail_gauge = 1067  # 軌間 (mm)
        # 基本建築限界データは動的に作成（拡幅を考慮するため）
    
    def _create_clearance_data_with_widening(self, curve_radius_m: float) -> List[Tuple[float, float]]:
        """拡幅を考慮した建築限界データ作成（V21新機能）"""
        clearance_data = []
        heights = np.linspace(0, 5700, 1775)
        
        # 拡幅量計算
        if curve_radius_m > 0:
            widening = 23000.0 / curve_radius_m
        else:
            widening = 0
        
        for height in heights:
            if height < 0:
                clearance = float('inf')
            elif height < 25:
                base_clearance = 1225
            elif height < 375:
                base_clearance = 1225 + (height - 25) * (1575 - 1225) / (375 - 25)
            elif height < 920:
                base_clearance = 1575
            elif height < 3156:
                base_clearance = 1900
            elif height < 3823:
                discriminant = 2150**2 - (height - 2150)**2
                if discriminant < 0:
                    base_clearance = 0
                else:
                    base_clearance = math.sqrt(discriminant)
            elif height < 5190:
                base_clearance = 1350
            else:
                discriminant = 1800**2 - (height - 4000)**2
                if discriminant < 0:
                    base_clearance = 0
                else:
                    base_clearance = math.sqrt(discriminant)
            
            # V21新機能: 拡幅を加算
            clearance_with_widening = base_clearance + widening
            clearance_data.append((clearance_with_widening, height))
        
        return clearance_data
    
    def coordinate_transform_to_rail_center(self, measurement_distance: float, measurement_height: float, 
                                          cant_mm: float) -> Tuple[float, float]:
        """測定点座標をレールセンター基準に変換"""
        if cant_mm == 0:
            return measurement_distance, measurement_height
        
        cant_angle = math.atan(cant_mm / self.rail_gauge)
        x_coord = measurement_distance - measurement_height * math.sin(cant_angle)
        y_coord = measurement_height * math.cos(cant_angle)
        
        return x_coord, y_coord
    
    def calculate_required_clearance_excel_method(self, measurement_distance: float, measurement_height: float,
                                                 cant_mm: float, curve_radius_m: float) -> float:
        """Excel D18セルの必要離れ計算完全再現"""
        # 座標変換（ExcelのA8, B8に相当）
        x_coord, y_coord = self.coordinate_transform_to_rail_center(measurement_distance, measurement_height, cant_mm)
        
        # 拡幅量計算
        if curve_radius_m > 0:
            widening = 23000.0 / curve_radius_m
        else:
            widening = 0
        
        # カント補正（元の測定座標を使用）
        if cant_mm == 0:
            cant_correction = 0
        else:
            cant_angle = math.atan(cant_mm / self.rail_gauge)
            cant_correction = measurement_height * math.sin(cant_angle)
        
        # Excelの高さ範囲判定による基本建築限界計算
        yd = y_coord  # B8の値
        
        if yd < 25:
            if yd <= 350:
                base_clearance = 1225 + yd
            else:
                base_clearance = 1225 + 350
        elif yd < 375:
            if yd <= 350:
                base_clearance = 1225 + yd
            else:
                base_clearance = 1225 + 350
        elif yd < 920:
            base_clearance = 1575
        elif yd < 3156:
            base_clearance = 1900
        elif yd < 3823:
            discriminant = 2150**2 - (yd - 2150)**2
            if discriminant < 0:
                base_clearance = 0
            else:
                base_clearance = math.sqrt(discriminant)
        elif yd < 5190:
            base_clearance = 1350
        else:
            discriminant = 1800**2 - (yd - 4000)**2
            if discriminant < 0:
                base_clearance = 0
            else:
                base_clearance = math.sqrt(discriminant)
        
        # 最終的な必要離れ
        required_clearance = base_clearance + widening + cant_correction
        
        return required_clearance
    
    def calculate_ag2_excel_method(self, measurement_distance: float, measurement_height: float,
                                  cant_mm: float, curve_radius_m: float) -> float:
        """Excel AG2セルの計算完全再現（V21: 拡幅考慮版）"""
        rail_x, rail_y = self.coordinate_transform_to_rail_center(measurement_distance, measurement_height, cant_mm)
        
        # V21新機能: 拡幅を考慮した建築限界データを使用
        clearance_data_with_widening = self._create_clearance_data_with_widening(curve_radius_m)
        
        min_distance = float('inf')
        
        for clearance_x, clearance_y in clearance_data_with_widening:
            dx = rail_x - clearance_x
            dy = rail_y - clearance_y
            distance = math.sqrt(dx**2 + dy**2)
            
            if distance < min_distance:
                min_distance = distance
        
        return min_distance
    
    def calculate_clearance_margin_excel_method(self, measurement_distance: float, measurement_height: float,
                                              cant_mm: float, curve_radius_m: float) -> Dict[str, Any]:
        """Excel B24セルの限界余裕計算完全再現（V21: 拡幅考慮版）"""
        ag2 = self.calculate_ag2_excel_method(measurement_distance, measurement_height, cant_mm, curve_radius_m)
        rail_x, rail_y = self.coordinate_transform_to_rail_center(measurement_distance, measurement_height, cant_mm)
        
        if ag2 < 5:
            corrected_margin = 0
            correction_method = "AG2 < 5: 結果 = 0"
        elif ag2 < 13:
            corrected_margin = math.sqrt(ag2**2 - 25)
            correction_method = f"5 ≤ AG2 < 13: 結果 = √({ag2:.1f}² - 25) = {corrected_margin:.1f}"
        else:
            corrected_margin = ag2
            correction_method = f"AG2 ≥ 13: 結果 = AG2 = {ag2:.1f}"
        
        is_inside_clearance = self._is_point_inside_building_clearance(rail_x, rail_y, curve_radius_m)
        is_interference = is_inside_clearance or ag2 < 5 or corrected_margin <= 0
        
        if is_interference:
            final_margin = math.ceil(corrected_margin)
        else:
            final_margin = math.floor(corrected_margin)
        
        return {
            'ag2': ag2,
            'corrected_margin': corrected_margin,
            'final_margin': final_margin,
            'correction_method': correction_method + (" (建築限界内側)" if is_inside_clearance else ""),
            'is_interference': is_interference,
            'rail_center_coords': (rail_x, rail_y),
            'is_inside_clearance': is_inside_clearance
        }
    
    def _is_point_inside_building_clearance(self, x: float, y: float, curve_radius_m: float) -> bool:
        """点が建築限界内側にあるかどうかを判定（V21: 拡幅考慮版）"""
        if y < 0 or y > 5700:
            return False
        
        # V21新機能: 拡幅量を考慮
        if curve_radius_m > 0:
            widening = 23000.0 / curve_radius_m
        else:
            widening = 0
        
        if y < 25:
            clearance_limit = 1225
        elif y < 375:
            clearance_limit = 1225 + (y - 25) * (1575 - 1225) / (375 - 25)
        elif y < 920:
            clearance_limit = 1575
        elif y < 3156:
            clearance_limit = 1900
        elif y < 3823:
            discriminant = 2150**2 - (y - 2150)**2
            if discriminant < 0:
                clearance_limit = 0
            else:
                clearance_limit = math.sqrt(discriminant)
        elif y < 5190:
            clearance_limit = 1350
        else:
            discriminant = 1800**2 - (y - 4000)**2
            if discriminant < 0:
                clearance_limit = 0
            else:
                clearance_limit = math.sqrt(discriminant)
        
        # 拡幅を加算
        clearance_limit_with_widening = clearance_limit + widening
        
        return abs(x) < clearance_limit_with_widening
    
    def calculate_all_excel_method(self, measurement_distance: float, measurement_height: float,
                                  cant_mm: float = 0, curve_radius_m: float = 0) -> Dict[str, Any]:
        """Excel完全再現統合計算"""
        required_clearance = self.calculate_required_clearance_excel_method(
            measurement_distance, measurement_height, cant_mm, curve_radius_m)
        
        margin_result = self.calculate_clearance_margin_excel_method(
            measurement_distance, measurement_height, cant_mm, curve_radius_m)
        
        return {
            'measurement_distance': measurement_distance,
            'measurement_height': measurement_height,
            'cant_mm': cant_mm,
            'curve_radius_m': curve_radius_m,
            'required_clearance': required_clearance,
            'clearance_margin': margin_result['final_margin'],
            'ag2_distance': margin_result['ag2'],
            'is_interference': margin_result['is_interference'],
            'correction_method': margin_result['correction_method'],
            'details': margin_result
        }

class NumericKeypad(tk.Toplevel):
    """テンキーパッド"""
    
    def __init__(self, parent, entry_widget, allow_negative=False):
        super().__init__(parent)
        self.entry_widget = entry_widget
        self.allow_negative = allow_negative
        self.result = None
        
        self.title("数値入力")
        self.geometry("300x400")
        self.transient(parent)
        self.grab_set()
        
        self.geometry("+%d+%d" % (parent.winfo_rootx() + 50, parent.winfo_rooty() + 50))
        
        self.create_widgets()
        
        self.bind('<Escape>', lambda e: self.destroy())
        
        current_value = self.entry_widget.get()
        if current_value and current_value != "0":
            self.display_var.set(current_value)
    
    def create_widgets(self):
        """ウィジェット作成"""
        display_frame = ttk.Frame(self)
        display_frame.pack(fill=tk.X, padx=10, pady=10)
        
        self.display_var = tk.StringVar(value="0")
        display_label = ttk.Label(display_frame, textvariable=self.display_var, 
                                 font=("Arial", 16), background="white", 
                                 relief="sunken", anchor="e")
        display_label.pack(fill=tk.X, ipady=10)
        
        button_frame = ttk.Frame(self)
        button_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        buttons = [
            ('C', 0, 0), ('±', 0, 1) if self.allow_negative else ('', 0, 1), ('⌫', 0, 2),
            ('7', 1, 0), ('8', 1, 1), ('9', 1, 2),
            ('4', 2, 0), ('5', 2, 1), ('6', 2, 2),
            ('1', 3, 0), ('2', 3, 1), ('3', 3, 2),
            ('0', 4, 0), ('.', 4, 1), ('確定', 4, 2)
        ]
        
        for (text, row, col) in buttons:
            if text:
                btn = ttk.Button(button_frame, text=text, 
                               command=lambda t=text: self.button_click(t))
                btn.grid(row=row, column=col, sticky="nsew", padx=2, pady=2)
        
        for i in range(5):
            button_frame.grid_rowconfigure(i, weight=1)
        for i in range(3):
            button_frame.grid_columnconfigure(i, weight=1)
    
    def button_click(self, text):
        """ボタンクリック処理"""
        current = self.display_var.get()
        
        if text == 'C':
            self.display_var.set("0")
        elif text == '⌫':
            if len(current) > 1:
                self.display_var.set(current[:-1])
            else:
                self.display_var.set("0")
        elif text == '±' and self.allow_negative:
            if current != "0":
                if current.startswith('-'):
                    self.display_var.set(current[1:])
                else:
                    self.display_var.set('-' + current)
        elif text == '.':
            if '.' not in current:
                self.display_var.set(current + '.')
        elif text == '確定':
            try:
                value = float(self.display_var.get())
                self.entry_widget.delete(0, tk.END)
                self.entry_widget.insert(0, str(value))
                self.destroy()
            except ValueError:
                messagebox.showerror("エラー", "無効な数値です")
        elif text.isdigit():
            if current == "0":
                self.display_var.set(text)
            else:
                self.display_var.set(current + text)

class ClearanceAppV22UI:
    """建築限界シミュレーターアプリケーション V22 文字化け修正版UI"""
    
    def __init__(self):
        """初期化"""
        self.root = tk.Tk()
        self.root.title("建築限界シミュレーター V22.0 文字化け修正版 - Excel完全準拠")
        
        window_width = 1100
        window_height = 700
        screen_width = self.root.winfo_screenwidth()
        screen_height = self.root.winfo_screenheight()
        x = (screen_width - window_width) // 2
        y = (screen_height - window_height) // 2
        
        self.root.geometry(f"{window_width}x{window_height}+{x}+{y}")
        self.root.minsize(1100, 700)
        
        # V22新機能: 日本語フォント設定
        self.setup_matplotlib_japanese_font()
        
        # 計算エンジン（V22の文字化け修正版）
        self.excel_calculator = ExcelAccurateCalculatorV22()
        
        # 建築限界モデル（V22）
        self.clearance_model = ClearanceModelV22()
        self.base_clearance = self.clearance_model.create_accurate_clearance()
        
        # 計算結果保存用
        self.calculation_result = None
        self.is_calculated = False
        
        # 日本語フォント設定
        self.setup_japanese_font()
        
        # UI構築
        self.create_widgets()
        
        # 初期表示更新
        self.setup_initial_graph()
    
    def setup_matplotlib_japanese_font(self):
        """V22新機能: Matplotlib日本語フォント設定"""
        system = platform.system()
        
        try:
            if system == "Windows":
                # Windows環境での日本語フォント設定
                possible_fonts = ['Yu Gothic', 'Meiryo', 'MS Gothic', 'NotoSansCJK-Regular']
                for font_name in possible_fonts:
                    try:
                        plt.rcParams['font.family'] = font_name
                        # テスト描画で確認
                        fig, ax = plt.subplots()
                        ax.text(0.5, 0.5, 'テスト', fontsize=12)
                        plt.close(fig)
                        print(f"V22: Matplotlibフォント設定成功 - {font_name}")
                        break
                    except:
                        continue
                else:
                    # フォールバック
                    plt.rcParams['font.family'] = 'DejaVu Sans'
                    print("V22: デフォルトフォントを使用")
                    
            elif system == "Darwin":  # macOS
                # macOS環境での日本語フォント設定
                possible_fonts = ['Hiragino Sans', 'Hiragino Kaku Gothic Pro', 'Arial Unicode MS']
                for font_name in possible_fonts:
                    try:
                        plt.rcParams['font.family'] = font_name
                        fig, ax = plt.subplots()
                        ax.text(0.5, 0.5, 'テスト', fontsize=12)
                        plt.close(fig)
                        print(f"V22: Matplotlibフォント設定成功 - {font_name}")
                        break
                    except:
                        continue
                else:
                    plt.rcParams['font.family'] = 'DejaVu Sans'
                    print("V22: デフォルトフォントを使用")
                    
            else:  # Linux/WSL
                # Linux環境での日本語フォント設定
                possible_fonts = ['Noto Sans CJK JP', 'Takao Gothic', 'IPAexGothic', 'DejaVu Sans']
                for font_name in possible_fonts:
                    try:
                        # システムにフォントが存在するかチェック
                        available_fonts = [f.name for f in fm.fontManager.ttflist]
                        if any(font_name in f for f in available_fonts):
                            plt.rcParams['font.family'] = font_name
                            # テスト描画で確認
                            fig, ax = plt.subplots()
                            ax.text(0.5, 0.5, 'テスト', fontsize=12)
                            plt.close(fig)
                            print(f"V22: Matplotlibフォント設定成功 - {font_name}")
                            break
                    except Exception as e:
                        print(f"フォント {font_name} の設定に失敗: {e}")
                        continue
                else:
                    # 最終フォールバック
                    plt.rcParams['font.family'] = 'DejaVu Sans'
                    print("V22: デフォルトフォントを使用")
            
            # 共通設定
            plt.rcParams['font.size'] = 10
            plt.rcParams['axes.unicode_minus'] = False  # マイナス記号文字化け防止
            
        except Exception as e:
            print(f"V22: Matplotlibフォント設定エラー: {e}")
            plt.rcParams['font.family'] = 'DejaVu Sans'
    
    def setup_japanese_font(self):
        """日本語フォント設定"""
        system = platform.system()
        if system == "Windows":
            self.default_font = ("Meiryo UI", 10)
            self.label_font = ("Meiryo UI", 11, "bold")
            self.title_font = ("Meiryo UI", 14, "bold")
        elif system == "Darwin":  # macOS
            self.default_font = ("Hiragino Sans", 12)
            self.label_font = ("Hiragino Sans", 13, "bold")
            self.title_font = ("Hiragino Sans", 16, "bold")
        else:  # Linux/その他
            self.default_font = ("Noto Sans CJK JP", 10)
            self.label_font = ("Noto Sans CJK JP", 11, "bold")
            self.title_font = ("Noto Sans CJK JP", 14, "bold")
        
        self.root.option_add("*Font", self.default_font)
    
    def create_widgets(self):
        """ウィジェット作成"""
        main_container = ttk.Frame(self.root)
        main_container.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        self.create_input_panel(main_container)
        self.create_display_area(main_container)
    
    def create_input_panel(self, parent):
        """入力パネル作成"""
        input_frame = ttk.LabelFrame(parent, text="測定パラメータ入力", padding="20")
        input_frame.pack(side=tk.LEFT, fill=tk.Y, padx=(0, 10))
        
        # 測定離れ
        ttk.Label(input_frame, text="測定離れ (mm):", font=self.label_font).grid(row=0, column=0, sticky=tk.W, pady=10)
        self.distance_var = tk.StringVar(value="0")
        self.distance_entry = ttk.Entry(input_frame, textvariable=self.distance_var, width=15, font=self.default_font)
        self.distance_entry.grid(row=0, column=1, pady=10)
        
        distance_keypad_btn = ttk.Button(input_frame, text="📱", width=3,
                                        command=lambda: self.open_keypad(self.distance_entry, True))
        distance_keypad_btn.grid(row=0, column=2, padx=5)
        
        ttk.Label(input_frame, text="(正: 左側, 負: 右側)", font=("", 9)).grid(row=1, column=0, columnspan=3, pady=(0, 10))
        
        # 測定高さ
        ttk.Label(input_frame, text="測定高さ (mm):", font=self.label_font).grid(row=2, column=0, sticky=tk.W, pady=10)
        self.height_var = tk.StringVar(value="0")
        self.height_entry = ttk.Entry(input_frame, textvariable=self.height_var, width=15, font=self.default_font)
        self.height_entry.grid(row=2, column=1, pady=10)
        
        height_keypad_btn = ttk.Button(input_frame, text="📱", width=3, 
                                      command=lambda: self.open_keypad(self.height_entry, False))
        height_keypad_btn.grid(row=2, column=2, padx=5)
        
        # カント
        ttk.Label(input_frame, text="カント (mm):", font=self.label_font).grid(row=3, column=0, sticky=tk.W, pady=10)
        self.cant_var = tk.StringVar(value="0")
        self.cant_entry = ttk.Entry(input_frame, textvariable=self.cant_var, width=15, font=self.default_font)
        self.cant_entry.grid(row=3, column=1, pady=10)
        
        cant_keypad_btn = ttk.Button(input_frame, text="📱", width=3,
                                     command=lambda: self.open_keypad(self.cant_entry, False))
        cant_keypad_btn.grid(row=3, column=2, padx=5)
        
        # 曲線半径
        ttk.Label(input_frame, text="曲線半径 (m):", font=self.label_font).grid(row=4, column=0, sticky=tk.W, pady=10)
        self.radius_var = tk.StringVar(value="0")
        self.radius_entry = ttk.Entry(input_frame, textvariable=self.radius_var, width=15, font=self.default_font)
        self.radius_entry.grid(row=4, column=1, pady=10)
        
        radius_keypad_btn = ttk.Button(input_frame, text="📱", width=3,
                                      command=lambda: self.open_keypad(self.radius_entry, False))
        radius_keypad_btn.grid(row=4, column=2, padx=5)
        
        ttk.Label(input_frame, text="(0 = 直線)", font=("", 9)).grid(row=5, column=0, columnspan=3, pady=(0, 10))
        
        # ボタンフレーム
        button_frame = ttk.Frame(input_frame)
        button_frame.grid(row=6, column=0, columnspan=3, pady=20)
        
        # 測定開始ボタン
        self.calc_button = ttk.Button(button_frame, text="測定開始", command=self.calculate,
                                     style="Primary.TButton")
        self.calc_button.pack(side=tk.LEFT, padx=5)
        
        # リセットボタン
        self.reset_button = ttk.Button(button_frame, text="リセット", command=self.reset_values)
        self.reset_button.pack(side=tk.LEFT, padx=5)
        
        # 結果表示エリア
        result_frame = ttk.LabelFrame(input_frame, text="判定結果", padding="10")
        result_frame.grid(row=7, column=0, columnspan=3, sticky=(tk.W, tk.E), pady=20)
        
        self.result_text = tk.Text(result_frame, height=12, width=40, font=self.default_font)
        self.result_text.pack(fill=tk.BOTH, expand=True)
        
        # スタイル設定
        style = ttk.Style()
        style.configure("Primary.TButton", font=self.label_font)
    
    def create_display_area(self, parent):
        """表示エリア作成"""
        display_frame = ttk.Frame(parent)
        display_frame.pack(side=tk.RIGHT, fill=tk.BOTH, expand=True)
        
        # タイトル
        title_label = ttk.Label(display_frame, text="建築限界モデル（V22 文字化け修正版）", font=self.title_font)
        title_label.pack(pady=(0, 10))
        
        # Matplotlibフィギュア
        self.figure = Figure(figsize=(8, 6), dpi=100)
        self.ax = self.figure.add_subplot(111)
        
        # キャンバス
        self.canvas = FigureCanvasTkAgg(self.figure, display_frame)
        self.canvas.draw()
        self.canvas.get_tk_widget().pack(side=tk.TOP, fill=tk.BOTH, expand=True)
    
    def setup_initial_graph(self):
        """初期グラフ設定（V22: 日本語表示対応）"""
        self.ax.clear()
        
        # 基本建築限界表示
        clearance_coords = np.array(self.base_clearance)
        x_coords = clearance_coords[:, 0]
        y_coords = clearance_coords[:, 1]
        
        self.ax.fill(x_coords, y_coords, color='lightblue', alpha=0.3, label='建築限界')
        self.ax.plot(x_coords, y_coords, 'b-', linewidth=2)
        
        # レール表示
        rail_width = 100
        self.ax.fill_between([-rail_width/2, rail_width/2], [0, 0], [50, 50], 
                           color='brown', alpha=0.7, label='レール')
        
        # グリッドと軸設定（V22: 日本語表示）
        self.ax.grid(True, alpha=0.3)
        self.ax.set_xlabel('距離 (mm)', fontsize=12)
        self.ax.set_ylabel('高さ (mm)', fontsize=12)
        self.ax.set_title('建築限界シミュレーション v22.0 文字化け修正版', fontsize=14)
        self.ax.set_xlim(-3000, 3000)
        self.ax.set_ylim(-500, 6000)
        self.ax.legend(loc='upper right')
        
        self.canvas.draw()
    
    def open_keypad(self, entry_widget, allow_negative):
        """テンキーパッド開く"""
        NumericKeypad(self.root, entry_widget, allow_negative)
    
    def calculate(self):
        """計算実行（V22の文字化け修正版を使用）"""
        try:
            height = float(self.height_var.get())
            distance = float(self.distance_var.get())
            cant = float(self.cant_var.get())
            radius = float(self.radius_var.get())
            
            # Excel計算方式で結果取得
            result = self.excel_calculator.calculate_all_excel_method(
                abs(distance), height, cant, radius
            )
            
            self.calculation_result = result
            self.is_calculated = True
            
            # V11スタイルの表示更新
            self.update_display()
            self.display_results()
            
        except ValueError as e:
            messagebox.showerror("入力エラー", "正しい数値を入力してください。")
            self.is_calculated = False
    
    def display_results(self):
        """結果表示（V11の優れた表示方式を採用）"""
        if not self.calculation_result:
            return
        
        result = self.calculation_result
        self.result_text.delete(1.0, tk.END)
        
        # 判定結果を最初に大きく表示（V11方式）
        if result['is_interference']:
            judgment_text = "❌ 建築限界抵触\n"
            judgment_tag = "interference_big"
        else:
            judgment_text = "✅ 建築限界適合\n"
            judgment_tag = "safe_big"
        
        self.result_text.insert(tk.END, "【判定結果】\n")
        self.result_text.insert(tk.END, judgment_text)
        self.result_text.insert(tk.END, "\n")
        
        # 重要な数値を目立つように表示（V11方式）
        self.result_text.insert(tk.END, "【重要な数値】\n")
        self.result_text.insert(tk.END, f"必要離れ: {result['required_clearance']:.0f} mm\n")
        
        # 支障時は限界支障量、適合時は限界余裕を表示（V11方式）
        if result['is_interference']:
            self.result_text.insert(tk.END, f"限界支障量: {result['clearance_margin']:.0f} mm\n")
        else:
            self.result_text.insert(tk.END, f"限界余裕: {result['clearance_margin']:.0f} mm\n")
        
        # V21追加: 曲線半径が設定されている場合の情報表示
        if result['curve_radius_m'] > 0:
            widening = 23000.0 / result['curve_radius_m']
            self.result_text.insert(tk.END, f"\n【曲線情報】\n")
            self.result_text.insert(tk.END, f"曲線半径: {result['curve_radius_m']:.0f} m\n")
            self.result_text.insert(tk.END, f"拡幅量: {widening:.1f} mm\n")
        
        # スタイル設定（V11方式）
        if result['is_interference']:
            # 抵触時は赤色で強調
            self.result_text.tag_add("interference_big", "2.0", "2.end")
            self.result_text.tag_config("interference_big", foreground="red", 
                                      font=(self.default_font[0], self.default_font[1] + 4, "bold"))
            # 重要数値も赤色
            self.result_text.tag_add("numbers_red", "5.0", "8.end")
            self.result_text.tag_config("numbers_red", foreground="red", 
                                      font=(self.default_font[0], self.default_font[1] + 1, "bold"))
        else:
            # 適合時は緑色で強調
            self.result_text.tag_add("safe_big", "2.0", "2.end")
            self.result_text.tag_config("safe_big", foreground="green", 
                                      font=(self.default_font[0], self.default_font[1] + 4, "bold"))
            # 重要数値も緑色
            self.result_text.tag_add("numbers_green", "5.0", "8.end")
            self.result_text.tag_config("numbers_green", foreground="green", 
                                      font=(self.default_font[0], self.default_font[1] + 1, "bold"))
    
    def update_display(self):
        """表示更新（V22: 日本語文字化け修正版）"""
        if not self.is_calculated:
            return
        
        result = self.calculation_result
        
        # 現在の値を取得
        cant = result['cant_mm']
        radius = result['curve_radius_m'] 
        distance = result['measurement_distance']
        height = result['measurement_height']
        
        self.ax.clear()
        
        # レール表示（V11方式）
        rail_gauge = self.clearance_model.rail_gauge
        self.ax.plot([-rail_gauge/2, rail_gauge/2], [0, 0], 
                    'k-', linewidth=4, label='レール')
        
        # 変形後建築限界表示（V21: 曲線拡幅を含む座標変換）
        # 入力された測定離れの符号で実際の測定離れを決定
        actual_measurement_distance = float(self.distance_var.get())  # 符号付きの値
        
        transformed_clearance = self.clearance_model.transform_clearance_excel_display_method(
            self.base_clearance, cant, radius, actual_measurement_distance
        )
        
        if transformed_clearance:
            coords = np.array(transformed_clearance)
            x_coords = coords[:, 0]
            y_coords = coords[:, 1]
            
            # 建築限界の色設定（V11方式）
            if result['is_interference']:
                color = 'red'
                if radius > 0:
                    label = f'建築限界（支障・R{radius:.0f}m）'
                else:
                    label = '建築限界（支障）'
            else:
                color = 'blue'
                if radius > 0:
                    label = f'建築限界（安全・R{radius:.0f}m）'
                else:
                    label = '建築限界（安全）'
            
            # 建築限界塗りつぶしと輪郭
            self.ax.fill(x_coords, y_coords, alpha=0.3, color=color)
            self.ax.plot(x_coords, y_coords, color=color, linewidth=2, label=label)
        
        # 測定点表示（V21: 入力値通りの固定位置）
        if distance > 0:
            display_measurement_x = -abs(distance)  # 正の値は左側（負の座標）
        else:
            display_measurement_x = abs(distance)   # 負の値は右側（正の座標）
        display_measurement_y = height
        
        self.ax.plot(display_measurement_x, display_measurement_y, 'ro', markersize=6, label='測定点')
        
        # 最短距離線表示（V21: 拡幅考慮版）
        if transformed_clearance:
            # レールセンター基準の測定点座標（計算用）
            rail_x, rail_y = self.excel_calculator.coordinate_transform_to_rail_center(
                abs(distance), height, cant
            )
            
            # 表示用に符号調整
            if distance > 0:
                rail_x = -abs(rail_x)
            
            min_distance = float('inf')
            closest_point = None
            
            for clearance_x, clearance_y in transformed_clearance:
                dx = rail_x - clearance_x
                dy = rail_y - clearance_y
                distance_to_point = math.sqrt(dx**2 + dy**2)
                
                if distance_to_point < min_distance:
                    min_distance = distance_to_point
                    closest_point = (clearance_x, clearance_y)
            
            # 最短距離線を緑の点線で表示
            if closest_point:
                if result['is_interference']:
                    label_text = f'限界支障量: {result["clearance_margin"]}mm'
                else:
                    label_text = f'限界余裕: {result["clearance_margin"]}mm'
                
                self.ax.plot([display_measurement_x, closest_point[0]], 
                           [display_measurement_y, closest_point[1]], 
                           'g--', linewidth=2, label=label_text)
                # 最近点をマーク（小さく）
                self.ax.plot(closest_point[0], closest_point[1], 'go', markersize=4)
        
        # グラフ設定（V22: 日本語表示対応）
        self.ax.grid(True, alpha=0.3)
        self.ax.set_xlabel('離れ (mm)', fontsize=12)
        self.ax.set_ylabel('高さ (mm)', fontsize=12)
        self.ax.set_title('建築限界シミュレーション v22.0 文字化け修正版', fontsize=14)
        
        # 表示範囲
        try:
            distance_value = abs(distance)
            x_max = max(3000, distance_value + 1000)
        except:
            x_max = 3000
        self.ax.set_xlim(-x_max, x_max)
        self.ax.set_ylim(-500, 6000)
        
        # 凡例（V22: 日本語表示）
        self.ax.legend(loc='upper right')
        
        # 描画更新
        self.canvas.draw()
    
    def reset_values(self):
        """値リセット（V11方式）"""
        self.distance_var.set("0")
        self.height_var.set("0")
        self.cant_var.set("0")
        self.radius_var.set("0")
        self.result_text.delete(1.0, tk.END)
        self.calculation_result = None
        self.is_calculated = False
        self.setup_initial_graph()
    
    def run(self):
        """アプリケーション実行"""
        self.root.mainloop()

def main():
    """メイン処理"""
    app = ClearanceAppV22UI()
    app.run()

if __name__ == "__main__":
    main()