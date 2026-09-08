"use client";

import { FormEvent, useEffect, useRef, useState } from "react";
import { ResponseCard } from "@/components/ResponseCard";
import type { AskResponse, ChatMessage } from "@/lib/types";

const API_URL = process.env.NEXT_PUBLIC_API_URL || "/api/backend";

function newId() {
  return `${Date.now()}-${Math.random().toString(16).slice(2)}`;
}

export default function Page() {
  const [input, setInput] = useState("");
  const [messages, setMessages] = useState<ChatMessage[]>([]);
  const [pending, setPending] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const listRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    listRef.current?.scrollTo({ top: listRef.current.scrollHeight, behavior: "smooth" });
  }, [messages, pending, error]);

  async function onSubmit(event: FormEvent) {
    event.preventDefault();
    const question = input.trim();
    if (!question || pending) return;

    setInput("");
    setError(null);
    setPending(true);
    setMessages((current) => [...current, { id: newId(), role: "user", text: question }]);

    try {
      const response = await fetch(`${API_URL}/ask`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ question }),
      });
      if (!response.ok) {
        const body = await response.json().catch(() => ({}));
        throw new Error(body.detail || `Request failed (${response.status})`);
      }
      const data = (await response.json()) as AskResponse;
      setMessages((current) => [...current, { id: newId(), role: "assistant", response: data }]);
    } catch (err) {
      const message =
        err instanceof Error && err.message.includes("Failed to fetch")
          ? "Backend unreachable. Start the FastAPI server on port 8000."
          : err instanceof Error
            ? err.message
            : "Request failed.";
      setError(message);
    } finally {
      setPending(false);
    }
  }

  return (
    <div className="flex min-h-screen flex-col">
      <header className="border-b border-zinc-200 bg-white">
        <div className="mx-auto w-full max-w-3xl px-6 py-4">
          <p className="text-[13px] font-medium tracking-wide text-zinc-900">Craftify Support</p>
        </div>
      </header>

      <main className="mx-auto flex w-full max-w-3xl flex-1 flex-col px-6 py-6">
        <div ref={listRef} className="flex-1 space-y-6 overflow-y-auto pb-4">
          {messages.length === 0 && !error && (
            <p className="text-sm text-zinc-500">
              Ask about Craftify generation, exports, billing, or file a support ticket.
            </p>
          )}

          {messages.map((message) =>
            message.role === "user" ? (
              <div key={message.id} className="flex justify-end">
                <div className="max-w-[85%] rounded-lg border border-zinc-200 bg-white px-4 py-3 text-[15px] leading-6 text-zinc-900">
                  {message.text}
                </div>
              </div>
            ) : (
              <ResponseCard key={message.id} response={message.response} />
            ),
          )}

          {pending && (
            <p className="text-[13px] text-zinc-500">Looking through the Craftify docs…</p>
          )}

          {error && (
            <div className="rounded-lg border border-red-200 bg-red-50 px-4 py-3 text-sm text-red-700">
              {error}
            </div>
          )}
        </div>

        <form onSubmit={onSubmit} className="sticky bottom-0 bg-zinc-50 pt-2">
          <div className="flex items-end gap-2 rounded-xl border border-zinc-200 bg-white p-2 transition duration-150 ease-out focus-within:shadow-sm">
            <textarea
              value={input}
              onChange={(event) => setInput(event.target.value)}
              onKeyDown={(event) => {
                if (event.key === "Enter" && !event.shiftKey) {
                  event.preventDefault();
                  event.currentTarget.form?.requestSubmit();
                }
              }}
              rows={1}
              placeholder="Ask a question"
              className="min-h-[44px] flex-1 resize-none bg-transparent px-3 py-2 text-[15px] text-zinc-900 outline-none placeholder:text-zinc-400"
            />
            <button
              type="submit"
              disabled={pending || !input.trim()}
              className="rounded-lg bg-indigo-600 px-3 py-2 text-sm font-medium text-white transition duration-150 ease-out hover:bg-indigo-700 disabled:cursor-not-allowed disabled:bg-zinc-300"
            >
              Send
            </button>
          </div>
        </form>
      </main>
    </div>
  );
}
