/** A ballot card: one complete ranking, first choice on top. (x, y) is the card centre. */
import { DEST } from "../cast";
import { PERMS } from "../model/rankings";
import { CandBadge, HeartGlyph } from "./icons";

const INK = "#23213a";

export const CARD_RATIO = 1.42;

export function RankCard({
  k,
  x = 0,
  y = 0,
  w = 60,
  outline,
  heart = false,
  dim = false,
  numbers = true,
  shadow = true,
}: {
  k: number;
  x?: number;
  y?: number;
  w?: number;
  outline?: string;
  heart?: boolean;
  dim?: boolean;
  numbers?: boolean;
  shadow?: boolean;
}) {
  const h = w * CARD_RATIO;
  const pad = w * 0.1;
  const rowH = (h - 2 * pad) / 3;
  return (
    <g transform={`translate(${x - w / 2} ${y - h / 2})`} opacity={dim ? 0.35 : 1}>
      {shadow && <rect x={2} y={3} width={w} height={h} rx={w * 0.16} fill={INK} opacity={0.12} />}
      <rect
        width={w}
        height={h}
        rx={w * 0.16}
        fill="#fff"
        stroke={outline ?? INK}
        strokeWidth={outline ? Math.max(3, w * 0.06) : Math.max(1.5, w * 0.03)}
      />
      {PERMS[k].map((c, pos) => {
        const cy = pad + rowH * (pos + 0.5);
        return (
          <g key={pos}>
            {numbers && (
              <text
                x={w * 0.2}
                y={cy}
                dy="0.36em"
                textAnchor="middle"
                fontSize={w * 0.2}
                fontWeight={600}
                fill="#9a97ad"
              >
                {pos + 1}
              </text>
            )}
            <CandBadge c={c} x={numbers ? w * 0.6 : w / 2} y={cy} r={rowH * (pos === 0 ? 0.44 : 0.38)} ring={false} />
          </g>
        );
      })}
      {heart && (
        <g transform={`translate(${w - w * 0.04} ${w * 0.04}) scale(${w * 0.0042})`}>
          <circle r={34} fill="#fff" />
          <g transform="scale(0.7)">
            <HeartGlyph />
          </g>
        </g>
      )}
    </g>
  );
}

function topRounded(x: number, y: number, w: number, h: number, r: number) {
  return `M ${x} ${y + h} V ${y + r} A ${r} ${r} 0 0 1 ${x + r} ${y} H ${x + w - r} A ${r} ${r} 0 0 1 ${x + w} ${y + r} V ${y + h} Z`;
}
function bottomRounded(x: number, y: number, w: number, h: number, r: number) {
  return `M ${x} ${y} H ${x + w} V ${y + h - r} A ${r} ${r} 0 0 1 ${x + w - r} ${y + h} H ${x + r} A ${r} ${r} 0 0 1 ${x} ${y + h - r} Z`;
}

/** A tiny striped card (top stripe = first choice), centred on (0, 0). */
export function MiniCard({ k, w = 22, outline }: { k: number; w?: number; outline?: string }) {
  const h = w * CARD_RATIO;
  const r = w * 0.2;
  // The first choice gets half the card so the favourite colour reads at a glance.
  const s1 = h * 0.5;
  const s2 = h * 0.27;
  const [a, b, c] = PERMS[k];
  return (
    <g transform={`translate(${-w / 2} ${-h / 2})`}>
      <path d={topRounded(0, 0, w, s1 + 0.5, r)} fill={DEST[a].color} />
      <rect x={0} y={s1} width={w} height={s2 + 0.5} fill={DEST[b].color} />
      <path d={bottomRounded(0, s1 + s2, w, h - s1 - s2, r)} fill={DEST[c].color} />
      <rect
        width={w}
        height={h}
        rx={r}
        fill="none"
        stroke={outline ?? "#fff"}
        strokeWidth={outline ? 2.5 : 1.5}
      />
    </g>
  );
}
