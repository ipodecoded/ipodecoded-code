import React from 'react';
import { Calendar, TrendingUp, IndianRupee, ArrowUpRight, Clock, Building2, ShieldCheck, AlertTriangle } from 'lucide-react';

export default function IPOCard({ ipo, onSelect }) {
  if (!ipo) return null;

  // Format dates
  const formatDate = (dateStr) => {
    if (!dateStr) return 'TBA';
    try {
      const d = new Date(dateStr);
      return d.toLocaleDateString('en-IN', { day: 'numeric', month: 'short', year: 'numeric' });
    } catch {
      return dateStr;
    }
  };

  // Status badge styling
  const statusStyles = {
    Open: 'bg-emerald-50 text-emerald-700 border-emerald-200',
    Upcoming: 'bg-sky-50 text-sky-700 border-sky-200',
    Closed: 'bg-amber-50 text-amber-700 border-amber-200',
    Listed: 'bg-slate-100 text-slate-700 border-slate-300'
  };

  const statusBadge = statusStyles[ipo.status] || 'bg-slate-50 text-slate-700 border-slate-200';

  // Format price band
  const formatPriceBand = () => {
    if (ipo.price_band_low && ipo.price_band_high) {
      if (ipo.price_band_low === ipo.price_band_high) {
        return `₹${ipo.price_band_high}`;
      }
      return `₹${ipo.price_band_low} – ₹${ipo.price_band_high}`;
    } else if (ipo.price_band_high) {
      return `₹${ipo.price_band_high}`;
    }
    return 'Price TBA';
  };

  // Format currency
  const formatINR = (val) => {
    if (!val) return 'TBA';
    return `₹${Number(val).toLocaleString('en-IN')}`;
  };

  return (
    <div 
      onClick={() => onSelect(ipo.slug)}
      className="bg-white rounded-xl border border-slate-200 hover:border-sky-400 hover:shadow-lg transition-all cursor-pointer flex flex-col justify-between overflow-hidden group"
    >
      {/* Top Header */}
      <div className="p-4 sm:p-5 border-b border-slate-100">
        <div className="flex items-start justify-between gap-2 mb-2.5">
          <div className="flex items-center gap-1.5 flex-wrap">
            <span className={`text-[11px] font-bold px-2 py-0.5 rounded border uppercase tracking-wider ${
              ipo.ipo_type === 'SME' ? 'bg-purple-50 text-purple-700 border-purple-200' : 'bg-blue-50 text-blue-700 border-blue-200'
            }`}>
              {ipo.ipo_type}
            </span>
            <span className={`text-[11px] font-semibold px-2 py-0.5 rounded border ${statusBadge}`}>
              {ipo.status === 'Open' && <span className="inline-block w-1.5 h-1.5 rounded-full bg-emerald-500 mr-1.5 animate-pulse"></span>}
              {ipo.status}
            </span>
            {ipo.is_cross_validated && (
              <span className="text-[10px] font-semibold px-1.5 py-0.5 rounded border bg-emerald-50 text-emerald-700 border-emerald-200 inline-flex items-center gap-0.5" title="Cross-validated across multiple independent sources">
                <ShieldCheck className="w-2.5 h-2.5" /> Verified
              </span>
            )}
            {ipo.has_conflicts && (
              <span className="text-[10px] font-semibold px-1.5 py-0.5 rounded border bg-amber-50 text-amber-700 border-amber-200 inline-flex items-center gap-0.5" title="Cross-source variance detected and audited">
                <AlertTriangle className="w-2.5 h-2.5" /> Variance
              </span>
            )}
          </div>

          <span className="text-slate-400 group-hover:text-sky-600 transition-colors">
            <ArrowUpRight className="w-4 h-4" />
          </span>
        </div>

        <h3 className="font-bold text-slate-900 text-base sm:text-lg group-hover:text-sky-600 transition-colors line-clamp-1">
          {ipo.company_name} {ipo.company_name.toLowerCase().includes('ipo') ? '' : 'IPO'}
        </h3>
        <p className="text-xs text-slate-500 mt-0.5 flex items-center gap-1 truncate">
          <Building2 className="w-3 h-3 text-slate-400" />
          <span>
            {Array.isArray(ipo.sources_verified) && ipo.sources_verified.length > 0
              ? `Sources: ${ipo.sources_verified.join(', ')}`
              : (ipo.source_name || 'Primary Market Issue')}
          </span>
        </p>
      </div>

      {/* Financial Metrics Grid */}
      <div className="p-4 sm:p-5 bg-slate-50/50 space-y-3">
        <div className="grid grid-cols-2 gap-2 text-xs">
          <div>
            <span className="text-slate-500 block text-[11px]">Price Band</span>
            <span className="font-bold text-slate-900 font-mono text-sm">{formatPriceBand()}</span>
          </div>
          <div>
            <span className="text-slate-500 block text-[11px]">Lot Size</span>
            <span className="font-bold text-slate-900 font-mono text-sm">
              {ipo.lot_size ? `${ipo.lot_size} Shares` : 'TBA'}
            </span>
          </div>
          <div>
            <span className="text-slate-500 block text-[11px]">Min Investment</span>
            <span className="font-bold text-slate-800 font-mono">
              {formatINR(ipo.minimum_investment)}
            </span>
          </div>
          <div>
            <span className="text-slate-500 block text-[11px]">Issue Size</span>
            <span className="font-bold text-slate-800 font-mono">
              {ipo.issue_size ? `₹${Number(ipo.issue_size).toLocaleString('en-IN')} Cr` : 'TBA'}
            </span>
          </div>
        </div>

        {/* Timeline Dates */}
        <div className="pt-2 border-t border-slate-200/60 flex items-center justify-between text-xs text-slate-600">
          <div>
            <span className="text-slate-400 block text-[10px] uppercase">Open Date</span>
            <span className="font-semibold text-slate-700">{formatDate(ipo.open_date)}</span>
          </div>
          <div className="text-right">
            <span className="text-slate-400 block text-[10px] uppercase">Close Date</span>
            <span className="font-semibold text-slate-700">{formatDate(ipo.close_date)}</span>
          </div>
        </div>
      </div>

      {/* Live GMP Bar */}
      <div className="px-4 py-3 bg-gradient-to-r from-slate-900 to-slate-800 text-white flex items-center justify-between">
        <div>
          <div className="flex items-center gap-1.5 flex-wrap">
            <span className="text-[10px] uppercase font-bold tracking-wider text-slate-400">GMP (Unofficial)</span>
            {ipo.estimated_gain_percent !== null && (
              <span className="text-[10px] font-bold px-1.5 py-0.2 rounded bg-emerald-500/20 text-emerald-400">
                +{ipo.estimated_gain_percent}%
              </span>
            )}
            {ipo.gmp_spread && ipo.gmp_spread.includes('–') && (
              <span className="text-[9px] text-amber-300 font-mono bg-amber-950/70 px-1 py-0.5 rounded border border-amber-500/30" title={`Reconciled Spread: InvestorGain (₹${ipo.gmp_investorgain}) vs IPOWatch (₹${ipo.gmp_ipowatch})`}>
                {ipo.gmp_spread}
              </span>
            )}
            {ipo.gmp_divergence_alert && (
              <span className="text-[9px] font-bold text-amber-300 bg-amber-900/80 px-1.5 py-0.2 rounded border border-amber-500/40 inline-flex items-center gap-0.5" title={`Spread Divergence: InvestorGain (₹${ipo.gmp_investorgain}) vs IPOWatch (₹${ipo.gmp_ipowatch})`}>
                ⚠️ Divergence
              </span>
            )}
          </div>
          <div className="flex items-baseline gap-2 mt-0.5">
            <span className="text-base font-black font-mono text-emerald-400">
              {ipo.current_gmp !== null && ipo.current_gmp !== undefined ? `₹${ipo.current_gmp}` : 'No GMP data'}
            </span>
            {ipo.estimated_listing_price && (
              <span className="text-[11px] text-slate-300">
                Est: <span className="font-mono font-semibold">₹{ipo.estimated_listing_price}</span>
              </span>
            )}
          </div>
        </div>

        {/* Subscription or Updated Time */}
        <div className="text-right text-[11px]">
          {ipo.subscription_total ? (
            <div>
              <span className="text-[10px] text-slate-400 uppercase block">Subscribed</span>
              <span className="font-bold text-sky-400 font-mono">{ipo.subscription_total}x</span>
            </div>
          ) : ipo.gmp_updated_at ? (
            <div>
              <span className="text-[10px] text-slate-400 block flex items-center gap-1 justify-end">
                <Clock className="w-2.5 h-2.5" /> Updated
              </span>
              <span className="text-slate-300 text-[10px]">
                {new Date(ipo.gmp_updated_at).toLocaleTimeString('en-IN', { hour: '2-digit', minute: '2-digit' })}
              </span>
            </div>
          ) : (
            <span className="text-slate-400 text-[10px]">View Details &rarr;</span>
          )}
        </div>
      </div>
    </div>
  );
}
