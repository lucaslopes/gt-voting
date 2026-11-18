import { MotionConfig, motion, useScroll } from "motion/react";
import { PARAMS, PARAM_ORDER } from "./cast";
import { ParamIcon } from "./components/icons";
import { Playground } from "./playground/Playground";
import { Ch1Choice } from "./story/Ch1Choice";
import { Ch2Jar } from "./story/Ch2Jar";
import { Ch3Class } from "./story/Ch3Class";
import { Ch4Points } from "./story/Ch4Points";
import { Ch5Receptivity } from "./story/Ch5Receptivity";
import { Ch6Loyalty } from "./story/Ch6Loyalty";
import { Ch7Volatility } from "./story/Ch7Volatility";
import { Ch8Draw } from "./story/Ch8Draw";
import { Ch9Everyone } from "./story/Ch9Everyone";
import { Hero } from "./story/Hero";
import { StoryProvider } from "./story/world";

function Footer() {
  return (
    <footer className="footer">
      <div className="wrap cols">
        <div>
          <h3>What's under the hood</h3>
          <p>
            Every number in this page comes from a TypeScript copy of the GTIV reporting dynamics (
            <code>web/src/model</code>). A test replays rounds recorded from the Rust assembly engine (
            <code>gtiv-three</code>) and checks the scoreboard and every jar match.
          </p>
        </div>
        <div>
          <h3>The three habits</h3>
          {PARAM_ORDER.map((k) => (
            <p key={k}>
              <ParamIcon k={k} size={20} style={{ verticalAlign: -4 }} /> <b>{PARAMS[k].name}</b> ({PARAMS[k].greek},{" "}
              {k}): {PARAMS[k].tech}.
            </p>
          ))}
        </div>
        <div>
          <h3>What we kept simple</h3>
          <p>
            Three destinations, fifteen kids, and the degree- and rank-normalized cubic score. The board is the
            maximal lottery (the GT rule). Each jar is pictured with 20 cards, but the model's jars hold exact
            probabilities. Heart rankings are model inputs, not anyone's real preferences.
          </p>
        </div>
      </div>
    </footer>
  );
}

export function App() {
  const { scrollYProgress } = useScroll();
  return (
    <MotionConfig reducedMotion="user">
      <StoryProvider>
        <motion.div className="progress" style={{ scaleX: scrollYProgress }} aria-hidden />
        <Hero />
        <main>
          <Ch1Choice />
          <Ch2Jar />
          <Ch3Class />
          <Ch4Points />
          <Ch5Receptivity />
          <Ch6Loyalty />
          <Ch7Volatility />
          <Ch8Draw />
          <Ch9Everyone />
          <Playground />
        </main>
        <Footer />
      </StoryProvider>
    </MotionConfig>
  );
}
