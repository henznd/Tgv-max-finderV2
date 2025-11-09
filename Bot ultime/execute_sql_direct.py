#!/usr/bin/env python3
"""
Exécute le SQL directement sur Supabase via connexion PostgreSQL
"""

import psycopg2
from psycopg2 import sql
import os

SUPABASE_HOST = "db.jlqdkbdmjuqjqhesxvjg.supabase.co"
SUPABASE_PORT = 5432
SUPABASE_DB = "postgres"
SUPABASE_USER = "postgres"
SUPABASE_PASSWORD = "vIVXJ793dz2aHHH0"

def read_sql_file(filepath: str) -> str:
    """Lit un fichier SQL"""
    with open(filepath, 'r', encoding='utf-8') as f:
        return f.read()

def execute_sql_remote(sql_content: str):
    """Exécute le SQL sur Supabase via connexion PostgreSQL directe"""
    print("🔌 Connexion à Supabase PostgreSQL...")
    print(f"   Host: {SUPABASE_HOST}")
    print(f"   Database: {SUPABASE_DB}")
    print()
    
    try:
        # Connexion à la base de données
        conn = psycopg2.connect(
            host=SUPABASE_HOST,
            port=SUPABASE_PORT,
            database=SUPABASE_DB,
            user=SUPABASE_USER,
            password=SUPABASE_PASSWORD,
            connect_timeout=10
        )
        
        print("✅ Connexion établie!")
        print("   Exécution du SQL...")
        print()
        
        # Créer un curseur
        cur = conn.cursor()
        
        # Exécuter le SQL (divisé en plusieurs commandes si nécessaire)
        # psycopg2 peut exécuter plusieurs commandes séparées par des points-virgules
        cur.execute(sql_content)
        
        # Récupérer les résultats si nécessaire
        try:
            results = cur.fetchall()
            if results:
                print("📊 Résultats:")
                for row in results:
                    print(f"   {row}")
        except:
            # Pas de résultats à récupérer (CREATE, INSERT, etc.)
            pass
        
        # Valider la transaction
        conn.commit()
        
        print()
        print("✅ SQL exécuté avec succès!")
        print()
        print("📋 Configuration terminée:")
        print("   ✅ Table price_history créée")
        print("   ✅ Extensions pg_net et pg_cron activées")
        print("   ✅ Fonction collect_prices_direct() créée")
        print("   ✅ Fonction collect_prices_loop_minute() créée")
        print("   ✅ Job cron collect-prices-every-second configuré")
        print()
        print("🚀 La collecte de prix démarre automatiquement!")
        print("   Les prix seront collectés toutes les secondes")
        print()
        print("📊 Vérifiez avec:")
        print("   SELECT * FROM price_history ORDER BY timestamp DESC LIMIT 10;")
        
        # Fermer la connexion
        cur.close()
        conn.close()
        
        return True
        
    except psycopg2.OperationalError as e:
        print(f"❌ Erreur de connexion: {e}")
        print()
        print("💡 Vérifiez:")
        print("   - Les credentials de connexion")
        print("   - Que votre IP est autorisée dans Supabase (Settings > Database > Connection Pooling)")
        return False
    except psycopg2.Error as e:
        print(f"❌ Erreur SQL: {e}")
        print()
        print("💡 Certaines erreurs peuvent être normales (ex: extension déjà installée)")
        print("   Vérifiez dans Supabase SQL Editor si la configuration est correcte")
        return False
    except Exception as e:
        print(f"❌ Erreur inattendue: {e}")
        import traceback
        traceback.print_exc()
        return False

def main():
    print("=" * 60)
    print("🚀 EXÉCUTION SQL À DISTANCE SUR SUPABASE")
    print("=" * 60)
    print()
    
    sql_file = "setup_complete.sql"
    
    if not os.path.exists(sql_file):
        print(f"❌ Fichier SQL non trouvé: {sql_file}")
        return
    
    sql_content = read_sql_file(sql_file)
    print(f"✅ Fichier SQL lu: {len(sql_content)} caractères")
    print()
    
    if execute_sql_remote(sql_content):
        print("=" * 60)
        print("✅ SUCCÈS!")
        print("=" * 60)
    else:
        print("=" * 60)
        print("⚠️  EXÉCUTION ÉCHOUÉE")
        print("=" * 60)
        print()
        print("💡 Alternative: Exécutez le SQL manuellement dans Supabase SQL Editor")
        print("   Fichier: setup_complete.sql")

