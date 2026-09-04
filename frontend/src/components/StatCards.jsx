import React from 'react';
import { TrendingUp, Layers, Calendar, CheckCircle2, Award } from 'lucide-react';

export default function StatCards({ stats, onSelectFilter }) {
  if (!stats) return null;

  const topGainer = stats.top_gmp_gainers && stats.top_gmp_gainers.length > 0 ? stats.top_gmp_gainers[0] : null;

  return (
    <div className="grid grid-cols-2 md:grid-cols-4 lg:grid-cols-5 gap-3 sm:gap-4 mb-8">
      {/* Open IPOs */}
      <button
        onClick={() => onSelectFilter({ status: 'Open' })}
        className="bg-white p-4 rounded-xl border border-slate-200 hover:border-emerald-400 hover:shadow-md transition-all text-left group"
      >
        <div className="flex items-center justify-between mb-2">
          <span className="text-xs font-semibold text-slate-500 uppercase tracking-wider">Open Now</span>
          <span className="p-1.5 rounded-lg bg-emerald-50 text-emerald-600 group-hover:bg-emerald-600 group-hover:text-white transition-colors">
            <span className="w-2 h-2 rounded-full bg-emerald-500 inline-block animate-ping"></span>
          </span>
        </div>
        <div className="text-2xl font-black text-slate-900">{stats.open_ipos_count}</div>
        <p className="text-[11px] text-emerald-600 font-medium mt-1 flex items-center gap-1">
          Accepting applications
        </p>
      </button>

      {/* Upcoming IPOs */}
      <button
        onClick={() => onSelectFilter({ status: 'Upcoming' })}
        className="bg-white p-4 rounded-xl border border-slate-200 hover:border-sky-400 hover:shadow-md transition-all text-left group"
      >
        <div className="flex items-center justify-between mb-2">
          <span className="text-xs font-semibold text-slate-500 uppercase tracking-wider">Upcoming</span>
          <span className="p-1.5 rounded-lg bg-sky-50 text-sky-600 group-hover:bg-sky-600 group-hover:text-white transition-colors">
            <Calendar className="w-4 h-4" />
          </span>
        </div>
        <div className="text-2xl font-black text-slate-900">{stats.upcoming_ipos_count}</div>
        <p className="text-[11px] text-sky-600 font-medium mt-1">
          Announced issues
        </p>
      </button>

      {/* Recently Closed */}
      <button
        onClick={() => onSelectFilter({ status: 'Closed' })}
        className="bg-white p-4 rounded-xl border border-slate-200 hover:border-amber-400 hover:shadow-md transition-all text-left group"
      >
        <div className="flex items-center justify-between mb-2">
          <span className="text-xs font-semibold text-slate-500 uppercase tracking-wider">Closed</span>
          <span className="p-1.5 rounded-lg bg-amber-50 text-amber-600 group-hover:bg-amber-600 group-hover:text-white transition-colors">
            <Layers className="w-4 h-4" />
          </span>
        </div>
        <div className="text-2xl font-black text-slate-900">{stats.recently_closed_count}</div>
        <p className="text-[11px] text-amber-600 font-medium mt-1">
          Awaiting allotment/listing
        </p>
      </button>

      {/* SME IPOs */}
      <button
        onClick={() => onSelectFilter({ ipoType: 'SME' })}
        className="bg-white p-4 rounded-xl border border-slate-200 hover:border-purple-400 hover:shadow-md transition-all text-left group"
      >
        <div className="flex items-center justify-between mb-2">
          <span className="text-xs font-semibold text-slate-500 uppercase tracking-wider">SME Segment</span>
          <span className="p-1.5 rounded-lg bg-purple-50 text-purple-600 group-hover:bg-purple-600 group-hover:text-white transition-colors">
            <CheckCircle2 className="w-4 h-4" />
          </span>
        </div>
        <div className="text-2xl font-black text-slate-900">{stats.sme_count}</div>
        <p className="text-[11px] text-purple-600 font-medium mt-1">
          NSE Emerge & BSE SME
        </p>
      </button>

      {/* Top GMP Gainer */}
      <div className="col-span-2 md:col-span-4 lg:col-span-1 bg-gradient-to-br from-slate-900 to-slate-800 text-white p-4 rounded-xl border border-slate-700 shadow-sm flex flex-col justify-between">
        <div className="flex items-center justify-between mb-1">
          <span className="text-xs font-semibold text-slate-400 uppercase tracking-wider flex items-center gap-1">
            <Award className="w-3.5 h-3.5 text-amber-400" />
            Top GMP Gain
          </span>
          <span className="text-[10px] bg-emerald-500/20 text-emerald-400 px-1.5 py-0.5 rounded font-mono font-bold">
            +{topGainer ? topGainer.estimated_gain_percent : 0}%
          </span>
        </div>
        {topGainer ? (
          <div>
            <div className="font-bold text-sm text-slate-100 truncate">{topGainer.company_name}</div>
            <div className="text-xs text-slate-400 mt-0.5">
              GMP: <span className="text-emerald-400 font-bold font-mono">₹{topGainer.current_gmp}</span> &bull; Est. ₹{topGainer.estimated_listing_price}
            </div>
          </div>
        ) : (
          <div className="text-xs text-slate-400">Tracking active GMP...</div>
        )}
      </div>
    </div>
  );
}
