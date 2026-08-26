import type { Citation } from "@/lib/api";

export default function SourceCard({ citation }: { citation: Citation }) {
  return (
    <a
      href={citation.url}
      target="_blank"
      rel="noreferrer"
      className="block rounded-lg border border-neutral-800 p-3 hover:border-neutral-600 transition-colors"
    >
      <div className="flex items-center justify-between gap-2">
        <span className="text-sm font-medium truncate">{citation.title || citation.url}</span>
        <span
          className={
            "text-xs shrink-0 rounded px-1.5 py-0.5 " +
            (citation.verified ? "bg-green-900 text-green-300" : "bg-yellow-900 text-yellow-300")
          }
        >
          {citation.verified ? "verified" : "unverified"}
        </span>
      </div>
      <p className="text-xs text-neutral-500 truncate mt-1">{citation.url}</p>
    </a>
  );
}
