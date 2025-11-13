# 💻 Besoins en Ressources VPS

## 📊 Analyse de votre Bot

Votre bot d'arbitrage :
- **Taille actuelle** : ~105 MB (dont 104 MB de logs)
- **Code** : 15 fichiers Python, ~1200 lignes de code
- **Architecture** :
  - Bot asyncio (non-bloquant, performant)
  - WebSocket/REST API pour prix temps réel
  - Base de données externe (Supabase)
  - Interface web légère (HTML/JS vanilla)
  - 3 bots possibles (principal, stratégie, simple)

## 🎯 Configuration VPS Recommandée

### ⭐ **OPTION 1 : MINIMALE (Budget serré) - 4-6€/mois**

```
CPU     : 1 vCPU
RAM     : 1 GB
Storage : 10 GB SSD
Bande P.: 1 TB/mois
```

**✅ AVANTAGES**
- Prix imbattable (4-6€/mois)
- Suffisant pour un seul bot
- OK pour petit volume de trades

**⚠️ LIMITATIONS**
- CPU partagé (peut ralentir aux heures de pointe)
- RAM juste pour 1 bot + interface web
- Pas de marge pour pics d'activité

**📍 Où trouver** :
- Hostinger VPS 1 : 4.99€/mois
- Contabo VPS S : 5.99€/mois

---

### ⭐⭐⭐ **OPTION 2 : RECOMMANDÉE (Trading sérieux) - 6-12€/mois**

```
CPU     : 1-2 vCPU (dédié ou premium)
RAM     : 2 GB
Storage : 25 GB SSD
Bande P.: 2 TB/mois
```

**✅ AVANTAGES**
- Performances stables
- Peut gérer 2-3 bots simultanément
- Marge pour pics d'activité
- Logs + backups confortables

**🎯 IDÉAL POUR**
- Trading avec capital significatif
- Multi-stratégies
- Monitoring + interface web fluide

**📍 Où trouver** :
- DigitalOcean Basic Droplet : 12$/mois (⭐ Mon choix)
- Vultr Regular Performance : 12$/mois
- Hetzner CPX11 : 4.75€/mois (excellent rapport qualité/prix)

---

### ⭐⭐⭐⭐⭐ **OPTION 3 : OPTIMALE (Pro) - 18-24€/mois**

```
CPU     : 2-4 vCPU (dédié)
RAM     : 4 GB
Storage : 50 GB SSD NVMe
Bande P.: 4 TB/mois
```

**✅ AVANTAGES**
- Performances maximales
- Latence ultra-faible
- Peut gérer 5+ bots
- Backtesting possible sur VPS
- Monitoring avancé

**🎯 IDÉAL POUR**
- Trading haute fréquence
- Multi-exchanges (3+)
- Capital important
- Développement + production

**📍 Où trouver** :
- DigitalOcean CPU-Optimized : 24$/mois
- Vultr High Frequency : 18$/mois
- AWS Lightsail 2GB : 20$/mois

---

## 📈 Détail de la Consommation

### 💾 **Storage (Disque)**

| Composant | Taille | Notes |
|-----------|--------|-------|
| Code Python | ~1 MB | Très léger |
| Dépendances Python | ~150 MB | lighter-sdk, paradex-py, etc. |
| Logs (par mois) | ~500 MB - 2 GB | Dépend de la fréquence des trades |
| OS Ubuntu | ~2 GB | Système de base |
| **TOTAL MIN** | **~5 GB** | Sans historique |
| **TOTAL RECOMMANDÉ** | **25 GB** | Avec marge |

**💡 Astuce** : Configurez une rotation des logs pour éviter de remplir le disque.

### 🧠 **RAM (Mémoire)**

| Processus | RAM Utilisée | Notes |
|-----------|--------------|-------|
| Python Bot (1x) | ~200-400 MB | Par instance |
| Interface Web | ~50-100 MB | Serveur HTTP |
| OS Ubuntu | ~300-400 MB | Système |
| Connexions réseau | ~50-100 MB | WebSocket + REST |
| **TOTAL (1 bot)** | **~600 MB - 1 GB** | Minimum absolu |
| **TOTAL (avec marge)** | **2 GB** | ⭐ Recommandé |

**⚠️ Important** : Avec 1 GB de RAM, il faut :
- Configurer un swap (2 GB recommandé)
- Ne lancer qu'un seul bot à la fois
- Surveiller l'utilisation mémoire

### ⚡ **CPU (Processeur)**

Votre bot est **léger en CPU** car :
- ✅ Asyncio (non-bloquant)
- ✅ Pas de calculs complexes
- ✅ Principalement I/O réseau

**Utilisation moyenne** :
- **Repos** : 1-5% d'un vCPU
- **Pics (trade)** : 10-30% d'un vCPU
- **Backtest** : 40-80% d'un vCPU

**💡 1 vCPU suffit largement** pour le trading en temps réel.

### 🌐 **Réseau (Bande Passante)**

| Activité | Consommation | Par mois |
|----------|--------------|----------|
| Prix temps réel | ~10-50 KB/s | ~100 GB/mois |
| Exécution trades | ~1-5 KB/trade | ~1 GB/mois |
| Interface web | ~500 KB/visite | ~5 GB/mois |
| Logs Supabase | ~5-10 KB/s | ~30 GB/mois |
| **TOTAL** | | **~150 GB/mois** |

**💡 1 TB de bande passante** est largement suffisant.

---

## 🏆 Mes Recommandations par Budget

### 💰 **Budget < 10€/mois** : HETZNER CPX11

```
Prix    : 4.75€/mois
CPU     : 2 vCPU AMD
RAM     : 2 GB
Storage : 40 GB SSD
Réseau  : 20 TB/mois

✅ Meilleur rapport qualité/prix
✅ Datacenter en Allemagne (faible latence Europe)
✅ Performance excellente
```

