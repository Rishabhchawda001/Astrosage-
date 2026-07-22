"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";
import { motion, AnimatePresence } from "framer-motion";
import { Menu, X, MessageSquare, Search, Compass } from "lucide-react";
import { useState } from "react";
import { cn } from "@/lib/utils";

const navLinks = [
  { href: "/chat", label: "Chat", icon: MessageSquare },
  { href: "/search", label: "Search", icon: Search },
  { href: "/explore", label: "Explore", icon: Compass },
];

export function Navigation() {
  const [mobileOpen, setMobileOpen] = useState(false);
  const pathname = usePathname();
  const isHome = pathname === "/";

  return (
    <nav className="fixed top-0 left-0 right-0 z-50">
      <div className={cn(
        "mx-auto max-w-6xl px-5 sm:px-8 transition-all duration-500",
        isHome ? "pt-5" : "pt-0"
      )}>
        <div className={cn(
          "flex h-14 items-center justify-between rounded-2xl px-5 transition-all duration-500",
          isHome
            ? "bg-white/40 backdrop-blur-xl border border-border-subtle shadow-xs"
            : "bg-white/70 backdrop-blur-xl border border-border shadow-sm"
        )}>
          {/* Logo */}
          <Link href="/" className="flex items-center gap-2.5 group">
            <div className="h-7 w-7 rounded-lg bg-gradient-to-br from-gold-500 to-gold-600 flex items-center justify-center transition-all duration-300 group-hover:shadow-md group-hover:shadow-gold-500/15">
              <span className="text-white text-xs font-bold">🕉</span>
            </div>
            <span className="font-serif text-lg font-semibold text-text-primary hidden sm:block tracking-tight">
              AstroSage
            </span>
          </Link>

          {/* Desktop Nav */}
          <div className="hidden md:flex items-center gap-0.5">
            {navLinks.map((link) => (
              <Link
                key={link.href}
                href={link.href}
                className={cn(
                  "flex items-center gap-2 px-3.5 py-1.5 rounded-lg text-[13px] font-medium transition-all duration-200",
                  pathname === link.href
                    ? "bg-accent-subtle text-gold-700"
                    : "text-text-secondary hover:text-text-primary hover:bg-warm-100/60"
                )}
              >
                <link.icon className="h-3.5 w-3.5" />
                {link.label}
              </Link>
            ))}
          </div>

          {/* CTA */}
          <Link
            href="/chat"
            className="hidden md:inline-flex items-center gap-2 px-4 py-1.5 rounded-xl bg-gradient-to-br from-gold-500 to-gold-600 text-white text-[13px] font-semibold hover:from-gold-400 hover:to-gold-500 transition-all duration-300 shadow-sm shadow-gold-500/15 hover:shadow-md hover:shadow-gold-500/20"
          >
            <MessageSquare className="h-3.5 w-3.5" />
            Start Asking
          </Link>

          {/* Mobile menu button */}
          <button
            onClick={() => setMobileOpen(!mobileOpen)}
            className="md:hidden p-2 rounded-lg text-text-secondary hover:text-text-primary hover:bg-warm-100/60 transition-all"
            aria-label="Toggle menu"
          >
            {mobileOpen ? <X className="h-4 w-4" /> : <Menu className="h-4 w-4" />}
          </button>
        </div>
      </div>

      {/* Mobile menu */}
      <AnimatePresence>
        {mobileOpen && (
          <motion.div
            initial={{ opacity: 0, y: -8 }}
            animate={{ opacity: 1, y: 0 }}
            exit={{ opacity: 0, y: -8 }}
            transition={{ duration: 0.2, ease: "easeOut" }}
            className="md:hidden bg-white/90 backdrop-blur-xl mx-5 mt-2 rounded-2xl overflow-hidden border border-border shadow-lg"
          >
            <div className="p-2 space-y-0.5">
              {navLinks.map((link) => (
                <Link
                  key={link.href}
                  href={link.href}
                  onClick={() => setMobileOpen(false)}
                  className={cn(
                    "flex items-center gap-3 px-4 py-2.5 rounded-xl text-sm font-medium transition-all",
                    pathname === link.href
                      ? "bg-accent-subtle text-gold-700"
                      : "text-text-secondary hover:text-text-primary hover:bg-warm-100/60"
                  )}
                >
                  <link.icon className="h-4 w-4" />
                  {link.label}
                </Link>
              ))}
              <div className="h-px bg-border my-1" />
              <Link
                href="/chat"
                onClick={() => setMobileOpen(false)}
                className="flex items-center justify-center gap-2 px-4 py-2.5 rounded-xl bg-gradient-to-br from-gold-500 to-gold-600 text-white text-sm font-semibold"
              >
                <MessageSquare className="h-4 w-4" />
                Start Asking
              </Link>
            </div>
          </motion.div>
        )}
      </AnimatePresence>
    </nav>
  );
}
