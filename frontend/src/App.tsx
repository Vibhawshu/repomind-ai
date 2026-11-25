import { useEffect, useRef, useState } from "react";

type Source = {
  index: number;
  file_path: string;
  start_line: number;
  end_line: number;
  language?: string | null;
  symbol?: string | null;
  score?: number | null;
};

type ChatMsg = {
  role: "user" | "assistant";
  content: string;
  sources?: Source[];
};

const EXAMPLES = [
  { label: "Explain the architecture", q: "Explain the architecture of this repository" },
  { label: "Find authentication", q: "Where is authentication implemented?" },
  { label: "Database usage", q: "Which files interact with the database?" },
  { label: "Login flow", q: "What happens when a user logs in?" },
  { label: "List API endpoints", q: "List the main API endpoints" },
];

export default function App() {
  const [repoId, setRepoId] = useState<string | null>(null);
  const [repoInfo, setRepoInfo] = useState<{ files: number; chunks: number } | null>(null);
  const [uploading, setUploading] = useState(false);
  const [githubUrl, setGithubUrl] = useState("");
  const [question, setQuestion] = useState("");
  const [messages, setMessages] = useState<ChatMsg[]>([]);
  const [asking, setAsking] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [dragOver, setDragOver] = useState(false);
  const bottomRef = useRef<HTMLDivElement>(null);
  const inputRef = useRef<HTMLTextAreaElement>(null);

  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages, asking]);

  async function processResponse(res: Response) {
    const textData = await res.text();
    if (!textData) throw new Error("Backend crashed or timed out.");
    const data = JSON.parse(textData);
    if (!res.ok) throw new Error(data.detail || "Request failed");
    
    setRepoId(data.repo_id);
    setRepoInfo({ files: data.files_indexed, chunks: data.chunks_indexed });
    setError(null);
  }

  async function uploadZip(file: File) {
    if (!file.name.toLowerCase().endsWith(".zip")) {
      setError("Please upload a .zip file.");
      return;
    }
    resetRepo();
    setUploading(true);
    try {
      const form = new FormData();
      form.append("file", file);
      const res = await fetch("/api/repos/upload", { method: "POST", body: form });
      await processResponse(res);
    } catch (err: any) {
      setError(err.message);
    } finally {
      setUploading(false);
    }
  }

  async function uploadGithub(e: React.FormEvent) {
    e.preventDefault();
    if (!githubUrl.trim()) return;
    resetRepo();
    setUploading(true);
    try {
      const res = await fetch("/api/repos/github", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ url: githubUrl }),
      });
      await processResponse(res);
      setGithubUrl(""); // clear on success
    } catch (err: any) {
      setError(err.message);
    } finally {
      setUploading(false);
    }
  }

  function handleFileInput(e: React.ChangeEvent<HTMLInputElement>) {
    const file = e.target.files?.[0];
    if (file) uploadZip(file);
    e.target.value = "";
  }

  function onDragOver(e: React.DragEvent) {
    e.preventDefault(); e.stopPropagation(); setDragOver(true);
  }
  function onDragLeave(e: React.DragEvent) {
    e.preventDefault(); e.stopPropagation(); setDragOver(false);
  }
  function onDrop(e: React.DragEvent) {
    e.preventDefault(); e.stopPropagation(); setDragOver(false);
    const file = e.dataTransfer.files?.[0];
    if (file && !uploading) uploadZip(file);
  }

  async function ask(q: string) {
    if (!q.trim() || !repoId || asking) return;
    const question = q.trim();
    setQuestion("");
    setError(null);
    setMessages((m) => [...m, { role: "user", content: question }]);
    setAsking(true);

    try {
      const res = await fetch("/api/chat", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ repo_id: repoId, question }),
      });
      const textData = await res.text();
      if (!textData) throw new Error("Backend crashed.");
      const data = JSON.parse(textData);
      if (!res.ok) throw new Error(data.detail || "Chat failed");
      
      setMessages((m) => [...m, { role: "assistant", content: data.answer, sources: data.sources }]);
    } catch (err: any) {
      setError(err.message);
    } finally {
      setAsking(false);
      inputRef.current?.focus();
    }
  }

  function resetRepo() {
    setRepoId(null);
    setRepoInfo(null);
    setMessages([]);
    setQuestion("");
    setError(null);
  }

  return (
    <div className="app-bg h-full flex text-slate-100">
      {/* Sidebar */}
      <aside className="w-[320px] flex-shrink-0 border-r border-ink-700/60 bg-ink-900/70 backdrop-blur flex flex-col">
        <div className="px-5 py-5 border-b border-ink-700/60">
          <div className="flex items-center gap-3">
            <div className="w-10 h-10 rounded-xl bg-accent-gradient shadow-glow flex items-center justify-center">
              <svg className="w-5 h-5 text-white" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.2" strokeLinecap="round" strokeLinejoin="round">
                <path d="M8 6L3 12l5 6" /><path d="M16 6l5 6-5 6" />
              </svg>
            </div>
            <div>
              <h1 className="text-[15px] font-semibold tracking-tight text-white">RepoMind AI</h1>
              <p className="text-[11px] text-slate-500">Codebase Intelligence</p>
            </div>
          </div>
        </div>

        <div className="px-5 py-4 border-b border-ink-700/60">
          <div className="text-[10px] font-semibold text-slate-500 uppercase tracking-[0.12em] mb-2">
            Add Repository
          </div>

          <label
            onDragOver={onDragOver} onDragLeave={onDragLeave} onDrop={onDrop}
            className={`block rounded-xl border-2 border-dashed p-4 text-center cursor-pointer transition-all duration-200 ${
              dragOver ? "border-accent-500 bg-accent-500/20 scale-[1.02]" : "border-ink-700 hover:border-accent-600/60 hover:bg-ink-800/40"
            } ${uploading ? "opacity-60 cursor-wait" : ""}`}
          >
            <input type="file" accept=".zip" onChange={handleFileInput} disabled={uploading} className="hidden" />
            {uploading ? (
              <div className="flex items-center justify-center gap-2 text-sm text-slate-300"><Spinner /> Indexing...</div>
            ) : (
              <div className="pointer-events-none">
                <div className="w-8 h-8 mx-auto rounded-lg bg-ink-800 border border-ink-700 flex items-center justify-center mb-2">
                  <svg className="w-4 h-4 text-accent-400" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                    <path strokeLinecap="round" strokeLinejoin="round" d="M12 4v12m0-12l-4 4m4-4l4 4M4 20h16" />
                  </svg>
                </div>
                <div className="text-[13px] font-medium text-slate-200">Upload ZIP</div>
              </div>
            )}
          </label>

          <div className="my-3 text-center text-[10px] text-slate-600 font-semibold">OR</div>

          <form onSubmit={uploadGithub} className="flex gap-1.5">
            <input
              type="url"
              value={githubUrl}
              onChange={(e) => setGithubUrl(e.target.value)}
              placeholder="https://github.com/..."
              disabled={uploading}
              className="flex-1 px-2.5 py-1.5 rounded-lg bg-ink-800 border border-ink-700 text-[11px] text-slate-200 focus:outline-none focus:border-accent-500"
            />
            <button
              type="submit"
              disabled={uploading || !githubUrl.trim()}
              className="px-2.5 py-1.5 rounded-lg bg-ink-700 hover:bg-ink-600 text-slate-200 text-[11px] disabled:opacity-50"
            >
              Go
            </button>
          </form>

          {repoId && repoInfo && (
            <div className="mt-4 rounded-xl bg-ink-850/70 border border-ink-700 p-3 animate-fade-in">
              <div className="flex items-center justify-between mb-2">
                <span className="text-[11px] font-medium text-slate-400">Indexed</span>
                <span className="flex items-center gap-1.5 text-[11px] text-mint-400">
                  <span className="w-1.5 h-1.5 rounded-full bg-mint-400 animate-pulse" /> Ready
                </span>
              </div>
              <div className="grid grid-cols-2 gap-2 text-[11px]">
                <Stat label="Files" value={repoInfo.files} />
                <Stat label="Chunks" value={repoInfo.chunks} />
              </div>
              <button onClick={resetRepo} className="w-full mt-3 text-[11px] text-slate-500 hover:text-red-400 transition">
                Clear &amp; start over
              </button>
            </div>
          )}
        </div>

        <div className="px-5 py-4 flex-1 overflow-y-auto">
          <div className="text-[10px] font-semibold text-slate-500 uppercase tracking-[0.12em] mb-2">
            Try asking
          </div>
          <div className="space-y-1.5">
            {EXAMPLES.map((ex) => (
              <button
                key={ex.q}
                disabled={!repoId || asking}
                onClick={() => ask(ex.q)}
                className="group w-full text-left text-[12.5px] px-3 py-2 rounded-lg text-slate-300 hover:text-white hover:bg-ink-800/70 border border-transparent hover:border-ink-700 transition disabled:opacity-40 disabled:cursor-not-allowed disabled:hover:bg-transparent disabled:hover:text-slate-300"
              >
                <span className="text-slate-600 group-hover:text-accent-400 transition mr-1.5">›</span>
                {ex.label}
              </button>
            ))}
          </div>
        </div>

        <div className="px-5 py-3 border-t border-ink-700/60 text-[10px] text-slate-600 space-y-0.5">
          <div>Qdrant · MiniLM · Groq</div>
          <div>RepoMind AI · v0.1.0</div>
        </div>
      </aside>

      {/* Main */}
      <main className="flex-1 flex flex-col min-w-0">
        <header className="h-14 px-6 flex items-center justify-between border-b border-ink-700/60 bg-ink-900/40 backdrop-blur">
          <div className="text-[13px] text-slate-400 truncate">
            {repoId ? (
              <span className="flex items-center gap-2">
                <svg className="w-3.5 h-3.5 text-accent-400" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                  <path strokeLinecap="round" strokeLinejoin="round" d="M3 7v10a2 2 0 002 2h14a2 2 0 002-2V9a2 2 0 00-2-2h-6l-2-2H5a2 2 0 00-2 2z" />
                </svg>
                <span className="text-slate-500">Chatting with</span>
                <span className="font-mono text-slate-200">{repoId}</span>
              </span>
            ) : (
              <span className="text-slate-600">No repository loaded</span>
            )}
          </div>
          <div className="flex items-center gap-2 text-[11px] text-slate-500">
            <span className="w-1.5 h-1.5 rounded-full bg-mint-400 shadow-[0_0_8px_rgba(52,211,153,0.7)]" />
            Backend online
          </div>
        </header>

        {error && (
          <div className="mx-6 mt-3 px-4 py-2.5 rounded-lg bg-red-950/60 border border-red-800/80 text-red-200 text-[13px] flex items-start justify-between gap-3 animate-slide-up">
            <span>{error}</span>
            <button onClick={() => setError(null)} className="text-red-400 hover:text-red-200">✕</button>
          </div>
        )}

        <div className="flex-1 overflow-y-auto px-6 py-8">
          <div className="max-w-3xl mx-auto space-y-7">
            {messages.length === 0 && (
              <div className="text-center py-20 animate-fade-in">
                <div className="w-16 h-16 mx-auto rounded-2xl bg-accent-gradient shadow-glow flex items-center justify-center mb-6">
                  <svg className="w-8 h-8 text-white" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
                    <path d="M8 6L3 12l5 6" /><path d="M16 6l5 6-5 6" />
                  </svg>
                </div>
                <h2 className="text-xl font-semibold text-white mb-2 tracking-tight">
                  {repoId ? "Ask anything about your codebase" : "Upload a repository to begin"}
                </h2>
                <p className="text-[13.5px] text-slate-500 max-w-md mx-auto leading-relaxed">
                  {repoId ? "Grounded answers with file paths and line references. Pick a prompt on the left or ask your own." : "Drop a ZIP or paste a GitHub URL. We'll index it so you can chat with your code."}
                </p>
              </div>
            )}

            {messages.map((m, i) => (
              <MessageRow key={i} msg={m} />
            ))}

            {asking && (
              <div className="flex gap-3 animate-fade-in">
                <AssistantAvatar />
                <div className="pt-2 flex gap-1">
                  <Dot delay={0} /><Dot delay={150} /><Dot delay={300} />
                </div>
              </div>
            )}

            <div ref={bottomRef} />
          </div>
        </div>

        <form
          onSubmit={(e) => { e.preventDefault(); ask(question); }}
          className="border-t border-ink-700/60 bg-ink-900/50 backdrop-blur p-4"
        >
          <div className="max-w-3xl mx-auto">
            <div className="relative flex items-end gap-2 rounded-xl bg-ink-850 border border-ink-700 focus-within:border-accent-600 focus-within:ring-1 focus-within:ring-accent-600/40 transition p-1.5">
              <textarea
                ref={inputRef}
                value={question}
                onChange={(e) => setQuestion(e.target.value)}
                onKeyDown={(e) => {
                  if (e.key === "Enter" && !e.shiftKey) { e.preventDefault(); ask(question); }
                }}
                rows={1}
                placeholder={repoId ? "Ask about your codebase…" : "Upload a repository first"}
                disabled={!repoId || asking}
                className="flex-1 resize-none bg-transparent px-3 py-2 text-[13.5px] text-slate-100 placeholder-slate-600 focus:outline-none disabled:opacity-50 max-h-40"
              />
              <button
                type="submit"
                disabled={!repoId || asking || !question.trim()}
                className="flex-shrink-0 px-4 py-2 rounded-lg bg-accent-gradient text-white text-[13px] font-semibold disabled:opacity-30 disabled:cursor-not-allowed hover:opacity-95 transition shadow-glow"
              >
                Send
              </button>
            </div>
            <div className="text-[10.5px] text-slate-600 mt-1.5 text-center">
              Enter to send · Shift+Enter for new line
            </div>
          </div>
        </form>
      </main>
    </div>
  );
}

