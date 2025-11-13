#!/bin/bash
# Quick check script for dynamic paper trading

cd "/Users/harveyando/Local Sites/hermes-v1.0.0"

echo ""
echo "╔════════════════════════════════════════════════════════════════╗"
echo "║           DYNAMIC PAPER TRADING - QUICK CHECK                  ║"
echo "╚════════════════════════════════════════════════════════════════╝"
echo ""

# Check if running
if [ -f logs/dynamic_paper.pid ]; then
    PID=$(cat logs/dynamic_paper.pid)
    if ps -p $PID > /dev/null 2>&1; then
        echo "✅ Status: RUNNING (PID: $PID)"
    else
        echo "⚠️  Status: STOPPED (PID $PID not found)"
    fi
else
    echo "⚠️  Status: NOT STARTED (no PID file)"
fi

# Count snapshots
echo ""
echo "📊 Snapshots:"
ZEUS_COUNT=$(find data/snapshots/dynamic/zeus -name "*.json" 2>/dev/null | wc -l)
POLY_COUNT=$(find data/snapshots/dynamic/polymarket -name "*.json" 2>/dev/null | wc -l)
DEC_COUNT=$(find data/snapshots/dynamic/decisions -name "*.json" 2>/dev/null | wc -l)

echo "   Zeus:      $ZEUS_COUNT"
echo "   Polymarket: $POLY_COUNT"
echo "   Decisions:  $DEC_COUNT"

# Latest log
echo ""
echo "📝 Latest log (last 10 lines):"
tail -10 logs/dynamic_paper_*.log 2>/dev/null | grep -E "CYCLE|trades|Sleeping|edges" | tail -5

echo ""
echo "════════════════════════════════════════════════════════════════"
echo "For full report: python monitor_dynamic.py"
echo "To view live: tail -f logs/dynamic_paper_*.log"
echo "To stop: kill -INT \$(cat logs/dynamic_paper.pid)"
echo "════════════════════════════════════════════════════════════════"
echo ""

