'use client';

import { useState, useEffect } from 'react';
import DatePicker from 'react-datepicker';
import 'react-datepicker/dist/react-datepicker.css';

// Définition du type pour un trajet
interface Train {
  origine: string;
  destination: string;
  date: string;
  heure_depart: string;
  heure_arrivee: string;
  duree: string;
}

export default function Home() {
  // États pour les paramètres de base
  const [origin, setOrigin] = useState('PARIS');
  const [destination, setDestination] = useState('');
  const [departDate, setDepartDate] = useState<Date | null>(new Date());
  const [returnDate, setReturnDate] = useState('');
  const [dateRangeDays, setDateRangeDays] = useState(7);
  const [results, setResults] = useState<Train[]>([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  // Fonction pour obtenir la date du jour au format YYYY-MM-DD
  const getTodayString = () => {
    const today = new Date();
    const yyyy = today.getFullYear();
    const mm = String(today.getMonth() + 1).padStart(2, '0');
    const dd = String(today.getDate()).padStart(2, '0');
    return `${yyyy}-${mm}-${dd}`;
  };

  // Initialiser les dates avec la date du jour
  useEffect(() => {
    const todayStr = getTodayString();
    setDepartDate(new Date(todayStr));
    setReturnDate(todayStr);
  }, []);

  const handleSearch = async () => {
    setLoading(true);
    setResults([]);
    setError(null);
    try {
      const response = await fetch(
        `http://localhost:8000/api/trains/single?date=${departDate?.toISOString().split('T')[0]}&origin=${origin}${destination ? `&destination=${destination}` : ''}`
      );
      if (!response.ok) {
        throw new Error('La recherche a échoué. Veuillez réessayer.');
      }
      const data: Train[] = await response.json();
      setResults(data);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Une erreur inconnue est survenue.');
    } finally {
      setLoading(false);
    }
  };

  return (
    <main className="flex min-h-screen flex-col items-center p-4 sm:p-8 md:p-24 bg-gray-50 text-gray-800">
      <div className="z-10 w-full max-w-5xl flex flex-col items-center justify-between font-mono text-sm">
        <h1 className="text-3xl sm:text-4xl lg:text-5xl font-bold text-center text-blue-600 mb-4">
          TGV Max Finder
        </h1>
        <p className="text-gray-500 mb-8 text-center">
          Trouvez vos trajets en TGV Max en quelques clics.
        </p>
      </div>

      <div className="w-full max-w-2xl bg-white p-6 sm:p-8 rounded-xl shadow-lg">
        <div className="grid grid-cols-1 md:grid-cols-2 gap-4 mb-6">
          <div>
            <label htmlFor="origin" className="block text-sm font-medium text-gray-700 mb-1">
              Ville de départ
            </label>
            <input
              type="text"
              id="origin"
              value={origin}
              onChange={(e) => setOrigin(e.target.value)}
              className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500 transition"
              placeholder="Ex: Paris"
            />
          </div>
          <div>
            <label htmlFor="destination" className="block text-sm font-medium text-gray-700 mb-1">
              Ville d'arrivée (optionnel)
            </label>
            <input
              type="text"
              id="destination"
              value={destination}
              onChange={(e) => setDestination(e.target.value)}
              className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500 transition"
              placeholder="Ex: Lyon"
            />
          </div>
          <div className="md:col-span-2">
            <label htmlFor="date" className="block text-sm font-medium text-gray-700 mb-1">
              Date de départ
            </label>
            <DatePicker
              selected={departDate}
              onChange={(date: Date) => setDepartDate(date)}
              dateFormat="yyyy-MM-dd"
              className="border rounded px-2 py-1"
              todayButton="Aujourd'hui"
            />
          </div>
        </div>
        <button
          onClick={handleSearch}
          disabled={loading}
          className="w-full bg-blue-600 text-white font-bold py-3 px-6 rounded-lg hover:bg-blue-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-blue-500 transition duration-300 disabled:bg-blue-300"
        >
          {loading ? 'Recherche en cours...' : 'Rechercher les trains'}
        </button>
      </div>

      <div className="mt-12 w-full max-w-5xl">
        {error && (
          <div className="bg-red-100 border border-red-400 text-red-700 px-4 py-3 rounded-lg relative" role="alert">
            <strong className="font-bold">Erreur : </strong>
            <span className="block sm:inline">{error}</span>
          </div>
        )}
        {results.length > 0 ? (
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
            {results.map((train: Train, index: number) => (
              <div key={index} className="bg-white p-6 rounded-xl shadow-lg hover:shadow-xl transition-shadow duration-300">
                <div className="flex justify-between items-center mb-2">
                  <p className="font-bold text-lg text-blue-600">{train.origine}</p>
                  <p className="font-bold text-lg text-blue-600">→</p>
                  <p className="font-bold text-lg text-blue-600">{train.destination}</p>
                </div>
                <div className="text-sm text-gray-600">
                  <p><strong>Date :</strong> {train.date}</p>
                  <p><strong>Départ :</strong> {train.heure_depart}</p>
                  <p><strong>Arrivée :</strong> {train.heure_arrivee}</p>
                  <p><strong>Durée :</strong> {train.duree}</p>
                </div>
              </div>
            ))}
          </div>
        ) : (
          !loading && <p className="text-center text-gray-500 mt-8">Aucun résultat à afficher. Lancez une recherche !</p>
        )}
      </div>
    </main>
  );
} 