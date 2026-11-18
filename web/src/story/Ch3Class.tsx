import { AnimatePresence, motion } from "motion/react";
import { KIDS, MIA, STORY_HEARTS } from "../cast";
import { Avatar } from "../components/Avatar";
import { Arrow, Label, Pill } from "../components/Bits";
import { Board } from "../components/Board";
import { DuelBoard } from "../components/DuelBoard";
import { CandBadge } from "../components/icons";
import { MiniCard, RankCard } from "../components/RankCard";
import { Chapter, Scrolly } from "../components/Scrolly";
import { BoardTag, Dest, Grownups, Rank } from "../components/Text";
import { margins, maximalLottery } from "../model/lottery";
import { permIndex } from "../model/rankings";
import { R1_P, R1_TALLIES } from "./world";

const spring = { type: "spring", stiffness: 100, damping: 18 } as const;
const CYCLE_REPORTS = [
  ...Array(6).fill(permIndex("ABC")),
  ...Array(5).fill(permIndex("BCA")),
  ...Array(4).fill(permIndex("CAB")),
];
const CYCLE_M = margins(CYCLE_REPORTS);
const CYCLE_P = maximalLottery(CYCLE_M);

function clusterPose(i: number) {
  if (i === 14) return { x: 270, y: 480 };
  const g = i < 7 ? 0 : 1;
  const j = i % 7;
  const cx = g === 0 ? 150 : 450;
  return j < 4 ? { x: cx + (j - 1.5) * 66, y: 262 } : { x: cx + (j - 5) * 66, y: 350 };
}

function stripPose(i: number) {
  return { x: 32 + i * 38.3, y: 64 };
}

function Stage({ step }: { step: number }) {
  const strip = step >= 1 && step <= 3;
  const hidden = step === 4;
  return (
    <svg viewBox="0 0 600 600">
      {/* group labels */}
      <AnimatePresence>
        {step === 0 && (
          <motion.g key="labels" initial={{ opacity: 0 }} animate={{ opacity: 1 }} exit={{ opacity: 0 }}>
            <RankCard k={permIndex("ACB")} x={128} y={150} w={58} />
            <Label x={166} y={160} size={26} anchor="start">
              × 7
            </Label>
            <RankCard k={permIndex("BCA")} x={428} y={150} w={58} heart />
            <Label x={466} y={160} size={26} anchor="start">
              × 7
            </Label>
            <RankCard k={permIndex("ABC")} x={340} y={480} w={46} />
            <Label x={372} y={488} size={22} anchor="start">
              × 1
            </Label>
            <Label x={450} y={410} size={16} color="#a1520a">
              Mia's group
            </Label>
            <Label x={270} y={540} size={16} color="#4a4862">
              Zoe
            </Label>
          </motion.g>
        )}
      </AnimatePresence>

      {/* the kids */}
      {KIDS.map((kid, i) => {
        const p = strip ? stripPose(i) : clusterPose(i);
        return (
          <motion.g
            key={i}
            initial={false}
            animate={{ x: p.x, y: p.y, scale: strip ? 0.56 : 1, opacity: hidden ? 0 : 1 }}
            transition={{ ...spring, delay: strip ? i * 0.03 : 0 }}
          >
            <Avatar look={kid.look} size={62} ring={i === MIA ? "#f28a1e" : undefined} />
          </motion.g>
        );
      })}

      {/* everybody's ballot */}
      <AnimatePresence>
        {strip &&
          STORY_HEARTS.map((k, i) => {
            const p = stripPose(i);
            return (
              <motion.g
                key={i}
                initial={{ x: p.x, y: p.y, opacity: 0, scale: 0.4 }}
                animate={{ x: p.x, y: p.y + 56, opacity: 1, scale: 1 }}
                exit={{ opacity: 0 }}
                transition={{ ...spring, delay: 0.4 + i * 0.05 }}
              >
                <MiniCard k={k} w={24} />
              </motion.g>
            );
          })}
      </AnimatePresence>
      <AnimatePresence>
        {step === 1 && (
          <motion.g key="hint" initial={{ opacity: 0 }} animate={{ opacity: 1 }} exit={{ opacity: 0 }} transition={{ delay: 1.1 }}>
            <Label x={300} y={190} size={22}>
              15 ballots: everyone votes their heart
            </Label>
            <g transform="translate(180 300)">
              <MiniCard k={permIndex("ACB")} w={44} />
            </g>
            <Label x={212} y={308} size={20} anchor="start">
              7 ×
            </Label>
            <g transform="translate(300 300)">
              <MiniCard k={permIndex("BCA")} w={44} />
            </g>
            <Label x={332} y={308} size={20} anchor="start">
              7 ×
            </Label>
            <g transform="translate(420 300)">
              <MiniCard k={permIndex("ABC")} w={44} />
            </g>
            <Label x={452} y={308} size={20} anchor="start">
              1 ×
            </Label>
            <Label x={300} y={400} size={17} weight={500} color="#7d7a91">
              top stripe = first choice
            </Label>
          </motion.g>
        )}
      </AnimatePresence>

      {/* head-to-head duels */}
      <AnimatePresence>
        {step === 2 && (
          <motion.g key="duels" initial={{ opacity: 0, y: 20 }} animate={{ opacity: 1, y: 0 }} exit={{ opacity: 0 }}>
            <Label x={300} y={200} size={22}>
              Head-to-head duels
            </Label>
            <DuelBoard tallies={R1_TALLIES} x={100} y={270} w={400} gap={100} />
            <Label x={300} y={550} size={18} weight={500} color="#4a4862">
              ballots that rank one above the other
            </Label>
          </motion.g>
        )}
      </AnimatePresence>

      {/* the scoreboard */}
      <AnimatePresence>
        {step === 3 && (
          <motion.g key="board" initial={{ opacity: 0, scale: 0.9 }} animate={{ opacity: 1, scale: 1 }} exit={{ opacity: 0 }}>
            <Board p={R1_P} x={130} y={200} w={340} h={290} />
            <Label x={300} y={540} size={20}>
              Aquarium beats both rivals → 100%
            </Label>
          </motion.g>
        )}
      </AnimatePresence>

      {/* the rock-paper-scissors aside */}
      <AnimatePresence>
        {step === 4 && (
          <motion.g key="cycle" initial={{ opacity: 0 }} animate={{ opacity: 1 }} exit={{ opacity: 0 }}>
            <Label x={70} y={46} size={19} anchor="start">
              Another class:
            </Label>
            {[
              ["ABC", 6],
              ["BCA", 5],
              ["CAB", 4],
            ].map(([lab, n], i) => (
              <g key={i} transform={`translate(${300 + i * 90} 40)`}>
                <Label x={-8} y={6} size={19} anchor="end">
                  {`${n} ×`}
                </Label>
                <MiniCard k={permIndex(lab as string)} w={22} />
              </g>
            ))}
            <CandBadge c={0} x={300} y={110} r={34} />
            <CandBadge c={1} x={450} y={300} r={34} />
            <CandBadge c={2} x={150} y={300} r={34} />
            <Arrow d="M 328 138 L 420 262" width={4} color="#2f8fe0" />
            <Arrow d="M 412 304 L 190 304" width={4} color="#f28a1e" delay={0.3} />
            <Arrow d="M 170 266 L 270 136" width={4} color="#8b5bd8" delay={0.6} />
            <Pill x={404} y={186} text={`by ${CYCLE_M[0][1]}`} fill="#dcedfc" color="#155a99" />
            <Pill x={300} y={330} text={`by ${CYCLE_M[1][2]}`} fill="#ffe8cf" color="#a1520a" />
            <Pill x={196} y={186} text={`by ${CYCLE_M[2][0]}`} fill="#ece3fb" color="#5631a0" />
            <Board p={CYCLE_P} x={150} y={370} w={300} h={220} title="SHARES" />
          </motion.g>
        )}
      </AnimatePresence>
    </svg>
  );
}

