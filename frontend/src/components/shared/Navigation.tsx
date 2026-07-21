"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";
import { motion, AnimatePresence } from "framer-motion";
import { Menu, X, MessageSquare, Search, Compass, Sparkles } from "lucide-react";
import { useState } from "react";
import { cn } from "@/lib/utils";

const navLinks = [
  { href: "/", label: "Home", icon: Sparkles },
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
        "mx-auto max-w-7xl px-4 sm:px-6 transition-all duration-300",
        isHome ? "py-3" : "py-0"
      )}>
        <div className={cn(
          "flex h-16 items-center justify-between rounded-2xl px-4 transition-all duration-300",
          isHome
            ? "bg-white/35 backdrop-blur-xl border border-border/60 shadow-sm"
            : "bg-white/70 backdrop-blur-xl border border-border shadow-sm"
        )}>
          {/* Logo */}
          <Link href="/" className="flex items-center gap-2 group">
            <div className="h-8 w-8 rounded-lg bg-gradient-to-br from-gold-500 to-gold-700 flex items-center justify-center group-hover:shadow-lg group-hover:shadow-gold-500/20 transition-all duration-300">
              <span className="text-white text-sm font-bold">🕉</span>
            </div>
            <span className="font-serif text-xl font-semibold text-text-primary hidden sm:block">
              AstroSage
            </span>
          </Link>

          {/* Desktop Nav */}
          <div className="hidden md:flex items-center gap-1">
            {navLinks.map((link) => (
              <Link
                key={link.href}
                href={link.href}
                className={cn(
                  "flex items-center gap-2 px-4 py-2 rounded-lg text-sm font-medium transition-all duration-200",
                  pathname === link.href
                    ? "bg-gold-500/10 text-gold-700"
                    : "text-text-secondary hover:text-text-primary hover:bg-black/[0.04]"
                )}
              >
                <link.icon className="h-4 w-4" />
                {link.label}
              </Link>
            ))}
          </div>

          {/* CTA */}
          <Link
            href="/chat"
            className="hidden md:inline-flex items-center gap-2 px-5 py-2 rounded-lg bg-gradient-to-br from-gold-500 to-gold-600 text-white text-sm font-semibold hover:from-gold-400 hover:to-gold-500 transition-all duration-300 shadow-lg shadow-gold-500/10 hover:shadow-gold-500/20"
          >
            <MessageSquare className="h-4 w-4" />
            Start Asking
          </Link>

          {/* Mobile menu button */}
          <button
            onClick={() => setMobileOpen(!mobileOpen)}
            className="md:hidden p-2 rounded-lg text-text-secondary hover:text-text-primary hover:bg-black/[0.04] transition-all"
            aria-label="Toggle menu"
          >
            {mobileOpen ? <X className="h-5 w-5" /> : <Menu className="h-5 w-5" />}
          </button>
        </div>
      </div>

      {/* Mobile menu */}
      <AnimatePresence>
        {mobileOpen && (
          <motion.div
            initial={{ opacity: 0, y: -10 }}
            animate={{ opacity: 1, y: 0 }}
            exit={{ opacity: 0, y: -10 }}
            className="md:hidden bg-white/90 backdrop-blur-xl mx-4 mt-2 rounded-xl overflow-hidden border border-border shadow-lg"
          >
            <div className="p-2 space-y-1">
              {navLinks.map((link) => (
                <Link
                  key={link.href}
                  href={link.href}
                  onClick={() => setMobileOpen(false)}
                  className={cn(
                    "flex items-center gap-3 px-4 py-3 rounded-lg text-sm font-medium transition-all",
                    pathname === link.href
                      ? "bg-gold-500/10 text-gold-700"
                      : "text-text-secondary hover:text-text-primary hover:bg-black/[0.04]"
                  )}
                >
                  <link.icon className="h-4 w-4" />
                  {link.label}
                </Link>
              ))}
              <hr className="border-border my-2" />
              <Link
                href="/chat"
                onClick={() => setMobileOpen(false)}
                className="flex items-center justify-center gap-2 px-4 py-3 rounded-lg bg-gradient-to-br from-gold-500 to-gold-600 text-white font-semibold"
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
