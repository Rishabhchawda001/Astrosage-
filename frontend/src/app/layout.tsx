import type { Metadata } from "next";
import { Inter, Cormorant_Garamond } from "next/font/google";
import { Toaster } from "@/components/ui/sonner";
import "./globals.css";

const inter = Inter({
  subsets: ["latin"],
  variable: "--font-inter",
  display: "swap",
});

const cormorant = Cormorant_Garamond({
  subsets: ["latin"],
  weight: ["300", "400", "500", "600", "700"],
  variable: "--font-cormorant",
  display: "swap",
});

export const metadata: Metadata = {
  title: "AstroSage AI — Ancient Wisdom, Verified",
  description:
    "Explore thousands of years of Hindu knowledge with evidence-backed AI. Every answer is traced to canonical sources.",
  keywords: [
    "Hinduism", "scriptures", "Vedas", "Upanishads", "Bhagavad Gita",
    "knowledge graph", "AI", "ancient wisdom", "Sanatana Dharma",
  ],
  openGraph: {
    title: "AstroSage AI — Ancient Wisdom, Verified",
    description: "Every answer traced to canonical sources. Explore Hindu scriptures with AI.",
    type: "website",
    locale: "en_US",
  },
};

export default function RootLayout({
  children,
}: Readonly<{ children: React.ReactNode }>) {
  return (
    <html lang="en">
      <body className={`${inter.variable} ${cormorant.variable} font-sans antialiased`}>
        {children}
        <Toaster
          position="top-right"
          toastOptions={{
            style: {
              background: "rgba(255, 255, 255, 0.95)",
              border: "1px solid rgba(26, 22, 18, 0.06)",
              color: "#1a1612",
              backdropFilter: "blur(20px)",
              borderRadius: "14px",
              fontSize: "14px",
            },
          }}
        />
      </body>
    </html>
  );
}
