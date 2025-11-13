# ⚡ Guide de Démarrage Rapide - Déploiement VPS

## 🎯 En Bref

**Temps estimé** : 30 minutes  
**Coût** : 5-12€/mois  
**Difficulté** : Facile ✅

---

## 📋 Checklist Avant de Commencer

- [ ] Créé un fichier `.env` avec vos credentials (depuis `env.example`)
- [ ] Testé la latence avec `./deploy/test_latency.sh`
- [ ] Choisi un provider VPS (voir recommandations ci-dessous)
- [ ] Compte créé sur le provider choisi

---

## 🏆 Quel VPS Choisir ? (Réponse Simple)

### 💰 Budget < 10€/mois
**→ Hetzner CPX11** (4.75€/mois)
- 2 vCPU, 2 GB RAM, 40 GB SSD
- Meilleur rapport qualité/prix
- [Créer un compte](https://www.hetzner.com/cloud)

### 💵 Vous voulez la simplicité
**→ DigitalOcean Basic** (12$/mois)
- Interface la plus simple
- Documentation excellente
- [Créer un compte](https://www.digitalocean.com) (100$ de crédit offert)

### 💸 Trading intensif
**→ Vultr High Frequency** (18$/mois)
- CPU dédié, latence minimale
- [Créer un compte](https://www.vultr.com)

**❌ Ne prenez PAS Hostinger** pour du trading (CPU partagé, latence élevée)

---

## 🚀 Déploiement en 3 Étapes

### **Étape 1 : Créer le VPS** (5 min)

Sur votre provider :

1. **Créez un serveur** :
   - OS : **Ubuntu 22.04 LTS**
   - Région : **US East** (New York) ou **EU Central** (Francfort)
   - Plan : Minimum **2 GB RAM**

2. **Notez** :
   - L'adresse IP du serveur
   - Le mot de passe root (par email)

3. **Connectez-vous** pour tester :
   ```bash
   ssh root@VOTRE_IP
   ```

---

### **Étape 2 : Configuration du VPS** (15 min)

Sur **votre machine locale** :

```bash
cd "/Users/baptistecuchet/Desktop/Bot ultime"

# 1. Créez votre fichier .env avec VOS vraies valeurs
cp env.example .env
nano .env  # Remplissez vos clés privées

# 2. Envoyez le script d'installation sur le VPS
scp deploy/setup_vps.sh root@VOTRE_IP:~/

# 3. Connectez-vous et lancez l'installation
ssh root@VOTRE_IP
chmod +x setup_vps.sh
./setup_vps.sh
```

Le script va :
- ✅ Installer Python 3.11
- ✅ Installer les dépendances
- ✅ Configurer le firewall
- ✅ Créer le service systemd

**Patientez 5-10 minutes** pendant l'installation.

---

### **Étape 3 : Déployer le Bot** (10 min)

Sur **votre machine locale** :

```bash
cd "/Users/baptistecuchet/Desktop/Bot ultime"

# 1. Configurez le script de déploiement
nano deploy/deploy.sh
# Changez la ligne : VPS_IP="VOTRE_IP_VPS"

# 2. Rendez le script exécutable
chmod +x deploy/deploy.sh

# 3. Déployez !
./deploy/deploy.sh
```

Le script va :
- ✅ Créer une archive du projet
- ✅ L'envoyer sur le VPS
- ✅ Installer les dépendances Python
- ✅ Démarrer le bot automatiquement

---

## ✅ Vérification

### 1. Le bot tourne-t-il ?

```bash
ssh root@VOTRE_IP
sudo systemctl status arbitrage-bot
```

Vous devriez voir : `Active: active (running)`

### 2. L'interface web est-elle accessible ?

Ouvrez dans votre navigateur :
```
http://VOTRE_IP:8080
```

Vous devriez voir l'interface de contrôle du bot.

### 3. Les logs sont-ils OK ?

```bash
ssh root@VOTRE_IP
tail -f ~/bot-arbitrage/logs/web_server_*.log
```

---

## 🎛️ Commandes Utiles

### Gérer le Bot

```bash
# Arrêter le bot
ssh root@VOTRE_IP 'sudo systemctl stop arbitrage-bot'

# Démarrer le bot
ssh root@VOTRE_IP 'sudo systemctl start arbitrage-bot'

# Redémarrer le bot
ssh root@VOTRE_IP 'sudo systemctl restart arbitrage-bot'

# Voir les logs en temps réel
ssh root@VOTRE_IP 'tail -f ~/bot-arbitrage/logs/*.log'

# Voir l'état du système
ssh root@VOTRE_IP 'htop'
```

### Mettre à Jour le Bot

Après avoir modifié votre code localement :

```bash
cd "/Users/baptistecuchet/Desktop/Bot ultime"
./deploy/deploy.sh
```

Le bot sera automatiquement redémarré avec la nouvelle version.

---

## 🔒 Sécurité Minimale (Important !)

### 1. Changez le mot de passe root

```bash
ssh root@VOTRE_IP
passwd
# Entrez un nouveau mot de passe FORT
```

### 2. Créez un utilisateur dédié (recommandé)

```bash
ssh root@VOTRE_IP

# Créer l'utilisateur
adduser botuser
usermod -aG sudo botuser

# Copier le bot
cp -r ~/bot-arbitrage /home/botuser/
chown -R botuser:botuser /home/botuser/bot-arbitrage

# Modifier le service pour utiliser ce user
nano /etc/systemd/system/arbitrage-bot.service
# Changez : User=botuser
# Changez : WorkingDirectory=/home/botuser/bot-arbitrage

# Redémarrer
systemctl daemon-reload
systemctl restart arbitrage-bot
```

### 3. Configurez fail2ban (anti brute-force SSH)

```bash
ssh root@VOTRE_IP
apt install fail2ban -y
systemctl enable fail2ban
systemctl start fail2ban
```

---

## 🐛 Dépannage

### ❌ "Connection refused" sur le port 8080

```bash
# Vérifier que le firewall autorise le port
ssh root@VOTRE_IP 'sudo ufw allow 8080/tcp'

# Vérifier que le bot tourne
ssh root@VOTRE_IP 'sudo systemctl status arbitrage-bot'
```

### ❌ Le bot crash au démarrage

```bash
# Voir les erreurs
ssh root@VOTRE_IP 'sudo journalctl -u arbitrage-bot -n 50'

# Vérifier la config
ssh root@VOTRE_IP 'cd ~/bot-arbitrage && python3.11 config.py'
```

### ❌ "ModuleNotFoundError"

```bash
# Réinstaller les dépendances
ssh root@VOTRE_IP 'cd ~/bot-arbitrage && python3.11 -m pip install -r requirements.txt --upgrade'
```

### ❌ Manque de mémoire

```bash
# Créer un swap de 2 GB
ssh root@VOTRE_IP << 'EOF'
sudo fallocate -l 2G /swapfile
sudo chmod 600 /swapfile
sudo mkswap /swapfile
sudo swapon /swapfile
echo '/swapfile none swap sw 0 0' | sudo tee -a /etc/fstab
EOF
```

---

## 📊 Monitoring

### Surveiller l'utilisation des ressources

```bash
# Vue en temps réel (CPU, RAM, etc.)
ssh root@VOTRE_IP 'htop'

# Espace disque
ssh root@VOTRE_IP 'df -h'

# Mémoire
ssh root@VOTRE_IP 'free -h'
```

### Surveiller les trades

1. Via l'interface web : `http://VOTRE_IP:8080`
2. Via les logs : 
   ```bash
   ssh root@VOTRE_IP 'tail -f ~/bot-arbitrage/logs/arbitrage_bot_strategy_*.log'
   ```

---

## 💰 Coûts Mensuels Estimés

| Poste | Coût |
|-------|------|
| VPS (Hetzner CPX11) | 4.75€ |
| Backups (optionnel) | +2€ |
| **TOTAL** | **~7€/mois** |

**Ou** :
| Poste | Coût |
|-------|------|
| VPS (DigitalOcean) | 12$ (~11€) |
| Backups | +4$ (~3.5€) |
| **TOTAL** | **~14.5€/mois** |

---

## 🎉 Félicitations !

Votre bot est maintenant déployé et tourne 24/7 ! 🚀

### Prochaines Étapes

1. **Surveillez les premiers trades** via l'interface web
2. **Ajustez les paramètres** selon les performances
3. **Configurez des alertes** (email/Telegram) pour être notifié
4. **Activez les backups automatiques** sur votre VPS

### Ressources Utiles

- 📖 [Guide complet](DEPLOYMENT_GUIDE.md) - Toutes les options avancées
- 💻 [Besoins VPS](VPS_REQUIREMENTS.md) - Détails techniques
- 🔧 [Scripts de déploiement](.) - Tous les scripts fournis

---

## 📞 Besoin d'Aide ?

Si vous rencontrez des problèmes :

1. ✅ Vérifiez la section **Dépannage** ci-dessus
2. ✅ Consultez les logs du bot
3. ✅ Testez d'abord en local avant de déployer
4. ✅ Vérifiez que votre fichier `.env` est correct

**Bon trading ! 📈💰**

