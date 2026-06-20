import { useEffect, useMemo, useState } from "react";
import { Link, Navigate, useParams } from "react-router-dom";
import { ArrowLeft, ArrowUpRight } from "lucide-react";
import { getEssayBySlug } from "@/content/essays";
import { useDashboardData } from "@/context/DataContext";
import { constituencyLookupKey } from "@/lib/data";
import { routeConstituencyKey, routeStateKey } from "@/lib/format";

function formatEssayDate(isoDate: string): string {
  return new Date(`${isoDate}T12:00:00`).toLocaleDateString("en-IN", {
    year: "numeric",
    month: "long",
    day: "numeric",
  });
}

function slugifyHeading(heading: string): string {
  return heading
    .toLowerCase()
    .replace(/[^a-z0-9]+/g, "-")
    .replace(/^-|-$/g, "");
}

export function EssayDetailPage() {
  const { slug = "" } = useParams();
  const essay = getEssayBySlug(slug);
  const { data } = useDashboardData();
  const [activeSection, setActiveSection] = useState<string | null>(null);

  const tocItems = useMemo(
    () =>
      essay?.sections
        .filter((section) => section.heading)
        .map((section) => ({
          id: slugifyHeading(section.heading!),
          label: section.heading!,
        })) ?? [],
    [essay],
  );

  const validatedConstituencies = useMemo(() => {
    if (!essay?.featuredConstituencies || !data) return [];
    return essay.featuredConstituencies.filter((item) =>
      data.constituencyByKey.has(
        constituencyLookupKey(item.stateKey, item.constituencyKey),
      ),
    );
  }, [essay, data]);

  useEffect(() => {
    if (!tocItems.length) return;

    const observer = new IntersectionObserver(
      (entries) => {
        const visible = entries
          .filter((entry) => entry.isIntersecting)
          .sort((a, b) => b.intersectionRatio - a.intersectionRatio);
        if (visible[0]?.target.id) {
          setActiveSection(visible[0].target.id);
        }
      },
      { rootMargin: "-20% 0px -60% 0px", threshold: [0, 0.25, 0.5, 1] },
    );

    tocItems.forEach(({ id }) => {
      const element = document.getElementById(id);
      if (element) observer.observe(element);
    });

    return () => observer.disconnect();
  }, [tocItems]);

  if (!essay) {
    return <Navigate to="/essays" replace />;
  }

  return (
    <div className="mx-auto max-w-6xl">
      <Link
        to="/essays"
        className="inline-flex items-center gap-2 text-sm text-muted transition hover:text-primary"
      >
        <ArrowLeft className="h-4 w-4" />
        Back to The India Exception
      </Link>

      <div className="mt-6 lg:grid lg:grid-cols-[minmax(0,1fr)_220px] lg:gap-10 xl:grid-cols-[minmax(0,1fr)_240px]">
        <article className="min-w-0">
          <header className="max-w-[860px] border-b border-border pb-8">
            <p className="text-[10px] font-semibold uppercase tracking-[0.2em] text-primary">
              {essay.series}
            </p>
            <p className="mt-2 text-sm font-medium text-muted">{essay.subtitle}</p>
            <h1 className="mt-3 text-3xl font-semibold leading-tight tracking-tight text-text md:text-4xl lg:text-[2.75rem]">
              {essay.title}
            </h1>
            <p className="mt-5 text-lg leading-relaxed text-muted md:text-xl">{essay.dek}</p>
            <div className="mt-5 flex flex-wrap items-center gap-3 text-sm text-muted">
              <span>{formatEssayDate(essay.date)}</span>
              <span aria-hidden="true">·</span>
              <span>{essay.readTime}</span>
            </div>
            <div className="mt-4 flex flex-wrap gap-2">
              {essay.tags.map((tag) => (
                <span
                  key={tag}
                  className="rounded-full border border-border bg-bg/40 px-2.5 py-1 text-xs text-muted"
                >
                  {tag}
                </span>
              ))}
            </div>
          </header>

          <div className="mt-8 max-w-[820px] space-y-10">
            {essay.sections.map((section, index) => {
              const sectionId = section.heading ? slugifyHeading(section.heading) : undefined;
              return (
                <section key={section.heading ?? `section-${index}`} id={sectionId}>
                  {section.heading ? (
                    <h2 className="text-xl font-semibold tracking-tight text-text md:text-2xl">
                      {section.heading}
                    </h2>
                  ) : null}
                  <div className={section.heading ? "mt-4 space-y-4" : "space-y-4"}>
                    {section.body.map((paragraph) => (
                      <p
                        key={paragraph.slice(0, 48)}
                        className="text-base leading-[1.75] text-text/90 md:text-[1.05rem]"
                      >
                        {paragraph}
                      </p>
                    ))}
                  </div>
                </section>
              );
            })}
          </div>

          <aside className="mt-10 max-w-[820px] rounded-xl border border-warning/30 bg-warning/5 p-5">
            <h2 className="text-sm font-semibold text-text">Interpretive note</h2>
            <p className="mt-2 text-sm leading-relaxed text-muted">
              This essay is interpretive. It uses The 543&apos;s constituency-level data as a
              starting point, but correlations are not causal claims.
            </p>
          </aside>

          {validatedConstituencies.length > 0 ? (
            <section className="mt-12 max-w-[860px]">
              <h2 className="text-lg font-semibold text-text">Featured constituencies</h2>
              <p className="mt-2 text-sm text-muted">
                Explore seats referenced in this essay. Links open constituency profiles in The 543.
              </p>
              <div className="mt-5 grid gap-4 sm:grid-cols-2">
                {validatedConstituencies.map((item) => (
                  <Link
                    key={constituencyLookupKey(item.stateKey, item.constituencyKey)}
                    to={`/constituency/${routeStateKey(item.stateKey)}/${routeConstituencyKey(item.constituencyKey)}`}
                    className="group rounded-xl border border-border bg-card p-4 transition hover:border-primary/40 hover:bg-primary/5"
                  >
                    <div className="flex items-start justify-between gap-3">
                      <div>
                        <h3 className="font-medium text-text group-hover:text-primary">
                          {item.name}
                        </h3>
                        <p className="mt-1 text-xs text-muted">{item.state}</p>
                      </div>
                      <ArrowUpRight className="h-4 w-4 shrink-0 text-muted group-hover:text-primary" />
                    </div>
                    <p className="mt-3 text-sm leading-relaxed text-muted">{item.note}</p>
                  </Link>
                ))}
              </div>
            </section>
          ) : null}
        </article>

        {tocItems.length > 0 ? (
          <aside className="hidden lg:block">
            <nav className="sticky top-6 rounded-xl border border-border bg-card/80 p-4 backdrop-blur-sm">
              <p className="text-[10px] font-semibold uppercase tracking-wider text-muted">
                On this page
              </p>
              <ul className="mt-3 space-y-2">
                {tocItems.map((item) => (
                  <li key={item.id}>
                    <a
                      href={`#${item.id}`}
                      className={[
                        "block text-sm leading-snug transition",
                        activeSection === item.id
                          ? "font-medium text-primary"
                          : "text-muted hover:text-text",
                      ].join(" ")}
                    >
                      {item.label}
                    </a>
                  </li>
                ))}
              </ul>
            </nav>
          </aside>
        ) : null}
      </div>
    </div>
  );
}
