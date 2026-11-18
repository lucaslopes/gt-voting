import { AnimatePresence, motion } from "motion/react";
import { useMemo, useState } from "react";
import { DEST, KIDS, MIA, MIA_HEART, PARAMS, type ParamKey } from "../cast";
import { Avatar } from "../components/Avatar";
import { Label } from "../components/Bits";
import { DistBars } from "../components/DistBars";
import { CandBadge, ParamBadge } from "../components/icons";
import { Jar } from "../components/Jar";
import { MiniCard, RankCard } from "../components/RankCard";
import { Chapter, Scrolly } from "../components/Scrolly";
import { Dest, Grownups, Habit, Rank } from "../components/Text";
import { pctSoft } from "../lib/format";
import { roundCounts, tokensFromCounts } from "../lib/tokens";
import { drawIndex } from "../model/rng";
import { PERMS } from "../model/rankings";
import { R1_P, R1_REPORTS, miaDecision, useStory } from "./world";

const INK = "#23213a";

function aquariumTop(xAfter: readonly number[]) {
  return xAfter.reduce((s, v, k) => s + (PERMS[k][0] === 0 ? v : 0), 0);
}

function Station({
  y,
  n,
  title,
  sub,
  icon,
  children,
}: {
  y: number;
  n: number;
  title: string;
  sub: string;
  icon: React.ReactNode;
  children?: React.ReactNode;
}) {
  return (
    <motion.g initial={{ opacity: 0, x: -16 }} animate={{ opacity: 1, x: 0 }} transition={{ delay: 0.12 * n }}>
      <g transform={`translate(0 ${y})`}>
        {n > 0 && <line x1={44} x2={44} y1={-50} y2={-26} stroke={INK} strokeWidth={2.5} strokeDasharray="4 5" opacity={0.4} />}
        <circle cx={44} cy={0} r={26} fill="#fff" stroke={INK} strokeWidth={2} />
        <g transform="translate(44 0)">{icon}</g>
        <Label x={86} y={-3} size={18} anchor="start">
          {title}
        </Label>
        <Label x={86} y={18} size={14} anchor="start" weight={500} color="#7d7a91">
          {sub}
        </Label>
        <g transform="translate(400 -26)">{children}</g>
      </g>
    </motion.g>
  );
}

function Recap() {
  const { params } = useStory();
  const d = miaDecision(params);
  const pIcon = (k: ParamKey) => <ParamBadge k={k} r={20} />;
  return (
    <g transform="translate(10 52)">
      <Station y={0} n={0} title="Read the board" sub="which places are HOT or NOT" icon={<CandBadge c={0} r={18} />}>
        {R1_P.map((p, c) => (
          <rect key={c} x={c * 38} y={52 - Math.max(3, p * 48)} width={28} height={Math.max(3, p * 48)} rx={4} fill={DEST[c].color} />
        ))}
      </Station>
      <Station y={76} n={1} title="Look at friends' ballots" sub="what each friend wrote" icon={<Avatar look={KIDS[8].look} size={40} body={false} />}>
        {[0, 1, 2, 8, 9, 14].map((j, i) => (
          <g key={j} transform={`translate(${12 + i * 26} 26)`}>
            <MiniCard k={R1_REPORTS[j]} w={18} />
          </g>
        ))}
      </Station>
      <Station y={152} n={2} title="Score every card" sub="lead, cubed, averaged" icon={<text dy="0.35em" textAnchor="middle" fontSize={20} fontWeight={700}>x³</text>}>
        <DistBars values={d.scores} mode="score" w={160} h={54} showCards={false} showLabels={false} />
      </Station>
      <Station y={228} n={3} title="Receptivity β → wish list" sub={`β = ${params.beta.toFixed(1)}`} icon={pIcon("beta")}>
        <DistBars values={d.q} w={160} h={54} showCards={false} showLabels={false} color={PARAMS.beta.color} />
      </Station>
      <Station y={304} n={4} title="Loyalty α → plan" sub={`α = ${Math.round(params.alpha * 100)}% heart`} icon={pIcon("alpha")}>
        <DistBars values={d.plan} w={160} h={54} showCards={false} showLabels={false} color={PARAMS.alpha.color} />
      </Station>
      <Station y={380} n={5} title="Volatility η → new jar" sub={`η = ${Math.round(params.eta * 100)}% swapped`} icon={pIcon("eta")}>
        <DistBars values={d.xAfter} w={160} h={54} showCards={false} showLabels={false} color={PARAMS.eta.color} />
      </Station>
      <Station y={456} n={6} title="Pull a card" sub="that's the new ballot!" icon={<MiniCard k={MIA_HEART} w={20} />}>
        <g transform="translate(80 28)">
          <Label x={0} y={6} size={16} weight={600}>
            {`${pctSoft(d.xAfter[MIA_HEART])} heart · ${pctSoft(aquariumTop(d.xAfter))} Aquarium-first`}
          </Label>
        </g>
      </Station>
    </g>
  );
}

