"use client";

import { useState } from "react";
import { useRouter } from "next/navigation";
import Link from "next/link";
import { motion } from "framer-motion";
import { UserPlus, Eye, EyeOff, Loader2, Check } from "lucide-react";
import { Navigation } from "@/components/shared/Navigation";
import { StarField } from "@/components/landing/StarField";
import { auth } from "@/lib/api";
import { setTokens } from "@/lib/api";
import { useAuthStore } from "@/lib/store";
import { toast } from "sonner";

export default function RegisterPage() {
  const router = useRouter();
  const { login } = useAuthStore();
  const [username, setUsername] = useState("");
  const [password, setPassword] = useState("");
  const [confirmPassword, setConfirmPassword] = useState("");
  const [showPassword, setShowPassword] = useState(false);
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState("");

  const handleRegister = async (e: React.FormEvent) => {
    e.preventDefault();
    setError("");

    if (password !== confirmPassword) {
      setError("Passwords do not match");
      return;
    }
    if (password.length < 8) {
      setError("Password must be at least 8 characters");
      return;
    }

    setIsLoading(true);
    try {
      await auth.register({ username, password });
      // Auto-login after registration
      const tokens = await auth.login(username, password);
      setTokens(tokens.access_token, tokens.refresh_token);
      login(username, tokens.access_token, tokens.refresh_token);
      toast.success("Account created successfully!");
      router.push("/chat");
    } catch (err: unknown) {
      const apiErr = err as { message?: string };
      setError(apiErr?.message || "Registration failed. Please try again.");
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <div className="relative min-h-screen flex items-center justify-center">
      <StarField />
      <Navigation />

      <motion.div
        initial={{ opacity: 0, y: 20 }}
        animate={{ opacity: 1, y: 0 }}
        className="relative z-10 w-full max-w-md mx-4"
      >
        <div className="glass-strong rounded-3xl p-8">
          <div className="text-center mb-8">
            <div className="w-14 h-14 rounded-2xl bg-gradient-to-br from-gold-400 to-gold-600 flex items-center justify-center mx-auto mb-4">
              <UserPlus className="h-7 w-7 text-surface" />
            </div>
            <h1 className="font-serif text-2xl font-bold text-text-primary">
              Create Account
            </h1>
            <p className="text-text-secondary text-sm mt-2">
              Start your journey with AstroSage
            </p>
          </div>

          <form onSubmit={handleRegister} className="space-y-5">
            <div>
              <label htmlFor="reg-username" className="block text-sm font-medium text-text-primary mb-1.5">
                Username
              </label>
              <input
                id="reg-username"
                type="text"
                value={username}
                onChange={(e) => setUsername(e.target.value)}
                placeholder="Choose a username"
                className="w-full bg-surface-elevated rounded-xl px-4 py-3 text-sm text-text-primary placeholder-text-tertiary border border-border focus:outline-none focus:ring-1 focus:ring-gold-500/30"
                required
                minLength={3}
              />
            </div>

            <div>
              <label htmlFor="reg-password" className="block text-sm font-medium text-text-primary mb-1.5">
                Password
              </label>
              <div className="relative">
                <input
                  id="reg-password"
                  type={showPassword ? "text" : "password"}
                  value={password}
                  onChange={(e) => setPassword(e.target.value)}
                  placeholder="At least 8 characters"
                  className="w-full bg-surface-elevated rounded-xl px-4 py-3 pr-10 text-sm text-text-primary placeholder-text-tertiary border border-border focus:outline-none focus:ring-1 focus:ring-gold-500/30"
                  required
                  minLength={8}
                />
                <button
                  type="button"
                  onClick={() => setShowPassword(!showPassword)}
                  className="absolute right-3 top-1/2 -translate-y-1/2 text-text-tertiary hover:text-text-primary"
                >
                  {showPassword ? <EyeOff className="h-4 w-4" /> : <Eye className="h-4 w-4" />}
                </button>
              </div>
              {password && (
                <div className="flex items-center gap-1 mt-1.5">
                  <Check className={`h-3 w-3 ${password.length >= 8 ? "text-green-400" : "text-text-tertiary"}`} />
                  <span className={`text-xs ${password.length >= 8 ? "text-green-400" : "text-text-tertiary"}`}>
                    {password.length}/8 characters
                  </span>
                </div>
              )}
            </div>

            <div>
              <label htmlFor="reg-confirm" className="block text-sm font-medium text-text-primary mb-1.5">
                Confirm Password
              </label>
              <input
                id="reg-confirm"
                type="password"
                value={confirmPassword}
                onChange={(e) => setConfirmPassword(e.target.value)}
                placeholder="Repeat your password"
                className="w-full bg-surface-elevated rounded-xl px-4 py-3 text-sm text-text-primary placeholder-text-tertiary border border-border focus:outline-none focus:ring-1 focus:ring-gold-500/30"
                required
              />
            </div>

            {error && (
              <div className="p-3 rounded-xl bg-red-500/10 border border-red-500/20 text-sm text-red-400">
                {error}
              </div>
            )}

            <button
              type="submit"
              disabled={isLoading || !username.trim() || !password || password !== confirmPassword}
              className="w-full py-3 rounded-xl bg-gold-500 text-surface font-semibold hover:bg-gold-400 transition-all disabled:opacity-30 flex items-center justify-center gap-2"
            >
              {isLoading ? (
                <Loader2 className="h-4 w-4 animate-spin" />
              ) : (
                <>
                  <UserPlus className="h-4 w-4" />
                  Create Account
                </>
              )}
            </button>
          </form>

          <p className="text-center text-sm text-text-tertiary mt-6">
            Already have an account?{" "}
            <Link href="/login" className="text-gold-400 hover:text-gold-300 transition-colors">
              Sign in
            </Link>
          </p>
        </div>
      </motion.div>
    </div>
  );
}
