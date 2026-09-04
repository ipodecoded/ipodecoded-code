import React, { useState } from 'react';
import { TrendingUp, Clock, Info, ShieldAlert } from 'lucide-react';

export default function GMPHistoryChart({ records, priceBandHigh }) {
  const [hoveredIndex, setHoveredIndex] = useState(null);

  if (!records || records.length === 0) {
    return (
      <div className="bg-white rounded-xl border border-slate-200 p-6 text-center text-slate-500">
        <p className="text-sm">No historical GMP data recorded yet for this IPO.</p>
        <p className="text-xs text-slate-400 mt-1">Our automated pipeline records GMP changes as soon as public sources publish them.</p>
      </div>
    );
  }

  // Ensure chronological order
  const sorted = [...records].sort((a, b) => new Date(a.recorded_at) - new Date(b.recorded_at));

  // Chart dimensions & scaling
  const width = 600;
  const height = 220;
  const padding = { top: 25, right: 35, bottom: 35, left: 45 };
  const innerWidth = width - padding.left - padding.right;
  const innerHeight = height - padding.top - padding.bottom;

  const gmpValues = sorted.map(r => Number(r.gmp));
  const minVal = Math.min(0, ...gmpValues);
  const maxVal = Math.max(...gmpValues, 10);
  const valRange = maxVal - minVal || 1;

  // Calculate coordinates
  const points = sorted.map((r, i) => {
    const x = sorted.length === 1
      ? padding.left + innerWidth / 2
      : padding.left + (i / (sorted.length - 1)) * innerWidth;
    const y = padding.top + innerHeight - ((Number(r.gmp) - minVal) / valRange) * innerHeight;
    return { x, y, ...r };
  });

  // SVG path definition
  const pathD = sorted.length === 1
    ? `M ${padding.left} ${points[0].y} L ${padding.left + innerWidth} ${points[0].y}`
    : points.reduce((acc, pt, i) => {
        return i === 0 ? `M ${pt.x} ${pt.y}` : `${acc} L ${pt.x} ${pt.y}`;
      }, '');

  // Area under line
  const areaD = sorted.length === 1
    ? `M ${padding.left} ${points[0].y} L ${padding.left + innerWidth} ${points[0].y} L ${padding.left + innerWidth} ${padding.top + innerHeight} L ${padding.left} ${padding.top + innerHeight} Z`
    : `${pathD} L ${points[points.length - 1].x} ${padding.top + innerHeight} L ${points[0].x} ${padding.top + innerHeight} Z`;

  const formatDate = (dateStr) => {
    try {
      const d = new Date(dateStr);
      return d.toLocaleDateString('en-IN', { day: 'numeric', month: 'short' });
    } catch {
      return dateStr;
    }
  };

  const formatDateTime = (dateStr) => {
    try {
      const d = new Date(dateStr);
      return d.toLocaleString('en-IN', { 
        day: 'numeric', month: 'short', year: 'numeric',
        hour: '2-digit', minute: '2-digit' 
      });
    } catch {
      return dateStr;
    }
  };

  const activePoint = hoveredIndex !== null ? points[hoveredIndex] : points[points.length - 1];

  return (
    <div className="bg-white rounded-xl border border-slate-200 overflow-hidden shadow-sm">
      <div className="p-5 border-b border-slate-100 flex flex-col sm:flex-row justify-between sm:items-center gap-3">
        <div>
          <h4 className="font-bold text-slate-900 text-base flex items-center gap-2">
            <TrendingUp className="w-4 h-4 text-emerald-600" />
            Grey Market Premium (GMP) Trajectory
          </h4>
          <p className="text-xs text-slate-500 mt-0.5">
            Day-by-day historical changes captured automatically
          </p>
        </div>

        {/* Latest Snapshot Pill */}
        {activePoint && (
          <div className="flex items-center gap-3 bg-slate-50 px-3 py-1.5 rounded-lg border border-slate-200 self-start sm:self-auto">
            <div className="text-right">
              <span className="text-[10px] text-slate-400 block uppercase font-bold">GMP Selected</span>
              <span className="font-mono font-bold text-emerald-600 text-sm">₹{activePoint.gmp}</span>
            </div>
            {priceBandHigh && (
              <div className="text-right border-l border-slate-200 pl-3">
                <span className="text-[10px] text-slate-400 block uppercase font-bold">Est. Gain</span>
                <span className="font-mono font-bold text-slate-800 text-sm">
                  +{roundNumber((Number(activePoint.gmp) / priceBandHigh) * 100, 1)}%
                </span>
              </div>
            )}
          </div>
        )}
      </div>

      {/* Interactive SVG Chart */}
      <div className="p-4 sm:p-5 bg-gradient-to-b from-slate-50/50 to-white">
        <div className="relative w-full overflow-hidden">
          <svg
            viewBox={`0 0 ${width} ${height}`}
            className="w-full h-auto max-h-64 select-none"
          >
            <defs>
              <linearGradient id="gmpGradient" x1="0" y1="0" x2="0" y2="1">
                <stop offset="0%" stopColor="#10b981" stopOpacity="0.25" />
                <stop offset="100%" stopColor="#10b981" stopOpacity="0.0" />
              </linearGradient>
            </defs>

            {/* Grid Lines */}
            {[0, 0.25, 0.5, 0.75, 1].map((pct, i) => {
              const y = padding.top + innerHeight * (1 - pct);
              const val = Math.round(minVal + valRange * pct);
              return (
                <g key={i}>
                  <line
                    x1={padding.left}
                    y1={y}
                    x2={width - padding.right}
                    y2={y}
                    stroke="#e2e8f0"
                    strokeDasharray="4 4"
                    strokeWidth="1"
                  />
                  <text
                    x={padding.left - 8}
                    y={y + 3}
                    textAnchor="end"
                    fontSize="10"
                    fill="#94a3b8"
                    fontFamily="monospace"
                  >
                    ₹{val}
                  </text>
                </g>
              );
            })}

            {/* Shaded Area */}
            <path d={areaD} fill="url(#gmpGradient)" />

            {/* Main Trend Line */}
            <path
              d={pathD}
              fill="none"
              stroke="#059669"
              strokeWidth="2.5"
              strokeLinecap="round"
              strokeLinejoin="round"
            />

            {/* Data Points */}
            {points.map((pt, i) => (
              <g key={i}>
                <circle
                  cx={pt.x}
                  cy={pt.y}
                  r={hoveredIndex === i ? 6 : 4}
                  fill={hoveredIndex === i ? "#047857" : "#10b981"}
                  stroke="#ffffff"
                  strokeWidth="2"
                  className="cursor-pointer transition-all"
                  onMouseEnter={() => setHoveredIndex(i)}
                />
                <text
                  x={pt.x}
                  y={padding.top + innerHeight + 18}
                  textAnchor="middle"
                  fontSize="10"
                  fill="#64748b"
                >
                  {formatDate(pt.recorded_at)}
                </text>
              </g>
            ))}
          </svg>
        </div>
      </div>

      {/* Historical Audit Table */}
      <div className="border-t border-slate-200">
        <div className="px-4 py-2.5 bg-slate-50 text-[11px] font-bold uppercase tracking-wider text-slate-500 border-b border-slate-200">
          GMP Audit History
        </div>
        <div className="max-h-56 overflow-y-auto">
          <table className="w-full text-left text-xs">
            <thead className="bg-white text-slate-500 sticky top-0 border-b border-slate-100">
              <tr>
                <th className="py-2.5 px-4 font-semibold">Recorded Date & Time</th>
                <th className="py-2.5 px-3 font-semibold">GMP (₹)</th>
                {priceBandHigh && <th className="py-2.5 px-3 font-semibold">Est. Listing Price</th>}
                {priceBandHigh && <th className="py-2.5 px-3 font-semibold">Est. Gain %</th>}
                <th className="py-2.5 px-4 font-semibold text-right">Source</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-slate-100">
              {[...sorted].reverse().map((r, i) => {
                const gmpNum = Number(r.gmp);
                const estPrice = priceBandHigh ? priceBandHigh + gmpNum : null;
                const estGain = priceBandHigh ? ((gmpNum / priceBandHigh) * 100).toFixed(1) : null;
                return (
                  <tr key={r.id || i} className="hover:bg-slate-50">
                    <td className="py-2.5 px-4 text-slate-700">
                      {formatDateTime(r.recorded_at)}
                    </td>
                    <td className="py-2.5 px-3 font-mono font-bold text-emerald-600">
                      ₹{gmpNum}
                    </td>
                    {priceBandHigh && (
                      <td className="py-2.5 px-3 font-mono text-slate-800">
                        ₹{estPrice}
                      </td>
                    )}
                    {priceBandHigh && (
                      <td className="py-2.5 px-3">
                        <span className="font-mono font-bold text-emerald-600">
                          +{estGain}%
                        </span>
                      </td>
                    )}
                    <td className="py-2.5 px-4 text-right">
                      <span className={`text-[10px] font-semibold px-2 py-0.5 rounded border inline-block ${
                        r.source_name === 'InvestorGain'
                          ? 'bg-sky-50 text-sky-700 border-sky-200'
                          : r.source_name === 'IPOWatch'
                            ? 'bg-purple-50 text-purple-700 border-purple-200'
                            : 'bg-slate-50 text-slate-700 border-slate-200'
                      }`}>
                        {r.source_name === 'InvestorGain' ? 'InvestorGain (Primary)' : r.source_name === 'IPOWatch' ? 'IPOWatch (Secondary)' : r.source_name}
                      </span>
                    </td>
                  </tr>
                );
              })}
            </tbody>
          </table>
        </div>
      </div>
    </div>
  );
}

function roundNumber(num, decimals = 2) {
  return Number(Math.round(Number(num + 'e' + decimals)) + 'e-' + decimals);
}
