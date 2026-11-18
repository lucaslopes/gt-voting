/** Head-to-head duels between the three destinations. (x, y) is the top-left. */
import { motion } from "motion/react";
import { DEST } from "../cast";
import { useTweened } from "../lib/useTweened";
import { CandBadge, Crown } from "./icons";

const INK = "#23213a";
export const DUELS: [number, number][] = [
  [0, 1],
  [0, 2],
  [1, 2],
];

function Duel({
  a,
  b,
  wa,
  wb,
  y,
  w,
  show,
  delay,
}: {
  a: number;
  b: number;
  wa: number;
  wb: number;
  y: number;
  w: number;
  show: boolean;
  delay: number;
}) {
  const n = wa + wb || 1;
  const ta = useTweened(show ? wa : 0, 0.9);
  const tb = useTweened(show ? wb : 0, 0.9);
  const barX = 46;
  const barW = w - 92;
  const split = barW * (show ? wa / n : 0.5);
  const winner = wa > wb ? a : b;
  return (
    <g transform={`translate(0 ${y})`}>
      <CandBadge c={a} x={20} y={0} r={20} />
      <CandBadge c={b} x={w - 20} y={0} r={20} />
      <rect x={barX} y={-13} width={barW} height={26} rx={13} fill={INK} opacity={0.07} />
      <motion.rect
        x={barX}
        y={-13}
        height={26}
        rx={13}
        fill={DEST[a].color}
        initial={false}
        animate={{ width: show ? split : 0 }}
        transition={{ duration: 0.9, delay, ease: [0.22, 1, 0.36, 1] }}
      />
      <motion.rect
        y={-13}
        height={26}
        rx={13}
        fill={DEST[b].color}
        initial={false}
        animate={{ x: show ? barX + split : barX + barW, width: show ? barW - split : 0 }}
        transition={{ duration: 0.9, delay, ease: [0.22, 1, 0.36, 1] }}
      />
      <line x1={barX + barW / 2} x2={barX + barW / 2} y1={-18} y2={18} stroke={INK} strokeWidth={2} strokeDasharray="3 3" opacity={0.5} />
      <text x={barX + 14} y={6} fontSize={18} fontWeight={700} fill="#fff">
        {Math.round(ta)}
      </text>
      <text x={barX + barW - 14} y={6} textAnchor="end" fontSize={18} fontWeight={700} fill="#fff">
        {Math.round(tb)}
      </text>
      {show && (
        <motion.g
          initial={{ opacity: 0, y: 8 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ delay: delay + 0.8 }}
        >
          <Crown x={winner === a ? 20 : w - 20} y={-30} s={0.9} />
        </motion.g>
      )}
    </g>
  );
}

export function DuelBoard({
  tallies,
  x = 0,
  y = 0,
  w = 380,
  gap = 74,
  show = true,
}: {
  tallies: number[][];
  x?: number;
  y?: number;
  w?: number;
  gap?: number;
  show?: boolean;
}) {
  return (
    <g transform={`translate(${x} ${y})`}>
      {DUELS.map(([a, b], i) => (
        <Duel key={i} a={a} b={b} wa={tallies[a][b]} wb={tallies[b][a]} y={i * gap} w={w} show={show} delay={i * 0.35} />
      ))}
    </g>
  );
}
