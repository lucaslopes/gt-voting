/** Sticky illustration + scrolling text steps. The stage re-renders for the active step. */
import { useEffect, useRef, useState, type ReactNode } from "react";

export function Scrolly({
  steps,
  stage,
  label,
}: {
  steps: ReactNode[];
  stage: (active: number, inView: boolean) => ReactNode;
  label: string;
}) {
  const [active, setActive] = useState(0);
  const [inView, setInView] = useState(false);
  const refs = useRef<(HTMLDivElement | null)[]>([]);
  const root = useRef<HTMLDivElement | null>(null);

  useEffect(() => {
    if (!root.current) return;
    const io = new IntersectionObserver(([e]) => setInView(e.isIntersecting), { rootMargin: "0px" });
    io.observe(root.current);
    return () => io.disconnect();
  }, []);

  useEffect(() => {
    let io: IntersectionObserver | null = null;
    const build = () => {
      io?.disconnect();
      const narrow = window.matchMedia("(max-width: 900px)").matches;
      io = new IntersectionObserver(
        (entries) => {
          for (const e of entries) {
            if (e.isIntersecting) setActive(Number((e.target as HTMLElement).dataset.index));
          }
        },
        { rootMargin: narrow ? "-78% 0px -20% 0px" : "-48% 0px -48% 0px" },
      );
      refs.current.forEach((el) => el && io!.observe(el));
    };
    build();
    const mq = window.matchMedia("(max-width: 900px)");
    mq.addEventListener("change", build);
    return () => {
      io?.disconnect();
      mq.removeEventListener("change", build);
    };
  }, [steps.length]);

  return (
    <div className="scrolly" ref={root}>
      <div className="scrolly-stage" aria-label={label} role="img">
        <div className="stage-inner">{stage(active, inView)}</div>
      </div>
      <div className="scrolly-steps">
        {steps.map((s, i) => (
          <div
            key={i}
            className={`step${i === active ? " is-active" : ""}`}
            data-index={i}
            ref={(el) => {
              refs.current[i] = el;
            }}
          >
            <div className="step-card">{s}</div>
          </div>
        ))}
      </div>
    </div>
  );
}

export function Chapter({
  id,
  num,
  title,
  sub,
  children,
}: {
  id: string;
  num: string;
  title: ReactNode;
  sub?: ReactNode;
  children: ReactNode;
}) {
  return (
    <section className="chapter" id={id}>
      <header className="chapter-head">
        <span className="chapter-num">{num}</span>
        <h2>{title}</h2>
        {sub && <p className="sub">{sub}</p>}
      </header>
      {children}
    </section>
  );
}
