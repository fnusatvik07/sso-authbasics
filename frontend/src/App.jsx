import { useState, useRef, useEffect, useCallback } from "react";
import { motion, AnimatePresence } from "motion/react";
import ReactMarkdown from "react-markdown";
import "./App.css";

const API = "http://localhost:8000/chat";

const SUGGESTIONS = [
  "What is RAG?",
  "How do LangChain agents work?",
  "What is 256 \u00d7 128?",
  "Tell me about FAISS",
];

const Bolt = (props) => (
  <svg viewBox="0 0 24 24" fill="none" strokeLinecap="round" strokeLinejoin="round" {...props}>
    <path d="M13 2L3 14h9l-1 8 10-12h-9l1-8z" />
  </svg>
);

const Arrow = () => (
  <svg width="17" height="17" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round">
    <line x1="5" y1="12" x2="19" y2="12" /><polyline points="12 5 19 12 12 19" />
  </svg>
);

const SendIcon = () => (
  <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
    <path d="M22 2L11 13" /><path d="M22 2L15 22L11 13L2 9L22 2Z" />
  </svg>
);


/* ═══════════════════════════════════════════════════
   LANDING PAGE
   ═══════════════════════════════════════════════════ */

function Landing({ onChat }) {
  const [scrolled, setScrolled] = useState(false);

  useEffect(() => {
    const fn = () => setScrolled(window.scrollY > 30);
    window.addEventListener("scroll", fn);
    return () => window.removeEventListener("scroll", fn);
  }, []);

  const scrollTo = (id) =>
    document.getElementById(id)?.scrollIntoView({ behavior: "smooth" });

  return (
    <>
      {/* Nav */}
      <nav className={`nav ${scrolled ? "nav--glass" : ""}`}>
        <div className="nav__brand">
          <span className="nav__mark"><Bolt stroke="white" strokeWidth="2" /></span>
          <span className="nav__wordmark">AgentFlow</span>
        </div>
        <div className="nav__right">
          <button className="nav__link" onClick={() => scrollTo("features")}>Features</button>
          <button className="nav__link" onClick={() => scrollTo("how")}>How it works</button>
          <button className="nav__btn nav__btn--dark" onClick={onChat}>
            Open Chat
          </button>
        </div>
      </nav>

      {/* Hero */}
      <section className="hero">
        <motion.div
          className="hero__inner"
          initial={{ opacity: 0, y: 24 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.7, ease: [0.16, 1, 0.3, 1] }}
        >
          <motion.span
            className="hero__pill"
            initial={{ opacity: 0, scale: 0.92 }}
            animate={{ opacity: 1, scale: 1 }}
            transition={{ delay: 0.2, duration: 0.4 }}
          >
            <span className="hero__pill-dot" />
            Powered by LangChain &amp; LangGraph
          </motion.span>

          <h1 className="hero__h1">
            Research smarter<br />with <em>AgentFlow</em>
          </h1>

          <p className="hero__p">
            An AI assistant that autonomously retrieves knowledge,
            searches the web, and computes answers &mdash; so you don't have to.
          </p>

          <div className="hero__actions">
            <button className="hero__primary" onClick={onChat}>
              Start chatting <Arrow />
            </button>
            <button className="hero__secondary" onClick={() => scrollTo("how")}>
              See how it works
            </button>
          </div>

          <motion.div
            className="hero__proof"
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            transition={{ delay: 0.5, duration: 0.6 }}
          >
            <span className="hero__proof-label">Built with</span>
            <div className="hero__proof-logos">
              <span>LangChain</span>
              <span>LangGraph</span>
              <span>FastAPI</span>
              <span>FAISS</span>
              <span>OpenAI</span>
            </div>
          </motion.div>
        </motion.div>
      </section>

      {/* Features */}
      <section className="features" id="features">
        <div className="section-eyebrow">Built-in tools</div>
        <h2 className="section-title">Three tools. One intelligent agent.</h2>
        <div className="features__grid">
          {[
            { icon: "\u{1F50D}", c: "blue",  name: "Knowledge Base",
              desc: "Searches a FAISS vector store of documents using semantic similarity. Finds the most relevant context instantly." },
            { icon: "\u{1F310}", c: "pink",  name: "Web Search",
              desc: "When local knowledge isn\u2019t enough, the agent searches the web via Tavily for real-time information." },
            { icon: "\u{1F9EE}", c: "amber", name: "Calculator",
              desc: "Handles mathematical expressions on the fly. The agent recognizes math questions and routes them automatically." },
          ].map((f, i) => (
            <motion.div
              key={f.name}
              className="fcard"
              initial={{ opacity: 0, y: 16 }}
              whileInView={{ opacity: 1, y: 0 }}
              viewport={{ once: true }}
              transition={{ delay: i * 0.08, duration: 0.45, ease: [0.16, 1, 0.3, 1] }}
            >
              <div className={`fcard__icon fcard__icon--${f.c}`}>{f.icon}</div>
              <div className="fcard__name">{f.name}</div>
              <div className="fcard__desc">{f.desc}</div>
            </motion.div>
          ))}
        </div>
      </section>

      {/* How it works */}
      <section className="steps-section" id="how">
        <h2 className="section-title">How it works</h2>
        <div className="steps">
          {[
            { name: "You ask a question", desc: "Type anything \u2014 a factual question, math problem, or current events query." },
            { name: "The agent reasons", desc: "The LLM analyzes your question and decides which tool to call: knowledge base, web search, or calculator." },
            { name: "Tools execute", desc: "The selected tool runs autonomously \u2014 retrieving docs, searching the web, or computing results." },
            { name: "You get an answer", desc: "The agent synthesizes the output into a clear, grounded response." },
          ].map((s, i) => (
            <motion.div
              key={i} className="step"
              initial={{ opacity: 0, x: -10 }}
              whileInView={{ opacity: 1, x: 0 }}
              viewport={{ once: true }}
              transition={{ delay: i * 0.08, duration: 0.4, ease: [0.16, 1, 0.3, 1] }}
            >
              <div className="step__num">0{i + 1}</div>
              <div className="step__text">
                <div className="step__name">{s.name}</div>
                <div className="step__desc">{s.desc}</div>
              </div>
            </motion.div>
          ))}
        </div>
      </section>

      {/* CTA */}
      <section className="cta">
        <motion.div
          className="cta__box"
          initial={{ opacity: 0, y: 16 }}
          whileInView={{ opacity: 1, y: 0 }}
          viewport={{ once: true }}
          transition={{ duration: 0.5 }}
        >
          <h2 className="cta__title">Ready to try AgentFlow?</h2>
          <p className="cta__desc">No signup. Just open the chat and start asking.</p>
          <button className="cta__btn" onClick={onChat}>Launch Chat <Arrow /></button>
        </motion.div>
      </section>

      {/* Footer */}
      <footer className="footer">
        <span>AgentFlow &mdash; Built with LangChain, LangGraph &amp; FastAPI</span>
        <span>Agentic RAG</span>
      </footer>
    </>
  );
}


