import React from 'react';
import { ExternalLink, Database, ShieldAlert } from 'lucide-react';

export default function Footer() {
  return (
    <footer className="bg-white border-t border-slate-200 mt-16 text-slate-500 text-xs">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 py-10">
        <div className="grid grid-cols-1 md:grid-cols-4 gap-8 mb-8">
          {/* Col 1: Brand */}
          <div className="space-y-2 md:col-span-2">
            <div className="flex items-center gap-2">
              <img
                src="/ipo-decoded-logo.png"
                alt="IPODecoded Logo"
                className="w-7 h-7 rounded-lg object-cover bg-black shadow-sm"
              />
              <span className="font-black text-base text-slate-900">
                IPO<span className="text-sky-600">Decoded</span>
              </span>
              <span className="text-[10px] bg-slate-100 text-slate-600 px-1.5 py-0.5 rounded font-medium">
                V1 Production
              </span>
            </div>
            <p className="text-slate-600 leading-relaxed text-xs max-w-md">
              A high-density financial market portal tracking Indian Mainboard and SME IPOs, price bands, issue timetables, subscription multiples, and historical Grey Market Premiums automatically.
            </p>
            <p className="text-slate-400 text-[11px]">
              A subsidiary product of <a href="https://journaldecoded.in" target="_blank" rel="noreferrer" className="text-sky-600 font-semibold hover:underline">JournalDecoded.in</a>.
            </p>
          </div>

          {/* Col 2: Public Sources */}
          <div>
            <h5 className="font-bold text-slate-900 text-xs uppercase tracking-wider mb-3">
              Data & Regulatory Sources
            </h5>
            <ul className="space-y-1.5 text-xs text-slate-600">
              <li>
                <a href="https://www.bseindia.com" target="_blank" rel="noreferrer" className="hover:text-sky-600 flex items-center gap-1">
                  BSE India Public Issues <ExternalLink className="w-3 h-3 text-slate-400" />
                </a>
              </li>
              <li>
                <a href="https://www.nseindia.com" target="_blank" rel="noreferrer" className="hover:text-sky-600 flex items-center gap-1">
                  NSE India IPO Emerge <ExternalLink className="w-3 h-3 text-slate-400" />
                </a>
              </li>
              <li>
                <a href="https://www.sebi.gov.in" target="_blank" rel="noreferrer" className="hover:text-sky-600 flex items-center gap-1">
                  SEBI DRHP & Prospectus <ExternalLink className="w-3 h-3 text-slate-400" />
                </a>
              </li>
              <li>
                <span className="text-slate-400 text-[11px]">InvestorGain & Chittorgarh (GMP aggregations)</span>
              </li>
            </ul>
          </div>

          {/* Col 3: Architecture & System Status */}
          <div>
            <h5 className="font-bold text-slate-900 text-xs uppercase tracking-wider mb-3">
              Architecture
            </h5>
            <ul className="space-y-1.5 text-xs text-slate-600">
              <li className="flex items-center gap-1.5">
                <span className="w-2 h-2 rounded-full bg-emerald-500"></span>
                <span>Automated Data Pipeline</span>
              </li>
              <li>PostgreSQL / Supabase Storage</li>
              <li>Zero-cost serverless hosting</li>
              <li>Hourly GMP change detection</li>
            </ul>
          </div>
        </div>

        {/* Bottom Bar */}
        <div className="pt-6 border-t border-slate-100 flex flex-col sm:flex-row justify-between items-center gap-3 text-slate-400 text-[11px]">
          <div>
            &copy; {new Date().getFullYear()} IPODecoded &bull; JournalDecoded.in. All rights reserved.
          </div>
          <div className="flex items-center gap-4">
            <span>Market Data &bull; Unofficial GMP Estimates</span>
          </div>
        </div>
      </div>
    </footer>
  );
}