function Stat({ label, value }: { label: string; value: number }) {
  return (
    <div className="rounded-lg bg-ink-800/60 border border-ink-700/60 px-2 py-1.5">
      <div className="text-[9px] uppercase tracking-wider text-slate-500">{label}</div>
      <div className="text-[13px] font-semibold text-slate-200 font-mono">{value}</div>
    </div>
  );
}

function MessageRow({ msg }: { msg: ChatMsg }) {
  const isUser = msg.role === "user";
  return (
    <div className="flex gap-3 animate-slide-up">
      {isUser ? <UserAvatar /> : <AssistantAvatar />}
      <div className="flex-1 min-w-0">
        <div className="text-[11px] font-semibold text-slate-500 mb-1.5">
          {isUser ? "You" : "RepoMind AI"}
        </div>
        <div className={isUser ? "text-[13.5px] whitespace-pre-wrap break-words text-slate-100 bg-ink-800/70 border border-ink-700/60 rounded-xl px-3.5 py-2.5 inline-block max-w-full" : "answer text-[13.5px] whitespace-pre-wrap break-words text-slate-200 leading-relaxed"}>
          {isUser ? msg.content : <MarkdownLite text={msg.content} />}
        </div>

        {msg.sources && msg.sources.length > 0 && (
          <div className="mt-3">
            <div className="text-[10px] font-semibold text-slate-500 uppercase tracking-[0.12em] mb-1.5">Sources</div>
            <div className="flex flex-wrap gap-1.5">
              {msg.sources.map((s) => (
                <div key={s.index} className="flex items-center gap-2 text-[11.5px] px-2.5 py-1.5 rounded-lg bg-ink-850/80 border border-ink-700 hover:border-accent-600/50 hover:bg-ink-800 transition" title={`${s.file_path}:${s.start_line}-${s.end_line}`}>
                  <svg className="w-3 h-3 text-accent-400 flex-shrink-0" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                    <path strokeLinecap="round" strokeLinejoin="round" d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" />
                  </svg>
                  <span className="font-mono text-slate-300 truncate max-w-[180px]">{s.file_path}</span>
                  <span className="text-slate-500 font-mono">:{s.start_line}-{s.end_line}</span>
                  {typeof s.score === "number" && (
                    <span className="text-[10px] text-accent-400 font-mono bg-accent-500/10 rounded px-1">{s.score.toFixed(2)}</span>
                  )}
                </div>
              ))}
            </div>
          </div>
        )}
      </div>
    </div>
  );
}

