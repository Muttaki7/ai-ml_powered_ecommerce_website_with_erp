"use client";

import Link from "next/link";
import { useEffect, useState } from "react";
import { productApi, settingsApi } from "@/lib/api";
import { StorefrontHeader } from "@/components/StorefrontHeader";
import { Footer } from "@/components/Footer";
import { ProductCard } from "@/components/ProductCard";
import {
  ArrowRight, Sparkles, Truck, ShieldCheck, BadgePercent, ShoppingBag, Tags, Zap,
} from "lucide-react";

const CATEGORY_GRADIENTS = [
  "from-sky-500 to-indigo-600",
  "from-emerald-500 to-teal-600",
  "from-rose-500 to-orange-500",
  "from-violet-500 to-purple-600",
  "from-amber-500 to-yellow-500",
  "from-cyan-500 to-sky-600",
];

function SectionHead({ icon: Icon, title, href }: { icon: any; title: string; href: string }) {
  return (
    <div className="flex items-center justify-between">
      <h2 className="flex items-center gap-2 text-xl font-bold text-slate-900 dark:text-white">
        <Icon size={20} className="text-sky-600 dark:text-sky-400" /> {title}
      </h2>
      <Link
        href={href}
        className="flex items-center gap-1 text-sm font-semibold text-sky-600 dark:text-sky-400 hover:gap-2 transition-all"
      >
        View all <ArrowRight size={15} />
      </Link>
    </div>
  );
}

function Poster({ title, subtitle, accent }: { title: string; subtitle: string; accent: string }) {
  return (
    <div
      className={`rounded-2xl p-5 aspect-[4/3] flex flex-col justify-end text-white bg-gradient-to-br ${accent} shadow-md`}
    >
      <p className="text-xs font-bold uppercase tracking-widest">{title}</p>
      <p className="mt-1 font-semibold text-sm text-white/90">{subtitle}</p>
    </div>
  );
}

