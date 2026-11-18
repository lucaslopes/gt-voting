import { AnimatePresence, motion } from "motion/react";
import { KIDS, MIA, HIGH_LOYALTY_PARAMS, PARAMS, PARAM_ORDER, STORY_HEARTS, STORY_PARAMS } from "../cast";
import { Avatar } from "../components/Avatar";
import { Label, Pill } from "../components/Bits";
import { Board } from "../components/Board";
import { ClassView, Timeline } from "../components/ClassView";
import { CandBadge } from "../components/icons";
import { Jar } from "../components/Jar";
import { MiniCard } from "../components/RankCard";
import { Chapter, Scrolly } from "../components/Scrolly";
import { formatParam } from "../components/Slider";
import { Dest, Habit } from "../components/Text";
import { tokensFromCounts } from "../lib/tokens";
import { useSim, type Speed } from "../lib/useSim";
import type { Params } from "../model/update";

const INK = "#23213a";

const SCENARIOS: { params: Params; speed: Speed; seed: number }[] = [
  { params: STORY_PARAMS, speed: "normal", seed: 1 },
  { params: STORY_PARAMS, speed: "normal", seed: 1 },
  { params: { ...STORY_PARAMS, beta: 0 }, speed: "normal", seed: 2 },
  { params: HIGH_LOYALTY_PARAMS, speed: "turbo", seed: 21 },
];

function LoopDiagram() {
  const R = 175;
  const nodes = [
    { a: -90, label: "Jars", sub: "one per kid" },
    { a: 0, label: "Ballots", sub: "everyone pulls a card" },
    { a: 90, label: "Scoreboard", sub: "duels → shares" },
    { a: 180, label: "Decisions", sub: "points, wish list, plan, swap" },
  ];
  const pos = (a: number) => ({ x: 300 + R * Math.cos((a * Math.PI) / 180), y: 300 + R * Math.sin((a * Math.PI) / 180) });
  const jarTokens = tokensFromCounts([3, 2, 0, 15, 0, 0]);
  return (
    <g>
      <circle cx={300} cy={300} r={R} fill="none" stroke={INK} strokeWidth={3} strokeDasharray="2 10" strokeLinecap="round" opacity={0.5} />
      <motion.g
        style={{ originX: "300px", originY: "300px" }}
        animate={{ rotate: 360 }}
        transition={{ duration: 6, repeat: Infinity, ease: "linear" }}
      >
        <circle cx={300 + R} cy={300} r={9} fill="#f28a1e" stroke="#fff" strokeWidth={3} />
      </motion.g>
      {nodes.map((n, i) => {
        const p = pos(n.a);
        return (
          <g key={i}>
            <circle cx={p.x} cy={p.y} r={58} fill="#fff" stroke={INK} strokeWidth={2.5} />
            {i === 0 && <Jar tokens={jarTokens} x={p.x} y={p.y - 2} scale={0.3} />}
            {i === 1 &&
              [3, 1, 0].map((k, j) => (
                <g key={j} transform={`translate(${p.x - 22 + j * 22} ${p.y + (j === 1 ? -6 : 4)}) rotate(${(j - 1) * 12})`}>
                  <MiniCard k={k} w={24} />
                </g>
              ))}
            {i === 2 && (
              <g>
                <rect x={p.x - 34} y={p.y - 26} width={68} height={52} rx={8} fill="#2f5247" stroke="#c98b52" strokeWidth={4} />
                {[7 / 15, 3 / 15, 5 / 15].map((v, c) => (
                  <rect key={c} x={p.x - 24 + c * 18} y={p.y + 16 - v * 34} width={12} height={v * 34 + 1} rx={2} fill={["#2f8fe0", "#f28a1e", "#8b5bd8"][c]} />
                ))}
              </g>
            )}
            {i === 3 && <Avatar look={KIDS[MIA].look} x={p.x} y={p.y + 2} size={70} mood="think" />}
            <Label x={p.x} y={p.y + (i === 0 ? -88 : 84)} size={19}>
              {n.label}
            </Label>
            <Label x={p.x} y={p.y + (i === 0 ? -68 : 104)} size={14} weight={500} color="#7d7a91">
              {n.sub}
            </Label>
          </g>
        );
      })}
      <Label x={300} y={296} size={22}>
        one round
      </Label>
      <Label x={300} y={322} size={16} weight={500} color="#7d7a91">
        …and again, and again
      </Label>
    </g>
  );
}

