import { Github } from "lucide-react";
import { ChangeEvent } from "react";

export default function RepositoryInput({ repository, setRepository, disabled, onSubmit }: any) {
  function onInput(event: ChangeEvent<HTMLInputElement>) {
    setRepository(event.target.value);
  }

  return (
    <form className="mx-auto mt-12 w-full max-w-5xl space-y-7" onSubmit={onSubmit}>
      <div className="repo-input font-mono">
        <Github className="shrink-0 text-white/72" size={30} />
        <input
          value={repository}
          onChange={onInput}
          disabled={disabled}
          placeholder="Paste GitHub repository URL..."
          spellCheck={false}
          autoComplete="off"
          className="min-w-0 flex-1 bg-transparent text-lg text-white outline-none placeholder:text-white/38 disabled:cursor-wait"
        />
      </div>

<div className="mt-8 grid grid-cols-1 gap-4 md:grid-cols-3">

    <button
        type="submit"
        name="review"
        value="repository"
        className="analyze-button osiris-button review-button"
        disabled={disabled || !repository.trim()}
    >
        Repository Review
    </button>

    <button
        type="submit"
        name="review"
        value="code"
        className="analyze-button osiris-button review-button"
        disabled={disabled || !repository.trim()}
    >
        Code Review
    </button>

    <button
        type="submit"
        name="review"
        value="deep"
        className="analyze-button osiris-button review-button"
        disabled={disabled || !repository.trim()}
    >
        Deep Code Review
    </button>

</div>
    </form>
  );
}
