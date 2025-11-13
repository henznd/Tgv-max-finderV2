#!/bin/bash
# Script pour tester la latence vers les exchanges et choisir la meilleure localisation VPS

echo "🌐 Test de Latence vers les Exchanges"
echo "======================================"
echo ""

# Fonction pour tester la latence
test_latency() {
    local host=$1
    local name=$2
    
    echo "📍 Test vers $name ($host)..."
    
    if ping -c 5 -W 2 $host > /dev/null 2>&1; then
        avg_latency=$(ping -c 5 -W 2 $host 2>/dev/null | tail -1 | awk -F '/' '{print $5}')
        if [ ! -z "$avg_latency" ]; then
            echo "   ✅ Latence moyenne: ${avg_latency}ms"
        else
            echo "   ⚠️  Impossible de calculer la latence moyenne"
        fi
    else
        echo "   ❌ Host inaccessible"
    fi
    echo ""
}

# Tests vers les exchanges
echo "🔄 Test des Exchanges..."
echo "------------------------"
test_latency "api.lighter.xyz" "Lighter DEX"
test_latency "api.paradex.trade" "Paradex"

# Test de Supabase
echo "🗄️  Test Supabase..."
echo "------------------------"
test_latency "db.jlqdkbdmjuqjqhesxvjg.supabase.co" "Supabase DB"

echo ""
echo "🌍 Recommandations de Localisation VPS"
echo "======================================"
echo ""

# Tester quelques datacenters populaires
datacenters=(
    "speedtest-nyc1.digitalocean.com:New York (DigitalOcean)"
    "speedtest-fra1.digitalocean.com:Francfort (DigitalOcean)"
    "speedtest-ams3.digitalocean.com:Amsterdam (DigitalOcean)"
    "speedtest-lon1.digitalocean.com:Londres (DigitalOcean)"
    "fra-de-ping.vultr.com:Francfort (Vultr)"
    "nj-us-ping.vultr.com:New Jersey (Vultr)"
)

echo "📡 Test des Datacenters VPS populaires..."
echo ""

for dc in "${datacenters[@]}"; do
    IFS=':' read -r host name <<< "$dc"
    test_latency "$host" "$name"
done

echo ""
echo "💡 Interprétation des résultats"
echo "================================"
echo ""
echo "Latence < 50ms  : ⭐⭐⭐⭐⭐ Excellent pour le trading"
echo "Latence 50-100ms : ⭐⭐⭐⭐ Très bon"
echo "Latence 100-150ms: ⭐⭐⭐ Acceptable"
echo "Latence > 150ms  : ⚠️  Non recommandé pour l'arbitrage"
echo ""
echo "🎯 Choisissez le datacenter avec la latence la plus FAIBLE"
echo "   vers vos exchanges (Lighter + Paradex)"
echo ""