function MarkdownLite({ text }: { text: string }) {
  const parts: React.ReactNode[] = [];
  const fence = /```([a-zA-Z0-9]*)\n?([\s\S]*?)```/g;
  let last = 0, m: RegExpExecArray | null, key = 0;
  while ((m = fence.exec(text)) !== null) {
    if (m.index > last) parts.push(<InlineText key={key++} text={text.slice(last, m.index)} />);
    parts.push(<pre key={key++}><code>{m[2].replace(/\n$/, "")}</code></pre>);
    last = m.index + m[0].length;
  }
  if (last < text.length) parts.push(<InlineText key={key++} text={text.slice(last)} />);
  return <>{parts}</>;
}

function InlineText({ text }: { text: string }) {
  const tokens = text.split(/(`[^`]+`)/g);
  return (
    <>
      {tokens.map((t, i) => t.startsWith("`") && t.endsWith("`") ? <code key={i}>{t.slice(1, -1)}</code> : <span key={i}>{t}</span>)}
    </>
  );
}

function UserAvatar() {
  return <div className="w-8 h-8 flex-shrink-0 rounded-lg bg-ink-700 border border-ink-600 flex items-center justify-center text-[11px] font-bold text-slate-300">You</div>;
}

function AssistantAvatar() {
  return <div className="w-8 h-8 flex-shrink-0 rounded-lg bg-accent-gradient shadow-glow flex items-center justify-center text-[11px] font-bold text-white">R</div>;
}

function Dot({ delay }: { delay: number }) {
  return <span className="w-1.5 h-1.5 rounded-full bg-accent-400 animate-bounce" style={{ animationDelay: `${delay}ms` }} />;
}

function Spinner() {
  return (
    <svg className="w-4 h-4 animate-spin" viewBox="0 0 24 24" fill="none">
      <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4" />
      <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8v4a4 4 0 00-4 4H4z" />
    </svg>
  );
}