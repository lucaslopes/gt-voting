import { AnimatePresence, motion } from "motion/react";
import { useState } from "react";
import { DEST, KIDS, MIA, MIA_HEART } from "../cast";
import { Avatar } from "../components/Avatar";
import { Bubble, Label, Pill } from "../components/Bits";
import { Board } from "../components/Board";
import { DistBars } from "../components/DistBars";
import { CandBadge } from "../components/icons";
import { CARD_RATIO, MiniCard, RankCard } from "../components/RankCard";
import { Chapter, Scrolly } from "../components/Scrolly";
import { BoardTag, Dest, Grownups, Heart, Rank, rankName } from "../components/Text";
import { signed } from "../lib/format";
import { useTweened } from "../lib/useTweened";
import { centered } from "../model/lottery";
import { CANDS, PERMS, RANK, permIndex } from "../model/rankings";
import { allScores, contrast, cube } from "../model/response";
import { R1_P, R1_REPORTS } from "./world";

const INK = "#23213a";
const P_TILDE = centered(R1_P);
const FRIENDS = KIDS.map((_, i) => i).filter((i) => i !== MIA);
const FRIEND_REPORTS = FRIENDS.map((i) => R1_REPORTS[i]);
const SCORES = allScores(P_TILDE, FRIEND_REPORTS);
const PICK_FRIENDS = [8, 0, 14]; // Hugo (BCA), Ava (ACB), Zoe (ABC)

function rowY(cy: number, w: number, pos: number) {
  const h = w * CARD_RATIO;
  const pad = w * 0.1;
  return cy - h / 2 + pad + ((h - 2 * pad) / 3) * (pos + 0.5);
}

const pointsColor = (v: number) => (v > 1e-9 ? "#137451" : v < -1e-9 ? "#a8293a" : "#4a4862");
const pointsFill = (v: number) => (v > 1e-9 ? "#d8f3e6" : v < -1e-9 ? "#fbe0e3" : "#efebe4");

function Compare({ trial, friend }: { trial: number; friend: number }) {
  const theirs = R1_REPORTS[friend];
  const lead = contrast(P_TILDE, theirs, trial);
  const shownLead = useTweened(lead);
  const W = 116;
  return (
    <g>
      <Avatar look={KIDS[MIA].look} x={140} y={70} size={64} mood="think" />
      <Label x={140} y={128} size={17}>
        Mia tries…
      </Label>
      <Avatar look={KIDS[friend].look} x={460} y={70} size={64} />
      <Label x={460} y={128} size={17}>
        {`${KIDS[friend].name} wrote`}
      </Label>
      <RankCard k={trial} x={140} y={232} w={W} />
      <RankCard k={theirs} x={460} y={232} w={W} />
      {CANDS.map((c) => {
        const y1 = rowY(232, W, RANK[trial][c]);
        const y2 = rowY(232, W, RANK[theirs][c]);
        const gained = RANK[theirs][c] - RANK[trial][c];
        return (
          <motion.g key={`${trial}-${theirs}-${c}`} initial={{ opacity: 0 }} animate={{ opacity: 1 }} transition={{ delay: 0.15 * c }}>
            <path
              d={`M 204 ${y1} C 280 ${y1}, 320 ${y2}, 396 ${y2}`}
              fill="none"
              stroke={DEST[c].color}
              strokeWidth={5}
              strokeLinecap="round"
              opacity={0.85}
            />
            <Pill
              x={244}
              y={y1}
              text={gained === 0 ? "same" : `${gained > 0 ? "↑" : "↓"}${Math.abs(gained)}`}
              fill="#fff"
              stroke={DEST[c].color}
              color={DEST[c].ink}
              size={15}
            />
          </motion.g>
        );
      })}
      {/* the arithmetic, one destination per line */}
      <g transform="translate(70 360)">
        {CANDS.map((c) => {
          const gained = RANK[theirs][c] - RANK[trial][c];
          const part = P_TILDE[c] * gained;
          const hot = P_TILDE[c] > 0;
          return (
            <g key={c} transform={`translate(0 ${c * 44})`}>
              <CandBadge c={c} x={14} y={0} r={15} />
              <Label x={40} y={6} size={18} anchor="start" weight={500}>
                {gained === 0 ? "same place" : `${gained > 0 ? "up" : "down"} ${Math.abs(gained)}`}
              </Label>
              <Label x={170} y={6} size={18} anchor="start" weight={500} color={hot ? "#d4552b" : "#3d6f9c"}>
                {`× ${hot ? "HOT" : "NOT"} ${signed(P_TILDE[c])}`}
              </Label>
              <Label x={460} y={6} size={19} anchor="end" color={pointsColor(part)}>
                {`= ${signed(part)}`}
              </Label>
            </g>
          );
        })}
        <line x1={0} x2={460} y1={124} y2={124} stroke={INK} strokeWidth={1.5} opacity={0.3} />
        <Label x={0} y={156} size={19} anchor="start" weight={500}>
          {`total ${signed(lead * 2)} ÷ 2 = lead`}
        </Label>
        <rect x={300} y={134} width={160} height={34} rx={17} fill={pointsFill(lead)} />
        <Label x={380} y={158} size={20} color={pointsColor(lead)}>
          {signed(shownLead)}
        </Label>
      </g>
    </g>
  );
}

