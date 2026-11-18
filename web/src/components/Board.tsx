/** The class scoreboard: the published maximal lottery, drawn as a chalkboard. (x, y) is the top-left. */
import { motion } from "motion/react";
import { DEST } from "../cast";
import { useTweened } from "../lib/useTweened";
import { CandBadge } from "./icons";

const CHALK = "#f4f1e6";

function Col({
  c,
  p,
  cx,
  base,
  maxH,
  barW,
  showHot,
}: {
  c: number;
  p: number;
  cx: number;
  base: number;
  maxH: number;
  barW: number;
  showHot: boolean;
}) {
  const shown = useTweened(p);
  const h = Math.max(2, p * maxH);
  const tilde = p - 1 / 3;
  const hot = tilde > 1e-9;
  return (
    <g>
      <motion.rect
        x={cx - barW / 2}
        width={barW}
        rx={6}
        fill={DEST[c].color}
        initial={false}
        animate={{ y: base - h, height: h }}
        transition={{ type: "spring", stiffness: 120, damping: 20 }}
      />
      <text x={cx} y={base - shown * maxH - 10} textAnchor="middle" fontSize={22} fontWeight={600} fill={CHALK}>
        {Math.round(shown * 100)}%
      </text>
      <CandBadge c={c} x={cx} y={base + 24} r={17} />
      {showHot && (
        <motion.g initial={{ opacity: 0, scale: 0.6 }} animate={{ opacity: 1, scale: 1 }} transition={{ delay: 0.15 * c }}>
          <rect
            x={cx - 34}
            y={base + 46}
            width={68}
            height={24}
            rx={12}
            fill={hot ? "#ff7a45" : "#9fc5e8"}
          />
          <text x={cx} y={base + 63} textAnchor="middle" fontSize={14.5} fontWeight={600} fill={hot ? "#fff" : "#16324f"}>
            {hot ? "HOT" : "NOT"} {tilde >= 0 ? "+" : "−"}
            {Math.abs(tilde).toFixed(2)}
          </text>
        </motion.g>
      )}
    </g>
  );
}

export function Board({
  p,
  x = 0,
  y = 0,
  w = 300,
  h = 240,
  showFair = false,
  showHot = false,
  title = "SCOREBOARD",
  placeholder,
}: {
  p: readonly number[];
  x?: number;
  y?: number;
  w?: number;
  h?: number;
  showFair?: boolean;
  showHot?: boolean;
  title?: string;
  placeholder?: string;
}) {
  const extra = showHot ? 30 : 0;
  const base = h - 62 - extra;
  const maxH = base - 82 - (showFair ? 14 : 0);
  const barW = w * 0.16;
  const fairY = base - maxH / 3;
  return (
    <g transform={`translate(${x} ${y})`}>
      <rect x={3} y={5} width={w} height={h} rx={18} fill="#23213a" opacity={0.15} />
      <rect width={w} height={h} rx={18} fill="#c98b52" stroke="#23213a" strokeWidth={3} />
      <rect x={10} y={10} width={w - 20} height={h - 20} rx={11} fill="#2f5247" />
      <text x={w / 2} y={38} textAnchor="middle" fontSize={15} fontWeight={600} letterSpacing="0.16em" fill={CHALK} opacity={0.85}>
        {title}
      </text>
      {showFair && (
        <g>
          <line x1={22} x2={w - 22} y1={fairY} y2={fairY} stroke={CHALK} strokeWidth={2} strokeDasharray="6 6" opacity={0.75} />
          <line x1={w / 2 - 58} x2={w / 2 - 36} y1={56} y2={56} stroke={CHALK} strokeWidth={2} strokeDasharray="5 4" opacity={0.75} />
          <text x={w / 2 - 30} y={60} fontSize={12.5} fill={CHALK} opacity={0.9}>
            fair share ⅓
          </text>
        </g>
      )}
      {placeholder ? (
        <text x={w / 2} y={h / 2 + 8} textAnchor="middle" fontSize={22} fontWeight={500} fill={CHALK} opacity={0.8}>
          {placeholder}
        </text>
      ) : (
        [0, 1, 2].map((c) => (
          <Col key={c} c={c} p={p[c]} cx={w * (0.22 + 0.28 * c)} base={base} maxH={maxH} barW={barW} showHot={showHot} />
        ))
      )}
    </g>
  );
}
