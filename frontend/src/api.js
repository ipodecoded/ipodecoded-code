// API client for IPODecoded backend
const API_BASE = import.meta.env.VITE_API_URL || (typeof window !== 'undefined' ? '/api' : 'http://localhost:8000/api');

export async function fetchHealth() {
  try {
    const res = await fetch(`${API_BASE}/health`);
    if (!res.ok) throw new Error("Health check failed");
    return await res.json();
  } catch (err) {
    console.error("API health error:", err);
    return null;
  }
}

export async function fetchStats() {
  try {
    const res = await fetch(`${API_BASE}/stats`);
    if (!res.ok) throw new Error("Stats fetch failed");
    return await res.json();
  } catch (err) {
    console.error("API stats error:", err);
    return null;
  }
}

export async function fetchIPOs({ status, ipoType, search, sortBy, limit = 50, offset = 0 } = {}) {
  const params = new URLSearchParams();
  if (status && status !== "All") params.append("status", status);
  if (ipoType && ipoType !== "All") params.append("ipo_type", ipoType);
  if (search && search.trim()) params.append("search", search.trim());
  if (sortBy) params.append("sort_by", sortBy);
  params.append("limit", limit.toString());
  params.append("offset", offset.toString());

  try {
    const res = await fetch(`${API_BASE}/ipos?${params.toString()}`);
    if (!res.ok) throw new Error("Failed to fetch IPOs");
    return await res.json();
  } catch (err) {
    console.error("Fetch IPOs error:", err);
    return { total: 0, items: [] };
  }
}

export async function fetchIPODetail(slug) {
  try {
    const res = await fetch(`${API_BASE}/ipos/${encodeURIComponent(slug)}`);
    if (!res.ok) throw new Error(`Failed to fetch IPO detail for ${slug}`);
    return await res.json();
  } catch (err) {
    console.error("Fetch IPO detail error:", err);
    return null;
  }
}

export async function fetchGMPHistory(slug) {
  try {
    const res = await fetch(`${API_BASE}/ipos/${encodeURIComponent(slug)}/gmp-history`);
    if (!res.ok) throw new Error(`Failed to fetch GMP history for ${slug}`);
    return await res.json();
  } catch (err) {
    console.error("Fetch GMP history error:", err);
    return [];
  }
}

export async function triggerPipelineRun() {
  try {
    const res = await fetch(`${API_BASE}/pipeline/run`, { method: "POST" });
    if (!res.ok) throw new Error("Failed to trigger pipeline");
    return await res.json();
  } catch (err) {
    console.error("Trigger pipeline error:", err);
    return null;
  }
}