**👉 Mon choix N°1 pour débuter sérieusement**

---

### 💵 **Budget 10-15€/mois** : DIGITALOCEAN BASIC DROPLET

```
Prix    : 12$/mois (~11€)
CPU     : 1 vCPU (premium)
RAM     : 2 GB
Storage : 50 GB SSD
Réseau  : 2 TB/mois

✅ Interface ultra-simple
✅ Documentation excellente
✅ Réseau optimisé pour trading
✅ Snapshots/backups faciles
```

**👉 Le plus fiable et simple d'utilisation**

---

### 💸 **Budget > 15€/mois** : VULTR HIGH FREQUENCY

```
Prix    : 18$/mois (~16€)
CPU     : 1 vCPU (dédié haute fréquence)
RAM     : 2 GB
Storage : 64 GB NVMe SSD
Réseau  : 3 TB/mois

✅ CPU dédié (pas de partage)
✅ NVMe ultra-rapide
✅ Latence minimale
✅ Parfait pour HFT
```

**👉 Pour du trading intensif**

---

## 🚨 Éviter ces Erreurs Courantes

### ❌ **Prendre trop petit (512 MB RAM)**
- Python + dépendances = déjà 600 MB
- Le bot va crasher régulièrement
- Impossible de monitorer correctement

### ❌ **Prendre du CPU partagé bas de gamme**
- Ralentissements aux heures de pointe
- Latence imprévisible
- Trades ratés

### ❌ **Oublier la localisation**
- Un serveur à Singapour pour trader sur des exchanges US = +200ms de latence
- **Choisissez** : Europe (Francfort, Amsterdam) ou US (NY, SF) selon vos exchanges

### ❌ **Négliger les backups**
- Logs perdus = impossible de débugger
- Config perdue = bot arrêté
- **Solution** : Activer les snapshots automatiques (2-4€/mois de plus)

---

## 📍 Localisation du Serveur (Important!)

### 🌍 **Où sont vos exchanges ?**

```
Lighter DEX  : Serveurs US (probablement)
Paradex      : Serveurs US (probablement)
Supabase     : Configurable
```

**💡 Recommandation** : 
- **US East Coast** (New York) : Latence minimale vers les DEX
- **EU Central** (Francfort) : Si vous gérez depuis l'Europe + latence acceptable

**Test de latence** :
```bash
# Tester depuis votre machine
ping -c 10 api.lighter.xyz
ping -c 10 api.paradex.trade
```

Comparez avec la latence depuis le VPS avant d'acheter !

---

## 🎯 Ma Recommandation Finale

Pour votre bot d'arbitrage Lighter/Paradex :

### 🥇 **CHOIX OPTIMAL**

**Hetzner CPX11** - 4.75€/mois
- 2 vCPU, 2 GB RAM, 40 GB SSD
- Allemagne (Falkenstein ou Nuremberg)
- **Meilleur rapport qualité/prix du marché**

**Alternative si vous voulez simplicité** :
**DigitalOcean Basic** - 12$/mois
- Plus cher mais interface parfaite pour débutants
- Documentation FR disponible

---

## 📊 Tableau Comparatif Final

| Provider | Plan | Prix/mois | CPU | RAM | Storage | Trading Performance |
|----------|------|-----------|-----|-----|---------|-------------------|
| **Hetzner** | CPX11 | 4.75€ | 2 | 2 GB | 40 GB | ⭐⭐⭐⭐⭐ |
| **DigitalOcean** | Basic | 12$ | 1 | 2 GB | 50 GB | ⭐⭐⭐⭐⭐ |
| **Vultr** | HF | 18$ | 1 HF | 2 GB | 64 GB | ⭐⭐⭐⭐⭐ |
| **Hostinger** | VPS 1 | 5€ | 1 | 1 GB | 20 GB | ⭐⭐⭐ |
| **Contabo** | VPS S | 6€ | 4 | 8 GB | 200 GB | ⭐⭐⭐ |

**Légende** :
- **HF** : High Frequency (dédié)
- **Trading Performance** : Latence + stabilité + uptime

---

## 🔧 Configuration Post-Installation

Une fois le VPS choisi, pensez à :

1. **Swap** (si < 2 GB RAM)
```bash
sudo fallocate -l 2G /swapfile
sudo chmod 600 /swapfile
sudo mkswap /swapfile
sudo swapon /swapfile
```

2. **Rotation des logs**
```bash
# Dans /etc/logrotate.d/arbitrage-bot
/root/bot-arbitrage/logs/*.log {
    daily
    rotate 7
    compress
    missingok
    notifempty
}
```

3. **Monitoring**
```bash
# Installer htop pour surveiller
sudo apt install htop
```

---

## 💡 Questions Fréquentes

**Q: Puis-je upgrader plus tard ?**  
R: Oui ! Tous les providers permettent d'upgrader facilement.

**Q: Dois-je prendre des backups ?**  
R: OUI ! 2-4€/mois pour des snapshots automatiques = indispensable.

**Q: IPv4 ou IPv6 ?**  
R: IPv4 requis pour certains exchanges. Vérifiez que votre VPS a une IPv4.

**Q: Besoin d'un domaine ?**  
R: Non, l'IP suffit. Mais un domaine (10€/an) rend l'accès plus simple.

**Q: Combien de temps pour setup ?**  
R: 30 min avec mes scripts automatiques !

---

## 🚀 Prêt à Déployer ?

1. Choisissez votre VPS (Hetzner CPX11 recommandé)
2. Suivez `deploy/DEPLOYMENT_GUIDE.md`
3. Utilisez les scripts `setup_vps.sh` et `deploy.sh`
4. Profit ! 🎉

