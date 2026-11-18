import { AnimatePresence, motion } from "motion/react";
import { DEST, KIDS, MIA, MIA_HEART } from "../cast";
import { Avatar } from "../components/Avatar";
import { BallotBox, Bubble, Label } from "../components/Bits";
import { CandBadge } from "../components/icons";
import { RankCard } from "../components/RankCard";
import { Chapter, Scrolly } from "../components/Scrolly";
import { Dest, Grownups, Heart, Rank } from "../components/Text";
import { useTicker } from "../lib/useCycle";
import { PERMS } from "../model/rankings";

const INK = "#23213a";
const spring = { type: "spring", stiffness: 110, damping: 18 } as const;

/** Where each destination badge sits in each step. */
function badgePose(c: number, step: number) {
  if (step === 0) return { x: 120 + 180 * c, y: 280, s: 1, o: 1 };
  if (step === 1) {
    const pos = PERMS[MIA_HEART].indexOf(c as 0 | 1 | 2);
    const top = 300 - (150 * 1.42) / 2;
    const rowH = (150 * 1.42 - 30) / 3;
    return { x: 345 + 90, y: top + 15 + rowH * (pos + 0.5), s: (rowH * (pos === 0 ? 0.44 : 0.38)) / 64, o: 1 };
  }
  return { x: 300, y: 300, s: 0.2, o: 0 };
}

function Stage({ step }: { step: number }) {
  const tick = useTicker(1300, step === 3);
  const cycling = [MIA_HEART, 0, MIA_HEART, 4, 1, MIA_HEART, 5][tick % 7];
  return (
    <svg viewBox="0 0 600 600">
      {/* names under the big badges */}
      <AnimatePresence>
        {step === 0 &&
          DEST.map((d, c) => (
            <motion.g key={c} initial={{ opacity: 0, y: 10 }} animate={{ opacity: 1, y: 0 }} exit={{ opacity: 0 }}>
              <Label x={120 + 180 * c} y={392} size={28}>
                {d.name}
              </Label>
              <Label x={120 + 180 * c} y={424} size={17} weight={500} color="#7d7a91">
                {["see sharks & jellyfish", "sand, waves, ice cream", "towers & a real moat"][c]}
              </Label>
            </motion.g>
          ))}
      </AnimatePresence>

      {/* Mia and her card frame */}
      <AnimatePresence>
        {step === 1 && (
          <motion.g key="mia" initial={{ opacity: 0, x: -40 }} animate={{ opacity: 1, x: 0 }} exit={{ opacity: 0, x: -40 }}>
            <Avatar look={KIDS[MIA].look} x={160} y={330} size={170} />
            <Label x={160} y={445} size={24}>
              Mia
            </Label>
            <Bubble x={64} y={136} w={200} h={64} lines={["Beach first!", "Aquarium last."]} size={19} />
          </motion.g>
        )}
        {step === 1 && (
          <motion.g key="frame" initial={{ opacity: 0, scale: 0.9 }} animate={{ opacity: 1, scale: 1 }} exit={{ opacity: 0 }}>
            <rect x={347} y={196.5} width={150} height={213} rx={24} fill={INK} opacity={0.12} />
            <rect x={345} y={193.5} width={150} height={213} rx={24} fill="#fff" stroke={INK} strokeWidth={3} />
            {[0, 1, 2].map((pos) => (
              <text key={pos} x={375} y={238.5 + 61 * pos} dy="0.36em" textAnchor="middle" fontSize={30} fontWeight={600} fill="#9a97ad">
                {pos + 1}
              </text>
            ))}
            <Label x={420} y={450} size={18} weight={500} color="#7d7a91">
              favourite on top
            </Label>
          </motion.g>
        )}
      </AnimatePresence>

      {/* the three destinations travel into Mia's card */}
      {DEST.map((_, c) => {
        const p = badgePose(c, step);
        return (
          <motion.g key={c} initial={false} animate={{ x: p.x, y: p.y, scale: p.s, opacity: p.o }} transition={spring}>
            <CandBadge c={c} r={64} />
          </motion.g>
        );
      })}

      {/* all six cards */}
      <AnimatePresence>
        {step === 2 && (
          <motion.g key="six" exit={{ opacity: 0 }}>
            <Label x={300} y={96} size={24}>
              3 places → 6 possible cards
            </Label>
            {PERMS.map((_, k) => {
              const x = 140 + 160 * (k % 3);
              const y = 230 + 210 * Math.floor(k / 3);
              const mine = k === MIA_HEART;
              return (
                <motion.g
                  key={k}
                  initial={{ opacity: 0, scale: 0.4, x: 300 - x, y: 300 - y }}
                  animate={{ opacity: 1, scale: 1, x: 0, y: 0 }}
                  transition={{ ...spring, delay: 0.07 * k }}
                >
                  <RankCard k={k} x={x} y={y} w={104} heart={mine} outline={mine ? "#e5484d" : undefined} />
                  {mine && (
                    <Label x={x} y={y + 98} size={17} color="#b8323b">
                      Mia's heart
                    </Label>
                  )}
                </motion.g>
              );
            })}
          </motion.g>
        )}
      </AnimatePresence>

      {/* heart ranking (fixed) vs ballot (changes) */}
      <AnimatePresence>
        {step === 3 && (
          <motion.g key="hb" initial={{ opacity: 0 }} animate={{ opacity: 1 }} exit={{ opacity: 0 }}>
            <Label x={160} y={140} size={24} color="#b8323b">
              Heart ranking
            </Label>
            <RankCard k={MIA_HEART} x={160} y={290} w={140} heart outline="#e5484d" />
            <g transform="translate(160 430)">
              <rect x={-14} y={-8} width={28} height={22} rx={5} fill={INK} />
              <path d="M -8 -8 V -14 A 8 8 0 0 1 8 -14 V -8" fill="none" stroke={INK} strokeWidth={4} />
            </g>
            <Label x={160} y={478} size={18} weight={500} color="#4a4862">
              locked: never changes
            </Label>

            <Label x={440} y={140} size={24}>
              Ballot
            </Label>
            <AnimatePresence mode="popLayout">
              <motion.g
                key={tick}
                initial={{ opacity: 0, y: -60, rotate: -8 }}
                animate={{ opacity: 1, y: 0, rotate: 0 }}
                exit={{ opacity: 0, y: 60, scale: 0.6 }}
                transition={{ duration: 0.55 }}
              >
                <RankCard k={cycling} x={440} y={250} w={96} />
              </motion.g>
            </AnimatePresence>
            <BallotBox x={440} y={400} s={0.85} />
            <Label x={440} y={478} size={18} weight={500} color="#4a4862">
              can change every round
            </Label>
          </motion.g>
        )}
      </AnimatePresence>
    </svg>
  );
}

