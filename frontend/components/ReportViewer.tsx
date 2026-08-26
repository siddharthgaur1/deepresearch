import ReactMarkdown from "react-markdown";
import remarkGfm from "remark-gfm";
import type { Report } from "@/lib/api";
import { reportPdfUrl } from "@/lib/api";
import SourceCard from "./SourceCard";

export default function ReportViewer({ report }: { report: Report }) {
  return (
    <div className="flex flex-col gap-6">
      <div className="flex justify-end">
        <a
          href={reportPdfUrl(report.job_id)}
          className="text-sm rounded-md border border-neutral-700 px-3 py-1.5 hover:bg-neutral-800"
        >
          Export PDF
        </a>
      </div>

      <article className="prose prose-invert max-w-none">
        <ReactMarkdown remarkPlugins={[remarkGfm]}>{report.markdown}</ReactMarkdown>
      </article>

      {report.citations.length > 0 && (
        <div>
          <h3 className="font-semibold text-sm text-neutral-400 mb-2">Sources ({report.citations.length})</h3>
          <div className="grid grid-cols-1 sm:grid-cols-2 gap-2">
            {report.citations.map((c) => (
              <SourceCard key={c.id} citation={c} />
            ))}
          </div>
        </div>
      )}
    </div>
  );
}
