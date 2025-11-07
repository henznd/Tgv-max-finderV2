-- ============================================================
-- CONFIGURATION : Collecte de prix BTC toutes les secondes
-- ============================================================
-- Table séparée pour BTC

-- ============================================================
-- ÉTAPE 1: Créer la table price_history_btc
-- ============================================================

CREATE TABLE IF NOT EXISTS price_history_btc (
    id BIGSERIAL PRIMARY KEY,
    timestamp TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    token TEXT NOT NULL DEFAULT 'BTC',
    exchange TEXT NOT NULL CHECK (exchange IN ('lighter', 'paradex')),
    bid DECIMAL(20, 8) NOT NULL,
    ask DECIMAL(20, 8) NOT NULL,
    mid DECIMAL(20, 8) NOT NULL,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

-- Créer les index pour améliorer les performances
CREATE INDEX IF NOT EXISTS idx_price_history_btc_timestamp ON price_history_btc(timestamp DESC);
CREATE INDEX IF NOT EXISTS idx_price_history_btc_exchange ON price_history_btc(exchange);
CREATE INDEX IF NOT EXISTS idx_price_history_btc_token_timestamp ON price_history_btc(token, timestamp DESC);

-- Activer Row Level Security (RLS)
ALTER TABLE price_history_btc ENABLE ROW LEVEL SECURITY;

-- Créer une politique pour permettre la lecture publique
DROP POLICY IF EXISTS "Allow public read access" ON price_history_btc;
CREATE POLICY "Allow public read access" ON price_history_btc
    FOR SELECT
    USING (true);

-- Créer une politique pour permettre l'insertion
DROP POLICY IF EXISTS "Allow authenticated insert" ON price_history_btc;
CREATE POLICY "Allow authenticated insert" ON price_history_btc
    FOR INSERT
    WITH CHECK (true);

-- ============================================================
-- ÉTAPE 2: Fonction pour collecter les prix BTC
-- ============================================================

CREATE OR REPLACE FUNCTION collect_prices_btc_direct()
RETURNS void
LANGUAGE plpgsql
SECURITY DEFINER
AS $$
DECLARE
  lighter_result record;
  paradex_result record;
  lighter_bid float;
  lighter_ask float;
  paradex_bid float;
  paradex_ask float;
  timestamp_now timestamp with time zone;
BEGIN
  timestamp_now := now();
  
  -- Collecter les prix depuis Lighter (BTC market_id = 1)
  BEGIN
    SELECT * INTO lighter_result
    FROM net.http_get(
      url := 'https://mainnet.zklighter.elliot.ai/api/v1/orderBookOrders?market_id=1&limit=1',
      headers := '{"Content-Type": "application/json"}'::jsonb
    );
    
    IF lighter_result.status_code = 200 AND lighter_result.content IS NOT NULL THEN
      DECLARE
        lighter_data jsonb;
      BEGIN
        lighter_data := lighter_result.content::jsonb;
        
        IF lighter_data->'asks' IS NOT NULL AND 
           jsonb_array_length(lighter_data->'asks') > 0 AND
           lighter_data->'bids' IS NOT NULL AND 
           jsonb_array_length(lighter_data->'bids') > 0 THEN
          
          lighter_ask := (lighter_data->'asks'->0->>'price')::float;
          lighter_bid := (lighter_data->'bids'->0->>'price')::float;
          
          -- Insérer les prix Lighter
          INSERT INTO price_history_btc (timestamp, token, exchange, bid, ask, mid)
          VALUES (
            timestamp_now,
            'BTC',
            'lighter',
            lighter_bid,
            lighter_ask,
            (lighter_bid + lighter_ask) / 2
          ) ON CONFLICT DO NOTHING;
        END IF;
      EXCEPTION WHEN OTHERS THEN
        RAISE WARNING 'Erreur parsing Lighter BTC: %', SQLERRM;
      END;
    END IF;
  EXCEPTION WHEN OTHERS THEN
    RAISE WARNING 'Erreur collecte Lighter BTC: %', SQLERRM;
  END;
  
  -- Collecter les prix depuis Paradex (BTC-USD-PERP)
  BEGIN
    SELECT * INTO paradex_result
    FROM net.http_get(
      url := 'https://api.prod.paradex.trade/v1/orderbook/BTC-USD-PERP',
      headers := '{"Content-Type": "application/json"}'::jsonb
    );
    
    IF paradex_result.status_code = 200 AND paradex_result.content IS NOT NULL THEN
      DECLARE
        paradex_data jsonb;
      BEGIN
        paradex_data := paradex_result.content::jsonb;
        
        IF paradex_data->'asks' IS NOT NULL AND 
           jsonb_array_length(paradex_data->'asks') > 0 AND
           paradex_data->'bids' IS NOT NULL AND 
           jsonb_array_length(paradex_data->'bids') > 0 THEN
          
          paradex_ask := (paradex_data->'asks'->0->0)::text::float;
          paradex_bid := (paradex_data->'bids'->0->0)::text::float;
          
          -- Insérer les prix Paradex
          INSERT INTO price_history_btc (timestamp, token, exchange, bid, ask, mid)
          VALUES (
            timestamp_now,
            'BTC',
            'paradex',
            paradex_bid,
            paradex_ask,
            (paradex_bid + paradex_ask) / 2
          ) ON CONFLICT DO NOTHING;
        END IF;
      EXCEPTION WHEN OTHERS THEN
        RAISE WARNING 'Erreur parsing Paradex BTC: %', SQLERRM;
      END;
    END IF;
  EXCEPTION WHEN OTHERS THEN
    RAISE WARNING 'Erreur collecte Paradex BTC: %', SQLERRM;
  END;
END;
$$;

-- ============================================================
-- ÉTAPE 3: Fonction qui collecte en boucle (60 fois par minute)
-- ============================================================

CREATE OR REPLACE FUNCTION collect_prices_btc_loop_minute()
RETURNS void
LANGUAGE plpgsql
AS $$
DECLARE
  start_time timestamp;
  end_time timestamp;
  i int;
BEGIN
  start_time := now();
  end_time := start_time + interval '1 minute';
  i := 0;
  
  -- Collecter 60 fois (une fois par seconde pendant 1 minute)
  WHILE now() < end_time LOOP
    PERFORM collect_prices_btc_direct();
    PERFORM pg_sleep(1.0);  -- Attendre 1 seconde
    i := i + 1;
  END LOOP;
  
  RAISE NOTICE 'Collecté BTC % fois en 1 minute', i;
END;
$$;

-- ============================================================
-- ÉTAPE 4: Créer le job cron pour collecter toutes les minutes
-- ============================================================

-- Supprimer le job existant s'il existe
SELECT cron.unschedule('collect-prices-btc-every-second') WHERE EXISTS (
  SELECT 1 FROM cron.job WHERE jobname = 'collect-prices-btc-every-second'
);

-- Créer le nouveau job
SELECT cron.schedule(
  'collect-prices-btc-every-second',
  '* * * * *',  -- Toutes les minutes
  $$SELECT collect_prices_btc_loop_minute();$$
);

-- ============================================================
-- ÉTAPE 5: Vérifier que tout est configuré
-- ============================================================

-- Vérifier que le job est créé
SELECT 
  jobid,
  schedule,
  command,
  active,
  jobname
FROM cron.job 
WHERE jobname = 'collect-prices-btc-every-second';

-- Afficher un message de confirmation
DO $$
BEGIN
  RAISE NOTICE '✅ Configuration BTC terminée!';
  RAISE NOTICE '   La collecte de prix BTC démarre automatiquement';
  RAISE NOTICE '   Les prix seront collectés toutes les secondes';
  RAISE NOTICE '   Table: price_history_btc';
  RAISE NOTICE '   Vérifiez avec: SELECT * FROM price_history_btc ORDER BY timestamp DESC LIMIT 10;';
END $$;

-- ============================================================
-- COMMANDES UTILES
-- ============================================================

-- Pour tester manuellement la collecte BTC:
-- SELECT collect_prices_btc_direct();

-- Pour tester la boucle (1 minute):
-- SELECT collect_prices_btc_loop_minute();

-- Pour arrêter la collecte BTC:
-- SELECT cron.unschedule('collect-prices-btc-every-second');

-- Pour redémarrer la collecte BTC:
-- SELECT cron.schedule('collect-prices-btc-every-second', '* * * * *', $$SELECT collect_prices_btc_loop_minute();$$);

-- Pour voir les dernières collectes BTC:
-- SELECT * FROM price_history_btc ORDER BY timestamp DESC LIMIT 20;

-- Pour voir les statistiques BTC:
-- SELECT 
--   exchange,
--   COUNT(*) as count,
--   MIN(timestamp) as first,
--   MAX(timestamp) as last,
--   AVG(mid) as avg_price
-- FROM price_history_btc
-- GROUP BY exchange;

