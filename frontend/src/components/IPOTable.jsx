import React from 'react';
import { ArrowUpRight } from 'lucide-react';

export default function IPOTable({ ipos, onSelect }) {
  if (!ipos || ipos.length === 0) {
    return (
      <div className="bg-white rounded-xl border border-slate-200 p-8 text-center text-slate-500">
        No IPOs found matching your criteria.
      </div>
    );
  }

  const formatDate = (dateStr) => {
    if (!dateStr) return '—';
    try {
      const d = new Date(dateStr);
      return d.toLocaleDateString('en-IN', { day: 'numeric', month: 'short' });
    } catch {
      return dateStr;
    }
  };

  const statusStyles = {
    Open: 'bg-emerald-50 text-emerald-700 border-emerald-200',
    Upcoming: 'bg-sky-50 text-sky-700 border-sky-200',
    Closed: 'bg-amber-50 text-amber-700 border-amber-200',
    Listed: 'bg-slate-100 text-slate-700 border-slate-300'
  };

  return (
    <div className="bg-white rounded-xl border border-slate-200 overflow-hidden shadow-sm">
      <div className="overflow-x-auto">
        <table className="w-full text-left text-sm">
          <thead className="bg-slate-50 text-slate-600 text-xs uppercase tracking-wider border-b border-slate-200">
            <tr>
              <th className="py-3 px-4 font-bold">Company Name</th>
              <th className="py-3 px-3 font-bold">Type</th>
              <th className="py-3 px-3 font-bold">Status</th>
              <th className="py-3 px-3 font-bold">Price Band</th>
              <th className="py-3 px-3 font-bold">Lot</th>
              <th className="py-3 px-3 font-bold">Issue (₹ Cr)</th>
              <th className="py-3 px-3 font-bold">Open</th>
              <th className="py-3 px-3 font-bold">Close</th>
              <th className="py-3 px-3 font-bold text-right">GMP (₹)</th>
              <th className="py-3 px-3 font-bold text-right">Est. Gain</th>
              <th className="py-3 px-3 text-center">Action</th>
            </tr>
          </thead>
          <tbody className="divide-y divide-slate-100">
            {ipos.map((ipo) => {
              const statusBadge = statusStyles[ipo.status] || 'bg-slate-50 text-slate-700 border-slate-200';
              return (
                <tr 
                  key={ipo.id}
                  onClick={() => onSelect(ipo.slug)}
                  className="hover:bg-slate-50/80 transition-colors cursor-pointer group"
                >
                  <td className="py-3.5 px-4">
                    <div className="flex items-center gap-1.5 font-bold text-slate-900 group-hover:text-sky-600 transition-colors">
                      <span>{ipo.company_name}</span>
                      {ipo.is_cross_validated && (
                        <span className="text-[9px] text-emerald-700 font-bold bg-emerald-50 px-1 py-0.5 rounded border border-emerald-200">Multi-Source</span>
                      )}
                      {ipo.has_conflicts && (
                        <span className="text-[9px] text-amber-700 font-bold bg-amber-50 px-1 py-0.5 rounded border border-amber-200" title="Cross-source variance noted">Variance</span>
                      )}
                    </div>
                    <div className="text-[11px] text-slate-400 font-normal">
                      {Array.isArray(ipo.sources_verified) && ipo.sources_verified.length > 0 
                        ? ipo.sources_verified.join(', ')
                        : (ipo.source_name || 'Primary Market')}
                    </div>
                  </td>

                  <td className="py-3.5 px-3">
                    <span className={`text-[10px] font-bold px-1.5 py-0.5 rounded border uppercase ${
                      ipo.ipo_type === 'SME' ? 'bg-purple-50 text-purple-700 border-purple-200' : 'bg-blue-50 text-blue-700 border-blue-200'
                    }`}>
                      {ipo.ipo_type}
                    </span>
                  </td>

                  <td className="py-3.5 px-3">
                    <span className={`text-[11px] font-semibold px-2 py-0.5 rounded border inline-block ${statusBadge}`}>
                      {ipo.status}
                    </span>
                  </td>

                  <td className="py-3.5 px-3 font-mono text-xs font-semibold text-slate-800">
                    {ipo.price_band_low && ipo.price_band_high ? (
                      ipo.price_band_low === ipo.price_band_high ? `₹${ipo.price_band_high}` : `₹${ipo.price_band_low} - ₹${ipo.price_band_high}`
                    ) : (
                      'TBA'
                    )}
                  </td>

                  <td className="py-3.5 px-3 font-mono text-xs text-slate-700">
                    {ipo.lot_size ? ipo.lot_size : '—'}
                  </td>

                  <td className="py-3.5 px-3 font-mono text-xs font-semibold text-slate-900">
                    {ipo.issue_size ? `₹${Number(ipo.issue_size).toLocaleString('en-IN')}` : '—'}
                  </td>

                  <td className="py-3.5 px-3 text-xs text-slate-600 whitespace-nowrap">
                    {formatDate(ipo.open_date)}
                  </td>

                  <td className="py-3.5 px-3 text-xs text-slate-600 whitespace-nowrap">
                    {formatDate(ipo.close_date)}
                  </td>

                  <td className="py-3.5 px-3 text-right">
                    {ipo.current_gmp !== null && ipo.current_gmp !== undefined ? (
                      <div>
                        <span className="font-mono font-bold text-emerald-600 block" title={ipo.gmp_source_name ? `Primary Source: ${ipo.gmp_source_name}` : 'Primary GMP'}>
                          ₹{ipo.current_gmp}
                        </span>
                        {ipo.gmp_spread && ipo.gmp_spread.includes('–') && (
                          <span 
                            className={`text-[10px] font-mono font-semibold block ${ipo.gmp_divergence_alert ? 'text-amber-700 font-bold' : 'text-amber-600'}`} 
                            title={`Reconciled Spread: InvestorGain (₹${ipo.gmp_investorgain}) vs IPOWatch (₹${ipo.gmp_ipowatch})${ipo.gmp_divergence_alert ? ' - Wide Divergence Alert' : ''}`}
                          >
                            {ipo.gmp_divergence_alert && '⚠️ '}{ipo.gmp_spread}
                          </span>
                        )}
                      </div>
                    ) : (
                      <span className="text-slate-400 text-xs">—</span>
                    )}
                  </td>

                  <td className="py-3.5 px-3 text-right">
                    {ipo.estimated_gain_percent !== null && ipo.estimated_gain_percent !== undefined ? (
                      <span className="inline-block text-[11px] font-mono font-bold px-1.5 py-0.5 rounded bg-emerald-50 text-emerald-700 border border-emerald-200">
                        +{ipo.estimated_gain_percent}%
                      </span>
                    ) : (
                      <span className="text-slate-400 text-xs">—</span>
                    )}
                  </td>

                  <td className="py-3.5 px-3 text-center">
                    <span className="inline-flex p-1 rounded-md text-slate-400 group-hover:text-sky-600 group-hover:bg-sky-50 transition-colors">
                      <ArrowUpRight className="w-4 h-4" />
                    </span>
                  </td>
                </tr>
              );
            })}
          </tbody>
        </table>
      </div>
    </div>
  );
}
