const statuses = [
  "Analyzing repository...",
  "Fetching metadata...",
  "Running deterministic analysis...",
  "Generating engineering assessment...",
];

export default function LoadingStatus() {
  return (
    <div className="mx-auto mt-8 grid max-w-3xl gap-3 font-mono text-sm text-white/56 md:grid-cols-2">
      {statuses.map((status, index) => (
        <div className="status-line" style={{ animationDelay: `${index * 240}ms` }} key={status}>
          <span className="status-dot" />
          {status}
        </div>
      ))}
    </div>
  );
}
