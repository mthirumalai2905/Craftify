export type Source = {
  document: string;
  snippet: string;
};

export type AskResponse =
  | { type: "answer"; answer: string; sources: Source[] }
  | { type: "abstention"; message: string; sources: Source[] }
  | {
      type: "tool_call";
      tool: string;
      arguments: { summary: string; priority: string };
      result: { ticket_id: string; status: string };
    }
  | { type: "clarification"; message: string }
  | { type: "refusal"; message: string };

export type ChatMessage =
  | { id: string; role: "user"; text: string }
  | { id: string; role: "assistant"; response: AskResponse };
