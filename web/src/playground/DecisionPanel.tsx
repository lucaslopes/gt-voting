/** "Inside a kid's head": every stage of one voter's decision for the latest round. */
import { useMemo, type ReactNode } from "react";
import { DEST, PARAMS, kidFor, type ParamKey } from "../cast";
import { Arrow } from "../components/Bits";
import { Board } from "../components/Board";
import { Jar } from "../components/Jar";
import { roundCounts, swapTokens, tokensFromCounts } from "../lib/tokens";
import { DistBars } from "../components/DistBars";
import { CandBadge, ParamIcon } from "../components/icons";
import { MiniCard } from "../components/RankCard";
import { Rank } from "../components/Text";
import { pctSoft, signed } from "../lib/format";
import { useTweened } from "../lib/useTweened";
import { PERMS, countReports } from "../model/rankings";
import { decide, type Network, type Sim } from "../model/simulation";
import type { Params } from "../model/update";
import { receptivityNote } from "../story/Ch5Receptivity";
import { PlanBars } from "../story/Ch6Loyalty";
import { firstChoiceShares } from "../components/ClassView";

const INK = "#23213a";

function Panel({ n, title, k, children, note }: { n: number; title: string; k?: ParamKey; children: ReactNode; note: ReactNode }) {
  return (
    <div className="pcard" style={k ? { boxShadow: `inset 0 0 0 2px ${PARAMS[k].soft}` } : undefined}>
      <div className="pcard-head">
        <span className="pnum">{n}</span>
        <span className="ptitle">{title}</span>
        {k && <ParamIcon k={k} size={24} style={{ marginLeft: "auto" }} />}
      </div>
      <div className="pcard-viz">{children}</div>
      <div className="pnote">{note}</div>
    </div>
  );
}

/** The jar before and after the swap, drawn with 20 cards like in the story. */
function JarSwap({ before, plan, eta, heart }: { before: readonly number[]; plan: readonly number[]; eta: number; heart: number }) {
  const countsKey = roundCounts(before, 20).join(",");
  const beforeTokens = useMemo(() => tokensFromCounts(countsKey.split(",").map(Number)), [countsKey]);
  const swapped = Math.round(eta * 20);
  const planKey = `${swapped}|${roundCounts(plan, swapped).join(",")}`;
  // eslint-disable-next-line react-hooks/exhaustive-deps
  const swap = useMemo(() => swapTokens(beforeTokens, plan, eta), [beforeTokens, planKey]);
  return (
    <g>
      <Jar tokens={beforeTokens} x={64} y={98} scale={0.46} first={heart} />
      <Jar tokens={swap.tokens} x={236} y={98} scale={0.46} first={heart} outlineIds={swap.incoming} lidOpen />
      <Arrow d="M 128 92 Q 150 74 172 92" width={3} color={PARAMS.eta.color} draw={false} />
      <text x={150} y={118} textAnchor="middle" fontSize={13} fontWeight={600} fill={PARAMS.eta.color}>
        swap {swapped}
      </text>
      <text x={64} y={192} textAnchor="middle" fontSize={13} fill="#4a4862">
        before
      </text>
      <text x={236} y={192} textAnchor="middle" fontSize={13} fill="#4a4862">
        after
      </text>
    </g>
  );
}


