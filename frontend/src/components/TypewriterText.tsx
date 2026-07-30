import { useTypewriter } from "../hooks/useTypewriter";

function MarkdownLine({ line }: { line: string }) {
  if (line.startsWith("# ")) {
    return <h1>{line.slice(2)}</h1>;
  }

  if (line.startsWith("## ")) {
    return <h2>{line.slice(3)}</h2>;
  }

  if (line.startsWith("### ")) {
    return <h3>{line.slice(4)}</h3>;
  }

  if (!line.trim()) {
    return <div className="h-4" />;
  }

  return <p>{line}</p>;
}

export default function TypewriterText({ text, speed = 8 }: { text: string; speed?: number }) {
  const { value, done } = useTypewriter(text, speed);

  return (
    <div className="report-body" aria-live={done ? "off" : "polite"}>
      {value.split("\n").map((line, index) => (
        <MarkdownLine line={line} key={`${index}-${line}`} />
      ))}
      {!done && <span className="typing-caret" />}
    </div>
  );
}
