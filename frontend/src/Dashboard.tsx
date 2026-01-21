import React, { useState, useEffect } from 'react';

const Dashboard = () => {
  const [metrics, setMetrics] = useState<any>(null);
  const [connected, setConnected] = useState(false);
  const [loading, setLoading] = useState(true);

  // Login State
  const [refreshToken, setRefreshToken] = useState('');
  const [clientSecret, setClientSecret] = useState('');
  const [error, setError] = useState('');

  const checkStatus = () => {
    fetch('/api/auth/status')
      .then(res => res.json())
      .then(data => {
        if (data.status === 'connected') {
            setConnected(true);
            fetchMetrics();
        } else {
            setConnected(false);
            setLoading(false);
        }
      })
      .catch(() => setLoading(false));
  };

  const fetchMetrics = () => {
    fetch('/api/account/metrics')
      .then(res => {
          if (res.status === 401) {
              setConnected(false);
              return null;
          }
          return res.json();
      })
      .then(data => {
          if (data && !data.error) {
            setMetrics(data);
          }
          setLoading(false);
      })
      .catch(() => setLoading(false));
  };

  useEffect(() => {
    checkStatus();
    const interval = setInterval(() => {
        if (connected) fetchMetrics();
    }, 10000);
    return () => clearInterval(interval);
  }, [connected]);

  const handleLogin = async (e: React.FormEvent) => {
    e.preventDefault();
    setError('');
    setLoading(true);

    try {
        const res = await fetch('/api/auth/login', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ refresh_token: refreshToken, provider_secret: clientSecret })
        });
        const data = await res.json();

        if (res.ok) {
            setConnected(true);
            fetchMetrics();
        } else {
            setError(data.message || 'Login failed');
            setLoading(false);
        }
    } catch (err) {
        setError('Network error');
        setLoading(false);
    }
  };

  if (loading && !metrics && !error && !connected) return <div className="text-white bg-black min-h-screen p-10 font-mono">Scanning account...</div>;

  if (!connected) {
      return (
        <div className="min-h-screen bg-black p-10 font-mono text-white flex flex-col items-center justify-center">
            <h1 className="text-4xl font-bold tracking-tighter mb-8">THALAIVA COMMAND</h1>
            <div className="bg-zinc-900 p-8 border border-zinc-800 rounded-lg w-full max-w-md">
                <h2 className="text-xl mb-4">AUTHENTICATION REQUIRED</h2>
                {error && <div className="bg-red-900/50 p-2 text-red-200 text-sm mb-4 border border-red-800">{error}</div>}
                <p className="text-xs text-zinc-500 mb-6">
                    Enter your Tastytrade API credentials to connect.
                </p>
                <form onSubmit={handleLogin} className="space-y-4">
                    <div>
                        <label className="block text-xs uppercase text-zinc-500 mb-1">Refresh Token (JWT)</label>
                        <input
                            type="text"
                            className="w-full bg-black border border-zinc-700 p-2 text-white rounded focus:border-green-500 outline-none"
                            value={refreshToken}
                            onChange={e => setRefreshToken(e.target.value)}
                            placeholder="Enter your Refresh Token"
                        />
                        <div className="text-[10px] text-zinc-600 mt-1">Not a Client ID. Use auth script if needed.</div>
                    </div>
                    <div>
                        <label className="block text-xs uppercase text-zinc-500 mb-1">Client Secret</label>
                        <input
                            type="password"
                            className="w-full bg-black border border-zinc-700 p-2 text-white rounded focus:border-green-500 outline-none"
                            value={clientSecret}
                            onChange={e => setClientSecret(e.target.value)}
                            placeholder="Enter your Client Secret"
                        />
                    </div>
                    <button
                        type="submit"
                        disabled={loading}
                        className="w-full bg-green-900 hover:bg-green-800 text-green-100 py-3 rounded font-bold uppercase tracking-wider transition-colors disabled:opacity-50"
                    >
                        {loading ? 'Connecting...' : 'Connect to Casino'}
                    </button>
                </form>
            </div>
        </div>
      );
  }

  return (
    <div className="min-h-screen bg-black p-10 font-mono text-white">
      <header className="border-b border-gray-800 pb-5 mb-10 flex justify-between items-center">
        <h1 className="text-4xl font-bold tracking-tighter">THALAIVA COMMAND</h1>
        <div className="px-4 py-1 bg-green-900 text-green-400 rounded text-xs animate-pulse">
          LIVE CONNECTION
        </div>
      </header>

      {metrics ? (
      <main className="grid grid-cols-1 md:grid-cols-3 gap-8">
        {/* Metric Card: Net Liq */}
        <div className="bg-zinc-900 p-8 border border-zinc-800 rounded-lg">
          <p className="text-zinc-500 text-xs uppercase mb-2">Portfolio Value</p>
          <p className="text-5xl font-bold">${metrics.net_liq}</p>
          <p className="text-zinc-600 text-xs mt-4">DEFENDING $10,000 LINE</p>
        </div>

        {/* Metric Card: BP Usage */}
        <div className={`p-8 border rounded-lg ${metrics.bp_usage > 30 ? 'bg-red-900/20 border-red-500' : 'bg-zinc-900 border-zinc-800'}`}>
          <p className="text-zinc-500 text-xs uppercase mb-2">BP Usage (%)</p>
          <p className="text-5xl font-bold">{metrics.bp_usage}%</p>
          <p className={`text-sm mt-4 font-bold ${metrics.bp_usage > 30 ? 'text-red-400' : 'text-green-400'}`}>
            VERDICT: {metrics.verdict}
          </p>
        </div>

        {/* Metric Card: Active Positions */}
        <div className="bg-zinc-900 p-8 border border-zinc-800 rounded-lg">
          <p className="text-zinc-500 text-xs uppercase mb-2">In Play</p>
          <p className="text-5xl font-bold">{metrics.positions_count}</p>
          <p className="text-zinc-600 text-xs mt-4 font-mono italic">"WE ARE THE CASINO"</p>
        </div>
      </main>
      ) : (
          <div className="text-zinc-500">Scanning account metrics...</div>
      )}
    </div>
  );
};

export default Dashboard;
