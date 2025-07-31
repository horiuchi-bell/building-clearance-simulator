#!/usr/bin/env python3
"""
Claude Code 通知システム
WSL環境からWindowsのポップアップ通知を送信
"""
import json
import os
import sys
import subprocess
import time
from pathlib import Path

class ClaudeNotificationSystem:
    def __init__(self, config_path="/home/tems_kaihatu/github_config.json"):
        self.config_path = config_path
        self.config = self.load_config()
        
    def load_config(self):
        """設定ファイルを読み込み"""
        try:
            with open(self.config_path, 'r', encoding='utf-8') as f:
                return json.load(f)
        except FileNotFoundError:
            return {"notifications": {"enabled": True, "popup_notifications": True}}
    
    def is_notifications_enabled(self):
        """通知が有効かチェック"""
        return self.config.get("notifications", {}).get("enabled", True)
    
    def is_popup_enabled(self):
        """ポップアップ通知が有効かチェック"""
        return self.config.get("notifications", {}).get("popup_notifications", True)
    
    def send_windows_notification(self, title, message, duration=30):
        """CLIコンソール位置にポップアップを表示"""        
        try:
            # CLIコンソールの位置を取得してその中央に表示
            ps_script = f'''
Add-Type -AssemblyName System.Windows.Forms
Add-Type -AssemblyName System.Drawing

# アクティブなコンソールウィンドウを検索
Add-Type @"
    using System;
    using System.Runtime.InteropServices;
    public class Win32 {{
        [DllImport("kernel32.dll")]
        public static extern IntPtr GetConsoleWindow();
        [DllImport("user32.dll")]
        public static extern bool GetWindowRect(IntPtr hwnd, out RECT lpRect);
        [DllImport("user32.dll")]
        public static extern IntPtr GetForegroundWindow();
    }}
    public struct RECT {{
        public int Left;
        public int Top; 
        public int Right;
        public int Bottom;
    }}
"@

$consoleWindow = [Win32]::GetConsoleWindow()
$rect = New-Object RECT

if ($consoleWindow -ne [IntPtr]::Zero -and [Win32]::GetWindowRect($consoleWindow, [ref]$rect)) {{
    $centerX = ($rect.Left + $rect.Right) / 2 - 175
    $centerY = ($rect.Top + $rect.Bottom) / 2 - 75
}} else {{
    # フォールバック: 画面中央
    $centerX = ([System.Windows.Forms.Screen]::PrimaryScreen.Bounds.Width / 2) - 175
    $centerY = ([System.Windows.Forms.Screen]::PrimaryScreen.Bounds.Height / 2) - 75
}}

# ディスプレイ1（配列の0番目）を取得
$display1 = [System.Windows.Forms.Screen]::AllScreens[0]
if ($display1 -eq $null) {{ $display1 = [System.Windows.Forms.Screen]::PrimaryScreen }}

# ディスプレイ1の中央に最小サイズのウィンドウを配置
$centerX = $display1.Bounds.X + ($display1.Bounds.Width / 2) - 75
$centerY = $display1.Bounds.Y + ($display1.Bounds.Height / 2) - 35

$form = New-Object System.Windows.Forms.Form
$form.Text = "Claude"
$form.Size = New-Object System.Drawing.Size(150, 70)
$form.StartPosition = "Manual"
$form.Location = New-Object System.Drawing.Point($centerX, $centerY)
$form.TopMost = $true
$form.FormBorderStyle = "FixedToolWindow"
$form.MaximizeBox = $false
$form.MinimizeBox = $false
$form.BackColor = [System.Drawing.Color]::LightBlue

$label = New-Object System.Windows.Forms.Label
$label.Text = "{message}"
$label.Size = New-Object System.Drawing.Size(120, 25)
$label.Location = New-Object System.Drawing.Point(15, 5)
$label.Font = New-Object System.Drawing.Font("MS Gothic", 9)
$label.TextAlign = [System.Drawing.ContentAlignment]::MiddleCenter
$label.ForeColor = [System.Drawing.Color]::DarkBlue
$form.Controls.Add($label)

$okButton = New-Object System.Windows.Forms.Button
$okButton.Text = "OK"
$okButton.Size = New-Object System.Drawing.Size(40, 20)
$okButton.Location = New-Object System.Drawing.Point(55, 35)
$okButton.DialogResult = [System.Windows.Forms.DialogResult]::OK
$okButton.Font = New-Object System.Drawing.Font("MS Gothic", 10)
$form.Controls.Add($okButton)

$form.AcceptButton = $okButton
$form.Activate()
$form.BringToFront()

# タイマーなし - 手動で閉じるまで表示
$result = $form.ShowDialog()
'''
            
            cmd = ['powershell.exe', '-Command', ps_script]
            result = subprocess.run(cmd, capture_output=True, text=True)
            return result.returncode == 0
            
        except Exception as e:
            print(f"Windows通知送信エラー: {e}", file=sys.stderr)
            return False
    
    def send_terminal_notification(self, title, message):
        """ターミナル内通知（フォールバック）"""
        border = "=" * 60
        print(f"\n{border}")
        print(f"🔔 {title}")
        print(f"{border}")
        print(f"{message}")
        print(f"{border}\n")
    
    def notify(self, event_type, title, message, duration=5):
        """統合通知関数"""
        # 常に有効モードの確認
        always_notify = self.config.get("notifications", {}).get("always_notify", False)
        enabled_events = self.config.get("notifications", {}).get("hook_events", [])
        
        # 常に有効か、イベントが許可されている場合のみ通知
        if not always_notify and enabled_events != "all" and enabled_events and event_type not in enabled_events:
            return False
        
        print(f"[通知] {title}: {message}")
        
        # Windows通知を試行、失敗時はターミナル通知
        if not self.send_windows_notification(title, message, duration):
            self.send_terminal_notification(title, message)
        
        return True

def main():
    """コマンドライン実行用"""
    if len(sys.argv) < 4:
        print("使用方法: python notification_system.py <event_type> <title> <message> [duration]")
        print("例: python notification_system.py task_completed '作業完了' 'ファイル作成が完了しました'")
        sys.exit(1)
    
    event_type = sys.argv[1]
    title = sys.argv[2]
    message = sys.argv[3]
    duration = int(sys.argv[4]) if len(sys.argv) > 4 else 5
    
    notifier = ClaudeNotificationSystem()
    notifier.notify(event_type, title, message, duration)

if __name__ == "__main__":
    main()