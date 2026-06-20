import { Link } from "react-router-dom";
import { ArrowRight, BookOpen } from "lucide-react";
import { ESSAYS } from "@/content/essays";

function formatEssayDate(isoDate: string): string {
  return new Date(`${isoDate}T12:00:00`).toLocaleDateString("en-IN", {
    year: "numeric",
    month: "long",
    day: "numeric",
  });
}

function EssayCard({ slug, title, subtitle, dek, date, readTime, tags, featured }: {
  slug: string;
  title: string;
  subtitle: string;
  dek: string;
  date: string;
  readTime: string;
  tags: string[];
  featured?: boolean;
}) {
  return (
    <article
      className={[
        "group rounded-xl border bg-card transition hover:border-primary/40",
        featured ? "border-primary/30 bg-gradient-to-br from-card via-card to-primary/5 p-6 md:p-8" : "border-border p-5",
      ].join(" ")}
    >
      {featured ? (
        <p className="text-[10px] font-semibold uppercase tracking-[0.2em] text-primary">
          Featured essay
        </p>
      ) : null}
      <p className="mt-2 text-xs font-medium text-muted">{subtitle}</p>
      <h2 className="mt-2 text-xl font-semibold leading-snug text-text md:text-2xl">{title}</h2>
      <p className="mt-3 max-w-3xl text-sm leading-relaxed text-muted md:text-base">{dek}</p>
      <div className="mt-4 flex flex-wrap items-center gap-3 text-xs text-muted">
        <span>{formatEssayDate(date)}</span>
        <span aria-hidden="true">·</span>
        <span>{readTime}</span>
      </div>
      <div className="mt-4 flex flex-wrap gap-2">
        {tags.map((tag) => (
          <span
            key={tag}
            className="rounded-full border border-border bg-bg/40 px-2.5 py-1 text-[11px] text-muted"
          >
            {tag}
          </span>
        ))}
      </div>
      <Link
        to={`/essays/${slug}`}
        className="mt-6 inline-flex items-center gap-2 rounded-lg border border-primary/30 bg-primary/10 px-4 py-2.5 text-sm font-medium text-primary transition group-hover:bg-primary/15"
      >
        Read essay
        <ArrowRight className="h-4 w-4" />
      </Link>
    </article>
  );
}

export function EssaysPage() {
  const [featured, ...rest] = ESSAYS;

  return (
    <div className="mx-auto max-w-4xl space-y-8">
      <section className="rounded-xl border border-border bg-gradient-to-br from-card via-card to-primary/5 p-6 md:p-8">
        <div className="flex items-start gap-4">
          <div className="rounded-lg border border-primary/30 bg-primary/10 p-3">
            <BookOpen className="h-6 w-6 text-primary" />
          </div>
          <div>
            <p className="text-[10px] font-semibold uppercase tracking-[0.2em] text-primary">
              Essay series
            </p>
            <h1 className="mt-1 text-3xl font-semibold tracking-tight md:text-4xl">
              The India Exception
            </h1>
            <p className="mt-3 max-w-2xl text-sm leading-relaxed text-muted md:text-base">
              Essays on what makes Indian politics break familiar global patterns — interpreted
              through constituency-level data, with caution where correlation is not causation.
            </p>
          </div>
        </div>
      </section>

      {featured ? (
        <section className="space-y-4">
          <h2 className="text-sm font-medium text-muted">Latest</h2>
          <EssayCard {...featured} featured />
        </section>
      ) : null}

      {rest.length > 0 ? (
        <section className="space-y-4">
          <h2 className="text-sm font-medium text-muted">More in the series</h2>
          <div className="space-y-4">
            {rest.map((essay) => (
              <EssayCard key={essay.slug} {...essay} />
            ))}
          </div>
        </section>
      ) : (
        <section className="rounded-xl border border-dashed border-border bg-card/40 p-6 text-center">
          <h2 className="text-sm font-medium text-text">More essays coming soon</h2>
          <p className="mt-2 text-sm text-muted">
            Additional instalments in The India Exception series are in development.
          </p>
        </section>
      )}

      {rest.length === 0 ? null : (
        <section className="rounded-xl border border-dashed border-border bg-card/40 p-6 text-center">
          <h2 className="text-sm font-medium text-text">More essays coming soon</h2>
          <p className="mt-2 text-sm text-muted">
            Additional instalments in The India Exception series are in development.
          </p>
        </section>
      )}
    </div>
  );
}
