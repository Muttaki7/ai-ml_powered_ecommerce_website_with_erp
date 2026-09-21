"use client";

import { useEffect, useState } from "react";
import { useRouter } from "next/navigation";
import { authApi } from "@/lib/api";

/**
 * Admin-only guard for the `/admin/*` area.
 *
 * It requires the session to be an *admin* session (token_type === "admin")
 * AND validates the token against the backend (`GET /auth/admin/me`), so a
 * tampered localStorage cannot be enough. Non-admin sessions (customers or
 * expired/invalid admin tokens) are signed out and redirected to /admin/login.
 */
export function useAdminAuth(redirectTo: string = "/admin/login") {
  const router = useRouter();
  const [loading, setLoading] = useState(true);
  const [user, setUser] = useState<any>(null);

  useEffect(() => {
    let cancelled = false;

    async function guard() {
      const token = localStorage.getItem("access_token");
      const type = localStorage.getItem("token_type");
      if (!token || type !== "admin") {
        localStorage.removeItem("access_token");
        localStorage.removeItem("refresh_token");
        if (!cancelled) router.replace(redirectTo);
        if (!cancelled) setLoading(false);
        return;
      }
      try {
        const r = await authApi.adminMe();
        if (cancelled) return;
        setUser(r.data);
        localStorage.setItem("admin_user", JSON.stringify(r.data));
      } catch {
        if (cancelled) return;
        localStorage.removeItem("access_token");
        localStorage.removeItem("refresh_token");
        router.replace(redirectTo);
      } finally {
        if (!cancelled) setLoading(false);
      }
    }

    guard();
    return () => {
      cancelled = true;
    };
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [router]);

  return { user, loading };
}