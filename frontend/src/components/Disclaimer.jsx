import React from 'react';
import { AlertTriangle, ShieldCheck } from 'lucide-react';

export default function Disclaimer({ compact = false }) {
  if (compact) {
    return (
      <div className="bg-amber-50/80 border border-amber-200 rounded-lg p-3 text-xs text-amber-900 flex items-start gap-2.5">
        <AlertTriangle className="w-4 h-4 text-amber-600 shrink-0 mt-0.5" />
        <div>
          <span className="font-semibold">Statutory Disclaimer: </span>
          GMP (Grey Market Premium) is unofficial and may change dynamically. Estimated listing price and gain percentages are mathematical projections and not official indications of exchange listing price.
        </div>
      </div>
    );
  }

  return (
    <div className="bg-slate-50 border border-slate-200 rounded-xl p-4 sm:p-5 my-6 text-xs text-slate-600">
      <div className="flex items-center gap-2 mb-2">
        <ShieldCheck className="w-4 h-4 text-sky-600" />
        <span className="font-bold text-slate-800 uppercase tracking-wider text-[11px]">
          Regulatory & General Disclaimer
        </span>
      </div>
      <p className="leading-relaxed">
        <strong>IPODecoded</strong> (a product of <strong>JournalDecoded.in</strong>) provides IPO information for educational and informational purposes only. Grey Market Premium (GMP) is completely unofficial, unregulated, and may not accurately predict the actual listing price. IPODecoded does not facilitate grey market trading. Users should independently verify all prospectus and issue details from official SEBI, BSE, and NSE exchange filings before making any investment decisions.
      </p>
    </div>
  );
}
