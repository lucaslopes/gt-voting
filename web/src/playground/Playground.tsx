/** The complete tool: every piece from the story, with every dial in your hands. */
import { useEffect, useMemo, useRef, useState } from "react";
import { DEST, MIA, HIGH_LOYALTY_PARAMS, PARAMS, PARAM_ORDER, STORY_PARAMS, kidFor, type ParamKey } from "../cast";
import { Board } from "../components/Board";
import { ClassView, Timeline } from "../components/ClassView";
import { DestIcon, ParamIcon } from "../components/icons";
import { Slider } from "../components/Slider";
import { Rank } from "../components/Text";
import { SPEEDS, useSim, type Speed } from "../lib/useSim";
import { storyClass, randomClass, rockPaperScissorsClass, type Network } from "../model/simulation";
import type { Params } from "../model/update";
import { DecisionPanel } from "./DecisionPanel";

interface Preset {
  name: string;
  blurb: string;
  params: Params;
}

const PRESETS: Preset[] = [
  { name: "Story dials", blurb: "The settings used while telling Mia's story.", params: STORY_PARAMS },
  { name: "High loyalty", blurb: "A very loyal class with slow updates.", params: HIGH_LOYALTY_PARAMS },
  { name: "Nobody listens", blurb: "Receptivity 0: the board is ignored, strays are random.", params: { alpha: 0.5, eta: 0.5, beta: 0 } },
  { name: "Trend-chasers", blurb: "Little loyalty, quick to follow the crowd.", params: { alpha: 0.1, eta: 0.5, beta: 5 } },
  { name: "Fickle class", blurb: "Low loyalty, very volatile, very receptive.", params: { alpha: 0.2, eta: 0.9, beta: 20 } },
  { name: "Rock-solid", blurb: "Loyalty 100%: jars drift back to the heart and stay (Reset to start honest).", params: { alpha: 1, eta: 0.5, beta: 10 } },
];

type ClassKind = "story" | "rps" | "random";
const CLASSES: { kind: ClassKind; name: string; blurb: string }[] = [
  { kind: "story", name: "Mia's class", blurb: "7 love Aquarium › Castle › Beach, 7 love Beach › Castle › Aquarium, Zoe loves Aquarium › Beach › Castle." },
  { kind: "rps", name: "Rock-paper-scissors", blurb: "5 each of Aquarium › Beach › Castle, Beach › Castle › Aquarium and Castle › Aquarium › Beach." },
  { kind: "random", name: "Random hearts", blurb: "15 kids with random heart rankings (change the luck to reshuffle)." },
];

const same = (a: Params, b: Params) => PARAM_ORDER.every((k) => Math.abs(a[k] - b[k]) < 1e-9);

