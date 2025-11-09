-- Configuration simple pour collecter les prix en permanence
-- BUT: Collecter en permanence les prix des perps Lighter et Paradex
-- À exécuter dans l'éditeur SQL de Supabase

-- ============================================================================
-- 1. CRÉER LA TABLE POUR STOCKER LES PRIX
-- ============================================================================

CREATE TABLE IF NOT EXISTS price_history (
  id BIGSERIAL PRIMARY KEY,
  timestamp TIMESTAMPTZ NOT NULL DEFAULT NOW(),
  token VARCHAR(10) NOT NULL,
  exchange VARCHAR(20) NOT NULL,
  bid FLOAT NOT NULL,
  ask FLOAT NOT NULL,
  mid FLOAT NOT NULL,
  created_at TIMESTAMPTZ DEFAULT NOW()
);

-- Index pour les requêtes rapides
CREATE INDEX IF NOT EXISTS idx_price_history_timestamp ON price_history(timestamp DESC);
CREATE INDEX IF NOT EXISTS idx_price_history_token ON price_history(token);
CREATE INDEX IF NOT EXISTS idx_price_history_exchange ON price_history(exchange);

-- ============================================================================
-- 2. CRÉER LA FONCTION QUI APPELLE L'EDGE FUNCTION
-- ============================================================================

-- Activer les extensions nécessaires
CREATE EXTENSION IF NOT EXISTS pg_net;
CREATE EXTENSION IF NOT EXISTS pg_cron;

-- Fonction qui appelle l'Edge Function collect-prices
CREATE OR REPLACE FUNCTION call_collect_prices()
RETURNS void
LANGUAGE plpgsql
SECURITY DEFINER
AS $$
DECLARE
  service_role_key TEXT;
BEGIN
  -- Récupérer la clé depuis app_settings
  SELECT value INTO service_role_key 
  FROM app_settings 
  WHERE key = 'service_role_key';
  
  IF service_role_key IS NULL OR service_role_key = '' THEN
    RAISE WARNING 'Service role key non configurée. Configurez-la avec: INSERT INTO app_settings (key, value) VALUES (''service_role_key'', ''VOTRE_CLE'');';
    -- Tentative sans auth
    PERFORM net.http_post(
      url := 'https://jlqdkbdmjuqjqhesxvjg.supabase.co/functions/v1/collect-prices',
      headers := jsonb_build_object('Content-Type', 'application/json'),
      body := '{}'::jsonb
    );
  ELSE
    -- Appel avec authentification
    PERFORM net.http_post(
      url := 'https://jlqdkbdmjuqjqhesxvjg.supabase.co/functions/v1/collect-prices',
      headers := jsonb_build_object(
        'Content-Type', 'application/json',
        'Authorization', 'Bearer ' || service_role_key
      ),
      body := '{}'::jsonb
    );
  END IF;
END;
$$;

-- ============================================================================
-- 3. CRÉER LA FONCTION DE BOUCLE (60 appels = 1 minute)
-- ============================================================================

CREATE OR REPLACE FUNCTION collect_prices_loop_minute()
RETURNS void
LANGUAGE plpgsql
AS $$
DECLARE
  i int := 0;
BEGIN
  WHILE i < 60 LOOP
    BEGIN
      PERFORM call_collect_prices();
    EXCEPTION WHEN OTHERS THEN
      RAISE WARNING 'Erreur appel collect-prices: %', SQLERRM;
    END;
    PERFORM pg_sleep(1.0);  -- Attendre 1 seconde
    i := i + 1;
  END LOOP;
END;
$$;

-- ============================================================================
-- 4. CRÉER LA TABLE app_settings (si elle n'existe pas)
-- ============================================================================

CREATE TABLE IF NOT EXISTS app_settings (
  key TEXT PRIMARY KEY,
  value TEXT NOT NULL,
  created_at TIMESTAMPTZ DEFAULT NOW(),
  updated_at TIMESTAMPTZ DEFAULT NOW()
);

-- ============================================================================
-- 5. CRÉER LE CRON JOB
-- ============================================================================

-- Supprimer l'ancien cron job s'il existe
SELECT cron.unschedule('collect-prices-every-second') 
WHERE EXISTS (
  SELECT 1 FROM cron.job WHERE jobname = 'collect-prices-every-second'
);

-- Créer le nouveau cron job (s'exécute toutes les minutes, fait 60 appels)
SELECT cron.schedule(
  'collect-prices-every-second',
  '* * * * *',  -- Toutes les minutes
  $$SELECT collect_prices_loop_minute();$$
);

-- ============================================================================
-- 6. VÉRIFICATION
-- ============================================================================

SELECT 
  'Cron job créé' as status,
  jobname,
  active,
  schedule
FROM cron.job 
WHERE jobname = 'collect-prices-every-second';

