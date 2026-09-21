"use client";

import { useEffect, useState } from "react";
import { adminApi, formatBDT, getApiError } from "@/lib/api";
import { useAdminAuth } from "@/lib/useAdminAuth";
import { AdminShell } from "@/components/AdminShell";
import toast from "react-hot-toast";
import { Megaphone, ImageIcon, Truck, Save } from "lucide-react";

const ACCENTS = [
  "from-rose-500 to-orange-400",
  "from-emerald-500 to-teal-400",
  "from-sky-500 to-cyan-400",
  "from-indigo-500 to-violet-400",
  "from-amber-500 to-yellow-400",
  "from-fuchsia-500 to-pink-400",
  "from-slate-700 to-slate-900",
];

export default function AdminSettingsPage() {
  const { user, loading } = useAdminAuth();
  const [saving, setSaving] = useState(false);
  const [banner, setBanner] = useState({ badge: "", title: "", subtitle: "" });
  const [posters, setPosters] = useState<any[]>([]);
  const [delivery, setDelivery] = useState({
    inside_dhaka: 0,
    outside_dhaka: 0,
    free_delivery_enabled: false,
    free_delivery_threshold: 0,
  });

  useEffect(() => {
    if (loading) return;
    adminApi
      .settings()
      .then((r) => {
        const d = r.data || {};
        setBanner({
          badge: d.banner?.badge ?? "",
          title: d.banner?.title ?? "",
          subtitle: d.banner?.subtitle ?? "",
        });
        setPosters(
          (d.posters || []).map((p: any) => ({
            title: p.title ?? "",
            subtitle: p.subtitle ?? "",
            accent: p.accent ?? ACCENTS[0],
            visible: p.visible ?? true,
          }))
        );
        setDelivery({
          inside_dhaka: d.delivery?.inside_dhaka ?? 0,
          outside_dhaka: d.delivery?.outside_dhaka ?? 0,
          free_delivery_enabled: d.delivery?.free_delivery_enabled ?? false,
          free_delivery_threshold: d.delivery?.free_delivery_threshold ?? 0,
        });
      })
      .catch(() => toast.error("Failed to load settings"));
  }, [loading]);

  function updatePoster(i: number, patch: Partial<any>) {
    setPosters((ps) => ps.map((p, idx) => (idx === i ? { ...p, ...patch } : p)));
  }

  async function save(e: React.FormEvent) {
    e.preventDefault();
    setSaving(true);
    try {
      await adminApi.updateSettings({
        banner,
        posters,
        delivery: {
          inside_dhaka: parseFloat(delivery.inside_dhaka as any) || 0,
          outside_dhaka: parseFloat(delivery.outside_dhaka as any) || 0,
          free_delivery_enabled: delivery.free_delivery_enabled,
          free_delivery_threshold: parseFloat(delivery.free_delivery_threshold as any) || 0,
        },
      });
      toast.success("Settings saved");
    } catch (err: any) {
      toast.error(getApiError(err, "Save failed"));
    } finally {
      setSaving(false);
    }
  }

  if (loading) {
    return (
      <div className="min-h-screen bg-slate-100 dark:bg-slate-950 flex items-center justify-center">
        <div className="w-16 h-16 rounded-xl bg-slate-200 dark:bg-slate-800 animate-pulse" />
      </div>
    );
  }

  return (
    <AdminShell title="Store Settings" user={user}>
      <form onSubmit={save} className="space-y-6 max-w-4xl">
        {/* Banner */}
        <section className="card p-5 space-y-4">
          <h2 className="flex items-center gap-2 font-semibold text-slate-900 dark:text-white">
            <Megaphone size={18} className="text-sky-600" /> Homepage Banner
          </h2>
          <div className="grid md:grid-cols-3 gap-3">
            <div>
              <label className="block text-xs font-medium text-slate-500 dark:text-slate-400 mb-1">
                Badge
              </label>
              <input
                value={banner.badge}
                onChange={(e) => setBanner({ ...banner, badge: e.target.value })}
                placeholder="e.g. AI-powered pricing"
                className="input text-sm"
              />
            </div>
            <div>
              <label className="block text-xs font-medium text-slate-500 dark:text-slate-400 mb-1">
                Title
              </label>
              <input
                value={banner.title}
                onChange={(e) => setBanner({ ...banner, title: e.target.value })}
                placeholder="e.g. Shop smarter across Bangladesh"
                className="input text-sm"
              />
            </div>
            <div>
              <label className="block text-xs font-medium text-slate-500 dark:text-slate-400 mb-1">
                Subtitle
              </label>
              <input
                value={banner.subtitle}
                onChange={(e) => setBanner({ ...banner, subtitle: e.target.value })}
                placeholder="Short description under the title"
                className="input text-sm"
              />
            </div>
          </div>
        </section>

        {/* Posters */}
        <section className="card p-5 space-y-4">
          <h2 className="flex items-center gap-2 font-semibold text-slate-900 dark:text-white">
            <ImageIcon size={18} className="text-sky-600" /> Poster Cards
          </h2>
          <div className="grid md:grid-cols-2 gap-4">
            {posters.map((p, i) => (
              <div key={i} className="border dark:border-slate-700 rounded-xl p-4 space-y-3">
                <div className="flex items-center justify-between">
                  <span className="text-xs font-bold uppercase tracking-wide text-slate-400">
                    Poster {i + 1}
                  </span>
                  <label className="flex items-center gap-2 text-xs text-slate-600 dark:text-slate-300">
                    <input
                      type="checkbox"
                      checked={p.visible}
                      onChange={(e) => updatePoster(i, { visible: e.target.checked })}
                    />
                    Visible
                  </label>
                </div>
                <div className="grid grid-cols-2 gap-2">
                  <input
                    value={p.title}
                    onChange={(e) => updatePoster(i, { title: e.target.value })}
                    placeholder="Title"
                    className="input text-sm"
                  />
                  <input
                    value={p.subtitle}
                    onChange={(e) => updatePoster(i, { subtitle: e.target.value })}
                    placeholder="Subtitle"
                    className="input text-sm"
                  />
                </div>
                <div>
                  <label className="block text-xs font-medium text-slate-500 dark:text-slate-400 mb-1">
                    Accent color
                  </label>
                  <select
                    value={p.accent}
                    onChange={(e) => updatePoster(i, { accent: e.target.value })}
                    className="input text-sm"
                  >
                    {ACCENTS.map((a) => (
                      <option key={a} value={a}>
                        {a}
                      </option>
                    ))}
                  </select>
                </div>
                <div
                  className={`rounded-lg p-3 text-white text-xs bg-gradient-to-br ${p.accent} ${
                    p.visible ? "" : "opacity-40"
                  }`}
                >
                  <p className="font-bold uppercase tracking-widest">{p.title || "Title"}</p>
                  <p className="mt-1 text-white/90">{p.subtitle || "Subtitle"}</p>
                </div>
              </div>
            ))}
          </div>
        </section>

        {/* Delivery */}
        <section className="card p-5 space-y-4">
          <h2 className="flex items-center gap-2 font-semibold text-slate-900 dark:text-white">
            <Truck size={18} className="text-sky-600" /> Delivery Pricing
          </h2>
          <div className="grid md:grid-cols-3 gap-3">
            <div>
              <label className="block text-xs font-medium text-slate-500 dark:text-slate-400 mb-1">
                Inside Dhaka (charge)
              </label>
              <div className="flex items-center gap-1">
                <span className="text-slate-500 dark:text-slate-400 text-sm">৳</span>
                <input
                  type="number"
                  min="0"
                  step="0.01"
                  value={delivery.inside_dhaka}
                  onChange={(e) => setDelivery({ ...delivery, inside_dhaka: parseFloat(e.target.value) || 0 })}
                  className="input text-sm"
                />
              </div>
            </div>
            <div>
              <label className="block text-xs font-medium text-slate-500 dark:text-slate-400 mb-1">
                All over Bangladesh (charge)
              </label>
              <div className="flex items-center gap-1">
                <span className="text-slate-500 dark:text-slate-400 text-sm">৳</span>
                <input
                  type="number"
                  min="0"
                  step="0.01"
                  value={delivery.outside_dhaka}
                  onChange={(e) => setDelivery({ ...delivery, outside_dhaka: parseFloat(e.target.value) || 0 })}
                  className="input text-sm"
                />
              </div>
            </div>
            <div>
              <label className="block text-xs font-medium text-slate-500 dark:text-slate-400 mb-1">
                Free delivery threshold (৳)
              </label>
              <div className="flex items-center gap-1">
                <span className="text-slate-500 dark:text-slate-400 text-sm">৳</span>
                <input
                  type="number"
                  min="0"
                  step="0.01"
                  value={delivery.free_delivery_threshold}
                  onChange={(e) => setDelivery({ ...delivery, free_delivery_threshold: parseFloat(e.target.value) || 0 })}
                  className="input text-sm"
                />
              </div>
            </div>
          </div>
          <label className="flex items-center gap-2 text-sm text-slate-700 dark:text-slate-300">
            <input
              type="checkbox"
              checked={delivery.free_delivery_enabled}
              onChange={(e) => setDelivery({ ...delivery, free_delivery_enabled: e.target.checked })}
            />
            Enable free delivery on orders at or above the threshold
          </label>
          <p className="text-xs text-slate-500 dark:text-slate-400">
            Current Dhaka charge: {formatBDT(delivery.inside_dhaka)} · Rest of the country:{" "}
            {formatBDT(delivery.outside_dhaka)}
          </p>
        </section>

        <div className="flex justify-end">
          <button type="submit" disabled={saving} className="btn-primary inline-flex gap-2 disabled:opacity-50">
            <Save size={16} /> {saving ? "Saving..." : "Save Settings"}
          </button>
        </div>
      </form>
    </AdminShell>
  );
}