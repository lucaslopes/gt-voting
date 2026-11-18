import { AnimatePresence, motion } from "motion/react";
import { KIDS, MIA, MIA_HEART, PARAMS } from "../cast";
import { Avatar } from "../components/Avatar";
import { Arrow, Label, Pill } from "../components/Bits";
import { DistBars } from "../components/DistBars";
import { ParamBadge } from "../components/icons";
import { CARD_RATIO, RankCard } from "../components/RankCard";
import { Chapter, Scrolly } from "../components/Scrolly";
import { Slider } from "../components/Slider";
import { Grownups, Habit, Heart, Rank } from "../components/Text";
import { pctSoft } from "../lib/format";
import { useTweened } from "../lib/useTweened";
import { PERM_IDS } from "../model/rankings";
import { miaDecision, useStory } from "./world";

const ROSE = PARAMS.alpha.color;
const GOLD = PARAMS.beta.color;
const INK = "#23213a";

/** Plan bars split into the part that comes from the heart and the part from the wish list. */
export function PlanBars({
  q,
  alpha,
  heart,
  x,
  y,
  w,
  h,
  cardW = 34,
  labels = true,
}: {
  q: readonly number[];
  alpha: number;
  heart: number;
  x: number;
  y: number;
  w: number;
  h: number;
  cardW?: number;
  labels?: boolean;
}) {
  const slot = w / 6;
  const ch = cardW * CARD_RATIO;
  const barH = h - ch - 12 - (labels ? 22 : 0);
  const top = labels ? 22 : 0;
  const barW = Math.min(slot * 0.62, 44);
  return (
    <g transform={`translate(${x} ${y})`}>
      {PERM_IDS.map((k) => {
        const cx = slot * (k + 0.5);
        const wish = (1 - alpha) * q[k];
        const anchor = k === heart ? alpha : 0;
        const base = top + barH;
        const hw = Math.max(0, wish * barH);
        const ha = anchor * barH;
        return (
          <g key={k}>
            <rect x={cx - barW / 2} y={top} width={barW} height={barH} rx={6} fill={INK} opacity={0.04} />
            <motion.rect x={cx - barW / 2} width={barW} rx={4} fill={ROSE} initial={false} animate={{ y: base - ha, height: ha }} transition={{ type: "spring", stiffness: 130, damping: 20 }} />
            <motion.rect x={cx - barW / 2} width={barW} rx={4} fill={GOLD} initial={false} animate={{ y: base - ha - hw, height: hw }} transition={{ type: "spring", stiffness: 130, damping: 20 }} />
            {labels && <BarLabel x={cx} base={base} v={wish + anchor} barH={barH} />}
            <RankCard k={k} x={cx} y={top + barH + 10 + ch / 2} w={cardW} heart={k === heart} shadow={false} />
          </g>
        );
      })}
    </g>
  );
}

function BarLabel({ x, base, v, barH }: { x: number; base: number; v: number; barH: number }) {
  const t = useTweened(v);
  return (
    <text x={x} y={base - t * barH - 7} textAnchor="middle" fontSize={15} fontWeight={600} fill={INK}>
      {pctSoft(t)}
    </text>
  );
}

function Recipe({ alpha, x, y, w }: { alpha: number; x: number; y: number; w: number }) {
  const a = useTweened(alpha);
  return (
    <g transform={`translate(${x} ${y})`}>
      <rect width={w} height={30} rx={15} fill={GOLD} />
      <motion.rect height={30} rx={15} fill={ROSE} initial={false} animate={{ width: Math.max(alpha * w, alpha > 0 ? 30 : 0) }} />
      <Label x={10} y={20} size={15} anchor="start" color="#fff">
        {a > 0.12 ? `${Math.round(a * 100)}% heart` : ""}
      </Label>
      <Label x={w - 10} y={20} size={15} anchor="end" color="#fff">
        {a < 0.88 ? `${Math.round((1 - a) * 100)}% wish list` : ""}
      </Label>
    </g>
  );
}