function CubeChart({ lead }: { lead: number }) {
  const X = (v: number) => 300 + v * 200;
  const Y = (v: number) => 320 - v * 200;
  const curve = Array.from({ length: 81 }, (_, i) => {
    const v = -1 + i / 40;
    return `${i ? "L" : "M"} ${X(v)} ${Y(cube(v))}`;
  }).join(" ");
  const out = cube(lead);
  return (
    <g>
      <Label x={300} y={70} size={22}>
        points = lead × lead × lead
      </Label>
      <line x1={X(-1)} x2={X(1)} y1={Y(0)} y2={Y(0)} stroke={INK} strokeWidth={1.5} opacity={0.4} />
      <line x1={X(0)} x2={X(0)} y1={Y(1)} y2={Y(-1)} stroke={INK} strokeWidth={1.5} opacity={0.4} />
      <path d={`M ${X(-1)} ${Y(-1)} L ${X(1)} ${Y(1)}`} stroke={INK} strokeWidth={2} strokeDasharray="5 6" opacity={0.3} />
      <Label x={X(0.78)} y={Y(0.92)} size={14} anchor="end" weight={500} color="#7d7a91">
        without cubing
      </Label>
      <motion.path d={curve} fill="none" stroke="#1f9d6b" strokeWidth={5} strokeLinecap="round" initial={{ pathLength: 0 }} animate={{ pathLength: 1 }} transition={{ duration: 1.1 }} />
      <circle cx={X(0.5)} cy={Y(cube(0.5))} r={7} fill="#fff" stroke="#1f9d6b" strokeWidth={3} />
      <Label x={X(0.5) + 50} y={Y(0) - 8} size={17} anchor="start">
        ½ → ⅛
      </Label>
      <circle cx={X(-0.5)} cy={Y(cube(-0.5))} r={7} fill="#fff" stroke="#1f9d6b" strokeWidth={3} />
      <Label x={X(-0.5) - 50} y={Y(0) + 22} size={17} anchor="end">
        −½ → −⅛
      </Label>
      <motion.circle cx={X(lead)} cy={Y(out)} r={11} fill="#1f9d6b" stroke="#fff" strokeWidth={3} initial={{ scale: 0 }} animate={{ scale: 1 }} transition={{ delay: 0.9 }} />
      <Label x={X(-1)} y={Y(0) - 10} size={15} anchor="start" color="#7d7a91">
        lead −1
      </Label>
      <Label x={X(1)} y={Y(0) + 26} size={15} anchor="end" color="#7d7a91">
        lead +1
      </Label>
      <Pill x={300} y={560} text={`this lead ${signed(lead)} → ${signed(out)} points`} fill="#d8f3e6" color="#137451" size={18} />
    </g>
  );
}

