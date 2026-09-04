import React from 'react';
import StatCards from '../components/StatCards';
import IPOCard from '../components/IPOCard';
import Disclaimer from '../components/Disclaimer';
import { ArrowRight, Flame, Sparkles, TrendingUp } from 'lucide-react';

export default function Home({ ipos, stats, onSelectIPO, onNavigateToList }) {
  // Filter sections
  const openIPOs = ipos.filter(i => i.status === 'Open');
  const upcomingIPOs = ipos.filter(i => i.status === 'Upcoming');
  const closedIPOs = ipos.filter(i => i.status === 'Closed');
  const listedIPOs = ipos.filter(i => i.status === 'Listed');

  return (
    <div className="max-w-7xl mx-auto px-4 sm:px-6 py-6 sm:py-8">
      {/* Hero Welcome & Market Pulse */}
      <div className="mb-6">
        <div className="flex flex-col md:flex-row md:items-end justify-between gap-3 mb-2">
          <div>
            <h1 className="text-2xl sm:text-3xl font-black tracking-tight text-slate-900">
              Indian IPO Intelligence & GMP Dashboard
            </h1>
            <p className="text-slate-600 text-sm mt-1">
              Live tracking for Mainboard and SME IPO price bands, issue dates, subscription multiples, and Grey Market Premiums.
            </p>
          </div>
          <div className="flex items-center gap-2 text-xs font-semibold text-sky-700 bg-sky-50 border border-sky-200 px-3 py-1.5 rounded-lg shrink-0">
            <Sparkles className="w-3.5 h-3.5 text-sky-600" />
            <span>Automatic Data Pipeline &bull; Zero Manual Entry</span>
          </div>
        </div>
      </div>

      {/* Market Stat KPI Cards */}
      <StatCards 
        stats={stats} 
        onSelectFilter={(filter) => onNavigateToList(filter)} 
      />

      {/* SECTION 1: Currently Open IPOs */}
      <section className="mb-10">
        <div className="flex items-center justify-between mb-4">
          <div className="flex items-center gap-2">
            <span className="w-3 h-3 rounded-full bg-emerald-500 animate-ping"></span>
            <h2 className="text-lg sm:text-xl font-bold text-slate-900">
              Currently Open IPOs
            </h2>
            <span className="text-xs font-bold px-2 py-0.5 rounded-full bg-emerald-100 text-emerald-800">
              {openIPOs.length} Active
            </span>
          </div>
          {openIPOs.length > 0 && (
            <button
              onClick={() => onNavigateToList({ status: 'Open' })}
              className="text-xs font-semibold text-sky-600 hover:text-sky-800 flex items-center gap-1 group"
            >
              View all open <ArrowRight className="w-3.5 h-3.5 group-hover:translate-x-0.5 transition-transform" />
            </button>
          )}
        </div>

        {openIPOs.length > 0 ? (
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4 sm:gap-6">
            {openIPOs.map(ipo => (
              <IPOCard key={ipo.id} ipo={ipo} onSelect={onSelectIPO} />
            ))}
          </div>
        ) : (
          <div className="bg-white rounded-xl border border-slate-200 p-8 text-center text-slate-500">
            No IPOs are currently accepting bids today. Check the Upcoming section below!
          </div>
        )}
      </section>

      {/* SECTION 2: Upcoming IPOs */}
      <section className="mb-10">
        <div className="flex items-center justify-between mb-4">
          <div className="flex items-center gap-2">
            <h2 className="text-lg sm:text-xl font-bold text-slate-900">
              Upcoming IPOs
            </h2>
            <span className="text-xs font-bold px-2 py-0.5 rounded-full bg-sky-100 text-sky-800">
              {upcomingIPOs.length} Announced
            </span>
          </div>
          {upcomingIPOs.length > 0 && (
            <button
              onClick={() => onNavigateToList({ status: 'Upcoming' })}
              className="text-xs font-semibold text-sky-600 hover:text-sky-800 flex items-center gap-1 group"
            >
              View all upcoming <ArrowRight className="w-3.5 h-3.5 group-hover:translate-x-0.5 transition-transform" />
            </button>
          )}
        </div>

        {upcomingIPOs.length > 0 ? (
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4 sm:gap-6">
            {upcomingIPOs.map(ipo => (
              <IPOCard key={ipo.id} ipo={ipo} onSelect={onSelectIPO} />
            ))}
          </div>
        ) : (
          <div className="bg-white rounded-xl border border-slate-200 p-8 text-center text-slate-500">
            No upcoming IPOs announced yet.
          </div>
        )}
      </section>

      {/* SECTION 3: Recently Closed & Listed IPOs */}
      <section className="mb-10">
        <div className="flex items-center justify-between mb-4">
          <h2 className="text-lg sm:text-xl font-bold text-slate-900">
            Recently Closed & Listed
          </h2>
          <button
            onClick={() => onNavigateToList({ status: 'Closed' })}
            className="text-xs font-semibold text-sky-600 hover:text-sky-800 flex items-center gap-1 group"
          >
            View history <ArrowRight className="w-3.5 h-3.5 group-hover:translate-x-0.5 transition-transform" />
          </button>
        </div>

        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4 sm:gap-6">
          {[...closedIPOs, ...listedIPOs].slice(0, 6).map(ipo => (
            <IPOCard key={ipo.id} ipo={ipo} onSelect={onSelectIPO} />
          ))}
        </div>
      </section>

      {/* Mandatory Regulatory Disclaimer */}
      <Disclaimer />
    </div>
  );
}
