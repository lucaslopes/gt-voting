# The Ballot Jar

A scrollytelling web app that explains, step by step, how **one voter changes
their ranking report in one round** of the GTIV reporting dynamics. It is
written so a child can follow it, and it ends with a playground where every
parameter can be changed.

The three parameters are introduced as everyday habits:

| Habit | Symbol | What it does in the model |
| --- | --- | --- |
| **Loyalty** | α (`alpha`) | How strongly the distribution stays anchored to the baseline ranking. |
| **Volatility** | η (`eta`) | How quickly the distribution can change. |
| **Receptivity** | β (`beta`) | How strongly the published signal influences the response. |

## Run it

```bash
cd web
npm ci
npm run dev        # http://localhost:5173
npm run build      # static site in web/dist (relative paths, works from any folder)
npm test           # model tests, including parity with the Rust assembly
```

## The story

| Part | What the reader sees |
| --- | --- |
| 1. Three places, six ways to rank them | Destinations (A, B, C) become Aquarium, Beach and Castle; Mia's heart ranking (baseline) vs. her ballot (report). |
| 2. The ballot jar | The mixed reporting state as a jar of 20 cards; pulling a card is drawing a report. |
| 3. Everyone votes | A 15-voter example (7 ACB, 7 BCA, 1 ABC), pairwise duels, the maximal-lottery scoreboard, and a rock-paper-scissors cycle (6/5/4 blocks give 7/15, 3/15, 5/15). |
| 4. Reading the board | Centred signal p − ⅓ ("HOT/NOT"), the lead over one friend, cubing, averaging over friends, scores for all six cards. |
| Habit 1: Receptivity | Scores become a wish list, q = softmax(β·s). Inline β slider. |
| Habit 2: Loyalty | Plan = (1 − α)·q + α·heart. Inline α slider. |
| Habit 3: Volatility | New jar = (1 − η)·old jar + η·plan, animated as swapping cards. Inline η slider. |
| 5. The new ballot | Pull the next ballot from the new jar; recap of the whole decision. |
| 6. Everyone, round after round | Live class simulations: the bandwagon (story dials), β = 0 (luck takes over), and a high-loyalty example. |
| Playground | All three dials, presets, three classes, two friend networks, a seeded simulation, and a seven-panel "inside a kid's head" view of the selected voter's decision. Moving a dial re-makes the latest round's decision, so every panel reacts immediately. |

## How it maps to the model

`src/model/` implements the three-candidate cubic reporting dynamics in TypeScript:

- `lottery.ts`: pairwise margins and the maximal lottery (closed form for three
  candidates; odd electorates keep it unique).
- `response.ts`: `s_i(σ) = mean_j ((⟨p − 1/3, r_j − r_σ⟩ / 2)^3)` and `q_i = softmax(β s_i)`.
- `update.ts`: `x_i ← (1 − η) x_i + η[(1 − α) q_i + α δ_baseline]`.
- `simulation.ts`: the round timing (draw reports → publish lottery → respond → update), seeded draws, and the class presets.

`src/model/model.test.ts` replays synthetic rounds recorded by the public Rust
`Assembly` API and checks the published lottery and each voter's updated
distribution to 1e-9. Regenerate the fixture with `npm run fixture` from this
directory. GitHub Actions builds the static site and publishes it to
[GitHub Pages](https://lucaslopes.github.io/gtiv/).

## Code layout

```
src/
  cast.ts            destinations, kids, the three habits, story and paper settings
  model/             the GTIV maths (pure TypeScript, tested)
  components/        SVG illustrations: cards, jar, scoreboard, duels, bars, avatars, sliders, scrolly engine
  story/             the scrolling chapters
  playground/        the full tool
  lib/               tweening, token (card) rounding, simulation hook
```
