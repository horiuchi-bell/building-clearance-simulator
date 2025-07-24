#!/usr/bin/env python3
"""
Claude Code 通知ラッパーシステム
全てのBashコマンドをラップして適切なタイミングで通知
"""
import sys
import subprocess
import time
import json
import os
from pathlib import Path

class ClaudeNotificationWrapper:
    def __init__(self):
        self.notification_script = "/home/tems_kaihatu/notification_system.py"
        self.dangerous_commands = [
            'rm', 'rmdir', 'mv', 'cp', 'sudo', 'git', 'curl', 'wget', 'pip', 'apt',
            'systemctl', 'service', 'mount', 'umount', 'chmod', 'chown', 'kill'
        ]
        
    def is_dangerous_command(self, command):
        """危険なコマンドかチェック"""
        if not command.strip():
            return False
            
        first_word = command.strip().split()[0]
        return any(dangerous in first_word for dangerous in self.dangerous_commands)
    
    def send_notification(self, msg_type, message):
        """通知を送信"""
        try:
            subprocess.run([
                'python3', self.notification_script, 
                msg_type, "Claude Code", message, "30"
            ], capture_output=True, timeout=5)
        except Exception:
            pass
    
    def execute_with_notification(self, command, description=""):
        """コマンド実行を通知付きでラップ"""
        # 危険なコマンドの場合は事前通知
        if self.is_dangerous_command(command):
            self.send_notification("user_confirmation_required", "確認必要")
            # 通知が表示される時間を確保
            time.sleep(0.5)
        
        # コマンド実行
        try:
            result = subprocess.run(
                command, 
                shell=True, 
                capture_output=True, 
                text=True,
                timeout=300
            )
            
            return {
                'returncode': result.returncode,
                'stdout': result.stdout,
                'stderr': result.stderr
            }
        except subprocess.TimeoutExpired:
            return {
                'returncode': 124,
                'stdout': '',
                'stderr': 'Command timed out'
            }
        except Exception as e:
            return {
                'returncode': 1,
                'stdout': '',
                'stderr': str(e)
            }
    
    def completion_notification(self):
        """作業完了通知"""
        self.send_notification("session_ready", "回答完了")

def main():
    if len(sys.argv) < 2:
        print("使用方法: python3 claude_notification_wrapper.py <command>")
        sys.exit(1)
    
    command = ' '.join(sys.argv[1:])
    wrapper = ClaudeNotificationWrapper()
    
    result = wrapper.execute_with_notification(command)
    
    # 結果を出力
    if result['stdout']:
        print(result['stdout'], end='')
    if result['stderr']:
        print(result['stderr'], file=sys.stderr, end='')
    
    sys.exit(result['returncode'])

if __name__ == "__main__":
    main()