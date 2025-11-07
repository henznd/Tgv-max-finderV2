#!/bin/bash

echo "🚀 TESTING TRADING BOT SCRIPTS"
echo "================================"

echo ""
echo "📊 Testing Lighter DEX (Python 3.9)..."
echo "----------------------------------------"
/usr/bin/python3 lighter/lighter_trader.py

echo ""
echo "📊 Testing Paradex DEX (Python 3.11)..."
echo "----------------------------------------"
python3.11 paradex/paradex_trader.py

echo ""
echo "✅ Tests completed!"
