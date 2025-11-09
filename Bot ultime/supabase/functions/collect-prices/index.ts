// Edge Function simple pour collecter les prix des perps Lighter et Paradex
// BUT: Collecter les prix et les stocker dans price_history

import { createClient } from 'https://esm.sh/@supabase/supabase-js@2.75.0';

Deno.serve(async (req) => {
  try {
    console.log('🚀 Starting price collection...');
    
    // Initialize Supabase client
    const supabaseUrl = Deno.env.get('SUPABASE_URL')!;
    const supabaseServiceKey = Deno.env.get('SUPABASE_SERVICE_ROLE_KEY')!;
    const supabase = createClient(supabaseUrl, supabaseServiceKey);

    // Tokens à collecter: BTC et ETH
    const tokens = ['BTC', 'ETH'];
    const priceData: any[] = [];

    // Pour chaque token, récupérer les prix depuis get-dex-prices
    for (const token of tokens) {
      try {
        const { data: pricesData, error: invokeError } = await supabase.functions.invoke('get-dex-prices', {
          body: { tokens: [token] }
        });
        
        if (invokeError) {
          console.error(`❌ Error calling get-dex-prices for ${token}:`, invokeError);
          continue;
        }
        
        if (pricesData?.prices) {
          const timestamp = new Date().toISOString();
          
          // Extraire prix Lighter
          if (pricesData.prices.lighter?.[token]) {
            const { mid, bid, ask } = pricesData.prices.lighter[token];
            priceData.push({
              timestamp,
              token,
              exchange: 'lighter',
              mid,
              bid,
              ask
            });
            console.log(`✅ Lighter ${token}: mid=${mid}, bid=${bid}, ask=${ask}`);
          }
          
          // Extraire prix Paradex
          if (pricesData.prices.paradex?.[token]) {
            const { mid, bid, ask } = pricesData.prices.paradex[token];
            priceData.push({
              timestamp,
              token,
              exchange: 'paradex',
              mid,
              bid,
              ask
            });
            console.log(`✅ Paradex ${token}: mid=${mid}, bid=${bid}, ask=${ask}`);
          }
        }
      } catch (error) {
        console.error(`❌ Error processing ${token}:`, error);
      }
    }

    // Insérer tous les prix dans price_history (une seule table pour tous les tokens)
    if (priceData.length > 0) {
      const { error: insertError } = await supabase
        .from('price_history')
        .insert(priceData);
      
      if (insertError) {
        console.error('❌ Error inserting prices:', insertError);
        return new Response(
          JSON.stringify({ 
            success: false, 
            error: insertError.message 
          }),
          { 
            headers: { 'Content-Type': 'application/json' },
            status: 500 
          }
        );
      } else {
        console.log(`✅ Successfully inserted ${priceData.length} price records`);
      }
    } else {
      console.log('⚠️ No prices to insert');
    }

    return new Response(
      JSON.stringify({ 
        success: true, 
        inserted: priceData.length,
        message: 'Price collection completed'
      }),
      { 
        headers: { 'Content-Type': 'application/json' },
        status: 200 
      }
    );
    
  } catch (error) {
    console.error('❌ Price collection error:', error);
    const errorMessage = error instanceof Error ? error.message : 'Unknown error';
    return new Response(
      JSON.stringify({ 
        success: false, 
        error: errorMessage 
      }),
      { 
        headers: { 'Content-Type': 'application/json' },
        status: 500 
      }
    );
  }
});