function Legend({ x, values }: { x: number; values: readonly number[] }) {
  const rows = values
    .map((v, k) => ({ v, k }))
    .filter((r) => r.v >= 0.005)
    .sort((a, b) => b.v - a.v)
    .slice(0, 4);
  return (
    <g transform={`translate(${x} 0)`}>
      {rows.map((r, i) => (
        <motion.g key={r.k} initial={false} animate={{ y: 250 + i * 72 }}>
          <RankCard k={r.k} x={22} y={0} w={38} heart={r.k === MIA_HEART} shadow={false} />
          <Label x={54} y={8} size={22} anchor="start">
            {pctSoft(r.v)}
          </Label>
        </motion.g>
      ))}
      <Label x={0} y={210} size={18} anchor="start">
        Chance of each card:
      </Label>
    </g>
  );
}

function Stage({ step, draw }: { step: number; draw: { n: number; k: number } }) {
  const { params } = useStory();
  const d = miaDecision(params);
  const tokens = useMemo(() => tokensFromCounts(roundCounts(d.xAfter, 20)), [d.xAfter]);
  return (
    <svg viewBox="0 0 600 600">
      <AnimatePresence mode="wait">
        {step < 2 ? (
          <motion.g key="jar" initial={{ opacity: 0 }} animate={{ opacity: 1 }} exit={{ opacity: 0 }}>
            <Jar tokens={tokens} x={200} y={330} scale={1.02} first={MIA_HEART} label="Mia's new jar" lidOpen={step === 1} />
            <Label x={200} y={548} size={14} weight={500} color="#7d7a91">
              {step === 0 ? "picture rounded to 20 cards; exact chances on the right" : "picture rounded to 20 cards"}
            </Label>
            {step === 0 && <Legend x={400} values={d.xAfter} />}
            {step === 1 && (
              <AnimatePresence>
                <motion.g key={`d${draw.n}`} exit={{ opacity: 0 }}>
                  <motion.g
                    initial={{ x: 200, y: 190, scale: 0.3, opacity: 0, rotate: -25 }}
                    animate={{ x: 470, y: 230, scale: 1, opacity: 1, rotate: 0 }}
                    transition={{ type: "spring", stiffness: 70, damping: 13 }}
                  >
                    <RankCard k={draw.k} w={100} heart={draw.k === MIA_HEART} />
                  </motion.g>
                  <motion.g initial={{ opacity: 0 }} animate={{ opacity: 1 }} transition={{ delay: 0.5 }}>
                    <Avatar look={KIDS[MIA].look} x={470} y={430} size={96} mood={draw.k === MIA_HEART ? "calm" : "wow"} />
                    <Label x={470} y={520} size={18}>
                      {draw.k === MIA_HEART ? "Heart card again." : PERMS[draw.k][0] === 0 ? "Aquarium on top!" : "A surprise card!"}
                    </Label>
                  </motion.g>
                </motion.g>
              </AnimatePresence>
            )}
          </motion.g>
        ) : (
          <motion.g key="recap" initial={{ opacity: 0 }} animate={{ opacity: 1 }} exit={{ opacity: 0 }}>
            <Label x={300} y={30} size={21}>
              Mia's whole decision, in one round
            </Label>
            <Recap />
          </motion.g>
        )}
      </AnimatePresence>
    </svg>
  );
}

