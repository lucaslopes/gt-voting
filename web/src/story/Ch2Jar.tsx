import { AnimatePresence, motion } from "motion/react";
import { useMemo, useState } from "react";
import { KIDS, MIA, MIA_HEART } from "../cast";
import { Avatar } from "../components/Avatar";
import { Arrow, Label } from "../components/Bits";
import { Jar } from "../components/Jar";
import { RankCard } from "../components/RankCard";
import { Chapter, Scrolly } from "../components/Scrolly";
import { Grownups, Heart, Rank } from "../components/Text";
import { tokensFromCounts, type Token } from "../lib/tokens";
import { permIndex } from "../model/rankings";

const ABC = permIndex("ABC");
const ACB = permIndex("ACB");

function counts(tokens: readonly Token[]) {
  const c = [0, 0, 0, 0, 0, 0];
  tokens.forEach((t) => (c[t.k] += 1));
  return c;
}

function Legend({ tokens, x, y }: { tokens: readonly Token[]; x: number; y: number }) {
  const c = counts(tokens);
  const rows = c.map((n, k) => ({ n, k })).filter((r) => r.n > 0).sort((a, b) => b.n - a.n);
  return (
    <g transform={`translate(${x} ${y})`}>
      {rows.map((r, i) => (
        <motion.g key={r.k} initial={{ opacity: 0, x: 20 }} animate={{ opacity: 1, x: 0, y: i * 78 }} transition={{ delay: 0.1 * i }}>
          <RankCard k={r.k} x={22} y={0} w={40} heart={r.k === MIA_HEART} shadow={false} />
          <Label x={56} y={-4} size={20} anchor="start">
            {`${r.n} of 20`}
          </Label>
          <Label x={56} y={20} size={17} anchor="start" weight={500} color="#7d7a91">
            {`= ${r.n * 5}% chance`}
          </Label>
        </motion.g>
      ))}
    </g>
  );
}

function Stage({ step, draw, full, mixed }: { step: number; draw: { n: number; k: number }; full: Token[]; mixed: Token[] }) {
  const tokens = step >= 2 && step < 3 ? mixed : full;
  const two = step === 3;
  return (
    <svg viewBox="0 0 600 600">
      <motion.g initial={false} animate={{ x: two ? -70 : 0, scale: two ? 0.78 : 1 }} transition={{ type: "spring", stiffness: 90, damping: 18 }}>
        <Jar tokens={tokens} x={230} y={340} scale={1.1} first={MIA_HEART} label="Mia's ballot jar" lidOpen={!two} />
      </motion.g>
      <AnimatePresence>
        {step < 2 && (
          <motion.g key="mia" initial={{ opacity: 0 }} animate={{ opacity: 1 }} exit={{ opacity: 0 }}>
            <Avatar look={KIDS[MIA].look} x={70} y={520} size={86} mood="calm" />
          </motion.g>
        )}
      </AnimatePresence>

      {/* the card she pulls out */}
      <AnimatePresence>
        {!two && (
          <motion.g key={`draw${draw.n}`} exit={{ opacity: 0, transition: { duration: 0.2 } }}>
            <motion.g
              initial={{ x: 230, y: 200, scale: 0.3, opacity: 0, rotate: -20 }}
              animate={{ x: 488, y: 150, scale: 1, opacity: 1, rotate: 0 }}
              transition={{ type: "spring", stiffness: 70, damping: 14 }}
            >
              <RankCard k={draw.k} w={84} heart={draw.k === MIA_HEART} />
            </motion.g>
            <motion.g initial={{ opacity: 0 }} animate={{ opacity: 1 }} transition={{ delay: 0.5 }}>
              <Label x={488} y={232} size={18}>
                {draw.k === MIA_HEART ? "her ballot: heart card" : "her ballot: a different card!"}
              </Label>
            </motion.g>
          </motion.g>
        )}
      </AnimatePresence>

      <AnimatePresence>
        {(step === 1 || step === 2) && (
          <motion.g key={`legend${step}`} initial={{ opacity: 0 }} animate={{ opacity: 1 }} exit={{ opacity: 0 }}>
            <Legend tokens={tokens} x={420} y={310} />
          </motion.g>
        )}
      </AnimatePresence>

      <AnimatePresence>
        {two && (
          <motion.g key="next" initial={{ opacity: 0, x: 40 }} animate={{ opacity: 1, x: 0 }} exit={{ opacity: 0 }}>
            <Arrow d="M 250 230 Q 330 170 400 230" width={4} />
            <Label x={325} y={170} size={19}>
              next round
            </Label>
            <g transform="translate(450 340) scale(0.858)">
              <path
                d="M -62 -112 Q -62 -100 -90 -88 Q -110 -78 -110 -50 V 120 Q -110 146 -84 146 H 84 Q 110 146 110 120 V -50 Q 110 -78 90 -88 Q 62 -100 62 -112 Z"
                fill="#f6f2ea"
                stroke="#23213a"
                strokeWidth={3.5}
                strokeDasharray="10 8"
              />
              <rect x={-72} y={-140} width={144} height={28} rx={9} fill="#3b3858" opacity={0.5} />
              <text y={40} textAnchor="middle" fontSize={120} fontWeight={700} fill="#c9c0b0">
                ?
              </text>
            </g>
            <Label x={450} y={498} size={20}>
              which cards?
            </Label>
          </motion.g>
        )}
      </AnimatePresence>
    </svg>
  );
}

