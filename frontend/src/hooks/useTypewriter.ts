import { useEffect, useState } from "react";

export function useTypewriter(text: string, speed = 9) {
  const [value, setValue] = useState("");
  const [done, setDone] = useState(false);

  useEffect(() => {
    let frame = 0;
    let index = 0;
    let cancelled = false;
    let last = performance.now();

    setValue("");
    setDone(false);

    const tick = (now: number) => {
      if (cancelled) return;

      if (now - last >= speed) {
        const chunk = Math.max(1, Math.floor((now - last) / speed));
        index = Math.min(text.length, index + chunk);
        setValue(text.slice(0, index));
        last = now;
      }

      if (index >= text.length) {
        setDone(true);
        return;
      }

      frame = requestAnimationFrame(tick);
    };

    frame = requestAnimationFrame(tick);

    return () => {
      cancelled = true;
      cancelAnimationFrame(frame);
    };
  }, [text, speed]);

  return { value, done };
}
