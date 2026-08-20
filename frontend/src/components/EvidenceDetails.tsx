import type { EvidenceChunk } from "../types/api";

interface EvidenceDetailsProps {
  chunks: EvidenceChunk[];
}

export function EvidenceDetails({
  chunks,
}: EvidenceDetailsProps) {
  if (!chunks?.length) {
    return (
      <div className="text-sm text-slate-500">
        No evidence chunks are currently displayed.
      </div>
    );
  }

  return (
    <div className="space-y-3">
      {chunks.map((chunk, index) => (
        <details
          key={chunk.chunk_id || index}
          className="rounded-xl border border-slate-200 bg-white"
        >
          <summary className="cursor-pointer px-4 py-3 font-medium text-slate-800">
            Evidence {index + 1}
            {chunk.document_title
              ? ` — ${chunk.document_title}`
              : ""}
          </summary>

          <div className="border-t border-slate-100 px-4 py-4">
            <div className="mb-3 grid gap-1 text-xs text-slate-500">
              {chunk.section_title && (
                <div>
                  Section: {chunk.section_title}
                </div>
              )}

              {chunk.page_start !== undefined && (
                <div>
                  Page: {chunk.page_start}
                </div>
              )}

              {chunk.similarity !== undefined && (
                <div>
                  Similarity:{" "}
                  {chunk.similarity.toFixed(3)}
                </div>
              )}

              <div>
                Chunk ID: {chunk.chunk_id}
              </div>
            </div>

            <div className="max-h-72 overflow-y-auto whitespace-pre-wrap text-sm leading-6 text-slate-700">
              {chunk.content}
            </div>
          </div>
        </details>
      ))}
    </div>
  );
}
