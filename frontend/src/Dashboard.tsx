import React, { useState, useEffect } from 'react';

const Dashboard = () => {
  const [metrics, setMetrics] = useState<any>(null);

  useEffect(() => {
    fetch('/api/account/metrics')
      .then(res => res.json())
      .then(data => setMetrics(data));
  }, []);

  if (!metrics) return <div className="text-white">Scanning account...</div>;

  return (
    <div className="min-h-screen bg-black p-10 font-mono text-white">
      <header className="border-b border-gray-800 pb-5 mb-10 flex justify-between items-center">
        <h1 className="text-4xl font-bold tracking-tighter">THALAIVA COMMAND</h1>
        <div className="px-4 py-1 bg-green-900 text-green-400 rounded text-xs animate-pulse">
          LIVE CONNECTION
        </div>
      </header>

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
    </div>
  );
};

export default Dashboard;
