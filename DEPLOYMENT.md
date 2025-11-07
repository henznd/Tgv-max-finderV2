# 🚀 Guide de déploiement - Arbitrage Calculator

## 📋 Prérequis

### Installation de Node.js

1. **Sur macOS (avec Homebrew)**
   ```bash
   brew install node
   ```

2. **Sur Windows**
   - Télécharger depuis [nodejs.org](https://nodejs.org/)
   - Installer la version LTS

3. **Sur Linux (Ubuntu/Debian)**
   ```bash
   curl -fsSL https://deb.nodesource.com/setup_lts.x | sudo -E bash -
   sudo apt-get install -y nodejs
   ```

### Vérification de l'installation
```bash
node --version  # Doit afficher v18+ ou v20+
npm --version   # Doit afficher 9+ ou 10+
```

## 🛠️ Installation locale

1. **Cloner le repository**
   ```bash
   git clone <votre-repo-url>
   cd arbitrage-calculator
   ```

2. **Installer les dépendances**
   ```bash
   npm install
   ```

3. **Lancer en mode développement**
   ```bash
   npm run dev
   ```

4. **Ouvrir dans le navigateur**
   ```
   http://localhost:3000
   ```

## 🧪 Tests

### Test des calculs
```bash
node test-calculations.js
```

### Test de l'interface
Ouvrir `demo.html` dans un navigateur pour tester les calculs sans Next.js.

## 🚀 Déploiement sur Vercel (Recommandé)

### Méthode 1: Interface web Vercel

1. **Aller sur [vercel.com](https://vercel.com)**
2. **Se connecter avec GitHub**
3. **Cliquer sur "New Project"**
4. **Importer le repository**
5. **Configurer automatiquement** (Vercel détecte Next.js)
6. **Cliquer sur "Deploy"**

### Méthode 2: CLI Vercel

1. **Installer Vercel CLI**
   ```bash
   npm i -g vercel
   ```

2. **Se connecter**
   ```bash
   vercel login
   ```

3. **Déployer**
   ```bash
   vercel
   ```

4. **Suivre les instructions**

### Méthode 3: GitHub Integration

1. **Pousser le code sur GitHub**
   ```bash
   git add .
   git commit -m "Initial commit"
   git push origin main
   ```

2. **Connecter le repo à Vercel**
   - Aller sur Vercel Dashboard
   - Importer le repository GitHub
   - Configurer automatiquement

## 🌐 Déploiement sur d'autres plateformes

### Netlify

1. **Build command**: `npm run build`
2. **Publish directory**: `.next`
3. **Node version**: 18.x ou 20.x

### Railway

1. **Connecter le repository GitHub**
2. **Configurer automatiquement**
3. **Déployer**

### Heroku

1. **Créer un `Procfile`**
   ```
   web: npm start
   ```

2. **Configurer les variables d'environnement**
   ```bash
   heroku config:set NODE_ENV=production
   ```

3. **Déployer**
   ```bash
   heroku create
   git push heroku main
   ```

## 🔧 Configuration de production

### Variables d'environnement

Créer un fichier `.env.local` pour la production :
```env
NEXT_PUBLIC_APP_NAME=Arbitrage Calculator
NEXT_PUBLIC_APP_VERSION=1.0.0
```

### Optimisations

1. **Build de production**
   ```bash
   npm run build
   ```

2. **Test local de production**
   ```bash
   npm run start
   ```

3. **Analyse du bundle**
   ```bash
   npm run build
   # Vérifier les fichiers dans .next/static
   ```

## 📊 Monitoring et Analytics

### Vercel Analytics (Optionnel)

1. **Installer le package**
   ```bash
   npm install @vercel/analytics
   ```

2. **Ajouter dans `layout.tsx`**
   ```tsx
   import { Analytics } from '@vercel/analytics/react';
   
   export default function RootLayout({ children }) {
     return (
       <html>
         <body>
           {children}
           <Analytics />
         </body>
       </html>
     );
   }
   ```

## 🔒 Sécurité

### Headers de sécurité

Ajouter dans `next.config.js` :
```js
const nextConfig = {
  async headers() {
    return [
      {
        source: '/(.*)',
        headers: [
          {
            key: 'X-Frame-Options',
            value: 'DENY',
          },
          {
            key: 'X-Content-Type-Options',
            value: 'nosniff',
          },
        ],
      },
    ];
  },
};
```

## 📱 PWA (Progressive Web App)

### Installation des dépendances
```bash
npm install next-pwa
```

### Configuration
```js
const withPWA = require('next-pwa')({
  dest: 'public',
  register: true,
  skipWaiting: true,
});

module.exports = withPWA({
  // votre config Next.js
});
```

## 🐛 Debugging

### Logs de production
```bash
# Vercel
vercel logs

# Railway
railway logs

# Heroku
heroku logs --tail
```

### Erreurs courantes

1. **Module not found**
   - Vérifier que toutes les dépendances sont installées
   - Nettoyer le cache : `rm -rf .next node_modules && npm install`

2. **Build failed**
   - Vérifier les erreurs TypeScript : `npm run lint`
   - Corriger les imports manquants

3. **Runtime errors**
   - Vérifier les logs de production
   - Tester en local avec `npm run build && npm run start`

## 📈 Performance

### Optimisations recommandées

1. **Images optimisées**
   ```tsx
   import Image from 'next/image';
   
   <Image src="/logo.png" alt="Logo" width={200} height={100} />
   ```

2. **Lazy loading**
   ```tsx
   import dynamic from 'next/dynamic';
   
   const HeavyComponent = dynamic(() => import('./HeavyComponent'), {
     loading: () => <p>Chargement...</p>
   });
   ```

3. **Bundle analyzer**
   ```bash
   npm install @next/bundle-analyzer
   ```

## 🔄 Mise à jour

### Processus de mise à jour

1. **Modifier le code**
2. **Tester en local**
   ```bash
   npm run dev
   npm run build
   npm run start
   ```

3. **Pousser sur GitHub**
   ```bash
   git add .
   git commit -m "Update: description des changements"
   git push origin main
   ```

4. **Vérifier le déploiement automatique**

### Rollback

Si nécessaire, revenir à une version précédente :
```bash
git revert <commit-hash>
git push origin main
```

---

## 📞 Support

Pour toute question ou problème :
- 📧 Email : [votre-email]
- 🐛 Issues : [GitHub Issues]
- 📖 Documentation : [lien vers la doc]

---

**Développé avec ❤️ par [Votre nom]** 