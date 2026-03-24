import Link from "next/link";

import { Button } from "@/components/ui/button";

export default function NotFound() {
  return (
    <section className="surface mx-auto max-w-2xl p-8 text-center">
      <p className="eyebrow">404</p>
      <h1 className="mt-2 text-3xl font-semibold text-ink">Page not found</h1>
      <p className="mt-2 text-sm text-muted">The page you requested does not exist in this frontend scaffold.</p>
      <div className="mt-5 flex justify-center gap-2">
        <Button asChild>
          <Link href="/">Go Home</Link>
        </Button>
        <Button variant="subtle" asChild>
          <Link href="/jobs">Browse Jobs</Link>
        </Button>
      </div>
    </section>
  );
}
