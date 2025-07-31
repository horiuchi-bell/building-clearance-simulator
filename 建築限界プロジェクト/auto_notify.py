#!/usr/bin/env python3
"""
Claude Code 自動通知システム（監視ベース）
ファイル変更を監視して通知を送信
"""
import json
import os
import sys
import time
import subprocess
from pathlib import Path
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler

class ClaudeActivityMonitor(FileSystemEventHandler):
    def __init__(self, notification_script):
        self.notification_script = notification_script
        self.last_notification = 0
        self.cooldown = 2  # 2秒のクールダウン
        
    def should_notify(self, event_path):
        """通知すべきファイルかチェック"""
        path = Path(event_path)
        
        # 除外するファイル/ディレクトリ
        exclude_patterns = [
            '.git', '__pycache__', '.pyc', '.tmp', 
            'node_modules', '.vscode', '.claude-code'
        ]
        
        for pattern in exclude_patterns:
            if pattern in str(path):
                return False
        
        # 対象とするファイル拡張子
        include_extensions = [
            '.py', '.js', '.ts', '.html', '.css', '.json', 
            '.md', '.txt', '.sh', '.yml', '.yaml'
        ]
        
        return path.suffix.lower() in include_extensions
    
    def send_notification(self, title, message):
        """通知を送信"""
        current_time = time.time()
        if current_time - self.last_notification < self.cooldown:
            return
        
        try:
            subprocess.run([
                'python3', self.notification_script,
                'file_activity', title, message, '2'
            ], timeout=5)
            self.last_notification = current_time
        except Exception as e:
            print(f"通知送信エラー: {e}")
    
    def on_created(self, event):
        if not event.is_directory and self.should_notify(event.src_path):
            filename = Path(event.src_path).name
            self.send_notification("ファイル作成", f"{filename} が作成されました")
    
    def on_modified(self, event):
        if not event.is_directory and self.should_notify(event.src_path):
            filename = Path(event.src_path).name
            self.send_notification("ファイル編集", f"{filename} が更新されました")

def main():
    notification_script = "/home/tems_kaihatu/notification_system.py"
    watch_directory = "/home/tems_kaihatu"
    
    if not os.path.exists(notification_script):
        print(f"通知スクリプトが見つかりません: {notification_script}")
        sys.exit(1)
    
    print(f"Claude Code 活動監視を開始します: {watch_directory}")
    
    event_handler = ClaudeActivityMonitor(notification_script)
    observer = Observer()
    observer.schedule(event_handler, watch_directory, recursive=True)
    
    try:
        observer.start()
        print("監視開始（Ctrl+Cで停止）")
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        observer.stop()
        print("\n監視を停止しました")
    
    observer.join()

if __name__ == "__main__":
    main()