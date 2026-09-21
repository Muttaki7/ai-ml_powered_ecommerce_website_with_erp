"use client";

import { useEffect, useState, useCallback, Suspense } from "react";
import Link from "next/link";
import { useRouter, useSearchParams } from "next/navigation";
import { productApi } from "@/lib/api";
import { StorefrontHeader } from "@/components/StorefrontHeader";
import { Footer } from "@/components/Footer";
import { ProductCard } from "@/components/ProductCard";

function ProductsInner() {
  const router = useRouter();
  const searchParams = useSearchParams();
  const [products, setProducts] = useState<any[]>([]);
  const [categories, setCategories] = useState<any[]>([]);
  const [q, setQ] = useState(searchParams.get("q") || "");
  const [loading, setLoading] = useState(true);

  const categoryId = searchParams.get("category_id") || "";

  const load = useCallback(async () => {
    setLoading(true);
    try {
      const params: any = { limit: 48 };
      const qParam = searchParams.get("q");
      if (qParam) params.q = qParam;
      if (categoryId) params.category_id = categoryId;
      const r = await productApi.list(params);
      setProducts(Array.isArray(r.data) ? r.data : []);
    } catch {
      setProducts([]);
    } finally {
      setLoading(false);
    }
  }, [searchParams, categoryId]);

  useEffect(() => {
    productApi.categories().then((r) => setCategories(r.data || [])).catch(() => {});
  }, []);

  useEffect(() => {
    // eslint-disable-next-line react-hooks/set-state-in-effect
    load();
  }, [load]);

  function applySearch(e: React.FormEvent) {
    e.preventDefault();
    const params = new URLSearchParams();
    if (q.trim()) params.set("q", q.trim());
    if (categoryId) params.set("category_id", categoryId);
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

        <div className="mt-4 flex flex-wrap gap-2">
          <Link
            href="/products"
            className={`px-3 py-1.5 rounded-full text-xs font-medium border transition ${
              !categoryId
                ? "bg-sky-600 text-white border-sky-600"
                : "bg-white dark:bg-slate-900 text-slate-600 dark:text-slate-300 border-slate-200 dark:border-slate-700 hover:border-sky-400"
            }`}
          >
            All
          </Link>
          {categories.map((c) => (
            <Link
              key={c.id}
              href={`/products?category_id=${c.id}`}
              className={`px-3 py-1.5 rounded-full text-xs font-medium border transition ${
                categoryId === c.id
                  ? "bg-sky-600 text-white border-sky-600"
                  : "bg-white dark:bg-slate-900 text-slate-600 dark:text-slate-300 border-slate-200 dark:border-slate-700 hover:border-sky-400"
              }`}
            >
              {c.name}
            </Link>
          ))}
        </div>

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