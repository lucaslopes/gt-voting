/** Hand-drawn style SVG glyphs. Every glyph is drawn in a 100x100 box centred on (0, 0). */
import type { SVGProps } from "react";
import { DEST, PARAMS, type ParamKey } from "../cast";

const INK = "#23213a";

function Fish({ fg }: { fg: string }) {
  return (
    <g>
      <path d="M -22 0 C -8 -24, 22 -22, 34 0 C 22 22, -8 24, -22 0 Z" fill={fg} />
      <path d="M -20 0 L -40 -18 L -34 0 L -40 18 Z" fill={fg} />
      <path d="M 2 -15 Q 8 -27 18 -17" fill="none" stroke={fg} strokeWidth={6} strokeLinecap="round" />
      <circle cx={19} cy={-4} r={4.5} fill={INK} />
      <path d="M 4 -9 Q 9 0 4 9" fill="none" stroke={INK} strokeOpacity={0.35} strokeWidth={3} strokeLinecap="round" />
      <circle cx={38} cy={-24} r={4} fill="none" stroke={fg} strokeWidth={3} />
      <circle cx={44} cy={-36} r={2.6} fill="none" stroke={fg} strokeWidth={2.6} />
    </g>
  );
}

function Umbrella({ fg, tint }: { fg: string; tint: string }) {
  return (
    <g>
      <path d="M -4 -24 L 6 34" stroke={fg} strokeWidth={6} strokeLinecap="round" />
      <path
        d="M -40 4 A 38 32 0 0 1 32 -14 Q 22 -6 12 -6 Q 4 4 -10 2 Q -20 10 -40 4 Z"
        fill={fg}
        transform="rotate(10)"
      />
      <path d="M -3 -27 Q -16 -12 -14 6" fill="none" stroke={tint} strokeWidth={5} transform="rotate(10)" />
      <path d="M -3 -27 Q 10 -14 12 -4" fill="none" stroke={tint} strokeWidth={5} transform="rotate(10)" />
      <path d="M -42 36 Q -22 26 0 34 T 42 32" fill="none" stroke={fg} strokeWidth={6} strokeLinecap="round" />
    </g>
  );
}

function Castle({ fg }: { fg: string }) {
  return (
    <g>
      <path
        d="M -36 34 V -14 H -30 V -20 H -24 V -14 H -18 V -20 H -12 V -2 H 12 V -20 H 18 V -14 H 24 V -20 H 30 V -14 H 36 V 34 Z"
        fill={fg}
      />
      <path d="M -8 34 V 20 A 8 8 0 0 1 8 20 V 34 Z" fill={INK} fillOpacity={0.55} />
      <rect x={-27} y={-2} width={6} height={10} rx={3} fill={INK} fillOpacity={0.45} />
      <rect x={21} y={-2} width={6} height={10} rx={3} fill={INK} fillOpacity={0.45} />
      <path d="M 0 -2 V -38" stroke={fg} strokeWidth={4} strokeLinecap="round" />
      <path d="M 1 -38 L 20 -31 L 1 -24 Z" fill={fg} />
    </g>
  );
}

export function CandGlyph({ c, fg = "#fff", tint }: { c: number; fg?: string; tint?: string }) {
  if (c === 0) return <Fish fg={fg} />;
  if (c === 1) return <Umbrella fg={fg} tint={tint ?? DEST[1].color} />;
  return <Castle fg={fg} />;
}

/** Coloured disc with a white glyph. (x, y) is the centre. */
export function CandBadge({
  c,
  x = 0,
  y = 0,
  r = 20,
  ring = true,
  dim = false,
}: {
  c: number;
  x?: number;
  y?: number;
  r?: number;
  ring?: boolean;
  dim?: boolean;
}) {
  const d = DEST[c];
  return (
    <g transform={`translate(${x} ${y})`} opacity={dim ? 0.35 : 1}>
      <circle r={r} fill={d.color} stroke={ring ? "#fff" : "none"} strokeWidth={r * 0.12} />
      <g transform={`scale(${(r * 1.25) / 100})`}>
        <CandGlyph c={c} tint={d.color} />
      </g>
    </g>
  );
}

export function HeartGlyph({ fill = "#e5484d" }: { fill?: string }) {
  return (
    <path
      d="M 0 34 C -10 24, -44 4, -44 -16 C -44 -34, -22 -42, 0 -22 C 22 -42, 44 -34, 44 -16 C 44 4, 10 24, 0 34 Z"
      fill={fill}
    />
  );
}

