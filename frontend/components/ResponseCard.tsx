import type { AskResponse, UsageMeta } from "@/lib/types";

function formatCost(usd: number): string {
  if (usd > 0 && usd < 0.0001) {
    return `$${usd.toFixed(6)}`;
  }
  return `$${usd.toFixed(4)}`;
}

function MetaFooter({ meta }: { meta?: UsageMeta }) {
  if (!meta) return null;
  const parts = [`${meta.elapsed_ms}ms`, `${meta.total_tokens} tokens`];
  if (meta.estimated_cost_usd != null) {
    parts.push(formatCost(meta.estimated_cost_usd));
  }
  return <p className="mt-3 text-[12px] text-zinc-400">{parts.join(" · ")}</p>;
}

const badges: Record<AskResponse["type"], { label: string; className: string }> = {
  answer: {
    label: "ANSWER",
    className: "border-zinc-200 bg-zinc-50 text-zinc-600",
  },
  abstention: {
    label: "NOT IN DOCS",
    className: "border-amber-200 bg-amber-50 text-amber-700",
  },
  tool_call: {
    label: "TOOL CALL",
    className: "border-blue-200 bg-blue-50 text-blue-700",
  },
  clarification: {
    label: "CLARIFICATION",
    className: "border-violet-200 bg-violet-50 text-violet-700",
  },
  refusal: {
    label: "REFUSED",
    className: "border-red-200 bg-red-50 text-red-700",
  },
};

const frames: Record<AskResponse["type"], string> = {
  answer: "border-zinc-200 bg-white",
  abstention: "border-amber-200 bg-amber-50",
  tool_call: "border-blue-200 bg-blue-50",
  clarification: "border-violet-200 bg-violet-50",
  refusal: "border-red-200 bg-red-50",
};

function Badge({ type }: { type: AskResponse["type"] }) {
  const badge = badges[type];
  return (
    <span
      className={`inline-flex rounded-full border px-2 py-0.5 text-xs font-medium uppercase tracking-wide ${badge.className}`}
    >
      {badge.label}
    </span>
  );
}

export function ResponseCard({ response }: { response: AskResponse }) {
  return (
    <article className={`rounded-lg border p-4 ${frames[response.type]}`}>
      <div className="mb-3">
        <Badge type={response.type} />
      </div>

      {response.type === "answer" && (
        <div className="space-y-4">
          <p className="text-[15px] leading-6 text-zinc-900">{response.answer}</p>
          {response.sources.length > 0 && (
            <div className="space-y-3 border-t border-zinc-200 pt-3">
              <p className="text-[13px] font-medium text-zinc-500">Sources</p>
              <div className="space-y-2">
                {response.sources.map((source) => (
                  <div
                    key={source.document}
                    className="rounded-lg border border-zinc-200 bg-zinc-50 px-3 py-2"
                  >
                    <p className="font-mono text-[13px] text-zinc-900">{source.document}</p>
                    <p className="mt-1 font-mono text-[13px] leading-5 text-zinc-500">
                      {source.snippet}
                    </p>
                  </div>
                ))}
              </div>
            </div>
          )}
        </div>
      )}

      {response.type === "abstention" && (
        <p className="text-[15px] leading-6 text-amber-700">{response.message}</p>
      )}

      {response.type === "tool_call" && (
        <div className="space-y-2 text-[15px] leading-6 text-blue-700">
          <p>
            Tool <span className="font-mono">{response.tool}</span>
          </p>
          <p>
            Summary: <span className="font-mono">{response.arguments.summary}</span>
          </p>
          <p>
            Priority: <span className="font-mono">{response.arguments.priority}</span>
          </p>
          <p>
            Result:{" "}
            <span className="font-mono">
              {response.result.ticket_id} · {response.result.status}
            </span>
          </p>
        </div>
      )}

      {response.type === "clarification" && (
        <p className="text-[15px] leading-6 text-violet-700">{response.message}</p>
      )}

      {response.type === "refusal" && (
        <p className="text-[15px] leading-6 text-red-700">{response.message}</p>
      )}

      <MetaFooter meta={response.meta} />
    </article>
  );
}
