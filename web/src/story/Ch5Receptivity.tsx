import { AnimatePresence, motion } from "motion/react";
import { KIDS, MIA, MIA_HEART, PARAMS } from "../cast";
import { Avatar } from "../components/Avatar";
import { Arrow, Label, Pill } from "../components/Bits";
import { DistBars } from "../components/DistBars";
import { ParamBadge } from "../components/icons";
import { Chapter, Scrolly } from "../components/Scrolly";
import { Slider } from "../components/Slider";
import { Dest, Grownups, Habit } from "../components/Text";
import { softmax, topMass } from "../model/response";
import { miaDecision, useStory } from "./world";

const GOLD = PARAMS.beta.color;

export function receptivityNote(beta: number, q: readonly number[], scores: readonly number[]) {
  if (beta < 0.25) return "She ignores the points: all six cards look equally good.";
  const top = topMass(q, scores);
  if (top < 0.55) return "A gentle lean toward the best cards.";
  if (top < 0.95) return "A strong pull toward the best cards.";
  return "Almost all-in on the best cards.";
}

function Persona({ x, kid, beta, scores, name, active }: { x: number; kid: number; beta: number; scores: number[]; name: string; active?: boolean }) {
  const q = softmax(scores, beta);
  return (
    <g transform={`translate(${x} 0)`}>
      {active && <rect x={-4} y={70} width={186} height={470} rx={18} fill={PARAMS.beta.soft} />}
      <Avatar look={KIDS[kid].look} x={89} y={130} size={78} mood={beta < 1 ? "calm" : beta > 20 ? "wow" : "happy"} />
      <Label x={89} y={205} size={19}>
        {name}
      </Label>
      <Pill x={89} y={236} text={`β = ${beta.toFixed(1)}`} fill="#fff" color="#8f6500" size={15} stroke={GOLD} />
      <DistBars values={q} x={4} y={270} w={170} h={230} color={GOLD} cardW={22} showLabels={false} heart={MIA_HEART} />
      <Label x={89} y={528} size={15} weight={500} color="#4a4862">
        {`top cards: ${Math.round(topMass(q, scores) * 100)}%`}
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
          <motion.g key="flow" initial={{ opacity: 0 }} animate={{ opacity: 1 }} exit={{ opacity: 0 }}>
            <Label x={30} y={34} size={19} anchor="start">
              Points
            </Label>
            <DistBars values={d.scores} mode="score" x={30} y={44} w={540} h={190} cardW={30} labelSize={14} heart={MIA_HEART} />
            <Arrow d="M 300 248 V 300" width={4} color={GOLD} />
            <ParamBadge k="beta" x={250} y={274} r={20} />
            <Label x={330} y={282} size={19} anchor="start" color="#8f6500">
              {`receptivity β = ${params.beta.toFixed(1)}`}
            </Label>
            <Label x={30} y={330} size={19} anchor="start">
              Wish list: chance of picking each card
            </Label>
            <DistBars values={d.q} x={30} y={342} w={540} h={210} color={GOLD} cardW={30} labelSize={15} heart={MIA_HEART} />
            <Label x={300} y={586} size={17} weight={500} color="#4a4862">
              {receptivityNote(params.beta, d.q, d.scores)}
            </Label>
          </motion.g>
        ) : (
          <motion.g key="people" initial={{ opacity: 0 }} animate={{ opacity: 1 }} exit={{ opacity: 0 }}>
            <Label x={300} y={44} size={21}>
              Same points, different people
            </Label>
            <Persona x={8} kid={1} beta={0} scores={d.scores} name="Shrugger" />
            <Persona x={210} kid={MIA} beta={params.beta} scores={d.scores} name="Mia (you choose)" active />
            <Persona x={412} kid={10} beta={35} scores={d.scores} name="Trend-chaser" />
          </motion.g>
        )}
      </AnimatePresence>
    </svg>
  );
}

export function Ch5Receptivity() {
  const { params, set } = useStory();
  const steps = [
    <>
      <h3>From points to a wish list</h3>
      <p>
        Points are just points. Mia turns them into a <b>wish list</b>: how likely she'd be to pick each card if she
        followed the board. A higher score makes a card more likely.
      </p>
    </>,
    <>
      <h3>
        <Habit k="beta" />: how much the board gets to her
      </h3>
      <p>
        How much more likely? That depends on Mia's <b>receptivity</b>. It's how strongly the board pulls on her.
        Drag it and watch the wish list.
      </p>
      <div className="control">
        <Slider k="beta" value={params.beta} onChange={(v) => set("beta", v)} />
      </div>
      <p className="small muted" style={{ marginTop: 10 }}>
        At 0 she ignores the points (the board and her friends), so every card is equally likely. Turn it up and the cards with <Dest c={0} /> on
        top take over.
      </p>
    </>,
    <>
      <h3>People are different</h3>
      <p>
        Some people shrug at polls and buzz. Others jump on every trend. {PARAMS.beta.habit}
      </p>
      <p>
        Even a trend-chaser never rules a card out <i>completely</i>. Every card keeps at least a tiny chance.
      </p>
      <Grownups>
        Wish list = logit response q<sub>i</sub> = softmax(β · s<sub>i</sub>), so each card's chance grows like
        e<sup>β × points</sup>. The web model uses degree- and rank-normalized scores. Any
        finite β keeps every card's chance above zero.
      </Grownups>
    </>,
  ];
  return (
    <Chapter id="receptivity" num="Habit 1 of 3" title="Receptivity: turning points into a wish list">
      <Scrolly steps={steps} stage={(s) => <Stage step={s} />} label="Receptivity turns card scores into a wish list" />
    </Chapter>
  );
}
