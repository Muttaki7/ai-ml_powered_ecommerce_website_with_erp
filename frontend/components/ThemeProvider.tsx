"use client";

import { useEffect, useState } from "react";
import { Moon, Sun } from "lucide-react";

export function ThemeProvider({ children }: { children: React.ReactNode }) {
  const [theme, setTheme] = useState<"light" | "dark">("light");

  useEffect(() => {
    const stored = localStorage.getItem("theme");
    const preferDark =
      stored === "dark" || (!stored && window.matchMedia("(prefers-color-scheme: dark)").matches);
    // eslint-disable-next-line react-hooks/set-state-in-effect
    setTheme(preferDark ? "dark" : "light");
    document.documentElement.classList.toggle("dark", preferDark);
  }, []);

  function toggle() {
    const next = theme === "light" ? "dark" : "light";
    setTheme(next);
    document.documentElement.classList.toggle("dark", next === "dark");
    localStorage.setItem("theme", next);
  }

  return (
    <>
      {children}
      <button
        onClick={toggle}
        aria-label="Toggle theme"
        className="fixed bottom-5 right-5 z-50 w-11 h-11 rounded-full bg-slate-900 dark:bg-white text-white dark:text-slate-900 shadow-lg flex items-center justify-center hover:scale-105 transition-transform"
      >
        {theme === "light" ? <Moon size={18} /> : <Sun size={18} />}
      </button>
    </>
  );
}