function AllFriends({ trial }: { trial: number }) {
  const pts = FRIENDS.map((j) => cube(contrast(P_TILDE, R1_REPORTS[j], trial)));
  const avg = pts.reduce((a, b) => a + b, 0) / pts.length;
  const shownAvg = useTweened(avg);
  return (
    <g>
      <Label x={300} y={44} size={20}>
        Mia tries this card against all 14 friends
      </Label>
      <RankCard k={trial} x={300} y={100} w={44} />
      {FRIENDS.map((j, n) => {
        const x = 52 + (n % 7) * 82.5;
        const y = 200 + Math.floor(n / 7) * 160;
        return (
          <motion.g key={j} initial={{ opacity: 0, y: 12 }} animate={{ opacity: 1, y: 0 }} transition={{ delay: 0.04 * n }}>
            <Avatar look={KIDS[j].look} x={x} y={y} size={50} />
            <g transform={`translate(${x} ${y + 52})`}>
              <MiniCard k={R1_REPORTS[j]} w={22} />
            </g>
            <Pill x={x} y={y + 96} text={signed(pts[n])} fill={pointsFill(pts[n])} color={pointsColor(pts[n])} size={15} pad={8} />
          </motion.g>
        );
      })}
      <g transform="translate(80 540)">
        <Label x={0} y={-14} size={17} anchor="start" weight={500}>
          average points
        </Label>
        <rect x={0} y={0} width={440} height={14} rx={7} fill="#efebe4" />
        <line x1={220} x2={220} y1={-6} y2={20} stroke={INK} strokeWidth={2} opacity={0.4} />
        <motion.circle cy={7} r={13} fill={pointsColor(avg)} stroke="#fff" strokeWidth={3} initial={false} animate={{ cx: 220 + avg * 220 }} />
        <Label x={440} y={-14} size={20} anchor="end" color={pointsColor(avg)}>
          {signed(shownAvg)}
        </Label>
      </g>
    </g>
  );
}

function Stage({ step, trial, friend }: { step: number; trial: number; friend: number }) {
  const lead = contrast(P_TILDE, R1_REPORTS[friend], trial);
  return (
    <svg viewBox="0 0 600 600">
      <AnimatePresence mode="wait">
        <motion.g key={step} initial={{ opacity: 0 }} animate={{ opacity: 1 }} exit={{ opacity: 0 }} transition={{ duration: 0.3 }}>
          {step === 0 && (
            <g>
              <Board p={R1_P} x={110} y={50} w={380} h={320} showFair showHot />
              <Avatar look={KIDS[MIA].look} x={190} y={500} size={120} mood="think" />
              <Bubble x={270} y={410} w={270} h={70} lines={["Aquarium is HOT.", "Beach and Castle are NOT."]} tail="left" size={18} />
            </g>
          )}
          {step === 1 && <Compare trial={trial} friend={friend} />}
          {step === 2 && <CubeChart lead={lead} />}
          {step === 3 && <AllFriends trial={trial} />}
          {step === 4 && (
            <g>
              <Label x={300} y={60} size={22}>
                Points for every card Mia could write
              </Label>
              <DistBars values={SCORES} mode="score" x={30} y={100} w={540} h={400} heart={MIA_HEART} labelSize={17} cardW={52} />
              <Avatar look={KIDS[MIA].look} x={70} y={560} size={60} mood="wow" />
              <Label x={110} y={566} size={18} anchor="start" weight={500}>
                Her heart card ties for the lowest score!
              </Label>
            </g>
          )}
        </motion.g>
      </AnimatePresence>
    </svg>
  );
}

function CardPicker({ value, onPick }: { value: number; onPick: (k: number) => void }) {
  return (
    <div className="picker" role="group" aria-label="Pick a card for Mia to try">
      {PERMS.map((_, k) => (
        <button key={k} className="pick" aria-pressed={value === k} onClick={() => onPick(k)} aria-label={rankName(k)} title={rankName(k)}>
          <svg viewBox="-16 -21 32 42" width={24} height={32} aria-hidden>
            <MiniCard k={k} w={26} />
          </svg>
        </button>
      ))}
    </div>
  );
}

