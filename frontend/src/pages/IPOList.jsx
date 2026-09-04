import React, { useState } from 'react';
import IPOCard from '../components/IPOCard';
import IPOTable from '../components/IPOTable';
import Disclaimer from '../components/Disclaimer';
import { Filter, LayoutGrid, List, Search, ArrowUpDown, X } from 'lucide-react';

export default function IPOList({ ipos, filter, setFilter, onSelectIPO, searchQuery, onSearch }) {
  const [viewMode, setViewMode] = useState('grid'); // 'grid' | 'table'
  const [sortBy, setSortBy] = useState('default');

  const currentStatus = filter?.status || 'All';
  const currentType = filter?.ipoType || 'All';

  // Apply in-memory filtering for instant response
  const filteredIPOs = ipos.filter(item => {
    // Status filter
    if (currentStatus !== 'All' && item.status.toLowerCase() !== currentStatus.toLowerCase()) {
      return false;
    }
    // Type filter
    if (currentType !== 'All' && item.ipo_type.toLowerCase() !== currentType.toLowerCase()) {
      return false;
    }
    // Search query
    if (searchQuery && searchQuery.trim()) {
      const q = searchQuery.toLowerCase().trim();
      const matchName = item.company_name.toLowerCase().includes(q);
      const matchSlug = item.slug.toLowerCase().includes(q);
      if (!matchName && !matchSlug) return false;
    }
    return true;
  });

  // Apply sorting
  const sortedIPOs = [...filteredIPOs].sort((a, b) => {
    if (sortBy === 'name_asc') {
      return a.company_name.localeCompare(b.company_name);
    }
    if (sortBy === 'size_desc') {
      return (Number(b.issue_size) || 0) - (Number(a.issue_size) || 0);
    }
    if (sortBy === 'gmp_gain_desc') {
      return (Number(b.estimated_gain_percent) || -999) - (Number(a.estimated_gain_percent) || -999);
    }
    if (sortBy === 'date_asc') {
      return (new Date(a.open_date || '2099-01-01')) - (new Date(b.open_date || '2099-01-01'));
    }
    // Default
    return 0;
  });

  return (
    <div className="max-w-7xl mx-auto px-4 sm:px-6 py-6 sm:py-8">
      {/* Page Title & Breadcrumb */}
      <div className="mb-6">
        <h1 className="text-2xl sm:text-3xl font-black text-slate-900 tracking-tight">
          Indian IPO Directory & Screener
        </h1>
        <p className="text-slate-600 text-sm mt-1">
          Explore upcoming, open, and closed Mainboard and SME public issues with live GMP projections.
        </p>
      </div>

      {/* Filter Control Bar */}
      <div className="bg-white rounded-xl border border-slate-200 p-4 mb-6 shadow-sm space-y-3 sm:space-y-4">
        {/* Status Pills */}
        <div className="flex flex-wrap items-center justify-between gap-3">
          <div className="flex items-center gap-1.5 flex-wrap">
            <span className="text-xs font-bold text-slate-400 uppercase tracking-wider mr-1">Status:</span>
            {['All', 'Open', 'Upcoming', 'Closed', 'Listed'].map((st) => (
              <button
                key={st}
                onClick={() => setFilter(prev => ({ ...prev, status: st }))}
                className={`px-3 py-1.5 rounded-lg text-xs font-semibold transition-all ${
                  currentStatus.toLowerCase() === st.toLowerCase()
                    ? 'bg-slate-900 text-white shadow-sm'
                    : 'bg-slate-100 text-slate-600 hover:bg-slate-200'
                }`}
              >
                {st}
              </button>
            ))}
          </div>

          {/* View Mode Toggle */}
          <div className="flex items-center gap-1 bg-slate-100 p-1 rounded-lg self-end sm:self-auto">
            <button
              onClick={() => setViewMode('grid')}
              className={`p-1.5 rounded-md transition-all ${
                viewMode === 'grid' ? 'bg-white text-slate-900 shadow-sm' : 'text-slate-500 hover:text-slate-900'
              }`}
              title="Grid View"
            >
              <LayoutGrid className="w-4 h-4" />
            </button>
            <button
              onClick={() => setViewMode('table')}
              className={`p-1.5 rounded-md transition-all ${
                viewMode === 'table' ? 'bg-white text-slate-900 shadow-sm' : 'text-slate-500 hover:text-slate-900'
              }`}
              title="Table View"
            >
              <List className="w-4 h-4" />
            </button>
          </div>
        </div>

        {/* Sub-Filters: Type, Sorting, Search */}
        <div className="pt-3 border-t border-slate-100 flex flex-wrap items-center justify-between gap-3 text-xs">
          {/* Segment Filter (Mainboard vs SME) */}
          <div className="flex items-center gap-1.5">
            <span className="font-bold text-slate-400 uppercase tracking-wider mr-1">Segment:</span>
            {['All', 'Mainboard', 'SME'].map((typ) => (
              <button
                key={typ}
                onClick={() => setFilter(prev => ({ ...prev, ipoType: typ }))}
                className={`px-2.5 py-1 rounded-md font-semibold transition-all ${
                  currentType.toLowerCase() === typ.toLowerCase()
                    ? 'bg-sky-600 text-white shadow-sm'
                    : 'bg-slate-50 text-slate-600 border border-slate-200 hover:bg-slate-100'
                }`}
              >
                {typ}
              </button>
            ))}
          </div>

          {/* Sort Dropdown */}
          <div className="flex items-center gap-2">
            <span className="font-bold text-slate-400 uppercase tracking-wider">Sort by:</span>
            <select
              value={sortBy}
              onChange={(e) => setSortBy(e.target.value)}
              className="bg-slate-50 border border-slate-200 text-slate-800 rounded-lg px-2.5 py-1.5 focus:outline-none focus:ring-1 focus:ring-sky-500 font-medium cursor-pointer"
            >
              <option value="default">Default Priority</option>
              <option value="date_asc">Open Date (Earliest First)</option>
              <option value="gmp_gain_desc">GMP Gain % (Highest First)</option>
              <option value="size_desc">Issue Size (Largest First)</option>
              <option value="name_asc">Company Name (A-Z)</option>
            </select>
          </div>
        </div>

        {/* Active Filters Pill Bar */}
        {(currentStatus !== 'All' || currentType !== 'All' || searchQuery) && (
          <div className="pt-2 border-t border-slate-100 flex items-center gap-2 flex-wrap text-xs text-slate-500">
            <span>Active filters:</span>
            {currentStatus !== 'All' && (
              <span className="inline-flex items-center gap-1 bg-sky-50 text-sky-700 px-2 py-0.5 rounded-full border border-sky-200 font-medium">
                Status: {currentStatus}
                <X className="w-3 h-3 cursor-pointer" onClick={() => setFilter(prev => ({ ...prev, status: 'All' }))} />
              </span>
            )}
            {currentType !== 'All' && (
              <span className="inline-flex items-center gap-1 bg-purple-50 text-purple-700 px-2 py-0.5 rounded-full border border-purple-200 font-medium">
                Segment: {currentType}
                <X className="w-3 h-3 cursor-pointer" onClick={() => setFilter(prev => ({ ...prev, ipoType: 'All' }))} />
              </span>
            )}
            {searchQuery && (
              <span className="inline-flex items-center gap-1 bg-amber-50 text-amber-800 px-2 py-0.5 rounded-full border border-amber-200 font-medium">
                Search: "{searchQuery}"
                <X className="w-3 h-3 cursor-pointer" onClick={() => onSearch('')} />
              </span>
            )}
            <button
              onClick={() => {
                setFilter({ status: 'All', ipoType: 'All' });
                onSearch('');
              }}
              className="text-sky-600 hover:underline ml-auto text-[11px] font-semibold"
            >
              Clear All
            </button>
          </div>
        )}
      </div>

      {/* Results Header Count */}
      <div className="flex items-center justify-between text-xs text-slate-500 mb-4 px-1">
        <span>Showing <strong className="text-slate-900">{sortedIPOs.length}</strong> public issues</span>
        <span>Automatic live exchange & GMP feed</span>
      </div>

      {/* Main Listing View */}
      {viewMode === 'grid' ? (
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4 sm:gap-6">
          {sortedIPOs.map((ipo) => (
            <IPOCard key={ipo.id} ipo={ipo} onSelect={onSelectIPO} />
          ))}
        </div>
      ) : (
        <IPOTable ipos={sortedIPOs} onSelect={onSelectIPO} />
      )}

      {sortedIPOs.length === 0 && (
        <div className="bg-white rounded-xl border border-slate-200 p-12 text-center text-slate-500">
          <p className="text-base font-semibold text-slate-700">No issues found</p>
          <p className="text-xs text-slate-400 mt-1">Try broadening your search query or removing active status filters.</p>
        </div>
      )}

      <Disclaimer />
    </div>
  );
}
