/** Inline vocabulary for the prose: destinations, rankings, habits. */
import { DEST, PARAMS, type ParamKey } from "../cast";
import { PERMS } from "../model/rankings";
import { DestIcon, HeartIcon, ParamIcon } from "./icons";

export function Dest({ c, icon = true }: { c: number; icon?: boolean }) {
  return (
    <span className={`dest dest-${c}`}>
      {icon && <DestIcon c={c} size={22} />} {DEST[c].name}
    </span>
  );
}

export const rankName = (k: number) => PERMS[k].map((c) => DEST[c].name).join(" › ");

/** A ranking written as icons: Beach › Castle › Aquarium. */
export function Rank({ k, names = false }: { k: number; names?: boolean }) {
  return (
    <span className="rank" style={{ whiteSpace: "nowrap" }}>
      {PERMS[k].map((c, i) => (
        <span key={i}>
          {i > 0 && <span className="muted"> › </span>}
          {names ? <Dest c={c} /> : <DestIcon c={c} size={21} />}
        </span>
      ))}
    </span>
  );
}

export function Habit({ k }: { k: ParamKey }) {
  return (
    <span className={`tag tag-${k}`}>
      <ParamIcon k={k} size={18} /> {PARAMS[k].name}
    </span>
  );
}

export function Heart({ children = "heart ranking" }: { children?: string }) {
  return (
    <span className="tag tag-heart">
      <HeartIcon size={16} /> {children}
    </span>
  );
}

export function BoardTag({ children = "scoreboard" }: { children?: string }) {
  return <span className="tag tag-board">{children}</span>;
}

export function Grownups({ children }: { children: React.ReactNode }) {
  return (
    <div className="grownups">
      <b>For grown-ups · </b>
      {children}
    </div>
  );
}