export function Ch4Points() {
  const [trial, setTrial] = useState(permIndex("ABC"));
  const [friend, setFriend] = useState(PICK_FRIENDS[0]);
  const steps = [
    <>
      <h3>Mia reads the board</h3>
      <p>
        The <BoardTag /> is posted for everyone to see.
      </p>
      <p>
        A fair share would be one third each. <Dest c={0} /> got way more than its fair third, so it's <b>HOT</b>{" "}
        (+0.67). <Dest c={1} /> and <Dest c={2} /> got less, so they're <b>NOT</b> (−0.33 each).
      </p>
      <Grownups>
        The board is the published signal p<sub>t</sub>; HOT/NOT is the centred signal p − ⅓.
      </Grownups>
    </>,
    <>
      <h3>A little game against one friend</h3>
      <p>
        For each card she <i>could</i> write, Mia asks: <b>“Would this card be more in tune with the board than my
        friend's card?”</b>
      </p>
      <p>
        She compares her card with her friend's, place by place. Putting a HOT place <b>higher than her friend
        did</b> wins points. Putting a NOT place <b>lower</b> wins points too. The total, halved, is her{" "}
        <b>lead</b>. It runs from −1 to +1.
      </p>
      <div className="control">
        <div className="small muted">Mia tries the card:</div>
        <CardPicker value={trial} onPick={setTrial} />
        <div className="small muted" style={{ marginTop: 8 }}>
          against the ballot of:
        </div>
        <div className="picker">
          {PICK_FRIENDS.map((f) => (
            <button key={f} className="btn btn-sm" aria-pressed={friend === f} onClick={() => setFriend(f)}>
              {KIDS[f].name}
            </button>
          ))}
        </div>
      </div>
    </>,
    <>
      <h3>Big leads count a LOT more</h3>
      <p>
        Points = lead × lead × lead (that's <b>cubed</b>). A half lead is worth only ⅛ of a point, but a full lead is
        worth a whole point.
      </p>
      <p>So being a <i>little</i> ahead hardly matters. Being <i>way</i> ahead matters a lot.</p>
      <Grownups>
        Why cube? With a straight line, the friends' ballots cancel out exactly and only the board matters. The odd,
        curved f(x) = x³ keeps the friends in the story.
      </Grownups>
    </>,
    <>
      <h3>Play the game with every friend</h3>
      <p>
        Mia plays this mini-game against all 14 friends and takes the <b>average</b>. For example, with{" "}
        <Rank k={permIndex("ABC")} />, she's way ahead of the 6 Beach-lovers (+1 each) and level with the 8 who already put Aquarium first (0
        each): 6 ÷ 14 ≈ +0.43.
      </p>
      <div className="control">
        <div className="small muted">Try another card:</div>
        <CardPicker value={trial} onPick={setTrial} />
      </div>
    </>,
    <>
      <h3>Every card gets a score</h3>
      <p>
        Mia scores all six cards the same way. Cards with <Dest c={0} /> on top score best. Her own <Heart />,{" "}
        <Rank k={MIA_HEART} />, ties for the <b>lowest</b> score, because it puts the HOT place last.
      </p>
      <p>So should she just switch? Not so fast. Three very human habits decide what happens next.</p>
      <Grownups>
        Score of card σ: s<sub>i</sub>(σ) = average over friends j of f(⟨p − ⅓, r<sub>j</sub> − r<sub>σ</sub>⟩ / 2),
        with f(x) = x³ and r the place of each destination (0 = top). This is the degree- and rank-normalized
        cubic score of the gtiv package. Here every kid watches everyone else (a complete graph).
      </Grownups>
    </>,
  ];
  return (
    <Chapter id="points" num="Part 4" title="Mia reads the board and compares notes">
      <Scrolly
        steps={steps}
        stage={(s) => <Stage step={s} trial={trial} friend={friend} />}
        label="How Mia scores every card against her friends' ballots"
      />
    </Chapter>
  );
}