export function Playground() {
  const [params, setParams] = useState<Params>(STORY_PARAMS);
  const [kind, setKind] = useState<ClassKind>("story");
  const [network, setNetwork] = useState<Network>("everyone");
  const [seed, setSeed] = useState(7);
  const [running, setRunning] = useState(false);
  const [speed, setSpeed] = useState<Speed>("normal");
  const [selected, setSelected] = useState(MIA);

  const hearts = useMemo(
    () => (kind === "story" ? storyClass() : kind === "rps" ? rockPaperScissorsClass() : randomClass(15, seed)),
    [kind, seed],
  );
  const { sim, step, reset, jump, redecide } = useSim({ hearts, network, seed, params, running, speed });

  // Moving a dial re-makes the latest round's decisions, so every panel (and the class) reacts at once.
  useEffect(() => {
    redecide(params);
  }, [params, redecide]);

  const set = (k: ParamKey, v: number) => setParams((p) => ({ ...p, [k]: v }));

  // The dial bar compacts itself once it sticks to the top of the screen.
  const sentinel = useRef<HTMLDivElement | null>(null);
  const [stuck, setStuck] = useState(false);
  useEffect(() => {
    if (!sentinel.current) return;
    const io = new IntersectionObserver(([e]) => setStuck(!e.isIntersecting && e.boundingClientRect.top < 0));
    io.observe(sentinel.current);
    return () => io.disconnect();
  }, []);
  const kid = kidFor(selected);
  const avg = sim.stats.rounds ? sim.stats.pSum.map((v) => v / sim.stats.rounds) : null;
  const p = sim.last?.p ?? null;

  return (
    <section className="playground" id="playground">
      <div className="wrap">
        <header className="pg-head">
          <span className="chapter-num">Your turn</span>
          <h2>The Ballot Jar playground</h2>
          <p className="sub">
            Everything from the story, in one place. Pick a class, press play, and move the three dials. Each one is a
            human habit, and every panel updates the moment you touch it.
          </p>
        </header>

        <div ref={sentinel} aria-hidden />
        <div className={`card pg-dials${stuck ? " is-stuck" : ""}`}>
          {PARAM_ORDER.map((k) => (
            <Slider key={k} k={k} value={params[k]} onChange={(v) => set(k, v)} describe habit />
          ))}
        </div>

        <div className="card toolbar">
          <button className="btn btn-primary" onClick={() => setRunning((r) => !r)} aria-pressed={running}>
            {running ? "❚❚ Pause" : "▶ Play"}
          </button>
          <button className="btn" onClick={step} disabled={running}>
            Step 1 round
          </button>
          <button className="btn" onClick={() => jump(1000)}>
            +1,000 rounds
          </button>
          <button
            className="btn"
            onClick={() => {
              setRunning(false);
              reset();
            }}
          >
            ↺ Reset
          </button>
          <div className="seg speed" role="group" aria-label="Speed">
            {(Object.keys(SPEEDS) as Speed[]).map((sp) => (
              <button key={sp} className="btn btn-sm" aria-pressed={speed === sp} onClick={() => setSpeed(sp)}>
                {SPEEDS[sp].label}
              </button>
            ))}
          </div>
          <div className="round">
            Round <b>{sim.t.toLocaleString()}</b>
          </div>
        </div>

        <div className="pg-setup">
          <div className="card">
            <h3 className="card-title">Try a kind of class</h3>
            <div className="presets">
              {PRESETS.map((pr) => (
                <button key={pr.name} className="preset" aria-pressed={same(params, pr.params)} onClick={() => setParams(pr.params)} title={pr.blurb}>
                  <span className="preset-name">{pr.name}</span>
                  <span className="preset-vals">
                    {PARAM_ORDER.map((k) => (
                      <span key={k} style={{ color: PARAMS[k].color }}>
                        {PARAMS[k].greek} {k === "beta" ? pr.params[k].toFixed(1) : `${Math.round(pr.params[k] * 100)}%`}
                      </span>
                    ))}
                  </span>
                  <span className="preset-blurb">{pr.blurb}</span>
                </button>
              ))}
            </div>
          </div>
          <div className="card">
            <h3 className="card-title">Who's in the class</h3>
            <div className="seg" role="group" aria-label="Heart rankings">
              {CLASSES.map((c) => (
                <button key={c.kind} className="btn btn-sm" aria-pressed={kind === c.kind} onClick={() => setKind(c.kind)}>
                  {c.name}
                </button>
              ))}
            </div>
            <p className="small muted" style={{ margin: "8px 0 12px" }}>
              {CLASSES.find((c) => c.kind === kind)!.blurb}
            </p>
            <div className="small" style={{ fontWeight: 700, marginBottom: 6 }}>
              Who does each kid compare with?
            </div>
            <div className="seg" role="group" aria-label="Friends network">
              <button className="btn btn-sm" aria-pressed={network === "everyone"} onClick={() => setNetwork("everyone")}>
                Everyone
              </button>
              <button className="btn btn-sm" aria-pressed={network === "circle"} onClick={() => setNetwork("circle")}>
                4 nearest seats
              </button>
            </div>
            <div className="luck">
              <span className="small">
                Luck <span className="muted">(random seed)</span>: <b>{seed}</b>
              </span>
              <button className="btn btn-sm" onClick={() => setSeed((v) => (v * 7919 + 17) % 10007)}>
                🎲 New luck
              </button>
            </div>
          </div>
        </div>

        <div className="pg-live">
          <div className="pg-board">
            <div className="card board-card">
              <svg viewBox="0 0 300 250" aria-label="Current scoreboard">
                <Board
                  p={p ?? [0, 0, 0]}
                  w={300}
                  h={250}
                  showFair={!!p}
                  title={p ? `SCOREBOARD · ROUND ${sim.t}` : "SCOREBOARD"}
                  placeholder={p ? undefined : "press ▶ Play"}
                />
              </svg>
            </div>
            <div className="card stats">
              <h3 className="card-title">So far</h3>
              <table>
                <thead>
                  <tr>
                    <th />
                    <th>won</th>
                    <th>lost</th>
                    <th>avg share</th>
                  </tr>
                </thead>
                <tbody>
                  {DEST.map((d, c) => (
                    <tr key={c}>
                      <td>
                        <DestIcon c={c} size={20} /> {d.name}
                      </td>
                      <td>{sim.stats.wins[c].toLocaleString()}</td>
                      <td>{sim.stats.losses[c].toLocaleString()}</td>
                      <td>{avg ? `${Math.round(avg[c] * 100)}%` : "–"}</td>
                    </tr>
                  ))}
                </tbody>
              </table>
              <p className="small muted" style={{ marginTop: 8 }}>
                Won / lost = beat / lost to both rivals. Circles (shared win): {sim.stats.cycles.toLocaleString()}.
              </p>
            </div>
          </div>

          <div className="card">
            <div className="class-head">
              <h3 className="card-title">The class</h3>
              <span className="small muted">
                Click a kid to look inside their head. Left card: heart. Right card: this round's ballot (outlined if
                different). Bar: what their jar puts first.
              </span>
            </div>
            <svg viewBox="0 0 580 336" className="class-svg">
              <ClassView sim={sim} cellW={116} cellH={112} selected={selected} onSelect={setSelected} />
            </svg>
            <svg viewBox="0 0 580 44" className="timeline-svg" aria-label="Scoreboard over the last 120 rounds">
              <Timeline sim={sim} x={0} y={18} w={580} h={20} />
              <text x={0} y={9} fontSize={11.5} fill="#7d7a91">
                last 120 scoreboards (purple dot = Castle won)
              </text>
            </svg>
          </div>
        </div>

        <div className="card decision">
          <div className="decision-head">
            <h3>
              Inside {kid.name}'s head{sim.last ? `, round ${sim.t}` : ""}
            </h3>
            <span className="small muted">
              Heart: <Rank k={sim.hearts[selected]} />. While you drag a dial, this round's ballots and board stay the
              same; only the decision is re-made, exactly as in the story.
            </span>
          </div>
          <DecisionPanel sim={sim} voter={selected} params={params} network={network} />
          <div className="legend-row">
            {PARAM_ORDER.map((k) => (
              <span key={k} className="legend-item">
                <ParamIcon k={k} size={20} /> <b>{PARAMS[k].name}</b> <span className="muted">({PARAMS[k].greek})</span>:{" "}
                {PARAMS[k].tech}. <span className="muted">In the story: {PARAMS[k].model.toLowerCase()}</span>
              </span>
            ))}
          </div>
        </div>
      </div>
    </section>
  );
}