function Stage({ step }: { step: number }) {
  const { params } = useStory();
  const d = miaDecision(params);
  return (
    <svg viewBox="0 0 600 600">
      <AnimatePresence mode="wait">
        {step < 2 ? (
          <motion.g key="mix" initial={{ opacity: 0 }} animate={{ opacity: 1 }} exit={{ opacity: 0 }}>
            <Label x={110} y={36} size={19} color="#b8323b">
              Heart
            </Label>
            <RankCard k={MIA_HEART} x={110} y={120} w={76} heart outline="#e5484d" />
            <Label x={410} y={36} size={19} color="#8f6500">
              Wish list
            </Label>
            <DistBars values={d.q} x={250} y={46} w={320} h={150} color={GOLD} cardW={24} showLabels={false} heart={MIA_HEART} />
            <Arrow d="M 140 190 Q 190 240 250 262" width={4} color={ROSE} />
            <Arrow d="M 420 206 Q 400 240 360 262" width={4} color={GOLD} />
            <ParamBadge k="alpha" x={300} y={262} r={20} />
            <Recipe alpha={params.alpha} x={60} y={296} w={480} />
            <Label x={30} y={368} size={19} anchor="start">
              Plan for the jar
            </Label>
            <PlanBars q={d.q} alpha={params.alpha} heart={MIA_HEART} x={30} y={376} w={540} h={210} cardW={30} />
          </motion.g>
        ) : (
          <motion.g key="three" initial={{ opacity: 0 }} animate={{ opacity: 1 }} exit={{ opacity: 0 }}>
            <Label x={300} y={44} size={21}>
              Same wish list, different loyalty
            </Label>
            {[
              { a: 0, name: "Goes with the flow", kid: 4 },
              { a: params.alpha, name: "Mia (you choose)", kid: MIA },
              { a: 1, name: "Never budges", kid: 12 },
            ].map((p, i) => (
              <g key={i} transform={`translate(${8 + i * 202} 0)`}>
                {i === 1 && <rect x={-4} y={70} width={186} height={480} rx={18} fill={PARAMS.alpha.soft} />}
                <Avatar look={KIDS[p.kid].look} x={89} y={130} size={78} mood={p.a > 0.9 ? "calm" : "happy"} />
                <Label x={89} y={205} size={18}>
                  {p.name}
                </Label>
                <Pill x={89} y={236} text={`α = ${Math.round(p.a * 100)}%`} fill="#fff" color="#b3214a" size={15} stroke={ROSE} />
                <PlanBars q={d.q} alpha={p.a} heart={MIA_HEART} x={4} y={270} w={170} h={240} cardW={22} labels={false} />
                <Label x={89} y={536} size={15} weight={500} color="#4a4862">
                  {`heart card: ${pctSoft(p.a + (1 - p.a) * d.q[MIA_HEART])}`}
                </Label>
              </g>
            ))}
          </motion.g>
        )}
      </AnimatePresence>
    </svg>
  );
}

export function Ch6Loyalty() {
  const { params, set } = useStory();
  const steps = [
    <>
      <h3>Her heart still has a say</h3>
      <p>
        Mia won't simply follow her wish list. Part of her always stays true to her <Heart />,{" "}
        <Rank k={MIA_HEART} />. So her <b>plan</b> for the jar mixes the two.
      </p>
    </>,
    <>
      <h3>
        <Habit k="alpha" />: the anchor to her heart
      </h3>
      <p>
        Loyalty is the recipe. With <b>{Math.round(params.alpha * 100)}%</b> loyalty,{" "}
        {Math.round(params.alpha * 100)}% of her plan is her heart card and {100 - Math.round(params.alpha * 100)}%
        follows the wish list.
      </p>
      <div className="control">
        <Slider k="alpha" value={params.alpha} onChange={(v) => set("alpha", v)} />
      </div>
      <p className="small muted" style={{ marginTop: 10 }}>
        Pink is the share kept for the heart card. Gold is the share that follows the board.
      </p>
    </>,
    <>
      <h3>Loyal, or going with the flow?</h3>
      <p>
        At <b>100%</b> loyalty Mia never strays. At <b>0%</b> she follows the wish list completely. Most people are
        somewhere in between. {PARAMS.alpha.habit}
      </p>
      <Grownups>
        Plan = (1 − α) q<sub>i</sub> + α δ<sub>R<sub>i</sub><sup>0</sup></sub>. α = 1 freezes honest voting forever.
        A value near 1 represents a very loyal class.
      </Grownups>
    </>,
  ];
  return (
    <Chapter id="loyalty" num="Habit 2 of 3" title="Loyalty: mixing in her heart">
      <Scrolly steps={steps} stage={(s) => <Stage step={s} />} label="Loyalty mixes the heart ranking with the wish list" />
    </Chapter>
  );
}