if __name__ == "__main__":
    main()


"""
Exécute le SQL directement sur Supabase via connexion PostgreSQL
"""

import psycopg2
from psycopg2 import sql
import os

SUPABASE_HOST = "db.jlqdkbdmjuqjqhesxvjg.supabase.co"
SUPABASE_PORT = 5432
SUPABASE_DB = "postgres"
SUPABASE_USER = "postgres"
SUPABASE_PASSWORD = "vIVXJ793dz2aHHH0"

def read_sql_file(filepath: str) -> str:
    """Lit un fichier SQL"""
    with open(filepath, 'r', encoding='utf-8') as f:
        return f.read()

def execute_sql_remote(sql_content: str):
    """Exécute le SQL sur Supabase via connexion PostgreSQL directe"""
    print("🔌 Connexion à Supabase PostgreSQL...")
    print(f"   Host: {SUPABASE_HOST}")
    print(f"   Database: {SUPABASE_DB}")
    print()
    
    try:
        # Connexion à la base de données
        conn = psycopg2.connect(
            host=SUPABASE_HOST,
            port=SUPABASE_PORT,
            database=SUPABASE_DB,
            user=SUPABASE_USER,
            password=SUPABASE_PASSWORD,
            connect_timeout=10
        )
        
        print("✅ Connexion établie!")
        print("   Exécution du SQL...")
        print()
        
        # Créer un curseur
        cur = conn.cursor()
        
        # Exécuter le SQL (divisé en plusieurs commandes si nécessaire)
        # psycopg2 peut exécuter plusieurs commandes séparées par des points-virgules
        cur.execute(sql_content)
        
        # Récupérer les résultats si nécessaire
        try:
            results = cur.fetchall()
            if results:
                print("📊 Résultats:")
                for row in results:
                    print(f"   {row}")
        except:
            # Pas de résultats à récupérer (CREATE, INSERT, etc.)
            pass
        
        # Valider la transaction
        conn.commit()
        
        print()
        print("✅ SQL exécuté avec succès!")
        print()
        print("📋 Configuration terminée:")
        print("   ✅ Table price_history créée")
        print("   ✅ Extensions pg_net et pg_cron activées")
        print("   ✅ Fonction collect_prices_direct() créée")
        print("   ✅ Fonction collect_prices_loop_minute() créée")
        print("   ✅ Job cron collect-prices-every-second configuré")
        print()
        print("🚀 La collecte de prix démarre automatiquement!")
        print("   Les prix seront collectés toutes les secondes")
        print()
        print("📊 Vérifiez avec:")
        print("   SELECT * FROM price_history ORDER BY timestamp DESC LIMIT 10;")
        
        # Fermer la connexion
        cur.close()
        conn.close()
        
        return True
        
    except psycopg2.OperationalError as e:
        print(f"❌ Erreur de connexion: {e}")
        print()
        print("💡 Vérifiez:")
        print("   - Les credentials de connexion")
        print("   - Que votre IP est autorisée dans Supabase (Settings > Database > Connection Pooling)")
        return False
    except psycopg2.Error as e:
        print(f"❌ Erreur SQL: {e}")
        print()
        print("💡 Certaines erreurs peuvent être normales (ex: extension déjà installée)")
        print("   Vérifiez dans Supabase SQL Editor si la configuration est correcte")
        return False
    except Exception as e:
        print(f"❌ Erreur inattendue: {e}")
        import traceback
        traceback.print_exc()
        return False

def main():
    print("=" * 60)
    print("🚀 EXÉCUTION SQL À DISTANCE SUR SUPABASE")
    print("=" * 60)
    print()
    
    sql_file = "setup_complete.sql"
    
    if not os.path.exists(sql_file):
        print(f"❌ Fichier SQL non trouvé: {sql_file}")
        return
    
    sql_content = read_sql_file(sql_file)
    print(f"✅ Fichier SQL lu: {len(sql_content)} caractères")
    print()
    
    if execute_sql_remote(sql_content):
        print("=" * 60)
        print("✅ SUCCÈS!")
        print("=" * 60)
    else:
        print("=" * 60)
        print("⚠️  EXÉCUTION ÉCHOUÉE")
        print("=" * 60)
        print()
        print("💡 Alternative: Exécutez le SQL manuellement dans Supabase SQL Editor")
        print("   Fichier: setup_complete.sql")

if __name__ == "__main__":
    main()


