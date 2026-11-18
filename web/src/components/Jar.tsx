/** A glass jar of ballot cards. Drawn at width 220 around (0, 0); use ``scale`` to resize. */
import { AnimatePresence, motion } from "motion/react";
import type { Token } from "../lib/tokens";
import { MiniCard } from "./RankCard";

const INK = "#23213a";
const COLS = 5;

export const JAR_BODY =
  "M -62 -112 Q -62 -100 -90 -88 Q -110 -78 -110 -50 V 120 Q -110 146 -84 146 H 84 Q 110 146 110 120 V -50 Q 110 -78 90 -88 Q 62 -100 62 -112 Z";

function hash(id: string) {
  let h = 0;
  for (let i = 0; i < id.length; i++) h = (h * 31 + id.charCodeAt(i)) | 0;
  return h;
}

export function slotOf(i: number) {
  const col = i % COLS;
  const row = Math.floor(i / COLS);
  const stagger = row % 2 ? 6 : -6;
  return { x: -72 + col * 36 + stagger, y: 108 - row * 44 };
}

export function sortTokens(tokens: readonly Token[], first?: number) {
  return [...tokens].sort((a, b) => {
    const ra = a.k === first ? -1 : a.k;
    const rb = b.k === first ? -1 : b.k;
    return ra - rb || (a.id < b.id ? -1 : 1);
  });
}

export function Jar({
  tokens,
  x = 0,
  y = 0,
  scale = 1,
  first,
  enterFrom = { x: 0, y: -260 },
  exitTo = { x: 0, y: -260 },
  outlineIds,
  label,
  lidOpen = false,
}: {
  tokens: readonly Token[];
  x?: number;
  y?: number;
  scale?: number;
  /** card index to stack at the bottom (usually the heart ranking) */
  first?: number;
  enterFrom?: { x: number; y: number };
  exitTo?: { x: number; y: number };
  outlineIds?: Set<string>;
  label?: string;
  lidOpen?: boolean;
}) {
  const ordered = sortTokens(tokens, first);
  return (
    <g transform={`translate(${x} ${y}) scale(${scale})`}>
      <ellipse cx={0} cy={150} rx={118} ry={12} fill={INK} opacity={0.08} />
      <path d={JAR_BODY} fill="#eef7ff" stroke="none" />
      <AnimatePresence initial={false}>
        {ordered.map((t, i) => {
          const s = slotOf(i);
          const rot = ((hash(t.id) % 9) - 4) * 1.6;
          return (
            <motion.g
              key={t.id}
              initial={{ x: enterFrom.x, y: enterFrom.y, opacity: 0, rotate: rot * 3 }}
              animate={{ x: s.x, y: s.y, opacity: 1, rotate: rot }}
              exit={{ x: exitTo.x, y: exitTo.y, opacity: 0, transition: { duration: 0.7, ease: "easeIn" } }}
              transition={{ type: "spring", stiffness: 140, damping: 18, delay: 0.015 * i }}
            >
              <MiniCard k={t.k} w={28} outline={outlineIds?.has(t.id) ? INK : undefined} />
            </motion.g>
          );
        })}
      </AnimatePresence>
      <path d={JAR_BODY} fill="rgba(214, 236, 255, 0.28)" stroke={INK} strokeWidth={3.5} strokeLinejoin="round" />
      <path d="M -94 -46 V 96" stroke="#fff" strokeWidth={8} strokeLinecap="round" opacity={0.7} />
      <path d="M -94 108 V 118" stroke="#fff" strokeWidth={8} strokeLinecap="round" opacity={0.7} />
      <motion.g animate={{ rotate: lidOpen ? -24 : 0, x: lidOpen ? -30 : 0, y: lidOpen ? -26 : 0 }}>
        <rect x={-72} y={-140} width={144} height={28} rx={9} fill="#3b3858" stroke={INK} strokeWidth={3} />
        <rect x={-60} y={-133} width={70} height={6} rx={3} fill="#fff" opacity={0.25} />
      </motion.g>
      {label && (
        <text y={184} textAnchor="middle" fontSize={22} fontWeight={600} fill={INK}>
          {label}
        </text>
      )}
    </g>
  );
}