export function Ch3Class() {
  const steps = [
    <>
      <h3>Meet the class</h3>
      <p>Mia isn't alone. There are 15 kids, each with their own heart ranking:</p>
      <ul style={{ paddingLeft: "1.1em", margin: "0 0 0.6em" }}>
        <li>
          7 love <Rank k={permIndex("ACB")} />
        </li>
        <li>
          7 love <Rank k={permIndex("BCA")} />, like Mia
        </li>
        <li>
          and Zoe loves <Rank k={permIndex("ABC")} />
        </li>
      </ul>
    </>,
    <>
      <h3>Round 1: everyone hands in a card</h3>
      <p>
        Each kid pulls a card from their own jar. All the jars still hold only heart cards, so this time everybody
        votes their heart.
      </p>
    </>,
    <>
      <h3>Count the duels</h3>
      <p>
        Now the class compares the places two at a time. <Dest c={0} /> vs <Dest c={1} />: 8 ballots put Aquarium
        higher, 7 put Beach higher. Aquarium wins that duel, 8 to 7.
      </p>
      <p>
        The other two duels are also 8 to 7: Aquarium beats Castle, and Beach beats Castle.
      </p>
    </>,
    <>
      <h3>The scoreboard</h3>
      <p>
        <Dest c={0} /> beats <i>both</i> rivals, so it gets the whole win: 100% on the <BoardTag />. Everybody can see
        the board, and the next part is about what Mia does with it.
      </p>
    </>,
    <>
      <h3>What if the duels go in a circle?</h3>
      <p>
        In some classes the duels go round like rock-paper-scissors: Aquarium beats Beach, Beach beats Castle, and
        Castle beats Aquarium. Nobody beats everyone, so the board <b>shares the win</b>.
      </p>
      <p>
        Each place's share is the winning margin of the <i>other</i> duel, the one it isn't in. Aquarium isn't in
        Beach vs Castle, which Beach wins by 7, so Aquarium gets 7 parts out of 15 (7 + 5 + 3).
      </p>
      <Grownups>
        The board is the published maximal lottery p<sub>t</sub> (the GT rule) over candidates. A strict Condorcet
        winner gets probability 1. In a three-cycle, each candidate's probability is proportional to the margin of
        the duel it is not part of, here (7, 3, 5)/15. With an odd number of complete ballots no duel can tie, so
        the lottery is unique.
      </Grownups>
    </>,
  ];
  return (
    <Chapter id="class" num="Part 3" title="Everyone votes, the board shows the result">
      <Scrolly steps={steps} stage={(s) => <Stage step={s} />} label="The class votes and the scoreboard is posted" />
    </Chapter>
  );
}
