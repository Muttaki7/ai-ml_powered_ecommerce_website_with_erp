"use client";

import { useState } from "react";
import Link from "next/link";
import { useRouter } from "next/navigation";
import { authApi, getApiError } from "@/lib/api";
import toast from "react-hot-toast";
import { Mail, Lock, LogIn, Store } from "lucide-react";

export default function CustomerLoginPage() {
  const router = useRouter();
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [loading, setLoading] = useState(false);

  async function handleSubmit(e: React.FormEvent) {
    e.preventDefault();
    setLoading(true);
    try {
      const { data } = await authApi.customerLogin({ email, password });
      localStorage.setItem("access_token", data.access_token);
      localStorage.setItem("refresh_token", data.refresh_token);
      localStorage.setItem("token_type", "customer");
      localStorage.setItem("customer_user", JSON.stringify(data.user));
      toast.success(`Welcome back, ${data.user.full_name}`);
      router.push("/cart");
    } catch (err: any) {
      toast.error(getApiError(err, "Login failed"));
    } finally {
      setLoading(false);
    }
  }

  return (
    <div className="min-h-screen flex items-center justify-center bg-slate-50 dark:bg-slate-950 px-4 py-10">
      <div className="w-full max-w-md card p-8">
        <div className="w-12 h-12 mx-auto rounded-xl bg-sky-600 text-white flex items-center justify-center">
          <Store size={22} />
        </div>
        <h1 className="text-2xl font-bold text-center text-slate-900 dark:text-white mt-4">Customer Login</h1>
        <p className="text-center text-slate-500 dark:text-slate-400 text-sm mt-1">
          Sign in to place orders &amp; track deliveries
        </p>

        <form onSubmit={handleSubmit} className="mt-8 space-y-4">
          <div>
            <label className="block text-sm font-medium mb-1 text-slate-700 dark:text-slate-300">Email</label>
            <div className="relative">
              <Mail size={16} className="absolute left-3 top-1/2 -translate-y-1/2 text-slate-400" />
              <input
                type="email"
                value={email}
                onChange={(e) => setEmail(e.target.value)}
                className="input w-full !pl-10"
                placeholder="you@example.com"
                required
              />
            </div>
          </div>
          <div>
            <label className="block text-sm font-medium mb-1 text-slate-700 dark:text-slate-300">Password</label>
            <div className="relative">
              <Lock size={16} className="absolute left-3 top-1/2 -translate-y-1/2 text-slate-400" />
              <input
                type="password"
                value={password}
                onChange={(e) => setPassword(e.target.value)}
                className="input w-full !pl-10"
                placeholder="Your password"
                required
              />
            </div>
          </div>
          <button
            type="submit"
            disabled={loading}
            className="btn-primary w-full !py-3"
          >
            <LogIn size={17} /> {loading ? "Signing in..." : "Sign In"}
          </button>
        </form>

        <div className="mt-4 text-center text-sm">
          <Link href="/register" className="text-sky-600 dark:text-sky-400 hover:underline">
            New customer? Create an account
          </Link>
        </div>
        <Link href="/" className="block mt-4 text-center text-xs text-slate-400 hover:underline">
          Back to shop
        </Link>
      </div>
    </div>
  );
}