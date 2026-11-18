/** Everything the story names: destinations, kids, and the three human habits. */
import { delta } from "./model/rankings";
import { storyClass } from "./model/simulation";

export interface Destination {
  name: string;
  letter: string;
  color: string;
  soft: string;
  ink: string;
}

/** Candidates A, B and C become three field-trip destinations. */
export const DEST: Destination[] = [
  { name: "Aquarium", letter: "A", color: "#2F8FE0", soft: "#DCEDFC", ink: "#155A99" },
  { name: "Beach", letter: "B", color: "#F28A1E", soft: "#FFE8CF", ink: "#A1520A" },
  { name: "Castle", letter: "C", color: "#8B5BD8", soft: "#ECE3FB", ink: "#5631A0" },
];

export type HairStyle = "short" | "bun" | "curly" | "pigtails" | "spiky" | "long" | "bob";

export interface Look {
  skin: string;
  hair: string;
  style: HairStyle;
  shirt: string;
}

export interface Kid {
  name: string;
  look: Look;
}

const SKIN = ["#F6D3B3", "#E7B48C", "#C98E62", "#9C6644", "#F1C7A0", "#7A4E33"];
const HAIR = ["#2E1F17", "#6B3E1F", "#C9822F", "#1B1B1B", "#8C4A2F", "#E3B65B"];
const SHIRTS = ["#5BB1A9", "#F3B23E", "#E8697B", "#6F8EE8", "#9BC75B", "#C77DDB", "#4FB0E0"];

const NAMES = [
  // seven Aquarium > Castle > Beach
  "Ava", "Ben", "Cleo", "Dev", "Eli", "Finn", "Gia",
  // seven Beach > Castle > Aquarium (Mia is the first of them)
  "Mia", "Hugo", "Ivy", "Jay", "Kai", "Lena", "Omar",
  // the single Aquarium > Beach > Castle
  "Zoe",
];
const STYLES: HairStyle[] = ["long", "short", "curly", "spiky", "bob", "bun", "short", "pigtails", "spiky", "long", "curly", "short", "bob", "short", "bun"];

export const KIDS: Kid[] = NAMES.map((name, i) => ({
  name,
  look: {
    skin: SKIN[(i * 5 + 1) % SKIN.length],
    hair: HAIR[(i * 7 + 2) % HAIR.length],
    style: STYLES[i],
    shirt: SHIRTS[(i * 3) % SHIRTS.length],
  },
}));
// Mia's look is fixed so she is easy to spot everywhere.
KIDS[7].look = { skin: "#F1C7A0", hair: "#B5562B", style: "pigtails", shirt: "#F28A1E" };

/** Names for extra voters in larger random classes. */
export function kidFor(i: number): Kid {
  if (i < KIDS.length) return KIDS[i];
  return {
    name: `Kid ${i + 1}`,
    look: {
      skin: SKIN[(i * 5 + 1) % SKIN.length],
      hair: HAIR[(i * 7 + 2) % HAIR.length],
      style: STYLES[i % STYLES.length],
      shirt: SHIRTS[(i * 3) % SHIRTS.length],
    },
  };
}

/** The story's class: the running example (7 ACB, 7 BCA, 1 ABC). */
export const STORY_HEARTS = storyClass();
export const MIA = 7;
export const MIA_HEART = STORY_HEARTS[MIA];
export const MIA_START_JAR = delta(MIA_HEART);

export type ParamKey = "alpha" | "eta" | "beta";

export interface ParamInfo {
  key: ParamKey;
  greek: string;
  name: string;
  color: string;
  soft: string;
  min: number;
  max: number;
  step: number;
  /** what the parameter does, in the story's words (jar, heart ranking, scoreboard) */
  model: string;
  /** the same thing in model terms */
  tech: string;
  /** the everyday habit it stands for */
  habit: string;
  low: string;
  high: string;
}

export const PARAMS: Record<ParamKey, ParamInfo> = {
  alpha: {
    key: "alpha",
    greek: "α",
    name: "Loyalty",
    color: "#E0436A",
    soft: "#FCE3EA",
    min: 0,
    max: 1,
    step: 0.01,
    model: "How strongly the jar stays anchored to the heart ranking.",
    tech: "how strongly the distribution remains anchored to the baseline ranking",
    habit: "Sticking with your favourite team, even on a losing streak.",
    low: "goes with the flow",
    high: "never budges",
  },
  eta: {
    key: "eta",
    greek: "η",
    name: "Volatility",
    color: "#12A07C",
    soft: "#DDF5EE",
    min: 0,
    max: 1,
    step: 0.01,
    model: "How quickly the jar can change from one round to the next.",
    tech: "how quickly the distribution can change",
    habit: "Some people take weeks to change their mind; others change it by lunch.",
    low: "slow and steady",
    high: "changes overnight",
  },
  beta: {
    key: "beta",
    greek: "β",
    name: "Receptivity",
    color: "#D99A00",
    soft: "#FFF1CC",
    min: 0,
    max: 40,
    step: 0.5,
    model: "How strongly the published scoreboard pulls on the response.",
    tech: "how strongly the published signal influences the response",
    habit: "How much polls, buzz and what friends say get to you.",
    low: "shrugs it off",
    high: "hangs on every word",
  },
};

export const PARAM_ORDER: ParamKey[] = ["alpha", "eta", "beta"];

/** Friendly settings used while telling the story (big enough to see). */
export const STORY_PARAMS = { alpha: 0.5, eta: 0.5, beta: 10 };

/** Illustrative settings for a class with high loyalty. */
export const HIGH_LOYALTY_PARAMS = { alpha: 0.98, eta: 0.2, beta: 10 };
