#!/bin/bash
# Claude Code 通知システム起動スクリプト

SCRIPT_DIR="/home/tems_kaihatu"
MONITOR_SCRIPT="$SCRIPT_DIR/auto_notify.py"
NOTIFICATION_SCRIPT="$SCRIPT_DIR/notification_system.py"

echo "🔔 Claude Code 通知システムを起動しています..."

# 依存関係チェック
if [ ! -f "$NOTIFICATION_SCRIPT" ]; then
    echo "❌ 通知スクリプトが見つかりません: $NOTIFICATION_SCRIPT"
    exit 1
fi

if [ ! -f "$MONITOR_SCRIPT" ]; then
    echo "❌ 監視スクリプトが見つかりません: $MONITOR_SCRIPT"
    exit 1
fi

# 起動通知
python3 "$NOTIFICATION_SCRIPT" "system_start" "Claude Code 通知システム" "ファイル監視を開始しました" 3

echo "✅ 通知システムが起動しました"
echo "📁 監視対象: /home/tems_kaihatu"
echo "🔄 バックグラウンドで実行中..."

# バックグラウンドで監視開始
nohup python3 "$MONITOR_SCRIPT" > /tmp/claude_monitor.log 2>&1 &
MONITOR_PID=$!

echo "📋 監視プロセスID: $MONITOR_PID"
echo "$MONITOR_PID" > /tmp/claude_monitor.pid

echo "🛑 停止するには: kill $MONITOR_PID"
echo "📝 ログ確認: tail -f /tmp/claude_monitor.log"