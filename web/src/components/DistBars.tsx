/** Six bars, one per ballot card, with the cards drawn underneath. (x, y) is the top-left. */
import { motion } from "motion/react";
import { N_PERMS } from "../model/rankings";
import { pctSoft, signed } from "../lib/format";
import { useTweened } from "../lib/useTweened";
import { CARD_RATIO, RankCard } from "./RankCard";

const INK = "#23213a";
const GOOD = "#1f9d6b";
const BAD = "#d4495a";

function Bar({
  v,
  mode,
  cx,
  barW,
  top,
  height,
  max,
  color,
  bold,
  labelSize,
  showLabel,
}: {
  v: number;
  mode: "prob" | "score";
  cx: number;
  barW: number;
  top: number;
  height: number;
  max: number;
  color: string;
  bold: boolean;
  labelSize: number;
  showLabel: boolean;
}) {
  const shown = useTweened(v);
  if (mode === "prob") {
    const base = top + height;
    const h = Math.max(1.5, (Math.min(v, max) / max) * (height - labelSize - 6));
    const labelY = base - (Math.min(shown, max) / max) * (height - labelSize - 6) - 7;
    return (
      <g>
        <rect x={cx - barW / 2} y={top} width={barW} height={height} rx={6} fill={INK} opacity={0.04} />
        <motion.rect
          x={cx - barW / 2}
          width={barW}
          rx={6}
          fill={color}
          initial={false}
          animate={{ y: base - h, height: h }}
          transition={{ type: "spring", stiffness: 130, damping: 20 }}
        />
        {showLabel && <text
          x={cx}
          y={labelY}
          textAnchor="middle"
          fontSize={labelSize}
          fontWeight={bold ? 700 : 600}
          fill={INK}
        >
          {pctSoft(shown)}
        </text>}
      </g>
    );
  }
  const mid = top + height / 2;
  const half = height / 2 - labelSize - 4;
  const h = Math.max(1.5, Math.abs(v / max) * half);
  const pos = v >= 0;
  return (
    <g>
      <rect x={cx - barW / 2} y={top} width={barW} height={height} rx={6} fill={INK} opacity={0.04} />
      <motion.rect
        x={cx - barW / 2}
        width={barW}
        rx={5}
        fill={pos ? GOOD : BAD}
        initial={false}
        animate={{ y: pos ? mid - h : mid, height: h }}
        transition={{ type: "spring", stiffness: 130, damping: 20 }}
      />
      {showLabel && <text
        x={cx}
        y={pos ? mid - h - 7 : mid + h + labelSize + 2}
        textAnchor="middle"
        fontSize={labelSize}
        fontWeight={bold ? 700 : 600}
        fill={pos ? "#137451" : "#a8293a"}
      >
        {signed(shown)}
      </text>}
    </g>
  );
}

export function DistBars({
  values,
  x = 0,
  y = 0,
  w = 420,
  h = 220,
  mode = "prob",
  color = "#23213a",
  colors,
  max,
  heart,
  highlight,
  cardW,
  title,
  titleColor,
  labelSize = 15,
  order,
  showLabels = true,
  showCards = true,
}: {
  values: readonly number[];
  x?: number;
  y?: number;
  w?: number;
  h?: number;
  mode?: "prob" | "score";
  color?: string;
  colors?: readonly string[];
  max?: number;
  heart?: number;
  highlight?: number;
  cardW?: number;
  title?: string;
  titleColor?: string;
  labelSize?: number;
  order?: readonly number[];
  showLabels?: boolean;
  showCards?: boolean;
}) {
  const slots = order ?? Array.from({ length: N_PERMS }, (_, k) => k);
  const slotW = w / slots.length;
  const cw = cardW ?? Math.min(46, slotW * 0.7);
  const ch = showCards ? cw * CARD_RATIO : -12;
  const titleH = title ? 26 : 0;
  const barTop = titleH;
  const barH = h - ch - 12 - titleH;
  const lab = showLabels ? labelSize : 0;
  const barW = Math.min(slotW * 0.62, 44);
  const top = max ?? (mode === "prob" ? 1 : 1);
  return (
    <g transform={`translate(${x} ${y})`}>
      {title && (
        <text x={0} y={17} fontSize={17} fontWeight={600} fill={titleColor ?? INK}>
          {title}
        </text>
      )}
      {mode === "score" && (
        <line x1={0} x2={w} y1={barTop + barH / 2} y2={barTop + barH / 2} stroke={INK} strokeWidth={1.5} opacity={0.35} />
      )}
      {slots.map((k, i) => {
        const cx = slotW * (i + 0.5);
        return (
          <g key={k}>
            <Bar
              v={values[k]}
              mode={mode}
              cx={cx}
              barW={barW}
              top={barTop}
              height={barH}
              max={top}
              color={colors?.[k] ?? color}
              bold={highlight === k}
              labelSize={lab}
              showLabel={showLabels}
            />
            {showCards && <RankCard
              k={k}
              x={cx}
              y={barTop + barH + 10 + ch / 2}
              w={cw}
              heart={heart === k}
              outline={highlight === k ? INK : undefined}
              shadow={false}
            />}
          </g>
        );
      })}
    </g>
  );
}
