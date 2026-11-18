import { motion } from "motion/react";
import { useMemo } from "react";
import { KIDS, MIA, MIA_HEART, PARAMS, PARAM_ORDER } from "../cast";
import { Avatar } from "../components/Avatar";
import { Bubble } from "../components/Bits";
import { Board } from "../components/Board";
import { ParamBadge, ParamIcon } from "../components/icons";
import { Jar } from "../components/Jar";
import { RankCard } from "../components/RankCard";
import { tokensFromCounts } from "../lib/tokens";

const HABIT_SHORT = {
  alpha: "sticks to the heart",
  eta: "changes fast or slow",
  beta: "listens to the board",
} as const;

function Art() {
  const tokens = useMemo(() => tokensFromCounts([3, 2, 0, 15, 0, 0]), []);
  const float = (d: number) => ({
    animate: { y: [0, -8, 0] },
    transition: { duration: 3.2, repeat: Infinity, ease: "easeInOut" as const, delay: d },
  });
  return (
    <svg viewBox="0 0 560 540" className="hero-art" role="img" aria-label="Mia next to her jar of ballot cards and the class scoreboard">
      <Board p={[7 / 15, 3 / 15, 5 / 15]} x={300} y={14} w={240} h={196} />
      <Jar tokens={tokens} x={180} y={318} scale={0.98} first={MIA_HEART} lidOpen />
      <motion.g
        animate={{ x: [0, 40, 60], y: [0, -150, -170], rotate: [-12, 8, 10], opacity: [0, 1, 0] }}
        transition={{ duration: 3.6, repeat: Infinity, times: [0, 0.6, 1], ease: "easeOut", repeatDelay: 0.6 }}
      >
        <RankCard k={MIA_HEART} x={180} y={200} w={56} />
      </motion.g>
      <Avatar look={KIDS[MIA].look} x={440} y={430} size={150} mood="think" />
      <Bubble x={330} y={250} w={200} h={52} lines={["Which card next?"]} tail="down" size={19} />
      <motion.g {...float(0)}>
        <ParamBadge k="alpha" x={46} y={170} r={26} />
      </motion.g>
      <motion.g {...float(0.8)}>
        <ParamBadge k="eta" x={40} y={420} r={26} />
      </motion.g>
      <motion.g {...float(1.6)}>
        <ParamBadge k="beta" x={300} y={500} r={26} />
      </motion.g>
    </svg>
  );
}

export function Hero() {
  return (
    <header className="hero">
      <div className="wrap hero-grid">
        <div>
          <span className="eyebrow">An interactive story · the GTIV voting model</span>
          <h1>
            The Ballot <span className="accent">Jar</span>
          </h1>
          <p className="lede">
            Every round, a class votes on a school trip and the result goes up on the board. Then each kid quietly
            decides what to write next time. Follow Mia through one round and you'll see the whole decision, one
            simple step at a time.
          </p>
          <div className="habits">
            {PARAM_ORDER.map((k) => (
              <span className="habit" key={k}>
                <ParamIcon k={k} size={30} />
                <span>
                  {PARAMS[k].name} <small>· {HABIT_SHORT[k]}</small>
                </span>
              </span>
            ))}
          </div>
          <a className="scroll-cue" href="#choice">
            Start the story ↓
          </a>
          <a className="skip-link" href="#playground">
            or skip to the playground
          </a>
        </div>
        <Art />
      </div>
    </header>
  );
}