export default function HomePage() {
  const [featured, setFeatured] = useState<any[]>([]);
  const [newest, setNewest] = useState<any[]>([]);
  const [categories, setCategories] = useState<any[]>([]);
  const [loading, setLoading] = useState(true);
  const [banner, setBanner] = useState<any>(null);
  const [posters, setPosters] = useState<any[]>([]);

  useEffect(() => {
    settingsApi
      .public()
      .then((r) => {
        const d = r.data || {};
        setBanner(d.banner || null);
        setPosters((d.posters || []).filter((p: any) => p.visible).slice(0, 4));
      })
      .catch(() => {});
    productApi
      .list({ limit: 8, featured: true })
      .then((r) => setFeatured(Array.isArray(r.data) ? r.data : []))
      .catch(() => {})
      .finally(() => setLoading(false));
    productApi.list({ limit: 8 }).then((r) => setNewest(Array.isArray(r.data) ? r.data : [])).catch(() => {});
    productApi.categories().then((r) => setCategories(Array.isArray(r.data) ? r.data : [])).catch(() => {});
  }, []);

  return (
    <div className="min-h-screen bg-slate-50 dark:bg-slate-950 flex flex-col">
      <StorefrontHeader />

      <section className="relative overflow-hidden bg-gradient-to-br from-sky-700 via-sky-600 to-indigo-700 text-white">
        <div
          className="absolute inset-0 opacity-15"
          style={{
            backgroundImage:
              "radial-gradient(circle at 20% 30%, rgba(255,255,255,.25), transparent 40%), radial-gradient(circle at 80% 70%, rgba(255,255,255,.18), transparent 40%)",
          }}
          aria-hidden
        />
        <div className="relative max-w-7xl mx-auto px-4 py-16 md:py-24 grid md:grid-cols-2 gap-10 items-center">
          <div className="fade-up">
            <span className="inline-flex items-center gap-1.5 px-3 py-1 rounded-full bg-white/15 text-xs font-semibold">
              <Sparkles size={13} /> {banner?.badge || "AI-powered pricing & stock forecasting"}
            </span>
            <h1 className="mt-5 text-4xl md:text-5xl font-extrabold leading-tight">
              {banner?.title || "Shop smarter across Bangladesh"}
            </h1>
            <p className="mt-4 text-sky-100 text-lg">
              {banner?.subtitle ||
                "Products from trusted sellers. Cash on Delivery, bKash & Nagad — delivered fast to every division."}
            </p>
            <div className="mt-8 flex flex-wrap gap-3">
              <Link href="/products" className="btn bg-white text-sky-700 hover:bg-sky-50 font-bold !px-6 !py-3">
                <ShoppingBag size={18} /> Shop Now
              </Link>
              <Link
                href="/admin/login"
                className="btn border border-white/40 text-white hover:bg-white/10 !px-6 !py-3"
              >
                Open ERP Dashboard
              </Link>
            </div>
          </div>
          <div className="hidden md:grid grid-cols-2 gap-4 fade-up">
            {posters.length > 0
              ? posters.map((p, i) => (
                  <Poster
                    key={i}
                    title={p.title}
                    subtitle={p.subtitle}
                    accent={p.accent || CATEGORY_GRADIENTS[i % CATEGORY_GRADIENTS.length]}
                  />
                ))
              : [
                  { title: "Big Sale", subtitle: "Up to 50% off electronics", accent: "from-rose-500 to-orange-400" },
                  { title: "Best Price", subtitle: "Groceries at wholesale rates", accent: "from-emerald-500 to-teal-400" },
                  { title: "Free Delivery", subtitle: "On orders above ৳1,000", accent: "from-sky-500 to-cyan-400" },
                  { title: "New Arrivals", subtitle: "Fresh collection every week", accent: "from-indigo-500 to-violet-400" },
                ].map((p, i) => (
                  <Poster key={i} title={p.title} subtitle={p.subtitle} accent={p.accent} />
                ))}
          </div>
        </div>
      </section>

      <section className="border-b border-slate-200 dark:border-slate-800 bg-white dark:bg-slate-900">
        <div className="max-w-7xl mx-auto px-4 py-4 grid sm:grid-cols-3 gap-3 text-sm">
          {[
            { icon: Truck, t: "Nationwide delivery", s: "All 8 divisions" },
            { icon: ShieldCheck, t: "100% secure", s: "COD, bKash, Nagad & more" },
            { icon: BadgePercent, t: "Smart deals", s: "AI-driven discounts" },
          ].map((x) => (
            <div key={x.t} className="flex items-center gap-3 text-slate-700 dark:text-slate-200">
              <x.icon size={22} className="text-sky-600 shrink-0" />
              <span>
                <span className="block font-semibold">{x.t}</span>
                <span className="text-xs text-slate-500 dark:text-slate-400">{x.s}</span>
              </span>
            </div>
          ))}
        </div>
      </section>

      <section className="max-w-7xl mx-auto px-4 py-10 w-full">
        <SectionHead icon={Tags} title="Shop by category" href="/products" />
        <div className="mt-5 grid grid-cols-2 md:grid-cols-3 lg:grid-cols-6 gap-4">
          {categories.map((c, i) => (
            <Link
              key={c.id}
              href={`/products?category_id=${c.id}`}
              className={`rounded-2xl p-5 text-white font-bold shadow-sm hover:shadow-md hover:-translate-y-0.5 transition-all aspect-[4/3] flex flex-col justify-end bg-gradient-to-br ${
                CATEGORY_GRADIENTS[i % CATEGORY_GRADIENTS.length]
              }`}
            >
              <span className="text-lg leading-tight drop-shadow">{c.name}</span>
              <span className="mt-1 text-xs opacity-90 flex items-center gap-1">
                Explore <ArrowRight size={12} />
              </span>
            </Link>
          ))}
        </div>
      </section>

      <section className="max-w-7xl mx-auto px-4 pb-10 w-full">
        <SectionHead icon={Sparkles} title="Featured products" href="/products" />
        {loading ? (
          <div className="mt-5 grid grid-cols-2 md:grid-cols-4 gap-4">
            {[...Array(4)].map((_, i) => (
              <div key={i} className="h-80 rounded-2xl bg-slate-200 dark:bg-slate-800 animate-pulse" />
            ))}
          </div>
        ) : featured.length ? (
          <div className="mt-5 grid grid-cols-2 md:grid-cols-4 gap-4">
            {featured.map((p) => (
              <ProductCard key={p.id} p={p} />
            ))}
          </div>
        ) : (
          <p className="mt-6 text-slate-500 dark:text-slate-400 text-sm">Featured products will appear here soon.</p>
        )}
      </section>

      <section className="max-w-7xl mx-auto px-4 pb-10 w-full">
        <SectionHead icon={Zap} title="Just arrived" href="/products" />
        <div className="mt-5 grid grid-cols-2 md:grid-cols-4 gap-4">
          {newest.slice(0, 8).map((p) => (
            <ProductCard key={p.id} p={p} />
          ))}
        </div>
      </section>

      <Footer />
    </div>
  );
}