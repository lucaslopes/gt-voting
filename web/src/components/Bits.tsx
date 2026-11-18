/** Small SVG helpers: speech bubbles, arrows, pills, a ballot box. */
import { motion } from "motion/react";
import { useId, type ReactNode } from "react";

const INK = "#23213a";

export function Bubble({
  x,
  y,
  w,
  h = 46,
  lines,
  tail = "down",
  size = 18,
  fill = "#fff",
}: {
  x: number;
  y: number;
  w: number;
  h?: number;
  lines: string[];
  tail?: "down" | "left" | "right" | "none";
  size?: number;
  fill?: string;
}) {
  const t =
    tail === "down"
      ? `M ${w * 0.3} ${h - 1} L ${w * 0.22} ${h + 16} L ${w * 0.44} ${h - 1} Z`
      : tail === "left"
        ? `M 1 ${h * 0.45} L -16 ${h * 0.75} L 1 ${h * 0.7} Z`
        : tail === "right"
          ? `M ${w - 1} ${h * 0.45} L ${w + 16} ${h * 0.75} L ${w - 1} ${h * 0.7} Z`
          : "";
  return (
    <g transform={`translate(${x} ${y})`}>
      <rect width={w} height={h} rx={16} fill={fill} stroke={INK} strokeWidth={2.5} />
      {t && <path d={t} fill={fill} stroke={INK} strokeWidth={2.5} strokeLinejoin="round" />}
      {t && <rect x={tail === "down" ? w * 0.22 : tail === "left" ? 2 : w - 6} y={tail === "down" ? h - 6 : h * 0.4} width={tail === "down" ? w * 0.24 : 4} height={tail === "down" ? 5 : h * 0.36} fill={fill} />}
      {lines.map((l, i) => (
        <text
          key={i}
          x={w / 2}
          y={h / 2 + (i - (lines.length - 1) / 2) * size * 1.25}
          dy="0.35em"
          textAnchor="middle"
          fontSize={size}
          fontWeight={500}
          fill={INK}
        >
          {l}
        </text>
      ))}
    </g>
  );
}

export function Arrow({
  d,
  color = INK,
  width = 3,
  dash,
  delay = 0,
  draw = true,
}: {
  d: string;
  color?: string;
  width?: number;
  dash?: string;
  delay?: number;
  draw?: boolean;
}) {
  const id = useId().replace(/:/g, "");
  return (
    <g>
      <defs>
        <marker id={`ah${id}`} viewBox="0 0 10 10" refX="7" refY="5" markerWidth="5" markerHeight="5" orient="auto-start-reverse">
          <path d="M 0 0 L 10 5 L 0 10 z" fill={color} />
        </marker>
      </defs>
      <motion.path
        d={d}
        fill="none"
        stroke={color}
        strokeWidth={width}
        strokeLinecap="round"
        strokeDasharray={dash}
        markerEnd={`url(#ah${id})`}
        initial={draw ? { pathLength: 0, opacity: 0 } : false}
        animate={{ pathLength: 1, opacity: 1 }}
        transition={{ duration: 0.7, delay, ease: "easeOut" }}
      />
    </g>
  );
}

export function Pill({
  x,
  y,
  text,
  fill = "#fff",
  color = INK,
  size = 15,
  pad = 12,
  stroke,
  anchor = "middle",
}: {
  x: number;
  y: number;
  text: string;
  fill?: string;
  color?: string;
  size?: number;
  pad?: number;
  stroke?: string;
  anchor?: "start" | "middle" | "end";
}) {
  const w = text.length * size * 0.56 + pad * 2;
  const h = size * 1.75;
  const left = anchor === "middle" ? x - w / 2 : anchor === "start" ? x : x - w;
  return (
    <g>
      <rect x={left} y={y - h / 2} width={w} height={h} rx={h / 2} fill={fill} stroke={stroke} strokeWidth={stroke ? 2 : 0} />
      <text x={left + w / 2} y={y} dy="0.36em" textAnchor="middle" fontSize={size} fontWeight={600} fill={color}>
        {text}
      </text>
    </g>
  );
}

export function Label({
  x,
  y,
  children,
  size = 18,
  weight = 600,
  color = INK,
  anchor = "middle",
  opacity = 1,
}: {
  x: number;
  y: number;
  children: ReactNode;
  size?: number;
  weight?: number;
  color?: string;
  anchor?: "start" | "middle" | "end";
  opacity?: number;
}) {
  return (
    <text x={x} y={y} textAnchor={anchor} fontSize={size} fontWeight={weight} fill={color} opacity={opacity}>
      {children}
    </text>
  );
}

/** A ballot box centred on (0, 0), about 160 wide. */
export function BallotBox({ x = 0, y = 0, s = 1 }: { x?: number; y?: number; s?: number }) {
  return (
    <g transform={`translate(${x} ${y}) scale(${s})`}>
      <ellipse cx={0} cy={78} rx={92} ry={9} fill={INK} opacity={0.1} />
      <path d="M -80 -20 L 80 -20 L 70 74 L -70 74 Z" fill="#7aa6d9" stroke={INK} strokeWidth={3} strokeLinejoin="round" />
      <path d="M -88 -36 L 88 -36 L 80 -20 L -80 -20 Z" fill="#9cc0ea" stroke={INK} strokeWidth={3} strokeLinejoin="round" />
      <rect x={-40} y={-31} width={80} height={7} rx={3.5} fill={INK} />
      <text x={0} y={34} textAnchor="middle" fontSize={22} fontWeight={700} fill="#fff" letterSpacing="0.08em">
        VOTE
      </text>
    </g>
  );
}