export function Ch8Draw() {
  const { params } = useStory();
  const d = miaDecision(params);
  const [draw, setDraw] = useState({ n: 0, k: MIA_HEART });
  const [tally, setTally] = useState({ heart: 0, aqua: 0, other: 0 });
  const pull = () => {
    const k = drawIndex(d.xAfter, Math.random());
    setDraw((s) => ({ n: s.n + 1, k }));
    setTally((t) =>
      k === MIA_HEART ? { ...t, heart: t.heart + 1 } : PERMS[k][0] === 0 ? { ...t, aqua: t.aqua + 1 } : { ...t, other: t.other + 1 },
    );
  };
  const total = tally.heart + tally.aqua + tally.other;
  const steps = [
    <>
      <h3>Mia's new jar</h3>
      <p>
        After one round, here is Mia's jar.{" "}
        {d.xAfter[MIA_HEART] > 0.5 ? "Most cards are still her heart card. " : "Now fewer than half are her heart card! "}
        {aquariumTop(d.xAfter) > 0.005 ? (
          <>
            Some now put <Dest c={0} /> on top, because the board said Aquarium was winning.
          </>
        ) : (
          <>With these dials, almost nothing changed.</>
        )}
      </p>
      <p className="small muted">
        With your dials (<Habit k="beta" /> {params.beta.toFixed(1)}, <Habit k="alpha" />{" "}
        {Math.round(params.alpha * 100)}%, <Habit k="eta" /> {Math.round(params.eta * 100)}%), there's a{" "}
        <b>{pctSoft(aquariumTop(d.xAfter))}</b> chance that her next ballot puts Aquarium first.
      </p>
    </>,
    <>
      <h3>Her next ballot</h3>
      <p>Next round, Mia reaches into her new jar and pulls a card. That card is her new ballot. Try it a few times!</p>
      <button className="btn btn-primary" onClick={pull}>
        Pull Mia's next ballot
      </button>
      {total > 0 && (
        <p className="small" style={{ marginTop: 10 }}>
          In {total} pull{total === 1 ? "" : "s"}: heart card <b>{tally.heart}</b>, Aquarium first <b>{tally.aqua}</b>
          {tally.other > 0 && (
            <>
              , something else <b>{tally.other}</b>
            </>
          )}
          .
        </p>
      )}
    </>,
    <>
      <h3>That's the whole decision</h3>
      <ol style={{ paddingLeft: "1.2em", margin: "0 0 0.6em" }}>
        <li>Read the board: who's HOT, who's NOT.</li>
        <li>Look at what friends wrote.</li>
        <li>Score every card: lead over each friend, cubed, averaged.</li>
        <li>
          <Habit k="beta" /> turns the scores into a wish list.
        </li>
        <li>
          <Habit k="alpha" /> mixes the heart back in: the plan.
        </li>
        <li>
          <Habit k="eta" /> decides how much of the jar to swap.
        </li>
        <li>Pull a card: the new ballot.</li>
      </ol>
      <p className="small muted">
        Her heart <Rank k={MIA_HEART} /> never changed. Only the jar did.
      </p>
      <Grownups>
        One round of the anchored reporting dynamics for voter i: p<sub>t</sub> and the friends' reports give the
        cubic scores, q<sub>i</sub> = softmax(β s<sub>i</sub>), and x<sub>i</sub><sup>t</sup> = (1 − η)
        x<sub>i</sub><sup>t−1</sup> + η[(1 − α) q<sub>i</sub> + α δ<sub>R<sub>i</sub><sup>0</sup></sub>]. The next
        report is a draw from x<sub>i</sub><sup>t</sup>.
      </Grownups>
    </>,
  ];
  return (
    <Chapter id="draw" num="Part 5" title="The new ballot">
      <Scrolly steps={steps} stage={(s) => <Stage step={s} draw={draw} />} label="Mia's new jar and her next ballot" />
    </Chapter>
  );
}
