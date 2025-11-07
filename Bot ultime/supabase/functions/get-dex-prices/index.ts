import "https://deno.land/x/xhr@0.1.0/mod.ts";
import { serve } from "https://deno.land/std@0.168.0/http/server.ts";

const corsHeaders = {
  'Access-Control-Allow-Origin': '*',
  'Access-Control-Allow-Headers': 'authorization, x-client-info, apikey, content-type',
};

// Map tokens to Lighter market IDs
const LIGHTER_MARKET_IDS: Record<string, number> = {
  'BTC': 1,
  'ETH': 0,  // Correct market ID for ETH
  'BNB': 25,
  'SOL': 2
};

serve(async (req) => {
  // Handle CORS preflight requests
  if (req.method === 'OPTIONS') {
    return new Response(null, { headers: corsHeaders });
  }

  try {
    const { tokens } = await req.json();
    console.log('Fetching prices for tokens:', tokens);

    const prices = {
      lighter: {} as Record<string, { mid: number; bid: number; ask: number }>,
      paradex: {} as Record<string, { mid: number; bid: number; ask: number }>
    };

    // Fetch prices for each token
    for (const token of tokens) {
      // Fetch Lighter price
      try {
        const marketId = LIGHTER_MARKET_IDS[token];
        if (marketId !== undefined) {
          const lighterResponse = await fetch(
            `https://mainnet.zklighter.elliot.ai/api/v1/orderBookOrders?market_id=${marketId}&limit=1`
          );
          
          if (lighterResponse.ok) {
            const lighterData = await lighterResponse.json();
            
            // Get the best bid/ask and calculate mid price
            if (lighterData.asks && lighterData.asks.length > 0 && 
                lighterData.bids && lighterData.bids.length > 0) {
              const bestAsk = parseFloat(lighterData.asks[0].price);
              const bestBid = parseFloat(lighterData.bids[0].price);
              prices.lighter[token] = {
                mid: (bestAsk + bestBid) / 2,
                bid: bestBid,
                ask: bestAsk
              };
            }
          } else {
            console.error(`Lighter API error for ${token}:`, await lighterResponse.text());
          }
        }
      } catch (error) {
        console.error(`Error fetching Lighter price for ${token}:`, error);
      }

      // Fetch Paradex price
      try {
        const marketSymbol = `${token}-USD-PERP`;
        const paradexResponse = await fetch(
          `https://api.prod.paradex.trade/v1/orderbook/${marketSymbol}`
        );
        
        if (paradexResponse.ok) {
          const paradexData = await paradexResponse.json();
          
          // Get the best bid/ask and calculate mid price
          if (paradexData.asks && paradexData.asks.length > 0 && 
              paradexData.bids && paradexData.bids.length > 0) {
            const bestAsk = parseFloat(paradexData.asks[0][0]); // [price, size]
            const bestBid = parseFloat(paradexData.bids[0][0]);
            prices.paradex[token] = {
              mid: (bestAsk + bestBid) / 2,
              bid: bestBid,
              ask: bestAsk
            };
          }
        } else {
          console.error(`Paradex API error for ${token}:`, await paradexResponse.text());
        }
      } catch (error) {
        console.error(`Error fetching Paradex price for ${token}:`, error);
      }
    }

    console.log('Final prices:', prices);

    return new Response(JSON.stringify({ prices }), {
      headers: { ...corsHeaders, 'Content-Type': 'application/json' },
    });
  } catch (error) {
    const errorMessage = error instanceof Error ? error.message : 'Unknown error';
    console.error('Error in get-dex-prices function:', error);
    return new Response(JSON.stringify({ error: errorMessage }), {
      status: 500,
      headers: { ...corsHeaders, 'Content-Type': 'application/json' },
    });
  }
});

