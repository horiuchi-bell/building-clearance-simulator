#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
建築限界ビューワー - メインアプリケーション
カント・曲線半径に応じた建築限界モデルの視覚的表示
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

class BuildingClearanceViewer:
    def __init__(self):
        """建築限界ビューワーの初期化"""
        self.root = tk.Tk()
        self.root.title("建築限界シミュレーター")
        self.root.geometry("1200x800")
        
        # 日本語フォント設定
        self.setup_japanese_font()
        
        # データの初期化
        self.clearance_data = None
        self.base_coordinates = []
        self.current_coordinates = []
        
        # UI要素の初期化
        self.cant_var = tk.DoubleVar(value=0.0)
        self.radius_var = tk.DoubleVar(value=0.0)
        self.rank_var = tk.StringVar(value="E")
        
        # データの読み込み
        self.load_clearance_data()
        
        # UIの構築
        self.create_widgets()
        
        # 初期表示
        self.update_display()
    
    def setup_japanese_font(self):
        """日本語フォントの設定"""
        system = platform.system()
        
        if system == "Windows":
            self.default_font = ("Meiryo UI", 9)
            self.title_font = ("Meiryo UI", 12, "bold")
        elif system == "Darwin":  # macOS
            self.default_font = ("Hiragino Sans", 12)
            self.title_font = ("Hiragino Sans", 14, "bold")
        else:  # Linux/WSL
            # 利用可能な日本語フォントを検出
            japanese_fonts = ["Noto Sans CJK JP", "Takao Gothic", "IPAexGothic", "DejaVu Sans"]
            self.default_font = None
            
            for font_name in japanese_fonts:
                try:
                    test_font = tkFont.Font(family=font_name, size=10)
                    # フォントが実際に利用可能かテスト
                    self.default_font = (font_name, 10)
                    self.title_font = (font_name, 12, "bold")
                    print(f"✅ 日本語フォント設定: {font_name}")
                    break
                except:
                    continue
            
            if not self.default_font:
                # フォールバック
                self.default_font = ("Arial", 10)
                self.title_font = ("Arial", 12, "bold")
                print("⚠️ 日本語フォントが見つかりません。デフォルトフォントを使用します。")
        
        # matplotlibの日本語フォント設定
        self.setup_matplotlib_japanese_font()
    
    def setup_matplotlib_japanese_font(self):
        """matplotlibの日本語フォント設定"""
        try:
            # システムに応じた日本語フォント設定
            if platform.system() == "Windows":
                plt.rcParams['font.family'] = 'Meiryo'
            elif platform.system() == "Darwin":
                plt.rcParams['font.family'] = 'Hiragino Sans'
            else:  # Linux/WSL
                # 利用可能なフォントを試行
                japanese_matplotlib_fonts = ['Noto Sans CJK JP', 'Takao Gothic', 'IPAexGothic']
                for font in japanese_matplotlib_fonts:
                    try:
                        plt.rcParams['font.family'] = font
                        break
                    except:
                        continue
                else:
                    plt.rcParams['font.family'] = 'DejaVu Sans'
            
            plt.rcParams['axes.unicode_minus'] = False  # マイナス記号の文字化け対策
            print("✅ matplotlib日本語フォント設定完了")
            
        except Exception as e:
            print(f"⚠️ matplotlibフォント設定エラー: {e}")
    
    def load_clearance_data(self):
        """建築限界データの読み込み"""
        try:
            with open("building_clearance_data.json", 'r', encoding='utf-8') as f:
                self.clearance_data = json.load(f)
            
            self.base_coordinates = self.clearance_data.get("base_shape", [])
            print(f"✅ 建築限界データ読み込み完了: {len(self.base_coordinates)}点")
            
        except FileNotFoundError:
            messagebox.showerror("エラー", "建築限界データファイルが見つかりません。\\nbuilding_clearance_extractor.pyを先に実行してください。")
            self.base_coordinates = self.generate_sample_clearance()
        except Exception as e:
            messagebox.showerror("エラー", f"データ読み込みエラー: {e}")
            self.base_coordinates = self.generate_sample_clearance()
    
    def generate_sample_clearance(self) -> List[Tuple[float, float]]:
        """サンプルの建築限界データを生成"""
        print("📝 サンプル建築限界データを生成中...")
        
        # 標準的な建築限界形状を模擬
        points = []
        
        # 下部（レール面付近）
        points.extend([(-1372, 0), (-1372, 200), (-1067, 400)])
        
        # 側面（車両側面）
        for y in range(400, 3200, 100):
            points.append((-1067, y))
        
        # 上部（架線関連）
        points.extend([(-1067, 3200), (-500, 3800), (500, 3800), (1067, 3200)])
        
        # 反対側（対称）
        for y in range(3200, 400, -100):
            points.append((1067, y))
        
        points.extend([(1067, 400), (1372, 200), (1372, 0)])
        
        return points
    
    def create_widgets(self):
        """UIウィジェットの作成"""
        # メインフレーム
        main_frame = ttk.Frame(self.root)
        main_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        # 左パネル（入力コントロール）
        self.create_control_panel(main_frame)
        
        # 右パネル（グラフ表示）
        self.create_graph_panel(main_frame)
    
    def create_control_panel(self, parent):
        """入力コントロールパネルの作成"""
        control_frame = ttk.LabelFrame(parent, text="入力パラメータ", padding=15)
        control_frame.pack(side=tk.LEFT, fill=tk.Y, padx=(0, 10))
        
        # タイトル
        title_label = tk.Label(control_frame, text="建築限界シミュレーター", 
                              font=self.title_font, fg="blue")
        title_label.pack(pady=(0, 20))
        
        # カント入力
        cant_frame = ttk.Frame(control_frame)
        cant_frame.pack(fill=tk.X, pady=10)
        
        ttk.Label(cant_frame, text="カント値 (mm):", font=self.default_font).pack(anchor=tk.W)
        cant_spinbox = ttk.Spinbox(cant_frame, from_=-200, to=200, increment=10, 
                                  textvariable=self.cant_var, width=10, 
                                  command=self.on_parameter_change)
        cant_spinbox.pack(fill=tk.X, pady=5)
        
        # カント値のプリセット
        cant_preset_frame = ttk.Frame(control_frame)
        cant_preset_frame.pack(fill=tk.X, pady=5)
        
        ttk.Label(cant_preset_frame, text="プリセット:", font=self.default_font).pack(anchor=tk.W)
        cant_buttons = [
            ("傾きなし", 0),
            ("標準カント", 100),
            ("高速カント", 140),
            ("逆カント", -80)
        ]
        
        for text, value in cant_buttons:
            btn = ttk.Button(cant_preset_frame, text=text, 
                           command=lambda v=value: self.set_cant_value(v))
            btn.pack(side=tk.LEFT, padx=2, pady=2)
        
        # 曲線半径入力
        radius_frame = ttk.Frame(control_frame)
        radius_frame.pack(fill=tk.X, pady=10)
        
        ttk.Label(radius_frame, text="曲線半径 (m):", font=self.default_font).pack(anchor=tk.W)
        radius_spinbox = ttk.Spinbox(radius_frame, from_=0, to=2000, increment=50,
                                    textvariable=self.radius_var, width=10,
                                    command=self.on_parameter_change)
        radius_spinbox.pack(fill=tk.X, pady=5)
        
        # 曲線半径のプリセット
        radius_preset_frame = ttk.Frame(control_frame)
        radius_preset_frame.pack(fill=tk.X, pady=5)
        
        ttk.Label(radius_preset_frame, text="プリセット:", font=self.default_font).pack(anchor=tk.W)
        radius_buttons = [
            ("直線", 0),
            ("急曲線", 300),
            ("標準曲線", 600),
            ("緩曲線", 1200)
        ]\n        \n        for text, value in radius_buttons:\n            btn = ttk.Button(radius_preset_frame, text=text,\n                           command=lambda v=value: self.set_radius_value(v))\n            btn.pack(side=tk.LEFT, padx=2, pady=2)\n        \n        # ランク表示\n        rank_frame = ttk.LabelFrame(control_frame, text=\"判定結果\", padding=10)\n        rank_frame.pack(fill=tk.X, pady=20)\n        \n        self.rank_label = tk.Label(rank_frame, text=\"ランク: E\", \n                                  font=self.title_font, fg=\"green\")\n        self.rank_label.pack()\n        \n        self.status_label = tk.Label(rank_frame, text=\"状態: 正常\", \n                                    font=self.default_font, fg=\"blue\")\n        self.status_label.pack()\n        \n        # 統計情報\n        stats_frame = ttk.LabelFrame(control_frame, text=\"統計情報\", padding=10)\n        stats_frame.pack(fill=tk.X, pady=10)\n        \n        self.stats_label = tk.Label(stats_frame, text=\"座標点数: 0\", \n                                   font=self.default_font, justify=tk.LEFT)\n        self.stats_label.pack(anchor=tk.W)\n        \n        # 更新ボタン\n        update_btn = ttk.Button(control_frame, text=\"表示更新\", \n                               command=self.update_display)\n        update_btn.pack(pady=20)\n        \n        # リセットボタン\n        reset_btn = ttk.Button(control_frame, text=\"初期値に戻す\", \n                              command=self.reset_parameters)\n        reset_btn.pack(pady=5)\n    \n    def create_graph_panel(self, parent):\n        \"\"\"グラフ表示パネルの作成\"\"\"\n        graph_frame = ttk.LabelFrame(parent, text=\"建築限界表示\", padding=10)\n        graph_frame.pack(side=tk.RIGHT, fill=tk.BOTH, expand=True)\n        \n        # matplotlibの図を作成\n        self.fig = Figure(figsize=(10, 8), dpi=100)\n        self.ax = self.fig.add_subplot(111)\n        \n        # グラフの基本設定\n        self.ax.set_xlabel('水平距離 (mm)', fontsize=10)\n        self.ax.set_ylabel('高さ (mm)', fontsize=10)\n        self.ax.set_title('建築限界断面図（在来・一般・片線用）', fontsize=12, pad=20)\n        self.ax.grid(True, alpha=0.3)\n        self.ax.set_aspect('equal')\n        \n        # グラフをtkinterに埋め込み\n        self.canvas = FigureCanvasTkAgg(self.fig, graph_frame)\n        self.canvas.get_tk_widget().pack(fill=tk.BOTH, expand=True)\n    \n    def set_cant_value(self, value):\n        \"\"\"カント値のプリセット設定\"\"\"\n        self.cant_var.set(value)\n        self.on_parameter_change()\n    \n    def set_radius_value(self, value):\n        \"\"\"曲線半径のプリセット設定\"\"\"\n        self.radius_var.set(value)\n        self.on_parameter_change()\n    \n    def reset_parameters(self):\n        \"\"\"パラメータを初期値にリセット\"\"\"\n        self.cant_var.set(0.0)\n        self.radius_var.set(0.0)\n        self.update_display()\n    \n    def on_parameter_change(self):\n        \"\"\"パラメータ変更時のイベント処理\"\"\"\n        # 少し遅延を入れて連続的な更新を抑制\n        if hasattr(self, 'update_timer'):\n            self.root.after_cancel(self.update_timer)\n        self.update_timer = self.root.after(300, self.update_display)\n    \n    def transform_coordinates(self, coordinates: List[Tuple[float, float]], \n                            cant_value: float, curve_radius: float) -> List[Tuple[float, float]]:\n        \"\"\"座標変換（カント・曲線半径適用）\"\"\"\n        if not coordinates:\n            return []\n        \n        coords = np.array(coordinates)\n        \n        # カント変換\n        if cant_value != 0:\n            gauge = 1067  # 軌間(mm)\n            angle_rad = np.arctan(cant_value / gauge)\n            \n            # 回転行列\n            cos_angle = np.cos(angle_rad)\n            sin_angle = np.sin(angle_rad)\n            \n            rotation_matrix = np.array([\n                [cos_angle, -sin_angle],\n                [sin_angle, cos_angle]\n            ])\n            \n            # 座標変換\n            coords = coords @ rotation_matrix.T\n        \n        # 曲線拡幅（簡略化）\n        if curve_radius > 0 and curve_radius < 2000:\n            widening_factor = max(0, 1000.0 / curve_radius)\n            coords[:, 0] = coords[:, 0] + np.sign(coords[:, 0]) * widening_factor\n        \n        return coords.tolist()\n    \n    def determine_rank_and_status(self, cant_value: float, curve_radius: float) -> Tuple[str, str, str]:\n        \"\"\"ランク・状態判定\"\"\"\n        abs_cant = abs(cant_value)\n        \n        if abs_cant > 150:\n            return \"A\", \"支障\", \"red\"\n        elif abs_cant > 100:\n            return \"B\", \"支障\", \"red\"\n        elif abs_cant > 50:\n            return \"D\", \"正常\", \"orange\"\n        elif abs_cant > 0:\n            return \"E\", \"正常\", \"green\"\n        else:\n            return \"E\", \"正常\", \"green\"\n    \n    def update_display(self):\n        \"\"\"表示の更新\"\"\"\n        cant_value = self.cant_var.get()\n        curve_radius = self.radius_var.get()\n        \n        # 座標変換\n        transformed_coords = self.transform_coordinates(\n            self.base_coordinates, cant_value, curve_radius\n        )\n        \n        # ランク判定\n        rank, status, color = self.determine_rank_and_status(cant_value, curve_radius)\n        \n        # グラフ更新\n        self.update_graph(transformed_coords, cant_value, curve_radius)\n        \n        # UI更新\n        self.rank_label.config(text=f\"ランク: {rank}\", fg=color)\n        self.status_label.config(text=f\"状態: {status}\", fg=color)\n        self.stats_label.config(text=f\"座標点数: {len(transformed_coords)}\\n\"\n                                    f\"カント: {cant_value}mm\\n\"\n                                    f\"曲線半径: {curve_radius}m\")\n    \n    def update_graph(self, coordinates: List[Tuple[float, float]], \n                    cant_value: float, curve_radius: float):\n        \"\"\"グラフの更新\"\"\"\n        self.ax.clear()\n        \n        if not coordinates:\n            self.ax.text(0, 0, 'データなし', ha='center', va='center', fontsize=14)\n            self.canvas.draw()\n            return\n        \n        # 座標を配列に変換\n        coords = np.array(coordinates)\n        x_coords = coords[:, 0]\n        y_coords = coords[:, 1]\n        \n        # 建築限界を描画\n        self.ax.plot(x_coords, y_coords, 'b-', linewidth=2, label='建築限界')\n        self.ax.fill(x_coords, y_coords, color='lightblue', alpha=0.3)\n        \n        # レール位置を示すライン\n        self.ax.axhline(y=0, color='black', linewidth=3, alpha=0.7, label='レール面')\n        self.ax.axvline(x=-533.5, color='red', linewidth=2, linestyle='--', alpha=0.5, label='レール中心')\n        self.ax.axvline(x=533.5, color='red', linewidth=2, linestyle='--', alpha=0.5)\n        \n        # カント傾斜の視覚化\n        if cant_value != 0:\n            gauge = 1067\n            angle_deg = np.degrees(np.arctan(cant_value / gauge))\n            self.ax.text(0, -300, f'カント: {cant_value}mm\\n傾斜角: {angle_deg:.2f}°', \n                        ha='center', va='top', fontsize=10, \n                        bbox=dict(boxstyle='round', facecolor='wheat', alpha=0.8))\n        \n        # 曲線半径の表示\n        if curve_radius > 0:\n            self.ax.text(1000, 4000, f'曲線半径: {curve_radius}m', \n                        ha='left', va='top', fontsize=10,\n                        bbox=dict(boxstyle='round', facecolor='lightgreen', alpha=0.8))\n        \n        # グラフの設定\n        self.ax.set_xlabel('水平距離 (mm)', fontsize=10)\n        self.ax.set_ylabel('高さ (mm)', fontsize=10)\n        self.ax.set_title(f'建築限界断面図（カント: {cant_value}mm, 曲線半径: {curve_radius}m）', \n                         fontsize=12, pad=20)\n        self.ax.grid(True, alpha=0.3)\n        self.ax.legend(loc='upper right')\n        \n        # 軸の範囲設定\n        margin = 500\n        if coordinates:\n            x_min, x_max = min(x_coords) - margin, max(x_coords) + margin\n            y_min, y_max = min(y_coords) - margin, max(y_coords) + margin\n            self.ax.set_xlim(x_min, x_max)\n            self.ax.set_ylim(y_min, y_max)\n        \n        self.ax.set_aspect('equal')\n        self.canvas.draw()\n    \n    def run(self):\n        \"\"\"アプリケーション実行\"\"\"\n        print(\"🚀 建築限界ビューワーを起動...\")\n        try:\n            self.root.mainloop()\n        except KeyboardInterrupt:\n            print(\"\\n👋 アプリケーションを終了します\")\n        except Exception as e:\n            print(f\"❌ エラーが発生しました: {e}\")\n            messagebox.showerror(\"エラー\", f\"アプリケーションエラー: {e}\")\n\ndef main():\n    \"\"\"メイン実行関数\"\"\"\n    print(\"🏗️ 建築限界ビューワーを初期化中...\")\n    \n    try:\n        app = BuildingClearanceViewer()\n        app.run()\n    except Exception as e:\n        print(f\"❌ 初期化エラー: {e}\")\n        messagebox.showerror(\"初期化エラー\", f\"アプリケーションの初期化に失敗しました: {e}\")\n\nif __name__ == \"__main__\":\n    main()