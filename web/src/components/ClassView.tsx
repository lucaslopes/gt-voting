/** The whole class at a glance: who they are, their heart, their ballot, and what their jar holds. */
import { motion } from "motion/react";
import { DEST, kidFor } from "../cast";
import { PERMS } from "../model/rankings";
import type { Sim } from "../model/simulation";
import { Avatar } from "./Avatar";
import { HeartGlyph } from "./icons";
import { MiniCard } from "./RankCard";

const INK = "#23213a";

/** Share of the jar that puts each destination first. */
export function firstChoiceShares(x: readonly number[]) {
  const s = [0, 0, 0];
  x.forEach((v, k) => (s[PERMS[k][0]] += v));
  return s;
}

function JarBar({ x, w, y }: { x: readonly number[]; w: number; y: number }) {
  const s = firstChoiceShares(x);
  let acc = -w / 2;
  return (
    <g>
      <rect x={-w / 2} y={y} width={w} height={9} rx={4.5} fill="#efebe4" />
      {s.map((v, c) => {
        const x0 = acc;
        acc += v * w;
        return (
          <motion.rect
            key={c}
            y={y}
            height={9}
            fill={DEST[c].color}
            initial={false}
            animate={{ x: x0, width: Math.max(0, v * w) }}
            transition={{ duration: 0.25 }}
          />
        );
      })}
      <rect x={-w / 2} y={y} width={w} height={9} rx={4.5} fill="none" stroke={INK} strokeOpacity={0.25} />
    </g>
  );
}

export function ClassView({
  sim,
  x = 0,
  y = 0,
  cols = 5,
  cellW = 116,
  cellH = 112,
  selected,
  onSelect,
  highlight,
}: {
  sim: Sim;
  x?: number;
  y?: number;
  cols?: number;
  cellW?: number;
  cellH?: number;
  selected?: number;
  onSelect?: (i: number) => void;
  highlight?: number;
}) {
  const reports = sim.last?.reports ?? sim.hearts;
  return (
    <g transform={`translate(${x} ${y})`}>
      {sim.hearts.map((heart, i) => {
        const cx = (i % cols) * cellW + cellW / 2;
        const cy = Math.floor(i / cols) * cellH;
        const kid = kidFor(i);
        const ballot = reports[i];
        const strayed = ballot !== heart;
        const isSel = selected === i;
        return (
          <g
            key={i}
            transform={`translate(${cx} ${cy})`}
            onClick={onSelect ? () => onSelect(i) : undefined}
            onKeyDown={onSelect ? (e) => (e.key === "Enter" || e.key === " ") && onSelect(i) : undefined}
            role={onSelect ? "button" : undefined}
            tabIndex={onSelect ? 0 : undefined}
            aria-label={onSelect ? `Show ${kid.name}'s decision` : undefined}
            aria-pressed={onSelect ? isSel : undefined}
            style={{ cursor: onSelect ? "pointer" : undefined, outline: "none" }}
            className={onSelect ? "kid-cell" : undefined}
          >
            {isSel && <rect x={-cellW / 2 + 4} y={2} width={cellW - 8} height={cellH - 6} rx={14} fill="#fff" stroke={INK} strokeWidth={2.5} />}
            {!isSel && highlight === i && <rect x={-cellW / 2 + 4} y={2} width={cellW - 8} height={cellH - 6} rx={14} fill="#fff7ea" />}
            <Avatar look={kid.look} x={0} y={25} size={40} mood={strayed ? "wow" : "happy"} />
            <text y={60} textAnchor="middle" fontSize={13} fontWeight={600} fill={INK}>
              {kid.name}
            </text>
            <g transform="translate(-34 77) scale(0.12)">
              <HeartGlyph />
            </g>
            <g transform="translate(-17 77)">
              <MiniCard k={heart} w={15} />
            </g>
            <text x={2} y={81} textAnchor="middle" fontSize={13} fill="#7d7a91">
              →
            </text>
            <g transform="translate(21 77)">
              <motion.g
                key={`${i}-${sim.t}`}
                initial={{ scale: 0.6, opacity: 0.4 }}
                animate={{ scale: 1, opacity: 1 }}
                transition={{ duration: 0.25 }}
              >
                <MiniCard k={ballot} w={15} outline={strayed ? INK : undefined} />
              </motion.g>
            </g>
            <JarBar x={sim.x[i]} w={Math.min(cellW - 30, 86)} y={93} />
          </g>
        );
      })}
    </g>
  );
}

/** Recent rounds as a ribbon: each sliver is one round's scoreboard. */
export function Timeline({ sim, x = 0, y = 0, w = 560, h = 22, slots = 120 }: { sim: Sim; x?: number; y?: number; w?: number; h?: number; slots?: number }) {
  const rows = sim.timeline.slice(-slots);
  const sw = w / slots;
  return (
    <g transform={`translate(${x} ${y})`}>
      <rect width={w} height={h} rx={5} fill="#efebe4" />
      {rows.map((r, i) => {
        let acc = 0;
        return (
          <g key={r.t} transform={`translate(${(slots - rows.length + i) * sw} 0)`}>
            {r.p.map((p, c) => {
              const y0 = acc;
              acc += p * h;
              return p > 0 ? <rect key={c} y={y0} width={sw + 0.3} height={p * h} fill={DEST[c].color} /> : null;
            })}
            {r.winner === 2 && <circle cx={sw / 2} cy={-6} r={3} fill={DEST[2].color} />}
          </g>
        );
      })}
    </g>
  );
}