function SimPanel({ step, running }: { step: number; running: boolean }) {
  const sc = SCENARIOS[step];
  const { sim } = useSim({ hearts: STORY_HEARTS, network: "everyone", seed: sc.seed, params: sc.params, running, speed: sc.speed });
  const p = sim.last?.p ?? [1, 0, 0];
  return (
    <g>
      <Board p={p} x={14} y={10} w={250} h={210} />
      <g transform="translate(290 24)">
        <Label x={0} y={18} size={24} anchor="start">
          {`Round ${sim.t}`}
        </Label>
        {PARAM_ORDER.map((k, i) => (
          <Pill
            key={k}
            x={i * 98}
            y={56}
            text={`${PARAMS[k].greek} ${formatParam(k, sc.params[k])}`}
            fill={PARAMS[k].soft}
            color={INK}
            size={14}
            anchor="start"
          />
        ))}
        <Label x={0} y={104} size={15} anchor="start" weight={500} color="#4a4862">
          rounds won so far:
        </Label>
        {[0, 1, 2].map((c) => (
          <g key={c} transform={`translate(${c * 98} 140)`}>
            <CandBadge c={c} x={16} y={0} r={16} />
            <text x={40} y={7} fontSize={20} fontWeight={600} fill={INK}>
              {sim.stats.wins[c].toLocaleString()}
            </text>
          </g>
        ))}
        <Label x={0} y={190} size={14} anchor="start" weight={500} color="#7d7a91">
          {`circles (shared win): ${sim.stats.cycles.toLocaleString()}`}
        </Label>
      </g>
      <ClassView sim={sim} x={10} y={232} cellW={116} cellH={104} highlight={MIA} />
      <Timeline sim={sim} x={20} y={560} w={560} h={18} />
      <Label x={20} y={597} size={14} anchor="start" weight={500} color="#7d7a91">
        last 120 rounds of the scoreboard · dot = Castle won
      </Label>
    </g>
  );
}

function Stage({ step, inView }: { step: number; inView: boolean }) {
  return (
    <svg viewBox="0 0 600 600">
      <AnimatePresence mode="wait">
        <motion.g key={step === 0 ? "loop" : `sim${step}`} initial={{ opacity: 0 }} animate={{ opacity: 1 }} exit={{ opacity: 0 }}>
          {step === 0 ? <LoopDiagram /> : <SimPanel step={step} running={inView} />}
        </motion.g>
      </AnimatePresence>
    </svg>
  );
}

export function Ch9Everyone() {
  const steps = [
    <>
      <h3>Everyone does it, at the same time</h3>
      <p>
        All 15 kids make Mia's decision at once. Their new jars give new ballots. The new ballots give a new board.
        The new board changes the next decisions. Round after round, it's a <b>loop</b>.
      </p>
    </>,
    <>
      <h3>When the board shouts, people listen</h3>
      <p>
        Here's the class with the dials we started with (<Habit k="alpha" /> 50%, <Habit k="eta" /> 50%,{" "}
        <Habit k="beta" /> 10). Watch the bars under the Beach-lovers fill with blue: they put <Dest c={0} /> on top
        more and more.
      </p>
      <p>
        That makes Aquarium win its duels by even more. It's a <b>bandwagon</b>: the board says Aquarium, so more
        ballots say Aquarium, so Aquarium wins by more.
      </p>
      <p className="small muted">
        It isn't forever: over thousands of rounds, a lucky streak can now and then tip the bandwagon toward the
        Beach. Try it in the playground.
      </p>
      <p className="small muted">Outlined ballots are the ones that differ from the kid's heart.</p>
    </>,
    <>
      <h3>Nobody listens: luck takes over</h3>
      <p>
        Now set <Habit k="beta" /> to <b>0</b>. Nobody pays attention to the points (the board or their friends), so
        when kids stray from their heart they pick a card at random.
      </p>
      <p>
        The winner starts to jump around. Even the <Dest c={2} />, which <i>nobody</i> ranks first in their heart,
        wins some rounds!
      </p>
    </>,
    <>
      <h3>A very loyal class</h3>
      <p>
        Set <Habit k="alpha" /> to 98%, <Habit k="eta" /> to 20% and <Habit k="beta" /> to 10.
        Kids mostly vote their heart ranking. Watch Castle’s counter to see how occasional changes
        to ballots can affect the outcome.
      </p>
    </>,
  ];
  return (
    <Chapter id="everyone" num="Part 6" title="Now everyone does it, round after round">
      <Scrolly steps={steps} stage={(s, v) => <Stage step={s} inView={v} />} label="The whole class repeating the decision round after round" />
    </Chapter>
  );
}
