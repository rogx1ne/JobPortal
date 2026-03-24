"use client";

import Link from "next/link";
import { usePathname, useRouter } from "next/navigation";
import { useEffect, useMemo, useState } from "react";

import { clearSession, isLoggedIn } from "@/lib/auth";
import { cn } from "@/lib/utils";
import { Button } from "@/components/ui/button";

const links = [
  { href: "/", label: "Home" },
  { href: "/jobs", label: "Jobs" },
  { href: "/dashboard", label: "Dashboard" },
];

export function SiteHeader() {
  const pathname = usePathname();
  const router = useRouter();
  const [authed, setAuthed] = useState(false);

  useEffect(() => {
    setAuthed(isLoggedIn());
  }, [pathname]);

  const heading = useMemo(() => {
    if (pathname.startsWith("/jobs")) return "Discover";
    if (pathname.startsWith("/dashboard")) return "Control Center";
    if (pathname.startsWith("/auth")) return "Authentication";
    return "JobPortal";
  }, [pathname]);

  const logout = () => {
    clearSession();
    setAuthed(false);
    router.push("/auth/login");
  };

  return (
    <header className="sticky top-0 z-40 border-b border-border/70 bg-bg/90 backdrop-blur-xl">
      <div className="mx-auto flex w-full max-w-7xl items-center justify-between gap-4 px-4 py-4 sm:px-6">
        <div>
          <p className="font-mono text-xs uppercase tracking-[0.2em] text-muted">AI Job Aggregator</p>
          <p className="text-lg font-semibold text-ink">{heading}</p>
        </div>

        <nav className="flex items-center gap-1 rounded-2xl border border-border bg-panel/80 p-1">
          {links.map((link) => {
            const active = pathname === link.href || pathname.startsWith(`${link.href}/`);
            return (
              <Link
                key={link.href}
                href={link.href}
                className={cn(
                  "rounded-xl px-3 py-2 text-sm font-medium transition-colors",
                  active ? "bg-accent text-white" : "text-ink hover:bg-[#ebf3e9]",
                )}
              >
                {link.label}
              </Link>
            );
          })}
        </nav>

        <div className="flex items-center gap-2">
          {!authed ? (
            <>
              <Button variant="subtle" size="sm" asChild>
                <Link href="/auth/register">Register</Link>
              </Button>
              <Button size="sm" asChild>
                <Link href="/auth/login">Login</Link>
              </Button>
            </>
          ) : (
            <Button variant="subtle" size="sm" onClick={logout}>
              Logout
            </Button>
          )}
        </div>
      </div>
    </header>
  );
}
