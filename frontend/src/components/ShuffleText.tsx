import { useEffect, useState } from "react";

type ShuffleTextProps = {
  text: string;
  className?: string;
  delay?: number;
};

const glyphs = "KR01_AI<>/{}[]$#KODIPALLY";

export function ShuffleText({ text, className, delay = 0 }: ShuffleTextProps) {
  const [value, setValue] = useState(text);

  useEffect(() => {
    let frame = 0;
    let interval = 0;
    const start = window.setTimeout(() => {
      interval = window.setInterval(() => {
        frame += 1;
        setValue(
          text
            .split("")
            .map((letter, index) => {
              if (letter === " ") return " ";
              return index < frame / 2 ? letter : glyphs[(index + frame) % glyphs.length];
            })
            .join(""),
        );
        if (frame > text.length * 2 + 4) {
          window.clearInterval(interval);
          setValue(text);
        }
      }, 45);
    }, delay);

    return () => {
      window.clearTimeout(start);
      window.clearInterval(interval);
    };
  }, [delay, text]);

  return <span className={className}>{value}</span>;
}
