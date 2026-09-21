import Link from "next/link";
import { Store, Truck, ShieldCheck, Headset, MapPin, Mail, Phone } from "lucide-react";

const FEATURES = [
  { icon: Truck, title: "Fast Nationwide Delivery", sub: "Free over ৳1,000" },
  { icon: ShieldCheck, title: "Secure Checkout", sub: "COD · bKash · Nagad · Rocket" },
  { icon: Headset, title: "24/7 Support", sub: "Call or chat any time" },
];

export function Footer() {
  return (
    <footer className="border-t border-slate-200 dark:border-slate-800 bg-white dark:bg-slate-950 mt-auto">
      <div className="max-w-7xl mx-auto px-4 py-12 grid gap-8 md:grid-cols-4">
        <div>
          <div className="flex items-center gap-2 font-extrabold text-lg">
            <span className="w-8 h-8 rounded-lg bg-sky-600 text-white flex items-center justify-center">
              <Store size={16} />
            </span>
            BD<span className="text-sky-600">Shop</span>
          </div>
          <p className="mt-3 text-sm text-slate-500 dark:text-slate-400">
            Bangladesh&apos;s modern commerce &amp; ERP platform powered by AI demand forecasting.
          </p>
        </div>
        <div>
          <h4 className="font-semibold text-slate-900 dark:text-white">Shop</h4>
          <ul className="mt-3 space-y-2 text-sm text-slate-500 dark:text-slate-400">
            <li><Link href="/products" className="hover:text-sky-600">All Products</Link></li>
            <li><Link href="/products?q=" className="hover:text-sky-600">Featured</Link></li>
            <li><Link href="/cart" className="hover:text-sky-600">Cart</Link></li>
            <li><Link href="/orders" className="hover:text-sky-600">My Orders</Link></li>
          </ul>
        </div>
        <div>
          <h4 className="font-semibold text-slate-900 dark:text-white">Get in touch</h4>
          <ul className="mt-3 space-y-2 text-sm text-slate-500 dark:text-slate-400">
            <li className="flex items-center gap-2"><MapPin size={15} /> Dhaka, Bangladesh</li>
            <li className="flex items-center gap-2"><Mail size={15} /> support@bdshop.local</li>
            <li className="flex items-center gap-2"><Phone size={15} /> +880 1700-000000</li>
          </ul>
        </div>
        <div>
          <h4 className="font-semibold text-slate-900 dark:text-white">Featured</h4>
          <ul className="mt-3 space-y-3">
            {FEATURES.map((f) => (
              <li key={f.title} className="flex items-start gap-3 text-sm">
                <f.icon size={18} className="text-sky-600 shrink-0 mt-0.5" />
                <span>
                  <span className="block font-medium text-slate-700 dark:text-slate-200">{f.title}</span>
                  <span className="text-slate-500 dark:text-slate-400 text-xs">{f.sub}</span>
                </span>
              </li>
            ))}
          </ul>
        </div>
      </div>
      <div className="border-t border-slate-200 dark:border-slate-800 py-5 text-center text-xs text-slate-400 dark:text-slate-500">
        © {new Date().getFullYear()} BD Commerce + ERP · Built for Bangladesh
      </div>
    </footer>
  );
}