export function DecisionPanel({ sim, voter, params, network }: { sim: Sim; voter: number; params: Params; network: Network }) {
  const last = sim.last;
  const kid = kidFor(voter);
  if (!last) {
    return (
      <div className="pempty">
        Press <b>Play</b> or <b>Step</b> to run round 1. Then this panel shows, step by step, how {kid.name} decides.
      </div>
    );
  }
  const d = decide(voter, sim.hearts, last.xBefore[voter], last.reports, last.p, network, params);
  const friendCounts = countReports(d.friendReports);
  const best = d.scores.indexOf(Math.max(...d.scores));
  const after = firstChoiceShares(d.xAfter);
  const hotList = DEST.filter((_, c) => d.pTilde[c] > 1e-9).map((x) => x.name);
  return (
    <div className="pipeline">
      <Panel
        n={1}
        title="Read the board"
        note={
          last.winner !== null ? (
            <>
              {DEST[last.winner].name} beat both rivals, so it gets 100%. HOT: {hotList.join(", ")}.
            </>
          ) : (
            <>Duels went in a circle, so the win is shared. HOT: {hotList.join(", ") || "none"}.</>
          )
        }
      >
        <svg viewBox="0 0 300 270">
          <Board p={last.p} w={300} h={270} showFair showHot />
        </svg>
      </Panel>
      <Panel
        n={2}
        title="Friends' ballots"
        note={
          <>
            {kid.name} watches {d.friends.length} {network === "everyone" ? "classmates (everyone)" : "neighbours"}. These are the cards
            they handed in.
          </>
        }
      >
        <svg viewBox="0 0 300 200">
          {PERMS.map((_, k) => {
            const cx = 25 + k * 50;
            return (
              <g key={k} opacity={friendCounts[k] ? 1 : 0.3}>
                <g transform={`translate(${cx} 60)`}>
                  <MiniCard k={k} w={34} />
                </g>
                <text x={cx} y={130} textAnchor="middle" fontSize={22} fontWeight={600} fill={INK}>
                  ×{friendCounts[k]}
                </text>
              </g>
            );
          })}
          <text x={150} y={180} textAnchor="middle" fontSize={14} fill="#7d7a91">
            top stripe = first choice
          </text>
        </svg>
      </Panel>
      <Panel
        n={3}
        title="Score every card"
        note={
          <>
            Lead over each friend, cubed, averaged. Best: <Rank k={best} /> ({signed(d.scores[best])}).
          </>
        }
      >
        <svg viewBox="0 0 300 200">
          <DistBars values={d.scores} mode="score" w={300} h={200} cardW={26} labelSize={12.5} heart={d.heart} />
        </svg>
      </Panel>
      <Panel n={4} title="Wish list" k="beta" note={<>Receptivity {params.beta.toFixed(1)}. {receptivityNote(params.beta, d.q, d.scores)}</>}>
        <svg viewBox="0 0 300 200">
          <DistBars values={d.q} w={300} h={200} cardW={26} labelSize={12.5} color={PARAMS.beta.color} heart={d.heart} />
        </svg>
      </Panel>
      <Panel
        n={5}
        title="Plan"
        k="alpha"
        note={
          <>
            Loyalty {Math.round(params.alpha * 100)}%: pink comes from the heart card, gold from the wish list.
          </>
        }
      >
        <svg viewBox="0 0 300 200">
          <PlanBars q={d.q} alpha={params.alpha} heart={d.heart} x={0} y={0} w={300} h={200} cardW={26} />
        </svg>
      </Panel>
      <Panel
        n={6}
        title="Swap part of the jar"
        k="eta"
        note={
          <>
            Volatility {Math.round(params.eta * 100)}%: {Math.round(params.eta * 20)} of 20 cards are swapped for plan
            cards (outlined). Heart card {pctSoft(d.xBefore[d.heart])} → {pctSoft(d.xAfter[d.heart])}.
          </>
        }
      >
        <svg viewBox="0 0 300 200">
          <JarSwap before={d.xBefore} plan={d.plan} eta={params.eta} heart={d.heart} />
        </svg>
      </Panel>
      <Panel n={7} title="Next ballot" note={<>Chance that {kid.name}'s next ballot puts each place first.</>}>
        <svg viewBox="0 0 300 200">
          <g transform="translate(18 34)">
            {after.map((v, c) => (
              <g key={c} transform={`translate(0 ${c * 50})`}>
                <CandBadge c={c} x={14} y={0} r={15} />
                <rect x={40} y={-10} width={170} height={20} rx={10} fill="#efebe4" />
                <AnimatedHBar v={v} color={DEST[c].color} />
                <text x={264} y={7} textAnchor="end" fontSize={18} fontWeight={600} fill={INK}>
                  {pctSoft(v)}
                </text>
              </g>
            ))}
          </g>
          <text x={150} y={190} textAnchor="middle" fontSize={14.5} fill="#4a4862">
            heart card: {pctSoft(d.xAfter[d.heart])}
          </text>
        </svg>
      </Panel>
    </div>
  );
}

function AnimatedHBar({ v, color }: { v: number; color: string }) {
  const t = useTweened(v, 0.4);
  return <rect x={40} y={-10} width={Math.max(t > 0 ? 6 : 0, t * 170)} height={20} rx={10} fill={color} />;
}
