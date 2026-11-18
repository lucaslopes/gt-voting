/** A friendly kid face drawn in a 100x100 box centred on (0, 0). */
import type { Look } from "../cast";

const INK = "#23213a";

export type Mood = "happy" | "think" | "wow" | "calm";

function Hair({ look, layer }: { look: Look; layer: "back" | "front" }) {
  const c = look.hair;
  switch (look.style) {
    case "long":
      return layer === "back" ? (
        <path d="M -32 -10 Q -34 -42 0 -42 Q 34 -42 32 -10 L 34 26 Q 18 32 0 30 Q -18 32 -34 26 Z" fill={c} />
      ) : (
        <path d="M -29 -6 Q -30 -38 0 -38 Q 30 -38 29 -6 Q 22 -22 6 -24 Q -12 -16 -29 -6 Z" fill={c} />
      );
    case "bob":
      return layer === "back" ? (
        <path d="M -33 10 Q -36 -40 0 -40 Q 36 -40 33 10 Q 24 14 22 4 L -22 4 Q -24 14 -33 10 Z" fill={c} />
      ) : (
        <path d="M -29 -4 Q -30 -38 0 -38 Q 30 -38 29 -4 Q 18 -20 -2 -20 Q -18 -20 -29 -4 Z" fill={c} />
      );
    case "bun":
      return layer === "back" ? (
        <circle cx={0} cy={-40} r={12} fill={c} />
      ) : (
        <path d="M -29 -6 Q -30 -38 0 -38 Q 30 -38 29 -6 Q 16 -24 0 -24 Q -16 -24 -29 -6 Z" fill={c} />
      );
    case "pigtails":
      return layer === "back" ? (
        <g fill={c}>
          <ellipse cx={-34} cy={2} rx={9} ry={13} />
          <ellipse cx={34} cy={2} rx={9} ry={13} />
        </g>
      ) : (
        <g>
          <path d="M -29 -6 Q -30 -38 0 -38 Q 30 -38 29 -6 Q 14 -26 0 -18 Q -14 -26 -29 -6 Z" fill={c} />
          <circle cx={-27} cy={-12} r={4} fill="#ffd34d" />
          <circle cx={27} cy={-12} r={4} fill="#ffd34d" />
        </g>
      );
    case "curly":
      return layer === "back" ? null : (
        <g fill={c}>
          {[-24, -12, 0, 12, 24].map((x, i) => (
            <circle key={i} cx={x} cy={-30 + Math.abs(x) * 0.35} r={11} />
          ))}
          <circle cx={-28} cy={-12} r={8} />
          <circle cx={28} cy={-12} r={8} />
        </g>
      );
    case "spiky":
      return layer === "back" ? null : (
        <path
          d="M -29 -6 L -30 -26 L -20 -24 L -18 -40 L -6 -30 L 2 -44 L 10 -30 L 22 -40 L 22 -24 L 31 -26 L 29 -6 Q 14 -22 0 -20 Q -14 -22 -29 -6 Z"
          fill={c}
        />
      );
    default:
      return layer === "back" ? null : (
        <path d="M -29 -8 Q -30 -40 0 -38 Q 30 -40 29 -8 Q 22 -24 2 -24 Q -18 -26 -29 -8 Z" fill={c} />
      );
  }
}

function Face({ mood }: { mood: Mood }) {
  return (
    <g>
      {mood === "think" ? (
        <g fill={INK}>
          <circle cx={-9} cy={-6} r={3.2} />
          <circle cx={11} cy={-6} r={3.2} />
        </g>
      ) : mood === "calm" ? (
        <g fill="none" stroke={INK} strokeWidth={2.6} strokeLinecap="round">
          <path d="M -13 -3 Q -9 -7 -5 -3" />
          <path d="M 5 -3 Q 9 -7 13 -3" />
        </g>
      ) : (
        <g fill={INK}>
          <ellipse cx={-10} cy={-3} rx={3.2} ry={mood === "wow" ? 4.2 : 3.4} />
          <ellipse cx={10} cy={-3} rx={3.2} ry={mood === "wow" ? 4.2 : 3.4} />
        </g>
      )}
      <circle cx={-18} cy={7} r={4.5} fill="#ff8a8a" opacity={0.45} />
      <circle cx={18} cy={7} r={4.5} fill="#ff8a8a" opacity={0.45} />
      {mood === "wow" ? (
        <ellipse cx={0} cy={11} rx={4.5} ry={5.5} fill={INK} />
      ) : mood === "think" ? (
        <path d="M -7 10 Q 1 16 9 9" fill="none" stroke={INK} strokeWidth={2.6} strokeLinecap="round" />
      ) : (
        <path d="M -8 8 Q 0 16 8 8" fill="none" stroke={INK} strokeWidth={2.8} strokeLinecap="round" />
      )}
    </g>
  );
}

export function Avatar({
  look,
  x = 0,
  y = 0,
  size = 60,
  mood = "happy",
  ring,
  body = true,
}: {
  look: Look;
  x?: number;
  y?: number;
  size?: number;
  mood?: Mood;
  ring?: string;
  body?: boolean;
}) {
  const s = size / 100;
  return (
    <g transform={`translate(${x} ${y}) scale(${s})`}>
      {ring && <circle r={52} fill="none" stroke={ring} strokeWidth={6} />}
      {body && <path d="M -32 50 Q -32 20 0 20 Q 32 20 32 50 Z" fill={look.shirt} />}
      <Hair look={look} layer="back" />
      <circle cx={0} cy={-6} r={27} fill={look.skin} />
      <Hair look={look} layer="front" />
      <Face mood={mood} />
    </g>
  );
}