export function Ch2Jar() {
  const full = useMemo(() => tokensFromCounts([0, 0, 0, 20, 0, 0]), []);
  const mixed = useMemo(() => [...full.slice(0, 15), ...tokensFromCounts([3, 2, 0, 0, 0, 0])], [full]);
  const [draw, setDraw] = useState({ n: 0, k: MIA_HEART });
  const [mixedTally, setMixedTally] = useState({ heart: 0, other: 0 });
  const pull = (mix: boolean) => {
    let k = MIA_HEART;
    if (mix) {
      const u = Math.random() * 20;
      k = u < 15 ? MIA_HEART : u < 18 ? ABC : ACB;
      setMixedTally((t) => (k === MIA_HEART ? { ...t, heart: t.heart + 1 } : { ...t, other: t.other + 1 }));
    }
    setDraw((d) => ({ n: d.n + 1, k }));
  };

  const steps = [
    <>
      <h3>Mia's ballot jar</h3>
      <p>
        Here's a trick for picturing Mia's mind: a <b>jar of ballot cards</b>. Each round, she closes her eyes, reaches
        in, and pulls out one card. That card is the ballot she hands in.
      </p>
      <button className="btn" onClick={() => pull(false)}>
        Pull a card
      </button>
    </>,
    <>
      <h3>At first, every card is her heart card</h3>
      <p>
        Today all 20 cards in the jar are her <Heart />, <Rank k={MIA_HEART} />. Whatever she pulls, she votes her
        heart: a <b>100%</b> chance.
      </p>
      <button className="btn" onClick={() => pull(false)}>
        Pull again
      </button>
    </>,
    <>
      <h3>But a jar can hold a mix</h3>
      <p>
        Suppose 15 cards were her heart card and 5 were other cards. Then she'd <i>usually</i> vote her heart, but
        not always. Each card is a 5% chance.
      </p>
      <button className="btn" onClick={() => pull(true)}>
        Pull from the mixed jar
      </button>
      {mixedTally.heart + mixedTally.other > 0 && (
        <p className="small muted" style={{ marginTop: 10 }}>
          You pulled her heart card {mixedTally.heart} time{mixedTally.heart === 1 ? "" : "s"} and another card{" "}
          {mixedTally.other} time{mixedTally.other === 1 ? "" : "s"}.
        </p>
      )}
    </>,
    <>
      <h3>The big question</h3>
      <p>
        Mia never changes her heart. What changes is <b>the mix of cards in her jar</b>. Next we'll follow, step by
        step, how one round of voting swaps some cards in and out.
      </p>
      <Grownups>
        The jar is the voter's mixed reporting state x<sub>i</sub><sup>t</sup>: a probability distribution over the
        3! = 6 rankings. Honest start: x<sub>i</sub><sup>0</sup> = δ<sub>R<sub>i</sub><sup>0</sup></sub> (all cards
        are the heart card). We draw 20 cards so each one is 5%; the real jar can hold any fraction.
      </Grownups>
    </>,
  ];
  return (
    <Chapter id="jar" num="Part 2" title="The ballot jar">
      <Scrolly
        steps={steps}
        stage={(s) => <Stage step={s} draw={draw} full={full} mixed={mixed} />}
        label="Mia's jar of ballot cards"
      />
    </Chapter>
  );
}
