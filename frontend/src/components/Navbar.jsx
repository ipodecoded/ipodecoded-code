import React, { useState } from 'react';
import { TrendingUp, RefreshCw, Search, ShieldAlert, CheckCircle2 } from 'lucide-react';

export default function Navbar({ activePage, setActivePage, onSearch, searchQuery, onRefresh, isRefreshing }) {
  return (
    <header className="sticky top-0 z-50 bg-white border-b border-slate-200 shadow-sm">
      {/* Top Banner */}
      <div className="bg-slate-900 text-slate-300 text-xs py-1.5 px-4 sm:px-6">
        <div className="max-w-7xl mx-auto flex flex-wrap justify-between items-center gap-2">
          <div className="flex items-center gap-2">
            <span className="inline-block w-2 h-2 rounded-full bg-emerald-400 animate-pulse"></span>
            <span>Indian Primary Markets Data Feed &bull; Live Updates</span>
            <span className="text-slate-500">|</span>
            <span className="text-slate-400">A Subsidiary of <a href="https://journaldecoded.in" target="_blank" rel="noreferrer" className="text-sky-400 hover:underline font-medium">JournalDecoded.in</a></span>
          </div>
          <div className="flex items-center gap-3 text-[11px] text-slate-400">
            <span>Unofficial GMP data updated hourly</span>
            <span className="hidden sm:inline">&bull;</span>
            <span className="hidden sm:inline">100% Automated Pipeline</span>
          </div>
        </div>
      </div>

      {/* Main Header */}
      <div className="max-w-7xl mx-auto px-4 sm:px-6 py-3.5 flex flex-col md:flex-row items-center justify-between gap-4">
        {/* Logo & Brand */}
        <div className="flex items-center justify-between w-full md:w-auto">
          <button 
            onClick={() => setActivePage({ name: 'home' })}
            className="flex items-center gap-3 text-left group focus:outline-none"
          >
            <img
              src="/ipo-decoded-logo.png"
              alt="IPODecoded Logo"
              className="w-10 h-10 rounded-xl object-cover bg-black shadow-md shadow-slate-900/15 group-hover:scale-105 transition-transform"
            />
            <div>
              <div className="flex items-center gap-1.5">
                <span className="text-xl font-black tracking-tight text-slate-900">IPO<span className="text-sky-600">Decoded</span></span>
                <span className="text-[10px] font-semibold uppercase tracking-wider px-1.5 py-0.5 rounded bg-sky-100 text-sky-800">V1 Live</span>
              </div>
              <p className="text-[11px] text-slate-500 font-medium">By JournalDecoded.in &bull; Automatic IPO Intelligence</p>
            </div>
          </button>

          {/* Refresh Button on Mobile */}
          <button
            onClick={onRefresh}
            disabled={isRefreshing}
            className="md:hidden p-2 text-slate-600 hover:text-sky-600 rounded-lg border border-slate-200"
            title="Refresh Data"
          >
            <RefreshCw className={`w-4 h-4 ${isRefreshing ? 'animate-spin text-sky-600' : ''}`} />
          </button>
        </div>

        {/* Global Search Bar */}
        <div className="w-full md:max-w-md relative">
          <Search className="w-4 h-4 text-slate-400 absolute left-3.5 top-1/2 -translate-y-1/2" />
          <input
            type="text"
            placeholder="Search IPOs (e.g. Bajaj Housing, Swiggy, SME)..."
            value={searchQuery}
            onChange={(e) => onSearch(e.target.value)}
            className="w-full pl-10 pr-4 py-2 text-sm bg-slate-50 border border-slate-200 rounded-lg focus:bg-white focus:outline-none focus:ring-2 focus:ring-sky-500/20 focus:border-sky-500 transition-all placeholder:text-slate-400"
          />
        </div>

        {/* Navigation Actions */}
        <div className="flex items-center gap-2 sm:gap-3 w-full md:w-auto justify-between md:justify-end">
          <nav className="flex items-center gap-1 bg-slate-100 p-1 rounded-lg text-xs font-medium text-slate-600">
            <button
              onClick={() => setActivePage({ name: 'home' })}
              className={`px-3 py-1.5 rounded-md transition-all ${
                activePage.name === 'home'
                  ? 'bg-white text-slate-900 shadow-sm font-semibold'
                  : 'hover:text-slate-900 hover:bg-slate-200/60'
              }`}
            >
              Dashboard
            </button>
            <button
              onClick={() => setActivePage({ name: 'list', filter: { status: 'All' } })}
              className={`px-3 py-1.5 rounded-md transition-all ${
                activePage.name === 'list' && (!activePage.filter || activePage.filter.status === 'All')
                  ? 'bg-white text-slate-900 shadow-sm font-semibold'
                  : 'hover:text-slate-900 hover:bg-slate-200/60'
              }`}
            >
              All IPOs
            </button>
            <button
              onClick={() => setActivePage({ name: 'list', filter: { ipoType: 'SME' } })}
              className={`px-3 py-1.5 rounded-md transition-all ${
                activePage.name === 'list' && activePage.filter?.ipoType === 'SME'
                  ? 'bg-white text-slate-900 shadow-sm font-semibold'
                  : 'hover:text-slate-900 hover:bg-slate-200/60'
              }`}
            >
              SME IPOs
            </button>
          </nav>

          <button
            onClick={onRefresh}
            disabled={isRefreshing}
            className="hidden md:flex items-center gap-2 px-3 py-1.5 text-xs font-semibold text-sky-700 bg-sky-50 hover:bg-sky-100 border border-sky-200 rounded-lg transition-colors disabled:opacity-50"
            title="Trigger automated pipeline data check"
          >
            <RefreshCw className={`w-3.5 h-3.5 ${isRefreshing ? 'animate-spin text-sky-600' : ''}`} />
            <span>{isRefreshing ? 'Syncing...' : 'Sync Live'}</span>
          </button>
        </div>
      </div>
    </header>
  );
}
