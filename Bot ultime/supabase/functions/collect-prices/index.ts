import { createClient } from 'https://esm.sh/@supabase/supabase-js@2.75.0';

Deno.serve(async (req) => {
  try {
    console.log('Starting price collection...');
    
    // Initialize Supabase client with service role for insert permissions
    const supabaseUrl = Deno.env.get('SUPABASE_URL')!;
    const supabaseServiceKey = Deno.env.get('SUPABASE_SERVICE_ROLE_KEY')!;
    const supabase = createClient(supabaseUrl, supabaseServiceKey);

    // Collect BTC (prioritaire) et ETH
    const tokens = ['BTC', 'ETH'];
    const priceData: any[] = [];

    // Call get-dex-prices function to fetch prices using Supabase client
    for (const token of tokens) {
      try {
        const { data: pricesData, error: invokeError } = await supabase.functions.invoke('get-dex-prices', {
          body: { tokens: [token] }
        });
        
        if (invokeError) {
          console.error(`Error calling get-dex-prices for ${token}:`, invokeError);
          continue;
        }
        
        if (pricesData) {
          // Check if response contains an error
          if (pricesData.error) {
            console.error(`Error response from get-dex-prices for ${token}:`, pricesData);
            continue;
          }
          
          if (pricesData.prices) {
            const timestamp = new Date().toISOString();
            
            // Extract Lighter price
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
              console.log(`Lighter ${token}: mid=${mid}, bid=${bid}, ask=${ask}`);
            }
            
            // Extract Paradex price
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
              console.log(`Paradex ${token}: mid=${mid}, bid=${bid}, ask=${ask}`);
            }
          }
        }
      } catch (error) {
        console.error(`Error processing ${token}:`, error);
      }
    }

    // Insert collected prices into database
    // BTC va dans price_history_btc, ETH dans price_history
    if (priceData.length > 0) {
      const btcData = priceData.filter(p => p.token === 'BTC');
      const ethData = priceData.filter(p => p.token === 'ETH');
      
      // Insert BTC into price_history_btc
      if (btcData.length > 0) {
        const { error: btcError } = await supabase
          .from('price_history_btc')
          .insert(btcData);
        
        if (btcError) {
          console.error('Error inserting BTC prices:', btcError);
        } else {
          console.log(`Successfully inserted ${btcData.length} BTC price records`);
        }
      }
      
      // Insert ETH into price_history
      if (ethData.length > 0) {
        const { error: ethError } = await supabase
          .from('price_history')
          .insert(ethData);
        
        if (ethError) {
          console.error('Error inserting ETH prices:', ethError);
        } else {
          console.log(`Successfully inserted ${ethData.length} ETH price records`);
        }
      }
    } else {
      console.log('No prices to insert');
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
    console.error('Price collection error:', error);
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
