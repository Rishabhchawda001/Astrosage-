"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";
import { motion, AnimatePresence } from "framer-motion";
import { Menu, X, Search, MessageSquare, Compass, LogIn, User } from "lucide-react";
import { useState } from "react";
import { useAuthStore } from "@/lib/store";
import { cn } from "@/lib/utils";

const navLinks = [
  { href: "/chat", label: "Chat", icon: MessageSquare },
  { href: "/search", label: "Search", icon: Search },
  { href: "/explore", label: "Explore", icon: Compass },
];

export function Navigation() {
  const [mobileOpen, setMobileOpen] = useState(false);
  const pathname = usePathname();
  const { isAuthenticated } = useAuthStore();

  return (
    <nav className="fixed top-0 left-0 right-0 z-50">
      <div className="glass-strong mx-auto max-w-7xl px-4 sm:px-6">
        <div className="flex h-16 items-center justify-between">
          {/* Logo */}
          <Link href="/" className="flex items-center gap-2 group">
            <div className="h-8 w-8 rounded-lg bg-gradient-to-br from-gold-400 to-gold-600 flex items-center justify-center">
              <span className="text-surface text-sm font-bold">🕉</span>
            </div>
            <span className="font-serif text-xl font-semibold gradient-gold hidden sm:block">
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
                  pathname.startsWith(link.href)
                    ? "bg-gold-500/10 text-gold-400"
                    : "text-text-secondary hover:text-text-primary hover:bg-white/5"
                )}
              >
                <link.icon className="h-4 w-4" />
                {link.label}
              </Link>
            ))}
          </div>

          {/* Auth */}
          <div className="hidden md:flex items-center gap-3">
            {isAuthenticated ? (
              <Link
                href="/chat"
                className="flex items-center gap-2 px-4 py-2 rounded-lg bg-gold-500/10 text-gold-400 text-sm font-medium hover:bg-gold-500/20 transition-all"
              >
                <User className="h-4 w-4" />
                Dashboard
              </Link>
            ) : (
              <>
                <Link
                  href="/login"
                  className="px-4 py-2 text-sm text-text-secondary hover:text-text-primary transition-colors"
                >
                  Log in
                </Link>
                <Link
                  href="/register"
                  className="px-4 py-2 rounded-lg bg-gold-500 text-surface text-sm font-semibold hover:bg-gold-400 transition-all"
                >
                  Get Started
                </Link>
              </>
            )}
          </div>

          {/* Mobile menu button */}
          <button
            onClick={() => setMobileOpen(!mobileOpen)}
            className="md:hidden p-2 rounded-lg text-text-secondary hover:text-text-primary hover:bg-white/5 transition-all"
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
            className="md:hidden glass-strong mx-4 mt-2 rounded-xl overflow-hidden border border-border"
          >
            <div className="p-2 space-y-1">
              {navLinks.map((link) => (
                <Link
                  key={link.href}
                  href={link.href}
                  onClick={() => setMobileOpen(false)}
                  className={cn(
                    "flex items-center gap-3 px-4 py-3 rounded-lg text-sm font-medium transition-all",
                    pathname.startsWith(link.href)
                      ? "bg-gold-500/10 text-gold-400"
                      : "text-text-secondary hover:text-text-primary hover:bg-white/5"
                  )}
                >
                  <link.icon className="h-4 w-4" />
                  {link.label}
                </Link>
              ))}
              <hr className="border-border my-2" />
              {isAuthenticated ? (
                <Link
                  href="/chat"
                  onClick={() => setMobileOpen(false)}
                  className="flex items-center gap-3 px-4 py-3 rounded-lg text-sm font-medium text-text-secondary hover:text-text-primary hover:bg-white/5"
                >
                  <User className="h-4 w-4" />
                  Dashboard
                </Link>
              ) : (
                <>
                  <Link
                    href="/login"
                    onClick={() => setMobileOpen(false)}
                    className="flex items-center gap-3 px-4 py-3 rounded-lg text-sm font-medium text-text-secondary hover:text-text-primary hover:bg-white/5"
                  >
                    <LogIn className="h-4 w-4" />
                    Log in
                  </Link>
                  <Link
                    href="/register"
                    onClick={() => setMobileOpen(false)}
                    className="flex items-center gap-3 px-4 py-3 rounded-lg bg-gold-500/10 text-gold-400 font-semibold"
                  >
                    Get Started
                  </Link>
                </>
              )}
            </div>
          </motion.div>
        )}
      </AnimatePresence>
    </nav>
  );
}
