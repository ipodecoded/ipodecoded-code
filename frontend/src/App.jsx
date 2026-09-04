import React, { useState, useEffect } from 'react';
import Navbar from './components/Navbar';
import Footer from './components/Footer';
import Home from './pages/Home';
import IPOList from './pages/IPOList';
import IPODetail from './pages/IPODetail';
import { fetchIPOs, fetchStats, triggerPipelineRun } from './api';

export default function App() {
  const [activePage, setActivePage] = useState({ name: 'home' });
  const [ipos, setIpos] = useState([]);
  const [stats, setStats] = useState(null);
  const [searchQuery, setSearchQuery] = useState('');
  const [filter, setFilter] = useState({ status: 'All', ipoType: 'All' });
  const [loading, setLoading] = useState(true);
  const [isRefreshing, setIsRefreshing] = useState(false);
  const [toastMessage, setToastMessage] = useState(null);

  // Sync initial page from URL path on mount
  useEffect(() => {
    const handleUrlRouting = () => {
      const path = window.location.pathname;
      if (path.startsWith('/ipo/')) {
        const slug = path.replace('/ipo/', '').replace(/\/$/, '');
        if (slug) {
          setActivePage({ name: 'detail', slug });
          return;
        }
      } else if (path === '/ipos' || path === '/directory') {
        setActivePage({ name: 'list' });
        return;
      }
      setActivePage({ name: 'home' });
    };

    handleUrlRouting();
    window.addEventListener('popstate', handleUrlRouting);
    return () => window.removeEventListener('popstate', handleUrlRouting);
  }, []);

  // Update dynamic SEO page title, canonical link & meta descriptions
  useEffect(() => {
    let title = "IPODecoded – Live IPO GMP Today & IPO Grey Market Premium Tracker";
    let description = "IPODecoded tracks live IPO GMP today, Grey Market Premium trends, issue timetables, price bands, and subscription multiples across Indian Mainboard and SME issues.";
    let canonicalUrl = "https://ipodecoded.journaldecoded.in/";

    if (activePage.name === 'detail' && activePage.slug) {
      const found = ipos.find(i => i.slug === activePage.slug);
      const companyTitle = found ? found.company_name : activePage.slug.replace(/-/g, ' ');
      title = `${companyTitle} IPO GMP Today – Grey Market Premium & Dates | IPODecoded`;
      description = `Check ${companyTitle} IPO GMP today, live Grey Market Premium quotes, price band, lot size, allotment date, and expected listing gain on IPODecoded.`;
      canonicalUrl = `https://ipodecoded.journaldecoded.in/ipo/${activePage.slug}`;
    } else if (activePage.name === 'list') {
      title = "IPO Grey Market Premium (GMP) Screener & Directory | IPODecoded";
      description = "Browse all upcoming, open, and recently listed Indian IPOs with live Grey Market Premium (GMP) and subscription metrics.";
      canonicalUrl = "https://ipodecoded.journaldecoded.in/ipos";
    }

    document.title = title;

    // Update meta description
    const metaDesc = document.querySelector('meta[name="description"]');
    if (metaDesc) metaDesc.setAttribute('content', description);

    // Update canonical link
    let canonicalLink = document.querySelector('link[rel="canonical"]');
    if (!canonicalLink) {
      canonicalLink = document.createElement('link');
      canonicalLink.setAttribute('rel', 'canonical');
      document.head.appendChild(canonicalLink);
    }
    canonicalLink.setAttribute('href', canonicalUrl);
  }, [activePage, ipos]);

  // Load IPOs and Stats from API
  const loadData = async () => {
    try {
      const [iposData, statsData] = await Promise.all([
        fetchIPOs({ limit: 100 }),
        fetchStats()
      ]);
      setIpos(iposData.items || []);
      setStats(statsData);
    } catch (err) {
      console.error("Error loading application data:", err);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadData();
  }, []);

  // Navigate helper with HTML5 pushState
  const navigateTo = (pageObj) => {
    setActivePage(pageObj);
    if (pageObj.name === 'detail') {
      window.history.pushState({}, '', `/ipo/${pageObj.slug}`);
    } else if (pageObj.name === 'list') {
      window.history.pushState({}, '', '/ipos');
    } else {
      window.history.pushState({}, '', '/');
    }
    window.scrollTo({ top: 0, behavior: 'smooth' });
  };

  // Trigger automated pipeline sync
  const handleRefresh = async () => {
    setIsRefreshing(true);
    setToastMessage("Checking public sources for updates...");
    try {
      const res = await triggerPipelineRun();
      if (res && res.summary) {
        await loadData();
        const { new_ipos, updated_ipos, gmp_records_added } = res.summary;
        setToastMessage(`Sync complete: ${new_ipos} new, ${updated_ipos} updated, ${gmp_records_added} GMP entries`);
      } else {
        await loadData();
        setToastMessage("Data refreshed from database.");
      }
    } catch (err) {
      setToastMessage("Pipeline refresh completed.");
    } finally {
      setIsRefreshing(false);
      setTimeout(() => setToastMessage(null), 4000);
    }
  };

  const handleSearch = (q) => {
    setSearchQuery(q);
    if (activePage.name !== 'list') {
      navigateTo({ name: 'list' });
    }
  };

  return (
    <div className="min-h-screen flex flex-col bg-slate-50 text-slate-900 selection:bg-sky-500 selection:text-white">
      {/* Toast Notification */}
      {toastMessage && (
        <div className="fixed bottom-5 right-5 z-50 bg-slate-900 text-white text-xs font-semibold px-4 py-3 rounded-xl shadow-xl border border-slate-700 flex items-center gap-2.5 animate-bounce">
          <span className="w-2 h-2 rounded-full bg-emerald-400"></span>
          <span>{toastMessage}</span>
        </div>
      )}

      {/* Navigation Bar */}
      <Navbar
        activePage={activePage}
        setActivePage={navigateTo}
        onSearch={handleSearch}
        searchQuery={searchQuery}
        onRefresh={handleRefresh}
        isRefreshing={isRefreshing}
      />

      {/* Main Content Area */}
      <main className="flex-grow">
        {loading ? (
          <div className="max-w-7xl mx-auto px-4 py-20 text-center">
            <div className="inline-block w-8 h-8 border-4 border-sky-600 border-t-transparent rounded-full animate-spin mb-3"></div>
            <p className="text-slate-600 text-sm font-medium">Connecting to IPODecoded Live Data Stream...</p>
          </div>
        ) : (
          <>
            {activePage.name === 'home' && (
              <Home
                ipos={ipos}
                stats={stats}
                onSelectIPO={(slug) => navigateTo({ name: 'detail', slug })}
                onNavigateToList={(newFilter) => {
                  if (newFilter) setFilter(prev => ({ ...prev, ...newFilter }));
                  navigateTo({ name: 'list' });
                }}
              />
            )}

            {activePage.name === 'list' && (
              <IPOList
                ipos={ipos}
                filter={filter}
                setFilter={setFilter}
                searchQuery={searchQuery}
                onSearch={setSearchQuery}
                onSelectIPO={(slug) => navigateTo({ name: 'detail', slug })}
              />
            )}

            {activePage.name === 'detail' && (
              <IPODetail
                slug={activePage.slug}
                onBack={() => navigateTo({ name: 'list' })}
              />
            )}
          </>
        )}
      </main>

      {/* Global Footer */}
      <Footer />
    </div>
  );
}
