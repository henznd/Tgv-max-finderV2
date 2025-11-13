# 🚀 Guide de Déploiement VPS

## 📋 Prérequis

- Un VPS Ubuntu 20.04+ (Hostinger, DigitalOcean, AWS, etc.)
- Accès SSH au VPS
- Minimum recommandé : 1 CPU, 1GB RAM, 10GB disque

## 🎯 Hostinger - Mon Avis

### ✅ **AVANTAGES**
- **Prix** : Très compétitif (3-10€/mois)
- **Simple** : Interface facile pour débutants
- **Support** : Support francophone disponible
- **Localisation** : Serveurs en Europe

### ⚠️ **INCONVÉNIENTS**
- **Performance** : CPU/RAM partagé (peut être lent)
- **Réseau** : Latence légèrement supérieure aux spécialistes
- **Flexibilité** : Moins d'options que DigitalOcean/AWS

### 🎯 **MON RECOMMANDATION**

Pour un bot de trading qui nécessite **faible latence et haute disponibilité** :

**1️⃣ DigitalOcean** (Recommandé) ⭐
- Prix : 6$/mois (Droplet basique)
- Latence ultra-faible
- Réseau excellent
- Parfait pour le trading

**2️⃣ Hostinger** (Budget serré)
- Prix : 4€/mois
- OK pour débuter
- Surveiller les performances

**3️⃣ AWS Lightsail** (Si expérience)
- Prix : 5$/mois
- Très performant
- Plus complexe

## 🛠️ Installation sur le VPS

### **Étape 1 : Connexion au VPS**

```bash
ssh root@VOTRE_IP_VPS
# ou
ssh votre_user@VOTRE_IP_VPS
```

### **Étape 2 : Configuration initiale**

Uploadez et exécutez le script de setup :

```bash
# Sur votre machine locale
scp deploy/setup_vps.sh root@VOTRE_IP_VPS:~/
ssh root@VOTRE_IP_VPS

# Sur le VPS
chmod +x setup_vps.sh
./setup_vps.sh
```

Ce script va :
- ✅ Installer Python 3.11
- ✅ Installer les dépendances système
- ✅ Configurer le firewall
- ✅ Créer le service systemd

### **Étape 3 : Configuration des credentials**

```bash
# Sur votre machine locale
cd /Users/baptistecuchet/Desktop/Bot\ ultime/

# 1. Créez votre fichier .env
cp .env.example .env
nano .env  # ou vi, vim, etc.

# 2. Remplissez avec VOS vraies valeurs :
SUPABASE_PASSWORD=votre_vrai_mot_de_passe
LIGHTER_PRIVATE_KEY=votre_vraie_clé
PARADEX_L2_PRIVATE_KEY=votre_vraie_clé
PARADEX_L1_ADDRESS=votre_vraie_adresse
```

### **Étape 4 : Déploiement**

```bash
# Sur votre machine locale
cd deploy/
nano deploy.sh  # Modifiez VPS_IP avec votre IP
chmod +x deploy.sh
./deploy.sh
```

### **Étape 5 : Vérification**

```bash
# Sur le VPS
sudo systemctl status arbitrage-bot
sudo journalctl -u arbitrage-bot -f  # Voir les logs en temps réel
```

## 🌐 Accès à l'interface web

Ouvrez votre navigateur : `http://VOTRE_IP_VPS:8080`

## 📊 Gestion du bot

### Commandes utiles

```bash
# Démarrer le bot
sudo systemctl start arbitrage-bot

# Arrêter le bot
sudo systemctl stop arbitrage-bot

# Redémarrer le bot
sudo systemctl restart arbitrage-bot

# Voir le statut
sudo systemctl status arbitrage-bot

# Voir les logs
tail -f ~/bot-arbitrage/logs/web_server_*.log

# Activer le démarrage automatique au boot
sudo systemctl enable arbitrage-bot
```

### Mise à jour du code

```bash
# Sur votre machine locale
cd deploy/
./deploy.sh  # Re-déploie automatiquement
```

## 🔒 Sécurité

### ✅ Déjà fait
- Credentials dans .env (pas dans le code)
- Firewall configuré (ports 22, 8080)
- Service systemd avec auto-restart

### 🚨 À faire en plus (recommandé)

1. **Changer le port SSH** (éviter 22)
```bash
sudo nano /etc/ssh/sshd_config
# Port 2222
sudo systemctl restart sshd
```

2. **Désactiver root login**
```bash
# Créer un utilisateur normal d'abord
sudo adduser botuser
sudo usermod -aG sudo botuser
# Puis dans /etc/ssh/sshd_config :
# PermitRootLogin no
```

3. **Configurer fail2ban**
```bash
sudo apt install fail2ban -y
```

4. **SSL/HTTPS pour l'interface web** (optionnel)
```bash
# Utiliser nginx + certbot
sudo apt install nginx certbot python3-certbot-nginx
```

## 📈 Monitoring

### Surveiller l'utilisation des ressources

```bash
# CPU et RAM
htop

# Espace disque
df -h

# Logs du bot
tail -f ~/bot-arbitrage/logs/*.log
```

### Alertes (optionnel)

Configurez des alertes email/Telegram en cas de problème.

## 🆘 Dépannage

### Le bot ne démarre pas

```bash
# Vérifier les logs
sudo journalctl -u arbitrage-bot -n 50

# Vérifier la config
cd ~/bot-arbitrage
python3.11 config.py

# Vérifier les dépendances
python3.11 -m pip install -r requirements.txt
```

### Port 8080 inaccessible

```bash
# Vérifier le firewall
sudo ufw status

# Ouvrir le port si besoin
sudo ufw allow 8080/tcp
```

### Problème de mémoire

```bash
# Créer un fichier swap
sudo fallocate -l 2G /swapfile
sudo chmod 600 /swapfile
sudo mkswap /swapfile
sudo swapon /swapfile
```

## 💰 Coûts estimés

| Provider | Plan | Prix/mois | Performance Trading |
|----------|------|-----------|-------------------|
| **DigitalOcean** | Basic Droplet | 6$ | ⭐⭐⭐⭐⭐ |
| **Hostinger** | VPS 1 | 4€ | ⭐⭐⭐ |
| **AWS Lightsail** | 512MB | 3.5$ | ⭐⭐⭐⭐ |
| **Vultr** | 1GB RAM | 6$ | ⭐⭐⭐⭐⭐ |

**Mon choix : DigitalOcean** pour le meilleur rapport performance/prix en trading.

## 📞 Support

En cas de problème :
1. Vérifiez les logs
2. Consultez ce guide
3. Testez sur votre machine locale d'abord

