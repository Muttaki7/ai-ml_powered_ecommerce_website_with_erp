"use client";

import { useEffect, useState } from "react";
import { adminApi, getApiError } from "@/lib/api";
import { useAdminAuth } from "@/lib/useAdminAuth";
import { AdminShell } from "@/components/AdminShell";
import toast from "react-hot-toast";
import { Plus, ShieldCheck, ShieldOff } from "lucide-react";

const ROLES = [
  "main_admin",
  "admin",
  "manager",
  "sales_manager",
  "inventory_manager",
  "accountant",
  "purchase_manager",
  "customer_support",
  "warehouse_staff",
  "delivery_manager",
  "marketing_manager",
  "analyst",
  "network_admin",
];

export default function AdminAdminsPage() {
  const { user, loading } = useAdminAuth();
  const [admins, setAdmins] = useState<any[]>([]);
  const [showForm, setShowForm] = useState(false);
  const [saving, setSaving] = useState(false);
  const [removing, setRemoving] = useState<string | null>(null);
  const [form, setForm] = useState({
    full_name: "",
    email: "",
    phone: "",
    temporary_password: "",
    role: "admin",
    two_factor_required: true,
  });

  useEffect(() => {
    if (!loading) load();
  }, [loading]);

  async function load() {
    try {
      const r = await adminApi.admins();
      setAdmins(r.data || []);
    } catch {
      setAdmins([]);
    }
  }

  async function createAdmin(e: React.FormEvent) {
    e.preventDefault();
    setSaving(true);
    try {
      await adminApi.createAdmin({
        full_name: form.full_name,
        email: form.email,
        phone: form.phone || undefined,
        temporary_password: form.temporary_password,
        role: form.role,
        two_factor_required: form.two_factor_required,
      });
      toast.success("Administrator created");
      setShowForm(false);
      setForm({ ...form, full_name: "", email: "", phone: "", temporary_password: "" });
      load();
    } catch (err: any) {
      toast.error(getApiError(err, "Create failed"));
    } finally {
      setSaving(false);
    }
  }

  async function removeAdmin(id: string) {
    if (!window.confirm("Remove this administrator? They will lose access immediately.")) return;
    setRemoving(id);
    try {
      await adminApi.disableAdmin(id);
      toast.success("Administrator removed");
      load();
    } catch (err: any) {
      toast.error(getApiError(err, "Remove failed"));
    } finally {
      setRemoving(null);
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
    <AdminShell title="Administrators" user={user}>
      <div className="space-y-6">
        <button onClick={() => setShowForm((s) => !s)} className="btn-primary !py-2 text-sm inline-flex">
          {showForm ? "Close Form" : "+ New Admin"}
        </button>

        {showForm && (
          <form onSubmit={createAdmin} className="card p-5 grid md:grid-cols-2 gap-3">
            <input
              required
              placeholder="Full name"
              value={form.full_name}
              onChange={(e) => setForm({ ...form, full_name: e.target.value })}
              className="input"
            />
            <input
              required
              type="email"
              placeholder="Email"
              value={form.email}
              onChange={(e) => setForm({ ...form, email: e.target.value })}
              className="input"
            />
            <input
              placeholder="Phone"
              value={form.phone}
              onChange={(e) => setForm({ ...form, phone: e.target.value })}
              className="input"
            />
            <input
              required
              type="text"
              placeholder="Temporary password (min 8)"
              value={form.temporary_password}
              onChange={(e) => setForm({ ...form, temporary_password: e.target.value })}
              className="input"
              minLength={8}
            />
            <select
              value={form.role}
              onChange={(e) => setForm({ ...form, role: e.target.value })}
              className="input"
            >
              {ROLES.map((r) => (
                <option key={r}>{r}</option>
              ))}
            </select>
            <label className="flex items-center gap-2 text-sm text-slate-700 dark:text-slate-300">
              <input
                type="checkbox"
                checked={form.two_factor_required}
                onChange={(e) => setForm({ ...form, two_factor_required: e.target.checked })}
              />
              Require 2FA
            </label>
            <div className="md:col-span-2 flex justify-end gap-2">
              <button
                type="button"
                onClick={() => setShowForm(false)}
                className="btn-outline text-sm"
              >
                Cancel
              </button>
              <button
                type="submit"
                disabled={saving}
                className="btn-primary text-sm disabled:opacity-50"
              >
                {saving ? "Saving..." : "Create Admin"}
              </button>
            </div>
          </form>
        )}

        <div className="card overflow-x-auto">
          <table className="w-full text-sm">
            <thead>
              <tr className="text-left text-slate-500 dark:text-slate-400 border-b dark:border-slate-700">
                <th className="py-3 px-4">Admin</th>
                <th>Email</th>
                <th>Role</th>
                <th>2FA</th>
                <th>Status</th>
                {user?.is_main_admin && <th>Actions</th>}
              </tr>
            </thead>
            <tbody>
              {admins.map((a) => (
                <tr key={a.id} className="border-b dark:border-slate-700 last:border-0 hover:bg-slate-50 dark:hover:bg-slate-800/50">
                  <td className="py-3 px-4 font-medium text-slate-900 dark:text-white">
                    {a.full_name}
                    {a.is_main_admin && (
                      <span className="ml-2 inline-flex items-center gap-1 text-xs bg-slate-900 dark:bg-sky-600 text-white rounded px-1.5 py-0.5">
                        <ShieldCheck size={10} /> main
                      </span>
                    )}
                  </td>
                  <td className="text-slate-500 dark:text-slate-400">{a.email}</td>
                  <td>
                    <span className="text-xs bg-slate-100 dark:bg-slate-800 text-slate-600 dark:text-slate-300 rounded px-2 py-0.5">
                      {a.role}
                    </span>
                  </td>
                  <td className="text-slate-600 dark:text-slate-400">{a.two_factor_required ? "Required" : "Optional"}</td>
                  <td>
                    <span
                      className={`text-xs rounded px-2 py-0.5 ${
                        a.status === "active"
                          ? "bg-emerald-100 text-emerald-700"
                          : "bg-rose-100 text-rose-600"
                      }`}
                    >
                      {a.status}
                    </span>
                  </td>
                  {user?.is_main_admin &&
                    !a.is_main_admin &&
                    a.id !== user.id &&
                    a.status === "active" && (
                      <td>
                        <button
                          onClick={() => removeAdmin(a.id)}
                          disabled={removing === a.id}
                          className="inline-flex items-center gap-1 text-xs text-rose-600 hover:text-rose-700 hover:bg-rose-50 dark:hover:bg-rose-500/10 rounded-lg px-2 py-1 disabled:opacity-50"
                        >
                          <ShieldOff size={13} /> {removing === a.id ? "Removing..." : "Remove"}
                        </button>
                      </td>
                    )}
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>
    </AdminShell>
  );
}