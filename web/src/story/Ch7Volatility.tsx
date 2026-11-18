import { AnimatePresence, motion } from "motion/react";
import { useEffect, useMemo, useRef, useState } from "react";
import { KIDS, MIA, MIA_HEART, PARAMS } from "../cast";
import { Avatar } from "../components/Avatar";
import { Arrow, Label, Pill } from "../components/Bits";
import { Jar } from "../components/Jar";
import { Chapter, Scrolly } from "../components/Scrolly";
import { Slider } from "../components/Slider";
import { Grownups, Habit } from "../components/Text";
import { JAR_CARDS, jarTokens, roundCounts, swapTokens, tokensFromCounts, type Token } from "../lib/tokens";
import { pctSoft } from "../lib/format";
import { miaDecision, useStory } from "./world";

const GREEN = PARAMS.eta.color;

/** Stable token sets so that dragging the slider doesn't reshuffle unchanged cards. */
function useSwap(start: Token[], plan: number[], eta: number) {
  const cache = useRef(new Map<string, ReturnType<typeof swapTokens>>());
  const swapped = Math.round(eta * JAR_CARDS);
  const key = `${swapped}|${roundCounts(plan, swapped).join(",")}`;
  return useMemo(() => {
    let hit = cache.current.get(key);
    if (!hit) {
      hit = swapTokens(start, plan, eta);
      cache.current.set(key, hit);
    }
    return hit;
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [key, start]);
}

function MiniJar({ x, eta, plan, name, kid, active }: { x: number; eta: number; plan: number[]; name: string; kid: number; active?: boolean }) {
  const tokens = useMemo(() => {
    const keep = Math.round((1 - eta) * JAR_CARDS);
    const inCounts = roundCounts(plan, JAR_CARDS - keep);
    inCounts[MIA_HEART] += keep;
    return tokensFromCounts(inCounts);
  }, [eta, plan]);
  const heartShare = tokens.filter((t) => t.k === MIA_HEART).length / JAR_CARDS;
  return (
    <g transform={`translate(${x} 0)`}>
      {active && <rect x={-90} y={70} width={180} height={490} rx={18} fill={PARAMS.eta.soft} />}
      <Avatar look={KIDS[kid].look} x={0} y={128} size={74} />
      <Label x={0} y={198} size={18}>
        {name}
      </Label>
      <Pill x={0} y={228} text={`η = ${Math.round(eta * 100)}%`} fill="#fff" color="#0b7a5d" size={15} stroke={GREEN} />
      <Jar tokens={tokens} x={0} y={380} scale={0.55} first={MIA_HEART} />
      <Label x={0} y={500} size={15} weight={500} color="#4a4862">
        {`swaps ${Math.round(eta * JAR_CARDS)} of 20 cards`}
      </Label>
      <Label x={0} y={524} size={15} weight={500} color="#4a4862">
        {`heart cards left: ${Math.round(heartShare * 100)}%`}
      </Label>
    </g>
  );
}

function Stage({ step, nonce }: { step: number; nonce: number }) {
  const { params } = useStory();
  const d = miaDecision(params);
  const start = useMemo(() => tokensFromCounts([0, 0, 0, JAR_CARDS, 0, 0]), []);
  const planTokens = useMemo(() => jarTokens(d.plan), [d.plan]);
  const swap = useSwap(start, d.plan, params.eta);
  const [rewind, setRewind] = useState(false);
  useEffect(() => {
    if (nonce === 0) return;
    setRewind(true);
    const id = window.setTimeout(() => setRewind(false), 700);
    return () => window.clearTimeout(id);
  }, [nonce]);

  const swapping = step === 1 && !rewind;
  const tokens = swapping ? swap.tokens : start;
  const out = JAR_CARDS - Math.round((1 - params.eta) * JAR_CARDS);
  return (
    <svg viewBox="0 0 600 600">
      <AnimatePresence mode="wait">
        {step < 2 ? (
          <motion.g key="swap" initial={{ opacity: 0 }} animate={{ opacity: 1 }} exit={{ opacity: 0 }}>
            <Jar
              tokens={tokens}
              x={190}
              y={330}
              scale={0.95}
              first={MIA_HEART}
              label="Mia's jar (rounded to 20 cards)"
              enterFrom={{ x: 300, y: -110 }}
              exitTo={{ x: -60, y: -330 }}
              outlineIds={swapping ? swap.incoming : undefined}
              lidOpen
            />
            <Jar tokens={planTokens} x={480} y={250} scale={0.5} first={MIA_HEART} />
            <Label x={480} y={360} size={18}>
              Plan
            </Label>
            <Label x={480} y={382} size={14} weight={500} color="#7d7a91">
              (from loyalty + wish list)
            </Label>
            <Arrow d="M 432 180 Q 360 120 300 168" width={4} color={GREEN} />
            <Label x={370} y={120} size={16} color="#0b7a5d">
              swap in
            </Label>
            {swapping ? (
              <motion.g key={`sum${out}`} initial={{ opacity: 0 }} animate={{ opacity: 1 }} transition={{ delay: 0.6 }}>
                <Pill x={480} y={440} text={`kept ${JAR_CARDS - out} old cards`} fill="#efebe4" size={16} />
                <Pill x={480} y={480} text={`${out} new from the plan`} fill={PARAMS.eta.soft} color="#0b7a5d" size={16} />
                <Label x={480} y={530} size={16} weight={500} color="#4a4862">
                  {`heart card: 100% → ${pctSoft(d.xAfter[MIA_HEART])}`}
                </Label>
              </motion.g>
            ) : (
              <Label x={480} y={470} size={16} weight={500} color="#4a4862">
                old jar: 20 heart cards
              </Label>
            )}
          </motion.g>
        ) : (
          <motion.g key="three" initial={{ opacity: 0 }} animate={{ opacity: 1 }} exit={{ opacity: 0 }}>
            <Label x={300} y={44} size={21}>
              Same plan, different speed
            </Label>
            <MiniJar x={100} eta={0.1} plan={d.plan} name="Slow and steady" kid={2} />
            <MiniJar x={300} eta={params.eta} plan={d.plan} name="Mia (you choose)" kid={MIA} active />
            <MiniJar x={500} eta={0.9} plan={d.plan} name="Changes overnight" kid={9} />
          </motion.g>
        )}
      </AnimatePresence>
    </svg>
  );
}

export function Ch7Volatility() {
  const { params, set } = useStory();
  const d = miaDecision(params);
  const keep = Math.round((1 - params.eta) * JAR_CARDS);
  const incoming = roundCounts(d.plan, JAR_CARDS - keep);
  const hearts = keep + incoming[MIA_HEART];
  const [nonce, setNonce] = useState(0);
  const steps = [
    <>
      <h3>She doesn't empty the whole jar</h3>
      <p>
        Mia now has a plan. But people rarely change everything at once. Each round she swaps only <b>some</b> of the
        cards in her jar for cards from her plan.
      </p>
    </>,
    <>
      <h3>
        <Habit k="eta" />: how much changes per round
      </h3>
      <p>
        Volatility is the share of the jar that gets swapped. With {Math.round(params.eta * 100)}%,{" "}
        {JAR_CARDS - keep} of her 20 cards go out and {JAR_CARDS - keep} plan cards come in (outlined).
      </p>
      <p>
        Some plan cards are heart cards too, so she ends up with <b>{hearts} heart cards out of 20</b>.
      </p>
      <div className="control">
        <Slider k="eta" value={params.eta} onChange={(v) => set("eta", v)} />
      </div>
      <button className="btn btn-sm" style={{ marginTop: 10 }} onClick={() => setNonce((n) => n + 1)}>
        ↺ Replay the swap
      </button>
    </>,
    <>
      <h3>Slow and steady, or overnight?</h3>
      <p>
        With low volatility, Mia changes very slowly. With high volatility, her jar can look completely different by
        the next round. At 0, nothing ever changes. {PARAMS.eta.habit}
      </p>
      <Grownups>
        New jar x<sub>i</sub><sup>t</sup> = (1 − η) x<sub>i</sub><sup>t−1</sup> + η · plan. The jar remembers the
        mix from earlier rounds, not the single ballots Mia happened to pull. Here every card is 5%, so 20 × η cards
        are swapped (rounded).
      </Grownups>
    </>,
  ];
  return (
    <Chapter id="volatility" num="Habit 3 of 3" title="Volatility: how fast the jar changes">
      <Scrolly steps={steps} stage={(s) => <Stage step={s} nonce={nonce} />} label="Volatility swaps part of the jar for the plan" />
    </Chapter>
  );
}
