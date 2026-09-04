import React, { useEffect, useState } from 'react';
import { fetchIPODetail, fetchGMPHistory } from '../api';
import GMPHistoryChart from '../components/GMPHistoryChart';
import Disclaimer from '../components/Disclaimer';
import { 
  Calendar, TrendingUp, IndianRupee, Layers, Clock, ExternalLink, 
  ArrowLeft, CheckCircle2, AlertCircle, Building2, ShieldAlert, Share2 
} from 'lucide-react';

export default function IPODetail({ slug, onBack }) {
  const [ipo, setIpo] = useState(null);
  const [gmpHistory, setGmpHistory] = useState([]);
  const [loading, setLoading] = useState(true);
  const [copied, setCopied] = useState(false);

  useEffect(() => {
    async function loadData() {
      setLoading(true);
      const detail = await fetchIPODetail(slug);
      setIpo(detail);

      if (detail) {
        const history = await fetchGMPHistory(slug);
        setGmpHistory(history);
      }
      setLoading(false);
    }
    loadData();
  }, [slug]);

  if (loading) {
    return (
      <div className="max-w-7xl mx-auto px-4 sm:px-6 py-16 text-center">
        <div className="inline-block w-8 h-8 border-4 border-sky-600 border-t-transparent rounded-full animate-spin mb-3"></div>
        <p className="text-slate-600 text-sm font-medium">Loading IPO profile & live GMP data...</p>
      </div>
    );
  }

  if (!ipo) {
    return (
      <div className="max-w-7xl mx-auto px-4 sm:px-6 py-16 text-center">
        <AlertCircle className="w-12 h-12 text-amber-500 mx-auto mb-3" />
        <h2 className="text-xl font-bold text-slate-900">IPO Profile Not Found</h2>
        <p className="text-slate-500 text-sm mt-1">The requested public issue slug '{slug}' could not be located.</p>
        <button
          onClick={onBack}
          className="mt-5 inline-flex items-center gap-2 px-4 py-2 bg-slate-900 text-white rounded-lg text-xs font-semibold hover:bg-slate-800"
        >
          <ArrowLeft className="w-4 h-4" /> Back to Dashboard
        </button>
      </div>
    );
  }

  const formatDate = (dateStr) => {
    if (!dateStr) return 'TBA';
    try {
      const d = new Date(dateStr);
      return d.toLocaleDateString('en-IN', { day: 'numeric', month: 'short', year: 'numeric' });
    } catch {
      return dateStr;
    }
  };

  const formatPriceBand = () => {
    if (ipo.price_band_low && ipo.price_band_high) {
      if (ipo.price_band_low === ipo.price_band_high) {
        return `₹${ipo.price_band_high} per share`;
      }
      return `₹${ipo.price_band_low} – ₹${ipo.price_band_high}`;
    } else if (ipo.price_band_high) {
      return `₹${ipo.price_band_high}`;
    }
    return 'TBA';
  };

  const handleShare = () => {
    if (navigator.clipboard) {
      navigator.clipboard.writeText(window.location.href);
      setCopied(true);
      setTimeout(() => setCopied(false), 2500);
    }
  };

  return (
    <div className="max-w-7xl mx-auto px-4 sm:px-6 py-6 sm:py-8">
      {/* Top Breadcrumb & Share */}
      <div className="flex items-center justify-between gap-4 mb-6">
        <button
          onClick={onBack}
          className="inline-flex items-center gap-2 text-xs font-semibold text-slate-600 hover:text-sky-600 transition-colors"
        >
          <ArrowLeft className="w-4 h-4" /> Back to IPO Listing
        </button>

        <button
          onClick={handleShare}
          className="inline-flex items-center gap-1.5 px-3 py-1.5 bg-white border border-slate-200 text-slate-600 hover:text-slate-900 rounded-lg text-xs font-medium shadow-sm transition-all"
        >
          <Share2 className="w-3.5 h-3.5" />
          <span>{copied ? 'Link Copied!' : 'Share IPO'}</span>
        </button>
      </div>

      {/* Main Header Card */}
      <div className="bg-white rounded-2xl border border-slate-200 p-6 sm:p-8 mb-6 shadow-sm">
        <div className="flex flex-col lg:flex-row lg:items-center justify-between gap-6">
          <div>
            <div className="flex items-center gap-2 mb-2 flex-wrap">
              <span className={`text-xs font-bold px-2.5 py-0.5 rounded border uppercase tracking-wider ${
                ipo.ipo_type === 'SME' ? 'bg-purple-50 text-purple-700 border-purple-200' : 'bg-blue-50 text-blue-700 border-blue-200'
              }`}>
                {ipo.ipo_type} Issue
              </span>
              <span className="text-xs font-semibold px-2.5 py-0.5 rounded border bg-emerald-50 text-emerald-700 border-emerald-200">
                Status: {ipo.status}
              </span>
              {ipo.subscription_status && (
                <span className="text-xs font-medium px-2 py-0.5 rounded bg-slate-100 text-slate-600">
                  {ipo.subscription_status}
                </span>
              )}
            </div>

            <h1 className="text-2xl sm:text-3xl lg:text-4xl font-black text-slate-900 tracking-tight">
              {ipo.company_name} {ipo.company_name.toLowerCase().includes('ipo') ? '' : 'IPO'}
            </h1>
            <p className="text-slate-500 text-xs sm:text-sm mt-1.5 flex items-center gap-2">
              <Building2 className="w-4 h-4 text-slate-400" />
              <span>Primary Market Public Offering</span>
              <span>&bull;</span>
              <span>Issue Type: 100% Book Built</span>
            </p>
          </div>

          {/* Quick GMP Highlight Card */}
          <div className="bg-gradient-to-br from-slate-950 to-slate-900 text-white rounded-xl p-5 sm:p-6 border border-slate-800 lg:min-w-[300px] shadow-lg">
            <div className="flex items-center justify-between text-xs text-slate-400 uppercase font-bold tracking-wider mb-2">
              <span>Live Grey Market</span>
              {ipo.estimated_gain_percent !== null && (
                <span className="text-emerald-400 font-mono font-bold bg-emerald-500/20 px-2 py-0.5 rounded">
                  +{ipo.estimated_gain_percent}%
                </span>
              )}
            </div>

            <div className="flex items-baseline gap-3">
              <div className="text-3xl font-black font-mono text-emerald-400">
                {ipo.current_gmp !== null && ipo.current_gmp !== undefined ? `₹${ipo.current_gmp}` : 'No GMP'}
              </div>
              {ipo.estimated_listing_price && (
                <div className="text-xs text-slate-300">
                  Est. Listing: <strong className="text-white font-mono text-sm">₹{ipo.estimated_listing_price}</strong>
                </div>
              )}
            </div>

            {/* Reconciled Spread & Divergence Alert */}
            {ipo.gmp_spread && ipo.gmp_spread.includes('–') && (
              <div className="mt-2 flex items-center gap-2 flex-wrap">
                <span className="text-[11px] font-mono text-amber-300 bg-amber-950/80 px-2 py-0.5 rounded border border-amber-500/30">
                  Spread: {ipo.gmp_spread}
                </span>
                {ipo.gmp_divergence_alert && (
                  <span className="text-[10px] font-bold text-amber-300 bg-amber-900/80 px-1.5 py-0.5 rounded border border-amber-500/40">
                    ⚠️ Divergence Alert
                  </span>
                )}
              </div>
            )}

            <div className="text-[11px] text-slate-400 mt-2.5 pt-2 border-t border-slate-800 flex items-center justify-between">
              <span>{ipo.gmp_source_name ? `${ipo.gmp_source_name} (Primary)` : 'Public GMP Source'}</span>
              <span>{ipo.gmp_updated_at ? new Date(ipo.gmp_updated_at).toLocaleTimeString('en-IN', { hour: '2-digit', minute: '2-digit' }) : 'Updated hourly'}</span>
            </div>
          </div>
        </div>
      </div>

      {/* Key Financial KPIs Grid */}
      <div className="grid grid-cols-2 sm:grid-cols-3 lg:grid-cols-6 gap-3 sm:gap-4 mb-8">
        <div className="bg-white p-4 rounded-xl border border-slate-200">
          <span className="text-slate-400 block text-[11px] font-bold uppercase">Price Band</span>
          <span className="font-bold text-slate-900 font-mono text-sm sm:text-base mt-0.5 block">
            {formatPriceBand()}
          </span>
        </div>

        <div className="bg-white p-4 rounded-xl border border-slate-200">
          <span className="text-slate-400 block text-[11px] font-bold uppercase">Lot Size</span>
          <span className="font-bold text-slate-900 font-mono text-sm sm:text-base mt-0.5 block">
            {ipo.lot_size ? `${ipo.lot_size} Shares` : 'TBA'}
          </span>
        </div>

        <div className="bg-white p-4 rounded-xl border border-slate-200">
          <span className="text-slate-400 block text-[11px] font-bold uppercase">Min Investment</span>
          <span className="font-bold text-slate-900 font-mono text-sm sm:text-base mt-0.5 block">
            {ipo.minimum_investment ? `₹${Number(ipo.minimum_investment).toLocaleString('en-IN')}` : 'TBA'}
          </span>
        </div>

        <div className="bg-white p-4 rounded-xl border border-slate-200">
          <span className="text-slate-400 block text-[11px] font-bold uppercase">Total Issue Size</span>
          <span className="font-bold text-slate-900 font-mono text-sm sm:text-base mt-0.5 block">
            {ipo.issue_size ? `₹${Number(ipo.issue_size).toLocaleString('en-IN')} Cr` : 'TBA'}
          </span>
        </div>

        <div className="bg-white p-4 rounded-xl border border-slate-200">
          <span className="text-slate-400 block text-[11px] font-bold uppercase">Fresh Issue</span>
          <span className="font-bold text-slate-900 font-mono text-sm sm:text-base mt-0.5 block">
            {ipo.fresh_issue !== null && ipo.fresh_issue !== undefined ? `₹${Number(ipo.fresh_issue).toLocaleString('en-IN')} Cr` : 'TBA'}
          </span>
        </div>

        <div className="bg-white p-4 rounded-xl border border-slate-200">
          <span className="text-slate-400 block text-[11px] font-bold uppercase">Offer For Sale (OFS)</span>
          <span className="font-bold text-slate-900 font-mono text-sm sm:text-base mt-0.5 block">
            {ipo.ofs !== null && ipo.ofs !== undefined ? `₹${Number(ipo.ofs).toLocaleString('en-IN')} Cr` : 'TBA'}
          </span>
        </div>
      </div>

      {/* ISSUE TIMETABLE PROGRESSION */}
      <div className="bg-white rounded-2xl border border-slate-200 p-6 sm:p-8 mb-8 shadow-sm">
        <h3 className="text-lg font-bold text-slate-900 mb-2 flex items-center gap-2">
          <Calendar className="w-5 h-5 text-sky-600" />
          Important Issue Timetable & Dates
        </h3>
        <p className="text-xs text-slate-500 mb-6">
          Official timeline schedule as submitted to SEBI and registrar
        </p>

        <div className="grid grid-cols-2 sm:grid-cols-3 lg:grid-cols-6 gap-4">
          <div className="p-3.5 rounded-xl bg-slate-50 border border-slate-200/80">
            <span className="text-[10px] uppercase font-bold text-slate-400 block">IPO Open Date</span>
            <span className="font-bold text-slate-900 text-sm mt-1 block">{formatDate(ipo.open_date)}</span>
          </div>

          <div className="p-3.5 rounded-xl bg-slate-50 border border-slate-200/80">
            <span className="text-[10px] uppercase font-bold text-slate-400 block">IPO Close Date</span>
            <span className="font-bold text-slate-900 text-sm mt-1 block">{formatDate(ipo.close_date)}</span>
          </div>

          <div className="p-3.5 rounded-xl bg-slate-50 border border-slate-200/80">
            <span className="text-[10px] uppercase font-bold text-slate-400 block">Basis of Allotment</span>
            <span className="font-bold text-slate-900 text-sm mt-1 block">{formatDate(ipo.allotment_date)}</span>
          </div>

          <div className="p-3.5 rounded-xl bg-slate-50 border border-slate-200/80">
            <span className="text-[10px] uppercase font-bold text-slate-400 block">Initiation of Refunds</span>
            <span className="font-bold text-slate-900 text-sm mt-1 block">{formatDate(ipo.refund_date)}</span>
          </div>

          <div className="p-3.5 rounded-xl bg-slate-50 border border-slate-200/80">
            <span className="text-[10px] uppercase font-bold text-slate-400 block">Credit to Demat</span>
            <span className="font-bold text-slate-900 text-sm mt-1 block">{formatDate(ipo.demat_date)}</span>
          </div>

          <div className="p-3.5 rounded-xl bg-emerald-50 border border-emerald-200">
            <span className="text-[10px] uppercase font-bold text-emerald-700 block">Listing Date</span>
            <span className="font-bold text-emerald-900 text-sm mt-1 block">{formatDate(ipo.listing_date)}</span>
          </div>
        </div>
      </div>

      {/* SUBSCRIPTION METRICS (If Available) */}
      {(ipo.subscription_total || ipo.subscription_retail) && (
        <div className="bg-white rounded-2xl border border-slate-200 p-6 sm:p-8 mb-8 shadow-sm">
          <h3 className="text-lg font-bold text-slate-900 mb-2 flex items-center gap-2">
            <Layers className="w-5 h-5 text-indigo-600" />
            Live Subscription Multiples
          </h3>
          <p className="text-xs text-slate-500 mb-6">
            Bidding demand breakdown by investor category
          </p>

          <div className="grid grid-cols-2 sm:grid-cols-4 gap-4">
            <div className="p-4 rounded-xl bg-slate-50 border border-slate-200">
              <span className="text-xs text-slate-500 font-medium">QIB Institutional</span>
              <span className="text-xl sm:text-2xl font-black font-mono text-slate-900 mt-1 block">
                {ipo.subscription_qib ? `${ipo.subscription_qib}x` : '—'}
              </span>
            </div>

            <div className="p-4 rounded-xl bg-slate-50 border border-slate-200">
              <span className="text-xs text-slate-500 font-medium">NII / HNI</span>
              <span className="text-xl sm:text-2xl font-black font-mono text-slate-900 mt-1 block">
                {ipo.subscription_nii ? `${ipo.subscription_nii}x` : '—'}
              </span>
            </div>

            <div className="p-4 rounded-xl bg-slate-50 border border-slate-200">
              <span className="text-xs text-slate-500 font-medium">Retail Individual</span>
              <span className="text-xl sm:text-2xl font-black font-mono text-slate-900 mt-1 block">
                {ipo.subscription_retail ? `${ipo.subscription_retail}x` : '—'}
              </span>
            </div>

            <div className="p-4 rounded-xl bg-sky-50 border border-sky-200">
              <span className="text-xs text-sky-700 font-bold uppercase tracking-wider">Total Subscription</span>
              <span className="text-xl sm:text-2xl font-black font-mono text-sky-900 mt-1 block">
                {ipo.subscription_total ? `${ipo.subscription_total}x` : '—'}
              </span>
            </div>
          </div>
        </div>
      )}

      {/* GMP HISTORY TRAJECTORY & AUDIT */}
      <div className="mb-8">
        <GMPHistoryChart 
          records={gmpHistory} 
          priceBandHigh={ipo.price_band_high ? Number(ipo.price_band_high) : null} 
        />
      </div>

      {/* COMPANY DESCRIPTION */}
      {ipo.company_description && (
        <div className="bg-white rounded-2xl border border-slate-200 p-6 sm:p-8 mb-8 shadow-sm">
          <h3 className="text-lg font-bold text-slate-900 mb-3">
            About {ipo.company_name}
          </h3>
          <p className="text-slate-600 text-sm leading-relaxed whitespace-pre-line">
            {ipo.company_description}
          </p>
        </div>
      )}

      {/* MULTI-SOURCE PROVENANCE & CONFLICT AUDITING */}
      <div className="bg-white rounded-2xl border border-slate-200 p-6 sm:p-8 mb-8 shadow-sm">
        <h3 className="text-lg font-bold text-slate-900 mb-2 flex items-center gap-2">
          <CheckCircle2 className="w-5 h-5 text-emerald-600" />
          Multi-Source Provenance & Verification Audit
        </h3>
        <p className="text-xs text-slate-500 mb-4">
          IPODecoded reconciles data across independent primary exchanges (NSE) and secondary aggregator/market sources (Chittorgarh, InvestorGain, IPOWatch).
        </p>

        <div className="grid grid-cols-1 md:grid-cols-2 gap-4 mb-4">
          <div className="p-4 rounded-xl bg-slate-50 border border-slate-200">
            <div className="flex items-center justify-between mb-1.5">
              <span className="text-xs font-bold uppercase text-slate-500">Master Data Status</span>
              {ipo.master_data_validated && (
                <span className="text-[10px] font-bold px-2 py-0.5 rounded bg-emerald-100 text-emerald-800 border border-emerald-300">
                  ✓ Master Data Validated
                </span>
              )}
            </div>
            <div className="flex items-center gap-1.5 flex-wrap mt-1">
              {Array.isArray(ipo.sources_verified) && ipo.sources_verified.length > 0 ? (
                ipo.sources_verified.map((src, i) => (
                  <span key={i} className="text-xs font-semibold px-2 py-0.5 bg-white border border-slate-300 rounded text-slate-800">
                    {src === 'NSE' ? '🏛️ NSE' : src === 'Chittorgarh' ? '📊 Chittorgarh' : src === 'InvestorGain' ? '📈 InvestorGain' : '📑 IPOWatch'}
                  </span>
                ))
              ) : (
                <span className="text-xs text-slate-600">{ipo.source_name || 'Primary Exchange'}</span>
              )}
            </div>
            <div className="mt-2 text-[11px] text-slate-500">
              {ipo.is_cross_validated 
                ? 'Official dates and prices cross-validated against NSE exchange records.' 
                : 'Aggregator schedule observation.'}
            </div>
          </div>

          <div className="p-4 rounded-xl bg-slate-50 border border-slate-200">
            <div className="flex items-center justify-between mb-1.5">
              <span className="text-xs font-bold uppercase text-slate-500">Independent GMP Quotes</span>
              {ipo.gmp_divergence_alert && (
                <span className="text-[10px] font-bold px-2 py-0.5 rounded bg-amber-100 text-amber-800 border border-amber-300">
                  ⚠️ Spread Divergence Alert
                </span>
              )}
            </div>
            <div className="grid grid-cols-2 gap-2 text-xs mb-2">
              <div className="bg-white p-2 rounded border border-slate-200">
                <span className="text-[10px] text-slate-400 uppercase block font-semibold">InvestorGain (Primary)</span>
                <span className="font-mono font-bold text-slate-900 text-sm">
                  {ipo.gmp_investorgain !== null && ipo.gmp_investorgain !== undefined ? `₹${ipo.gmp_investorgain}` : '—'}
                </span>
              </div>
              <div className="bg-white p-2 rounded border border-slate-200">
                <span className="text-[10px] text-slate-400 uppercase block font-semibold">IPOWatch (Secondary)</span>
                <span className="font-mono font-bold text-slate-900 text-sm">
                  {ipo.gmp_ipowatch !== null && ipo.gmp_ipowatch !== undefined ? `₹${ipo.gmp_ipowatch}` : '—'}
                </span>
              </div>
            </div>
            {ipo.gmp_spread && (
              <div className="text-xs font-mono font-semibold text-slate-800">
                Reconciled Spread: <span className="text-emerald-600 font-bold">{ipo.gmp_spread}</span>
              </div>
            )}
          </div>
        </div>

        {/* Display Cross-Source Discrepancies / Conflicts if any */}
        {ipo.has_conflicts && ipo.conflicts && (
          <div className="p-4 rounded-xl bg-amber-50 border border-amber-200 text-amber-900 text-xs space-y-2 mb-4">
            <div className="font-bold flex items-center gap-1.5 text-amber-800">
              <AlertCircle className="w-4 h-4 text-amber-600" />
              Cross-Source Variance Detected & Audited:
            </div>
            {Array.isArray(ipo.conflicts) ? (
              ipo.conflicts.map((c, i) => (
                <div key={i} className="pl-5 font-mono text-[11px] text-amber-800">
                  • <strong>{c.field}</strong>: {c.source_1} ({c.val_1}) vs {c.source_2} ({c.val_2}) &rarr; Resolution: <strong>{c.resolution || c.resolved_to}</strong>
                </div>
              ))
            ) : (
              <div className="pl-5 text-amber-800">Variance noted between source records.</div>
            )}
          </div>
        )}

        <div className="pt-3 border-t border-slate-100 flex items-center justify-between text-xs text-slate-500 flex-wrap gap-2">
          <span>Last live pipeline cycle: {ipo.updated_at ? new Date(ipo.updated_at).toLocaleString('en-IN') : 'Automated'}</span>
          {ipo.source_url && (
            <a
              href={ipo.source_url}
              target="_blank"
              rel="noreferrer"
              className="inline-flex items-center gap-1 text-sky-600 hover:text-sky-800 font-semibold"
            >
              <span>Verify Filing on {ipo.source_name || 'Source'}</span>
              <ExternalLink className="w-3.5 h-3.5" />
            </a>
          )}
        </div>
      </div>

      {/* Prominent Statutory Disclaimer Box */}
      <Disclaimer />
    </div>
  );
}
