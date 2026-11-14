"use client";

import { useCallback, useEffect, useState } from "react";
import Link from "next/link";
import { ThemeToggle } from "../components/theme-toggle";
import { SessionControls } from "../components/session-controls";

const API = "/api/backend";

type DocumentItem = { id: string; filename: string; status: string; chunk_count: number; created_at: string; error?: string | null };
type Source = { document_id: string; filename: string; page: number; score: number; excerpt: string };
type Message = { role: "user" | "assistant"; content: string; sources?: Source[] };

export default function Home() {
  const [patientId, setPatientId] = useState("");
  const [patientName, setPatientName] = useState("Demo patient");
  const [documents, setDocuments] = useState<DocumentItem[]>([]);
  const [messages, setMessages] = useState<Message[]>([
    { role: "assistant", content: "Welcome to SmartDoctor. Upload a synthetic patient document, then ask a question. Answers are grounded in retrieved document passages." },
  ]);
  const [question, setQuestion] = useState("");
  const [busy, setBusy] = useState(false);
  const [uploading, setUploading] = useState(false);
  const [error, setError] = useState("");
  const [conversationId, setConversationId] = useState("");

  const loadDocuments = useCallback(async (id: string) => {
    if (!id) return;
    const response = await fetch(`${API}/api/v1/workspace/documents?patient_id=${id}`);
    if (response.ok) setDocuments(await response.json());
  }, []);

  useEffect(() => {
    const initialize = async () => {
      try {
        let response = await fetch(`${API}/api/v1/workspace/bootstrap`, { method: "POST" });
        if (!response.ok && process.env.NEXT_PUBLIC_DEV_AUTH_ENABLED === "true") response = await fetch(`${API}/api/v1/workspace/demo/bootstrap`, { method: "POST" });
        if (!response.ok) throw new Error((await response.json()).detail || "Could not initialize workspace");
        const data = await response.json();
        setPatientId(data.patient_id);
        setPatientName(data.display_label);
        await loadDocuments(data.patient_id);
      } catch (e) {
        setError(e instanceof Error ? e.message : "API is unavailable");
      }
    };
    void initialize();
  }, [loadDocuments]);

  const upload = async (file?: File) => {
    if (!file || !patientId) return;
    setUploading(true); setError("");
    try {
      const body = new FormData(); body.append("file", file);
      const response = await fetch(`${API}/api/v1/workspace/documents?patient_id=${patientId}`, { method: "POST", body });
      const data = await response.json();
      if (!response.ok) throw new Error(data.detail || "Upload failed");
      await loadDocuments(patientId);
    } catch (e) { setError(e instanceof Error ? e.message : "Upload failed"); }
    finally { setUploading(false); }
  };

  const ask = async () => {
    const prompt = question.trim();
    if (!prompt || !patientId || busy) return;
    setMessages(current => [...current, { role: "user", content: prompt }]);
    setQuestion(""); setBusy(true); setError("");
    try {
      const response = await fetch(`${API}/api/v1/workspace/chat`, {
        method: "POST", headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ patient_id: patientId, question: prompt, conversation_id: conversationId || null }),
      });
      const data = await response.json();
      if (!response.ok) throw new Error(data.detail || "Chat request failed");
      setConversationId(data.conversation_id);
      setMessages(current => [...current, { role: "assistant", content: data.answer, sources: data.sources }]);
    } catch (e) {
      setError(e instanceof Error ? e.message : "Chat request failed");
      setMessages(current => [...current, { role: "assistant", content: "I couldn't complete that request. Please check the API and database services, then try again." }]);
    } finally { setBusy(false); }
  };

  return (
    <main className="app-shell">
      <aside className="sidebar">
        <a className="brand" href="#"><span className="brand-symbol">✚</span><span>smartdoctor</span></a>
        <div className="workspace-label">WORKSPACE</div>
        <a className="nav-item active" href="#overview"><span>▦</span> Overview</a>
        <a className="nav-item" href="#records"><span>▤</span> Patient records</a>
        <a className="nav-item" href="#assistant"><span>✧</span> AI assistant</a>
        <div className="workspace-label nav-spacer">PREFERENCES</div>
        <Link className="nav-item" href="/settings"><span>⚙</span> Settings</Link>
        <Link className="nav-item" href="/profile"><span>◉</span> My profile</Link>
        <div className="sidebar-bottom">
          <div className="secure-card"><span className="secure-icon">⌑</span><div><strong>Private workspace</strong><small>Authorized access only</small></div></div>
          <div className="profile"><div className="avatar">AM</div><div><strong>{patientName}</strong><small>Patient workspace</small></div><span className="dots">•••</span></div>
        </div>
      </aside>

      <section className="main-area">
        <header className="topbar">
          <div><span className="breadcrumb">Workspace / </span><strong>Overview</strong></div>
          <div className="top-actions"><span className="status-dot"></span><span>Local environment</span><ThemeToggle /><SessionControls /><span className="top-avatar">AM</span></div>
        </header>
        <div className="content" id="overview">
          <div className="welcome-row">
            <div><p className="eyebrow">PATIENT KNOWLEDGE HUB</p><h1>Your health records, connected.</h1><p className="subheading">Bring documents together and explore their contents with evidence-linked AI assistance.</p></div>
            <label className="upload-button">＋ Upload document<input type="file" accept=".pdf,.docx,.txt,.md" disabled={!patientId || uploading} onChange={e => { void upload(e.target.files?.[0]); e.currentTarget.value = ""; }} /></label>
          </div>
          {error && <div className="error-banner" role="alert">{error}</div>}
          <div className="stat-grid">
            <article className="stat-card"><div className="stat-icon teal">▤</div><span>Documents</span><strong>{documents.length}</strong><small>In this patient workspace</small></article>
            <article className="stat-card"><div className="stat-icon violet">✧</div><span>Indexed chunks</span><strong>{documents.reduce((n, d) => n + d.chunk_count, 0)}</strong><small>Available for semantic search</small></article>
            <article className="stat-card"><div className="stat-icon amber">◷</div><span>Storage status</span><strong className="status-text">Connected</strong><small>PostgreSQL · MongoDB · Qdrant</small></article>
          </div>

          <div className="section-heading" id="records"><div><h2>Patient documents</h2><p>Upload and index source records for this workspace.</p></div><span className="count-pill">{documents.length} files</span></div>
          <section className="documents-panel">
            {uploading && <div className="upload-progress">Processing document · extracting text, creating chunks and embeddings…</div>}
            {documents.length === 0 ? <div className="empty-state"><div className="empty-icon">▤</div><h3>No documents yet</h3><p>Upload a PDF, Word document or text file to build your patient knowledge base.</p><label className="secondary-button">Choose a file<input type="file" accept=".pdf,.docx,.txt,.md" onChange={e => { void upload(e.target.files?.[0]); e.currentTarget.value = ""; }} /></label></div> :
              <div className="document-list">{documents.map(doc => <article className="document-row" key={doc.id}><div className="file-icon">PDF</div><div className="document-meta"><strong>{doc.filename}</strong><small>{new Date(doc.created_at).toLocaleString()} · {doc.chunk_count} chunks</small></div><span className={`document-status ${doc.status}`}>{doc.status}</span></article>)}</div>}
          </section>

          <div className="section-heading assistant-heading" id="assistant"><div><h2>Ask your records</h2><p>Answers are grounded in retrieved passages and show their source.</p></div><span className="powered-pill">✧ RAG ASSISTANT</span></div>
          <section className="chat-panel">
            <div className="chat-messages">{messages.map((message, index) => <article className={`message ${message.role}`} key={index}><div className="message-avatar">{message.role === "assistant" ? "✚" : "AM"}</div><div className="message-body"><div className="message-author">{message.role === "assistant" ? "SmartDoctor assistant" : "You"}</div><p>{message.content}</p>{message.sources && message.sources.length > 0 && <div className="sources"><strong>Sources used</strong>{message.sources.map((source, i) => <div className="source-item" key={`${source.document_id}-${i}`}><span>[{i + 1}]</span><div><b>{source.filename} · page {source.page}</b><small>{source.excerpt}</small></div></div>)}</div>}</div></article>)}
              {busy && <div className="typing"><span></span><span></span><span></span> Searching patient records…</div>}
            </div>
            <form className="chat-composer" onSubmit={e => { e.preventDefault(); void ask(); }}><input value={question} onChange={e => setQuestion(e.target.value)} placeholder="Ask a question about the uploaded records…" disabled={!patientId || busy} /><button disabled={!question.trim() || busy}>Send <span>↗</span></button></form>
            <div className="chat-disclaimer">SmartDoctor provides document summaries, not medical diagnosis or treatment advice. Always confirm clinical decisions with a qualified professional.</div>
          </section>
          <footer className="page-footer">SmartDoctor · Development preview <span>Built for secure, evidence-aware care workflows</span></footer>
        </div>
      </section>
    </main>
  );
}
