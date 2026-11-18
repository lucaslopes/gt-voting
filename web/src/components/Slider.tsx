/** A parameter slider that speaks in human habits first and Greek letters second. */
import { useId, type CSSProperties } from "react";
import { PARAMS, type ParamKey } from "../cast";
import { ParamIcon } from "./icons";

export function formatParam(k: ParamKey, v: number) {
  if (k === "beta") return v.toFixed(1);
  return `${Math.round(v * 100)}%`;
}

export function Slider({
  k,
  value,
  onChange,
  describe = false,
  habit = false,
}: {
  k: ParamKey;
  value: number;
  onChange: (v: number) => void;
  describe?: boolean;
  habit?: boolean;
}) {
  const p = PARAMS[k];
  const id = `slider-${k}-${useId().replace(/:/g, "")}`;
  const fill = ((value - p.min) / (p.max - p.min)) * 100;
  const style = { "--c": p.color, "--soft": p.soft, "--fill": `${fill}%` } as CSSProperties;
  return (
    <div className="slider" style={style}>
      <div className="slider-top">
        <ParamIcon k={k} size={34} />
        <div className="slider-name">
          {p.name}
          <small>
            {p.greek} · {p.key}
          </small>
        </div>
        <output className="slider-value" htmlFor={id}>
          {formatParam(k, value)}
        </output>
      </div>
      <input
        id={id}
        type="range"
        min={p.min}
        max={p.max}
        step={p.step}
        value={value}
        aria-label={`${p.name} (${p.greek})`}
        aria-valuetext={formatParam(k, value)}
        onChange={(e) => onChange(Number(e.target.value))}
      />
      <div className="slider-ends">
        <span>{p.low}</span>
        <span>{p.high}</span>
      </div>
      {describe && <div className="slider-desc">{p.model}</div>}
      {habit && <div className="slider-desc muted">{p.habit}</div>}
    </div>
  );
}
