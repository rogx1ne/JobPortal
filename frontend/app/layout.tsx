import type { Metadata } from "next";
import { IBM_Plex_Mono, Space_Grotesk } from "next/font/google";

import { SiteHeader } from "@/components/site-header";

import "./globals.css";

const heading = Space_Grotesk({
  subsets: ["latin"],
  variable: "--font-heading",
});

const mono = IBM_Plex_Mono({
  subsets: ["latin"],
  variable: "--font-mono",
  weight: ["400", "500"],
});

export const metadata: Metadata = {
  title: "JobPortal",
  description: "AI-powered job discovery platform",
};

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <html lang="en">
      <body className={`${heading.variable} ${mono.variable} font-[family-name:var(--font-heading)]`}>
        <div className="page-shell">
          <SiteHeader />
          <main className="mx-auto w-full max-w-7xl px-4 pb-16 pt-8 sm:px-6">{children}</main>
        </div>
      </body>
    </html>
  );
}
