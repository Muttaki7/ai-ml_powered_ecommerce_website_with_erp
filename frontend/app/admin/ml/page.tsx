"use client";

import { useEffect, useState } from "react";
import { adminApi, productApi, getApiError } from "@/lib/api";
import { useAdminAuth } from "@/lib/useAdminAuth";
import { AdminShell } from "@/components/AdminShell";
import toast from "react-hot-toast";
import { RefreshCw } from "lucide-react";

export default function AdminMlPage() {
  const { user, loading } = useAdminAuth();
  const [products, setProducts] = useState<any[]>([]);
  const [selected, setSelected] = useState("");
  const [forecast, setForecast] = useState<any>(null);
  const [recs, setRecs] = useState<any[]>([]);
  const [loadingForecast, setLoadingForecast] = useState(false);
  const [runningBatch, setRunningBatch] = useState(false);

  async function runBatch() {
    setRunningBatch(true);
    try {
      const r = await adminApi.mlBatchForecast(30);
      toast.success(r.data?.message || "Batch forecast queued — re-check recommendations shortly");
      setTimeout(() => {
        adminApi.mlRecommendations().then((x) => setRecs(x.data || [])).catch(() => {});
        setRunningBatch(false);
      }, 6000);
    } catch (e: any) {
      toast.error(getApiError(e, "Batch forecast failed"));
      setRunningBatch(false);
    }
  }

  useEffect(() => {
    if (!loading) {
      productApi.list({ limit: 100 }).then((r) => setProducts(r.data || [])).catch(() => {});
      adminApi.mlRecommendations().then((r) => setRecs(r.data || [])).catch(() => {});
    }
  }, [loading]);

  async function loadForecast(id: string) {
    setSelected(id);
    if (!id) return setForecast(null);
    setLoadingForecast(true);
    try {
      const r = await adminApi.mlDemand(id);
      setForecast(r.data);
    } catch (e: any) {
      toast.error(getApiError(e, "Forecast failed"));
      setForecast(null);
    } finally {
      setLoadingForecast(false);
    }
  }

  const p30 = forecast?.predictions?.next_30_days || {};
  const p7 = forecast?.predictions?.next_7_days || {};
  const p90 = forecast?.predictions?.next_90_days || {};
  const rec = forecast?.recommendation || {};

  const horizonData = [
    { label: "Next 7 days", total: p7.predicted_total, trend: p7.trend },
    { label: "Next 30 days", total: p30.predicted_total, trend: p30.trend },
    { label: "Next 90 days", total: p90.predicted_total, trend: p90.trend },
  ];

  if (loading) {
    return (
      <div className="min-h-screen bg-slate-100 dark:bg-slate-950 flex items-center justify-center">
        <div className="w-16 h-16 rounded-xl bg-slate-200 dark:bg-slate-800 animate-pulse" />
      </div>
    );
  }

  return (
    <AdminShell title="ML & Demand Forecasting" user={user}>
      <div className="grid lg:grid-cols-2 gap-6">
        {/* Forecast */}
        <div className="card p-5">
          <h2 className="font-semibold mb-3 text-slate-900 dark:text-white">Demand Forecast</h2>
          <select
            value={selected}
            onChange={(e) => loadForecast(e.target.value)}
            className="input w-full mb-4"
          >
            <option value="">Select a product...</option>
            {products.map((p) => (
              <option key={p.id} value={p.id}>
                {p.name}
              </option>
            ))}
          </select>

          {loadingForecast && <p className="text-sm text-slate-500 dark:text-slate-400">Computing forecast...</p>}

          {forecast && !loadingForecast && (
            <div>
              <div className="flex items-center justify-between text-sm mb-2">
                <span className="text-slate-500 dark:text-slate-400 truncate">{forecast.name}</span>
                <span
                  className={`px-2 py-0.5 rounded-full text-xs font-medium ${
                    rec.action === "reorder"
                      ? "bg-rose-100 text-rose-700"
                      : rec.action === "watch"
                      ? "bg-amber-100 text-amber-700"
                      : "bg-emerald-100 text-emerald-700"
                  }`}
                >
                  {rec.action || "hold"}
                </span>
              </div>

              <div className="grid grid-cols-3 gap-3 text-center mb-4">
                {horizonData.map((h) => (
                  <div key={h.label} className="bg-slate-100 dark:bg-slate-800 rounded-xl p-3">
                    <p className="text-xs text-slate-500 dark:text-slate-400">{h.label}</p>
                    <p className="text-xl font-bold text-slate-900 dark:text-white">{Math.round(h.total || 0)}</p>
                    <p className="text-xs capitalize text-slate-600 dark:text-slate-400">{h.trend || "—"}</p>
                  </div>
                ))}
              </div>

              <div className="border dark:border-slate-700 rounded-xl p-3 text-sm">
                <p className="text-xs font-medium text-slate-500 dark:text-slate-400 uppercase">Recommendation</p>
                <p className="mt-1 font-medium capitalize text-slate-900 dark:text-white">{rec.action}</p>
                <p className="mt-1 text-xs text-slate-500 dark:text-slate-400">
                  {rec.reason}
                  {rec.qty ? ` Suggested quantity: ${rec.qty} units.` : ""}
                </p>
              </div>

              {forecast.current_stock != null && (
                <p className="mt-3 text-xs text-slate-500 dark:text-slate-400">
                  Current stock: <strong className="text-slate-800 dark:text-slate-200">{forecast.current_stock}</strong> · Min level:{" "}
                  <strong className="text-slate-800 dark:text-slate-200">{forecast.min_stock_level}</strong>
                </p>
              )}
            </div>
          )}
          {!forecast && !loadingForecast && (
            <p className="text-sm text-slate-400 dark:text-slate-500">Select a product to see its 30-day demand forecast.</p>
          )}
        </div>

        {/* Purchase recommendations */}
        <div className="card p-5">
          <div className="flex items-center justify-between mb-3">
            <h2 className="font-semibold text-slate-900 dark:text-white">Smart Purchase Recommendations</h2>
            <button
              onClick={runBatch}
              disabled={runningBatch}
              className="btn-primary !py-2 !px-3 text-xs inline-flex"
            >
              <RefreshCw size={13} className={runningBatch ? "animate-spin" : ""} />
              {runningBatch ? "Running..." : "Run batch forecast"}
            </button>
          </div>
          <p className="text-xs text-slate-400 dark:text-slate-500 mb-3">
            Batch forecast computes 30-day demand for top products, which powers the
            recommendations below.
          </p>
          {recs.length === 0 ? (
            <p className="text-sm text-slate-400 dark:text-slate-500">
              No recommendations right now. Products whose predicted 30-day demand exceeds stock
              will appear here after forecasts run.
            </p>
          ) : (
            <div className="space-y-3">
              {recs.map((r) => (
                <div key={r.product_id} className="border dark:border-slate-700 rounded-xl p-3 text-sm">
                  <p className="font-medium text-slate-900 dark:text-white">{r.name}</p>
                  <p className="text-xs text-slate-500 dark:text-slate-400 mt-1">{r.reason}</p>
                  <div className="mt-2 flex gap-4 text-xs text-slate-600 dark:text-slate-400">
                    <span>
                      Stock: <strong className="text-slate-900 dark:text-white">{r.current_stock}</strong>
                    </span>
                    <span>
                      Predicted 30d: <strong className="text-slate-900 dark:text-white">{Math.round(r.predicted_30d)}</strong>
                    </span>
                    <span className="text-sky-600 dark:text-sky-400 font-semibold">
                      Buy {r.recommended_purchase} units
                    </span>
                  </div>
                </div>
              ))}
            </div>
          )}
        </div>
      </div>
    </AdminShell>
  );
}