export function Ch1Choice() {
  const steps = [
    <>
      <h3>A class, a trip, three choices</h3>
      <p>
        Mia's class is voting on where to go for the school trip. There are three choices: the <Dest c={0} />, the{" "}
        <Dest c={1} /> and the <Dest c={2} />.
      </p>
    </>,
    <>
      <h3>Mia ranks all three</h3>
      <p>
        Mia doesn't just pick one. She puts all three in order, favourite on top. In her heart: <Dest c={1} /> first,
        then <Dest c={2} />, and <Dest c={0} /> last.
      </p>
      <p className="muted">
        We'll write that as <Rank k={MIA_HEART} />.
      </p>
    </>,
    <>
      <h3>Six possible cards</h3>
      <p>
        With three places there are exactly <b>six</b> ways to order them. Think of them as six different ballot cards.
        Every kid's ballot is one of these six.
      </p>
    </>,
    <>
      <h3>Heart ranking vs. ballot</h3>
      <p>
        Mia's real favourite order is her <Heart />. In this story it never changes.
      </p>
      <p>
        What <i>can</i> change is the card she actually hands in each round: her <b>ballot</b>. The rest of the story
        is about one question: <b>which card will Mia hand in next time, and why?</b>
      </p>
      <Grownups>
        The heart ranking is the baseline ranking R<sub>i</sub><sup>0</sup> (a fixed model input). The ballot is the
        report R<sub>i</sub><sup>t</sup>, which is drawn again every round.
      </Grownups>
    </>,
  ];
  return (
    <Chapter id="choice" num="Part 1" title="Three places, six ways to rank them">
      <Scrolly steps={steps} stage={(s) => <Stage step={s} />} label="Mia, the three destinations and the six ranking cards" />
    </Chapter>
  );
}
