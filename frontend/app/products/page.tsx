"use client";

import { useEffect, useState, useCallback, Suspense } from "react";
import { useRouter, useSearchParams } from "next/navigation";
import { productApi } from "@/lib/api";
import { StorefrontHeader } from "@/components/StorefrontHeader";
import { Footer } from "@/components/Footer";
import { ProductCard } from "@/components/ProductCard";

function ProductsInner() {
  const router = useRouter();
  const searchParams = useSearchParams();
  const [products, setProducts] = useState<any[]>([]);
  const [brands, setBrands] = useState<string[]>([]);
  const [q, setQ] = useState(searchParams.get("q") || "");
  const [loading, setLoading] = useState(true);

  const brandsParam = searchParams.get("brands") || "";
  const selectedBrands = brandsParam ? brandsParam.split(",").filter(Boolean) : [];

  const load = useCallback(async () => {
    setLoading(true);
    try {
      const params: any = { limit: 48 };
      const qParam = searchParams.get("q");
      if (qParam) params.q = qParam;
      const brandParam = searchParams.get("brands");
      if (brandParam) params.brand = brandParam;
      const r = await productApi.list(params);
      setProducts(Array.isArray(r.data) ? r.data : []);
    } catch {
      setProducts([]);
    } finally {
      setLoading(false);
    }
  }, [searchParams]);

  useEffect(() => {
    productApi.brands().then((r) => setBrands(Array.isArray(r.data) ? r.data : [])).catch(() => {});
  }, []);

  useEffect(() => {
    // eslint-disable-next-line react-hooks/set-state-in-effect
    setQ(searchParams.get("q") || "");
  }, [searchParams]);

  useEffect(() => {
    // eslint-disable-next-line react-hooks/set-state-in-effect
    load();
  }, [load]);

  function applySearch(e: React.FormEvent) {
    e.preventDefault();
    const params = new URLSearchParams();
    if (q.trim()) params.set("q", q.trim());
    if (brandsParam) params.set("brands", brandsParam);
    router.push(`/products?${params.toString()}`);
  }

  function toggleBrand(b: string) {
    const params = new URLSearchParams(searchParams.toString());
    const next = selectedBrands.includes(b)
      ? selectedBrands.filter((x) => x !== b)
      : [...selectedBrands, b];
    if (next.length) params.set("brands", next.join(","));
    else params.delete("brands");
    router.push(`/products?${params.toString()}`);
  }

  return (
    <div className="min-h-screen bg-slate-50 dark:bg-slate-950 flex flex-col">
      <StorefrontHeader />

      <main className="max-w-7xl mx-auto px-4 py-8 w-full flex-1">
        <h1 className="text-2xl font-bold text-slate-900 dark:text-white">Products</h1>

        <form onSubmit={applySearch} className="mt-4 flex gap-2 max-w-2xl">
          <input
            type="search"
            value={q}
            onChange={(e) => setQ(e.target.value)}
            placeholder="Search products..."
            className="input flex-1"
          />
          <button
            type="submit"
            className="px-4 py-2 rounded-xl bg-slate-900 dark:bg-sky-600 text-white text-sm font-medium hover:bg-slate-800 dark:hover:bg-sky-700 transition"
          >
            Search
          </button>
        </form>

        {brands.length > 0 && (
          <div className="mt-5">
            <p className="text-xs font-semibold text-slate-500 dark:text-slate-400 mb-2">
              Filter by brand {selectedBrands.length > 0 && `(${selectedBrands.length} selected)`}
            </p>
            <div className="flex flex-wrap gap-2">
              <button
                onClick={() => {
                  const params = new URLSearchParams(searchParams.toString());
                  params.delete("brands");
                  router.push(`/products?${params.toString()}`);
                }}
                className={`px-3 py-1.5 rounded-full text-xs font-medium border transition ${
                  selectedBrands.length === 0
                    ? "bg-sky-600 text-white border-sky-600"
                    : "bg-white dark:bg-slate-900 text-slate-600 dark:text-slate-300 border-slate-200 dark:border-slate-700 hover:border-sky-400"
                }`}
              >
                All Brands
              </button>
              {brands.map((b) => {
                const active = selectedBrands.includes(b);
                return (
                  <button
                    key={b}
                    onClick={() => toggleBrand(b)}
                    className={`px-3 py-1.5 rounded-full text-xs font-medium border transition ${
                      active
                        ? "bg-sky-600 text-white border-sky-600"
                        : "bg-white dark:bg-slate-900 text-slate-600 dark:text-slate-300 border-slate-200 dark:border-slate-700 hover:border-sky-400"
                    }`}
                  >
                    {b}
                  </button>
                );
              })}
            </div>
          </div>
        )}

        {loading ? (
          <div className="mt-6 grid grid-cols-2 md:grid-cols-4 gap-4">
            {[...Array(8)].map((_, i) => (
              <div key={i} className="h-64 rounded-2xl bg-slate-200 dark:bg-slate-800 animate-pulse" />
            ))}
          </div>
        ) : products.length === 0 ? (
          <p className="mt-10 text-slate-500 dark:text-slate-400">No products match your search.</p>
        ) : (
          <div className="mt-6 grid grid-cols-2 md:grid-cols-4 gap-4">
            {products.map((p) => (
              <ProductCard key={p.id} p={p} />
            ))}
          </div>
        )}
      </main>

      <Footer />
    </div>
  );
}

export default function ProductsPage() {
  return (
    <Suspense fallback={null}>
      <ProductsInner />
    </Suspense>
  );
}