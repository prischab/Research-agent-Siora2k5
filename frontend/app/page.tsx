"use client";

import { useState, useRef, useEffect } from "react";

const API_URL = "http://127.0.0.1:8000";

type Message = { role: "user" | "assistant"; content: string };
type Chat = { id: string; title: string; messages: Message[] };

const STORAGE_KEY = "siora2k5_chats";

export default function Home() {
  const [chats, setChats] = useState<Chat[]>([]);
  const [activeId, setActiveId] = useState<string | null>(null);
  const [input, setInput] = useState("");
  const [loading, setLoading] = useState(false);
  const [uploadStatus, setUploadStatus] = useState("");
  const [uploadedFiles, setUploadedFiles] = useState<string[]>([]);
  const [imageFile, setImageFile] = useState<File | null>(null);
  const [copiedIndex, setCopiedIndex] = useState<number | null>(null);
  const imageInputRef = useRef<HTMLInputElement>(null);
  const bottomRef = useRef<HTMLDivElement>(null);
  const fileInputRef = useRef<HTMLInputElement>(null);

  useEffect(() => {
    try {
      const saved = localStorage.getItem(STORAGE_KEY);
      if (saved) {
        const parsed: Chat[] = JSON.parse(saved);
        setChats(parsed);
        if (parsed.length > 0) setActiveId(parsed[0].id);
      }
    } catch {}
  }, []);

  useEffect(() => {
    try {
      localStorage.setItem(STORAGE_KEY, JSON.stringify(chats));
    } catch {}
  }, [chats]);

  const activeChat = chats.find((c) => c.id === activeId) || null;

  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [activeChat?.messages, loading]);

  function newChat() {
    setActiveId(null);
    setInput("");
  }

  function deleteChat(id: string, e: React.MouseEvent) {
    e.stopPropagation();
    setChats((prev) => prev.filter((c) => c.id !== id));
    if (activeId === id) setActiveId(null);
  }

  async function handleUpload(e: React.ChangeEvent<HTMLInputElement>) {
    const file = e.target.files?.[0];
    if (!file) return;
    setUploadStatus("Indexing...");
    try {
      const formData = new FormData();
      formData.append("file", file);
      const res = await fetch(`${API_URL}/upload`, { method: "POST", body: formData });
      const data = await res.json();
      setUploadStatus(data.message || "Added.");
      setUploadedFiles((prev) => [...prev, file.name]);
    } catch {
      setUploadStatus("Upload failed.");
    }
    setTimeout(() => setUploadStatus(""), 5000);
    if (fileInputRef.current) fileInputRef.current.value = "";
  }

  async function sendMessage() {
    if ((!input.trim() && !imageFile) || loading) return;
    const text = input;
    setInput("");
    setLoading(true);

    const displayText = imageFile ? (text || "[Image attached]") : text;
    let chatId = activeId;
    if (!chatId) {
      chatId = Date.now().toString();
      const title = displayText.length > 40 ? displayText.slice(0, 40) + "..." : displayText;
      const newC: Chat = { id: chatId, title, messages: [{ role: "user", content: displayText }] };
      setChats((prev) => [newC, ...prev]);
      setActiveId(chatId);
    } else {
      setChats((prev) =>
        prev.map((c) =>
          c.id === chatId ? { ...c, messages: [...c.messages, { role: "user", content: displayText }] } : c
        )
      );
    }

    try {
      let answer: string;
      if (imageFile) {
        const formData = new FormData();
        formData.append("file", imageFile);
        formData.append("message", text);
        const res = await fetch(`${API_URL}/chat-image`, { method: "POST", body: formData });
        const data = await res.json();
        answer = data.answer;
        setImageFile(null);
      } else {
        const res = await fetch(`${API_URL}/chat`, {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({ message: text }),
        });
        const data = await res.json();
        answer = data.answer;
      }
      setChats((prev) =>
        prev.map((c) =>
          c.id === chatId
            ? { ...c, messages: [...c.messages, { role: "assistant", content: answer }] }
            : c
        )
      );
    } catch {
      setChats((prev) =>
        prev.map((c) =>
          c.id === chatId
            ? { ...c, messages: [...c.messages, { role: "assistant", content: "I couldn't reach the server. Is the backend running?" }] }
            : c
        )
      );
    } finally {
      setLoading(false);
    }
  }

  const messages = activeChat?.messages || [];

  return (
    <div className="flex h-screen bg-[#F5F1E8] text-[#2A2724]" style={{ fontFamily: "'Newsreader', Georgia, serif" }}>
      {/* Sidebar */}
      <aside className="w-64 bg-[#EFE9DB] border-r border-[#E0D8C5] flex flex-col shrink-0">
        <div className="p-4">
          <div className="flex items-center gap-2.5 mb-5 px-1">
            <div className="w-8 h-8 rounded-lg bg-[#2A2724] flex items-center justify-center text-[#F5F1E8] font-semibold text-sm">S</div>
            <span className="font-semibold text-lg">Siora2k5</span>
          </div>
          <button
            onClick={newChat}
            className="w-full rounded-xl bg-[#2A2724] text-[#F5F1E8] py-2.5 text-sm font-medium hover:bg-[#403A33] transition-colors"
          >
            + New chat
          </button>
        </div>

        <div className="flex-1 overflow-y-auto px-2 pb-4 space-y-1">
          {chats.map((c) => (
            <div
              key={c.id}
              onClick={() => setActiveId(c.id)}
              className={`group flex items-center justify-between rounded-lg px-3 py-2.5 text-sm cursor-pointer transition-colors ${
                c.id === activeId ? "bg-[#E0D8C5]" : "hover:bg-[#E6DECC]"
              }`}
            >
              <span className="truncate text-[#3D3A33]">{c.title}</span>
              <button
                onClick={(e) => deleteChat(c.id, e)}
                className="opacity-0 group-hover:opacity-100 text-[#A8A085] hover:text-[#6B6453] ml-2 shrink-0"
                aria-label="Delete chat"
              >
                ×
              </button>
            </div>
          ))}
        </div>

        {/* Document upload */}
        <div className="p-3 border-t border-[#E0D8C5]">
          <input
            ref={fileInputRef}
            type="file"
            accept=".txt,.pdf"
            onChange={handleUpload}
            className="hidden"
          />
          <button
            onClick={() => fileInputRef.current?.click()}
            className="w-full rounded-xl border border-[#D8CDB5] bg-[#F5F1E8] py-2.5 text-sm font-medium text-[#5C564A] hover:bg-[#EFE9DB] transition-colors flex items-center justify-center gap-2"
          >
            <span>📄</span> Upload document
          </button>
          {uploadedFiles.length > 0 && (
            <div className="mt-3 space-y-1.5">
              {uploadedFiles.map((name, i) => (
                <div key={i} className="flex items-center gap-2 text-xs bg-[#F5F1E8] border border-[#E0D8C5] rounded-lg px-2.5 py-2 text-[#5C564A]">
                  <span>📎</span>
                  <span className="truncate">{name}</span>
                </div>
              ))}
            </div>
          )}
          {uploadStatus && (
            <p className="text-xs text-[#8A8270] mt-2 px-1">{uploadStatus}</p>
          )}
          <p className="text-[10px] text-[#B0A688] mt-2 px-1 leading-snug">
            Documents stay available across all chats.
          </p>
        </div>
      </aside>

      {/* Main chat column */}
      <div className="flex-1 flex flex-col">
        <main className="flex-1 overflow-y-auto">
          <div className="max-w-3xl mx-auto px-6 py-8">
            {messages.length === 0 && (
              <div className="text-center mt-24">
                <div className="w-14 h-14 rounded-2xl bg-[#2A2724] flex items-center justify-center text-[#F5F1E8] text-xl font-semibold mx-auto mb-5">S</div>
                <h2 className="text-2xl font-semibold mb-2">How can I help you today?</h2>
                <p className="text-[#8A8270] max-w-md mx-auto">
                  I can search the web, work through calculations, answer questions about documents you share, and understand images.
                </p>
              </div>
            )}
            <div className="space-y-6">
              {messages.map((msg, i) => (
                <div key={i} className={`flex flex-col ${msg.role === "user" ? "items-end" : "items-start"}`}>
                  <div className={`max-w-[85%] rounded-2xl px-5 py-3.5 leading-relaxed whitespace-pre-wrap ${
                    msg.role === "user" ? "bg-[#2A2724] text-[#F5F1E8]" : "bg-[#FBF8F1] border border-[#E8E0CF] text-[#2A2724]"
                  }`}>
                    {msg.content}
                  </div>
                  <button
                    onClick={() => {
                      navigator.clipboard.writeText(msg.content);
                      setCopiedIndex(i);
                      setTimeout(() => setCopiedIndex(null), 1500);
                    }}
                    className="mt-1.5 p-1 text-[#B0A688] hover:text-[#5C564A] transition-colors"
                    aria-label="Copy message"
                    title="Copy"
                  >
                    {copiedIndex === i ? (
                      <svg width="15" height="15" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.5" strokeLinecap="round" strokeLinejoin="round">
                        <polyline points="20 6 9 17 4 12"></polyline>
                      </svg>
                    ) : (
                      <svg width="15" height="15" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
                        <rect x="9" y="9" width="13" height="13" rx="2" ry="2"></rect>
                        <path d="M5 15H4a2 2 0 0 1-2-2V4a2 2 0 0 1 2-2h9a2 2 0 0 1 2 2v1"></path>
                      </svg>
                    )}
                  </button>
                </div>
              ))}
              {loading && (
                <div className="flex justify-start">
                  <div className="bg-[#FBF8F1] border border-[#E8E0CF] rounded-2xl px-5 py-3.5">
                    <span className="inline-flex gap-1">
                      <span className="w-2 h-2 bg-[#C4BBA5] rounded-full animate-bounce [animation-delay:-0.3s]"></span>
                      <span className="w-2 h-2 bg-[#C4BBA5] rounded-full animate-bounce [animation-delay:-0.15s]"></span>
                      <span className="w-2 h-2 bg-[#C4BBA5] rounded-full animate-bounce"></span>
                    </span>
                  </div>
                </div>
              )}
              <div ref={bottomRef} />
            </div>
          </div>
        </main>

        <div className="border-t border-[#E0D8C5] bg-[#F5F1E8]">
          <div className="max-w-3xl mx-auto px-6 py-4">
            {imageFile && (
              <div className="pb-2">
                <span className="inline-flex items-center gap-2 text-xs bg-[#EFE9DB] text-[#5C564A] rounded-lg px-2.5 py-1.5 border border-[#E0D8C5]">
                  🖼 {imageFile.name}
                  <button onClick={() => setImageFile(null)} className="text-[#8A8270] hover:text-[#5C564A]">×</button>
                </span>
              </div>
            )}
            <div className="flex items-end gap-2 bg-[#FBF8F1] border border-[#E0D8C5] rounded-2xl px-3 py-3 shadow-sm focus-within:border-[#2A2724] transition-colors">
              <input
                ref={imageInputRef}
                type="file"
                accept="image/*"
                onChange={(e) => setImageFile(e.target.files?.[0] || null)}
                className="hidden"
              />
              <button
                onClick={() => imageInputRef.current?.click()}
                className="shrink-0 w-8 h-8 flex items-center justify-center rounded-lg text-[#8A8270] hover:text-[#2A2724] hover:bg-[#EFE9DB] transition-colors"
                aria-label="Attach image"
                title="Attach an image"
              >
                <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
                  <rect x="3" y="3" width="18" height="18" rx="2" ry="2"></rect>
                  <circle cx="8.5" cy="8.5" r="1.5"></circle>
                  <polyline points="21 15 16 10 5 21"></polyline>
                </svg>
              </button>
              <textarea
                className="flex-1 resize-none outline-none bg-transparent max-h-32 text-[#2A2724] placeholder:text-[#B0A688]"
                placeholder="Ask Siora2k5 anything..."
                rows={1}
                value={input}
                onChange={(e) => setInput(e.target.value)}
                onKeyDown={(e) => {
                  if (e.key === "Enter" && !e.shiftKey) {
                    e.preventDefault();
                    sendMessage();
                  }
                }}
              />
              <button
                onClick={sendMessage}
                disabled={loading || (!input.trim() && !imageFile)}
                className="rounded-xl bg-[#2A2724] text-[#F5F1E8] w-9 h-9 flex items-center justify-center disabled:opacity-30 hover:bg-[#403A33] transition-colors shrink-0"
                aria-label="Send"
              >
                ↑
              </button>
            </div>
            <p className="text-center text-xs text-[#B0A688] mt-3">
              Siora2k5 can make mistakes. Verify important information.
            </p>
          </div>
        </div>
      </div>
    </div>
  );
}