export function AnchorGlyph({ fg }: { fg: string }) {
  return (
    <g fill="none" stroke={fg} strokeWidth={9} strokeLinecap="round" strokeLinejoin="round">
      <circle cx={0} cy={-30} r={9} />
      <path d="M 0 -21 V 36" />
      <path d="M -18 -8 H 18" />
      <path d="M -34 10 Q -30 36 0 36 Q 30 36 34 10" />
      <path d="M -40 16 L -34 6 L -26 14" />
      <path d="M 40 16 L 34 6 L 26 14" />
    </g>
  );
}

export function WindGlyph({ fg }: { fg: string }) {
  return (
    <g fill="none" stroke={fg} strokeWidth={9} strokeLinecap="round">
      <path d="M -40 -18 H 14 A 13 13 0 1 0 1 -31" />
      <path d="M -40 2 H 28 A 14 14 0 1 1 14 16" />
      <path d="M -40 22 H -2 A 10 10 0 1 1 -12 32" />
    </g>
  );
}

export function AntennaGlyph({ fg }: { fg: string }) {
  return (
    <g fill="none" stroke={fg} strokeWidth={8} strokeLinecap="round" strokeLinejoin="round">
      <path d="M 0 -8 L -16 38 M 0 -8 L 16 38 M -10 22 H 10" />
      <circle cx={0} cy={-14} r={7} fill={fg} />
      <path d="M -20 -32 A 26 26 0 0 0 -20 4" />
      <path d="M 20 -32 A 26 26 0 0 1 20 4" />
      <path d="M -34 -42 A 42 42 0 0 0 -34 14" />
      <path d="M 34 -42 A 42 42 0 0 1 34 14" />
    </g>
  );
}

export function ParamGlyph({ k, fg }: { k: ParamKey; fg: string }) {
  if (k === "alpha") return <AnchorGlyph fg={fg} />;
  if (k === "eta") return <WindGlyph fg={fg} />;
  return <AntennaGlyph fg={fg} />;
}

/** Round param badge for SVG scenes. */
export function ParamBadge({ k, x = 0, y = 0, r = 18 }: { k: ParamKey; x?: number; y?: number; r?: number }) {
  const p = PARAMS[k];
  return (
    <g transform={`translate(${x} ${y})`}>
      <circle r={r} fill={p.color} />
      <g transform={`scale(${(r * 1.2) / 100})`}>
        <ParamGlyph k={k} fg="#fff" />
      </g>
    </g>
  );
}

/** Stand-alone inline icons for HTML text. */
export function ParamIcon({ k, size = 28, ...rest }: { k: ParamKey; size?: number } & SVGProps<SVGSVGElement>) {
  return (
    <svg width={size} height={size} viewBox="-50 -50 100 100" aria-hidden {...rest}>
      <circle r={50} fill={PARAMS[k].color} />
      <g transform="scale(0.62)">
        <ParamGlyph k={k} fg="#fff" />
      </g>
    </svg>
  );
}

export function DestIcon({ c, size = 26 }: { c: number; size?: number }) {
  return (
    <svg width={size} height={size} viewBox="-50 -50 100 100" aria-hidden style={{ verticalAlign: "-0.32em" }}>
      <circle r={50} fill={DEST[c].color} />
      <g transform="scale(0.62)">
        <CandGlyph c={c} tint={DEST[c].color} />
      </g>
    </svg>
  );
}

export function HeartIcon({ size = 22 }: { size?: number }) {
  return (
    <svg width={size} height={size} viewBox="-50 -50 100 100" aria-hidden style={{ verticalAlign: "-0.2em" }}>
      <HeartGlyph />
    </svg>
  );
}

/** Small gold crown, centred on (0, 0), about 30 units wide. */
export function Crown({ x = 0, y = 0, s = 1 }: { x?: number; y?: number; s?: number }) {
  return (
    <g transform={`translate(${x} ${y}) scale(${s})`}>
      <path d="M -15 8 L -17 -9 L -7 -1 L 0 -13 L 7 -1 L 17 -9 L 15 8 Z" fill="#ffc83d" stroke="#23213a" strokeWidth={2} strokeLinejoin="round" />
      <rect x={-15} y={8} width={30} height={5} rx={2} fill="#ffc83d" stroke="#23213a" strokeWidth={2} />
    </g>
  );
}