/* ═══════════════════════════════════════════════════
   CHAT PAGE  —  ChatGPT / Claude layout
   ═══════════════════════════════════════════════════ */

function Chat({ onBack }) {
  const [messages, setMessages] = useState([]);
  const [input, setInput] = useState("");
  const [loading, setLoading] = useState(false);
  const endRef = useRef(null);
  const inputRef = useRef(null);
  const bodyRef = useRef(null);

  useEffect(() => {
    endRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages, loading]);

  useEffect(() => { inputRef.current?.focus(); }, []);

  const send = useCallback(async (text) => {
    const q = (text || input).trim();
    if (!q || loading) return;
    setInput("");
    setMessages((p) => [...p, { role: "user", text: q }]);
    setLoading(true);
    try {
      const r = await fetch(API, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ question: q }),
      });
      const d = await r.json();
      setMessages((p) => [...p, { role: "agent", text: d.answer }]);
    } catch {
      setMessages((p) => [...p, {
        role: "agent",
        text: "Couldn\u2019t reach the server. Is the backend running on port 8000?",
      }]);
    } finally {
      setLoading(false);
      inputRef.current?.focus();
    }
  }, [input, loading]);

  const onKey = (e) => {
    if (e.key === "Enter" && !e.shiftKey) { e.preventDefault(); send(); }
  };

  const hasMessages = messages.length > 0 || loading;

  return (
    <div className="chat-page">
      {/* Nav */}
      <nav className="nav nav--glass">
        <div className="nav__brand" onClick={onBack} style={{ cursor: "pointer" }}>
          <span className="nav__mark"><Bolt stroke="white" strokeWidth="2" /></span>
          <span className="nav__wordmark">AgentFlow</span>
        </div>
        <div className="nav__right">
          <button className="nav__btn nav__btn--ghost" onClick={onBack}>
            <svg width="15" height="15" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round"><polyline points="15 18 9 12 15 6" /></svg>
            Home
          </button>
        </div>
      </nav>

      {/* Body */}
      <div className="chat-body" ref={bodyRef}>
        {!hasMessages ? (
          <div className="chat-welcome">
            <motion.div
              className="chat-welcome__icon"
              initial={{ opacity: 0, scale: 0.9 }}
              animate={{ opacity: 1, scale: 1 }}
              transition={{ duration: 0.4 }}
            >
              <Bolt stroke="white" strokeWidth="2" />
            </motion.div>
            <motion.h2
              className="chat-welcome__title"
              initial={{ opacity: 0, y: 8 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ delay: 0.1, duration: 0.4 }}
            >
              What can I help with?
            </motion.h2>
            <motion.p
              className="chat-welcome__sub"
              initial={{ opacity: 0 }}
              animate={{ opacity: 1 }}
              transition={{ delay: 0.2, duration: 0.4 }}
            >
              Ask about LangChain, RAG, Python &mdash; or try a math problem.
              I'll pick the right tool.
            </motion.p>
            <motion.div
              className="chat-welcome__chips"
              initial={{ opacity: 0, y: 6 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ delay: 0.3, duration: 0.4 }}
            >
              {SUGGESTIONS.map((s) => (
                <button key={s} className="chip" onClick={() => send(s)}>{s}</button>
              ))}
            </motion.div>
          </div>
        ) : (
          <div className="chat-stream">
            {messages.map((m, i) => (
              <div className="chat-row" key={i}>
                <div className={`chat-msg chat-msg--${m.role === "user" ? "user" : "agent"}`}>
                  <div className="chat-msg__avatar">
                    {m.role === "user" ? "Y" : <Bolt stroke="currentColor" strokeWidth="2" />}
                  </div>
                  <div>
                    <div className="chat-msg__label">
                      {m.role === "user" ? "You" : "AgentFlow"}
                    </div>
                    <div className="chat-msg__text">
                      <ReactMarkdown>{m.text}</ReactMarkdown>
                    </div>
                  </div>
                </div>
              </div>
            ))}

            {loading && (
              <div className="chat-row">
                <div className="chat-msg chat-msg--agent">
                  <div className="chat-msg__avatar">
                    <Bolt stroke="currentColor" strokeWidth="2" />
                  </div>
                  <div>
                    <div className="chat-msg__label">AgentFlow</div>
                    <div className="typing-dots">
                      <span /><span /><span />
                    </div>
                  </div>
                </div>
              </div>
            )}

            <div ref={endRef} />
          </div>
        )}
      </div>

      {/* Input bar */}
      <div className="chat-input-bar">
        <div className="chat-input-box">
          <textarea
            ref={inputRef}
            placeholder="Message AgentFlow..."
            value={input}
            onChange={(e) => setInput(e.target.value)}
            onKeyDown={onKey}
            rows={1}
          />
          <button
            className="send-btn"
            onClick={() => send()}
            disabled={!input.trim() || loading}
            aria-label="Send"
          >
            <SendIcon />
          </button>
        </div>
      </div>
      <div className="chat-disclaimer">
        AgentFlow can make mistakes. Verify important information.
      </div>
    </div>
  );
}


/* ═══════════════════════════════════════════════════
   APP ROUTER
   ═══════════════════════════════════════════════════ */

export default function App() {
  const [page, setPage] = useState("landing");

  const goChat = () => { setPage("chat"); window.scrollTo(0, 0); };
  const goHome = () => { setPage("landing"); window.scrollTo(0, 0); };

  return (
    <AnimatePresence mode="wait">
      {page === "landing" ? (
        <motion.div key="l" initial={{ opacity: 0 }} animate={{ opacity: 1 }} exit={{ opacity: 0 }} transition={{ duration: 0.25 }}>
          <Landing onChat={goChat} />
        </motion.div>
      ) : (
        <motion.div key="c" initial={{ opacity: 0 }} animate={{ opacity: 1 }} exit={{ opacity: 0 }} transition={{ duration: 0.25 }}>
          <Chat onBack={goHome} />
        </motion.div>
      )}
    </AnimatePresence>
  );
}
