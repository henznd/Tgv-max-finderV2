'use client';

import React, { useState } from 'react';
import TabNavigation from '@/components/TabNavigation';
import ManualArbitrage from '@/components/ManualArbitrage';
import ArbitrageOpportunities from '@/components/ArbitrageOpportunities';

export default function Home() {
  const [activeTab, setActiveTab] = useState<'manual' | 'api'>('manual');
  const [selectedSport, setSelectedSport] = useState('');
  const [selectedBookmaker, setSelectedBookmaker] = useState('');

  return (
    <main className="min-h-screen bg-gray-50 py-8">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        <h1 className="text-3xl font-bold text-gray-900 mb-8">
          Arbitrage Calculator v2
        </h1>
        
        <TabNavigation activeTab={activeTab} onTabChange={setActiveTab} />

        {activeTab === 'manual' ? (
          <ManualArbitrage />
        ) : (
          <div>
            <div className="bg-white rounded-lg shadow-lg p-6 mb-6">
              <h2 className="text-2xl font-bold mb-6">
                Sélectionnez un Sport et un Bookmaker
              </h2>
              <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">
                    Sport
                  </label>
                  <select
                    value={selectedSport}
                    onChange={(e) => setSelectedSport(e.target.value)}
                    className="w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm focus:outline-none focus:ring-2 focus:ring-blue-500"
                  >
                    <option value="">Sélectionnez un sport</option>
                    <option value="soccer_france_ligue_1">Ligue 1</option>
                    <option value="soccer_france_ligue_2">Ligue 2</option>
                    <option value="soccer_uefa_champs_league">Champions League</option>
                  </select>
                </div>
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">
                    Bookmaker
                  </label>
                  <select
                    value={selectedBookmaker}
                    onChange={(e) => setSelectedBookmaker(e.target.value)}
                    className="w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm focus:outline-none focus:ring-2 focus:ring-blue-500"
                  >
                    <option value="">Sélectionnez un bookmaker</option>
                    <option value="betclic">Betclic</option>
                    <option value="winamax">Winamax</option>
                    <option value="unibet">Unibet</option>
                  </select>
                </div>
              </div>
            </div>
            <ArbitrageOpportunities 
              sportKey={selectedSport} 
              selectedBookmaker={selectedBookmaker} 
            />
          </div>
        )}
      </div>
    </main>
  );
} 