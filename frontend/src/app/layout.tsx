import type { Metadata } from "next";
import { Inter } from "next/font/google";
import "./globals.css";

const inter = Inter({
  subsets: ["latin"],
  variable: "--font-inter",
  display: "swap",
});

export const metadata: Metadata = {
  title: "Narrate-AI — Data to Story",
  description: "Upload a dataset and let IBM Granite turn it into a compelling narrative.",
  icons: { icon: "/favicon.ico" },
};

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="en" className={inter.variable}>
      <body style={{ fontFamily: "var(--font-inter), system-ui, sans-serif" }}>
        {children}
      </body>
    </html>
  );
}
