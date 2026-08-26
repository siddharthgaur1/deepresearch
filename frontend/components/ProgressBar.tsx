const STAGES = ["queued", "planning", "researching", "verifying", "writing", "done"];

export default function ProgressBar({ status }: { status: string }) {
  const index = Math.max(STAGES.indexOf(status), 0);
  const isFailed = status === "failed" || status === "cancelled";

  return (
    <div className="w-full">
      <div className="flex justify-between text-xs text-neutral-500 mb-1">
        {STAGES.map((s) => (
          <span key={s} className={s === status ? "text-neutral-200 font-medium" : ""}>
            {s}
          </span>
        ))}
      </div>
      <div className="h-2 w-full rounded-full bg-neutral-800 overflow-hidden">
        <div
          className={`h-full rounded-full transition-all duration-500 ${isFailed ? "bg-red-600" : "bg-blue-600"}`}
          style={{ width: `${((index + 1) / STAGES.length) * 100}%` }}
        />
      </div>
    </div>
  );
}
