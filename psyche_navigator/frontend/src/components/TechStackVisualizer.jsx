import { useState, useEffect, useRef } from 'react'

const NODES = [
  {
    id: 'guard',
    label: 'Guard',
    desc: 'LLM checks if the message is relevant to personal or interpersonal psychology — off-topic messages are short-circuited immediately',
    color: '#FB923C',
  },
  {
    id: 'retriever',
    label: 'Retriever',
    desc: 'Cosine similarity search across all 7,351 chunks from all 5 books — top 10 most relevant chunks returned',
    color: '#34D399',
    subSteps: [
      { label: 'HuggingFace Embed',   detail: 'Query → 384-dim vector via all-MiniLM-L6-v2',    color: '#6EE7B7' },
      { label: 'Cosine Similarity',   detail: 'ChromaDB scores all 7,351 chunks against query',  color: '#6EE7B7' },
      { label: 'Top 10 Returned',     detail: 'Highest similarity chunks passed to evaluator',    color: '#6EE7B7' },
    ],
  },
  {
    id: 'evaluator',
    label: 'Evaluator',
    desc: 'LLM judges whether retrieved chunks are actionable, relevant and concrete enough',
    color: '#FBBF24',
  },
  {
    id: 'query_builder',
    label: 'Query Refiner',
    desc: 'LLM rewrites the search query to improve chunk quality. Loops back to Retriever (max 3×)',
    color: '#F87171',
    isLoop: true,
  },
  {
    id: 'psychologist',
    label: 'Psychologist',
    desc: 'Infers the situation context from the conversation, then generates a warm evidence-based response grounded only in retrieved book excerpts (temp 0.7)',
    color: '#C084FC',
  },
  {
    id: 'action_planner',
    label: 'Action Planner',
    desc: 'Structures advice into concrete steps with framework used, source book & time horizon',
    color: '#F472B6',
  },
  {
    id: 'follow_up',
    label: 'Follow-up',
    desc: 'Generates one targeted follow-up question to deepen understanding or check progress',
    color: '#38BDF8',
  },
]

const STACK_GROUPS = [
  {
    label: 'Orchestration',
    items: [
      { name: 'LangGraph',  detail: 'Stateful agent graph — conditional routing, cycles & streaming', color: '#818CF8' },
      { name: 'LangChain',  detail: 'LLM chains, retrievers, document loaders & ensemble retriever',  color: '#34D399' },
    ],
  },
  {
    label: 'Language Model',
    items: [
      { name: 'Groq — Llama 3.3 70B', detail: 'LPU inference — ~4s full pipeline, 14,400 req/day free', color: '#F97316' },
    ],
  },
  {
    label: 'RAG Pipeline',
    items: [
      { name: 'ChromaDB',               detail: 'Persistent vector store — HNSW index — 7,351 chunks',    color: '#FBBF24' },
      { name: 'Sentence Transformers',   detail: 'all-MiniLM-L6-v2 dense text embeddings',                color: '#C084FC' },
      { name: 'Cosine Similarity',        detail: 'ChromaDB scores all 7,351 chunks — top 10 returned',     color: '#38BDF8' },
    ],
  },
  {
    label: 'Backend API',
    items: [
      { name: 'FastAPI',   detail: 'Async REST API — SSE streaming per LangGraph node event', color: '#34D399' },
      { name: 'Pydantic',  detail: 'Structured output validation for action plan schema',      color: '#F87171' },
      { name: 'Uvicorn',   detail: 'ASGI server',                                              color: '#94A3B8' },
    ],
  },
  {
    label: 'Frontend',
    items: [
      { name: 'React 18',    detail: 'Component UI — real-time SSE state updates per node', color: '#38BDF8' },
      { name: 'Vite',        detail: 'Fast build tooling & dev server',                      color: '#A78BFA' },
      { name: 'Tailwind CSS',detail: 'Utility-first styling with custom warm/forest palette', color: '#34D399' },
    ],
  },
]

// ─────────────────────────────────────────────
// Main component
// ─────────────────────────────────────────────
export default function TechStackVisualizer({ activeNode, retries }) {
  const [open, setOpen] = useState(false)
  const [tab, setTab] = useState('flow')

  return (
    <>
      {/* Keyframe animations */}
      <style>{`
        @keyframes v-spin   { to { transform: rotate(360deg); } }
        @keyframes v-pulse  { 0%,100% { opacity:1; } 50% { opacity:0.35; } }
      `}</style>

      {/* ── Toggle Button ── */}
      <button
        onClick={() => setOpen(v => !v)}
        title={open ? 'Hide tech stack visualizer' : 'Show tech stack visualizer'}
        style={{
          position: 'fixed',
          bottom: 24,
          right: open ? 404 : 24,
          zIndex: 1001,
          transition: 'right 0.35s cubic-bezier(0.4,0,0.2,1)',
          background: open
            ? '#1e293b'
            : 'linear-gradient(135deg,#4F46E5 0%,#7C3AED 100%)',
          color: 'white',
          border: open ? '1px solid #334155' : 'none',
          borderRadius: 12,
          padding: '10px 18px',
          fontSize: 13,
          fontWeight: 600,
          cursor: 'pointer',
          boxShadow: open
            ? '0 2px 12px rgba(0,0,0,.45)'
            : '0 4px 24px rgba(79,70,229,.45)',
          display: 'flex',
          alignItems: 'center',
          gap: 8,
          letterSpacing: '0.01em',
          userSelect: 'none',
        }}
      >
        {open ? (
          <svg width="14" height="14" viewBox="0 0 14 14" fill="none">
            <path d="M2 2l10 10M12 2L2 12" stroke="currentColor" strokeWidth="2" strokeLinecap="round"/>
          </svg>
        ) : (
          <svg width="15" height="15" viewBox="0 0 15 15" fill="none">
            <rect x="1"   y="1"   width="5.5" height="5.5" rx="1.5" stroke="white" strokeWidth="1.4"/>
            <rect x="8.5" y="1"   width="5.5" height="5.5" rx="1.5" stroke="white" strokeWidth="1.4"/>
            <rect x="1"   y="8.5" width="5.5" height="5.5" rx="1.5" stroke="white" strokeWidth="1.4"/>
            <rect x="8.5" y="8.5" width="5.5" height="5.5" rx="1.5" stroke="white" strokeWidth="1.4"/>
          </svg>
        )}
        {open ? 'Hide Viz' : 'Show Tech Viz'}
        {!open && activeNode && (
          <span style={{
            width: 7, height: 7, borderRadius: '50%',
            background: '#34D399',
            boxShadow: '0 0 8px #34D399',
            animation: 'v-pulse 1.5s infinite',
          }} />
        )}
      </button>

      {/* ── Side Panel ── */}
      <div
        aria-label="Tech stack visualizer panel"
        style={{
          position: 'fixed',
          top: 56,
          right: 0,
          bottom: 0,
          width: 380,
          transform: open ? 'translateX(0)' : 'translateX(100%)',
          transition: 'transform 0.35s cubic-bezier(0.4,0,0.2,1)',
          zIndex: 1000,
          background: '#0f172a',
          borderLeft: '1px solid #1e293b',
          display: 'flex',
          flexDirection: 'column',
          fontFamily: '-apple-system,BlinkMacSystemFont,"Segoe UI",sans-serif',
        }}
      >
        {/* Panel header */}
        <div style={{ padding: '14px 20px 0', borderBottom: '1px solid #1e293b', flexShrink: 0 }}>
          <div style={{ display: 'flex', alignItems: 'center', gap: 8, marginBottom: 12 }}>
            <span style={{
              width: 8, height: 8, borderRadius: '50%', flexShrink: 0,
              background: activeNode ? '#34D399' : '#334155',
              boxShadow: activeNode ? '0 0 8px #34D399' : 'none',
              animation: activeNode ? 'v-pulse 1.5s infinite' : 'none',
            }} />
            <span style={{ color: '#f1f5f9', fontSize: 13, fontWeight: 700 }}>
              Live Backend Visualizer
            </span>
          </div>

          {/* Tab bar */}
          <div style={{ display: 'flex', gap: 2 }}>
            {[{ id: 'flow', label: 'Agent Flow' }, { id: 'stack', label: 'Tech Stack' }].map(t => (
              <button key={t.id} onClick={() => setTab(t.id)} style={{
                padding: '6px 16px', fontSize: 12, fontWeight: 600,
                color: tab === t.id ? '#f1f5f9' : '#475569',
                background: 'none', border: 'none',
                borderBottom: tab === t.id ? '2px solid #818CF8' : '2px solid transparent',
                cursor: 'pointer', letterSpacing: '0.01em', transition: 'color 0.2s',
              }}>
                {t.label}
              </button>
            ))}
          </div>
        </div>

        {/* Scrollable content */}
        <div style={{ flex: 1, overflowY: 'auto', padding: '20px 20px 36px' }}>
          {tab === 'flow'
            ? <FlowTab activeNode={activeNode} retries={retries} />
            : <StackTab />
          }
        </div>
      </div>
    </>
  )
}

// ─────────────────────────────────────────────
// Agent Flow tab
// ─────────────────────────────────────────────
function FlowTab({ activeNode, retries }) {
  const [visited, setVisited] = useState(new Set())
  const prevRef = useRef(null)

  useEffect(() => {
    if (activeNode) {
      if (prevRef.current === null && visited.size > 0) {
        setVisited(new Set([activeNode]))
      } else {
        setVisited(prev => new Set([...prev, activeNode]))
      }
    }
    prevRef.current = activeNode
  }, [activeNode])

  return (
    <div>
      <p style={{ fontSize: 11, color: '#475569', marginBottom: 20, lineHeight: 1.65 }}>
        LangGraph compiles this 8-node directed graph at startup. Each node mutates an{' '}
        <code style={{ color: '#94a3b8', background: '#1e293b', padding: '1px 5px', borderRadius: 4, fontSize: 10 }}>
          AgentState
        </code>{' '}
        TypedDict, and streams its output to the frontend in real time via Server-Sent Events.
      </p>

      {NODES.map((node, i) => {
        const isActive = activeNode === node.id
        const isDone   = visited.has(node.id) && !isActive

        return (
          <div key={node.id}>
            {/* Node card */}
            <div style={{
              border:     `1px solid ${isActive ? node.color + '90' : isDone ? node.color + '50' : node.color + '25'}`,
              borderLeft: `3px solid ${isActive ? node.color   : isDone ? node.color + 'cc' : node.color + '55'}`,
              borderRadius: 8,
              padding: '10px 12px',
              background: isActive ? node.color + '18' : isDone ? node.color + '0c' : '#0d1a2e',
              boxShadow: isActive ? `0 0 28px ${node.color}28` : 'none',
              transition: 'all 0.3s ease',
            }}>
              <div style={{ display: 'flex', alignItems: 'center', gap: 8 }}>
                {/* Status dot */}
                <span style={{
                  width: 8, height: 8, borderRadius: '50%', flexShrink: 0,
                  background: isActive ? node.color : isDone ? node.color : node.color + '55',
                  boxShadow: isActive ? `0 0 10px ${node.color}` : isDone ? `0 0 6px ${node.color}80` : 'none',
                  animation: isActive ? 'v-pulse 1.5s infinite' : 'none',
                }} />

                {/* Label */}
                <span style={{
                  fontSize: 12, fontWeight: 700, flex: 1,
                  color: isActive ? node.color : isDone ? node.color + 'dd' : '#94a3b8',
                  transition: 'color 0.3s',
                }}>
                  {node.label}
                </span>

                {/* Retry badge */}
                {node.isLoop && retries > 0 && (
                  <span style={{
                    fontSize: 10, fontWeight: 700, color: node.color,
                    background: node.color + '20', border: `1px solid ${node.color}50`,
                    padding: '1px 7px', borderRadius: 10,
                  }}>
                    ×{retries}
                  </span>
                )}

                {/* Done check */}
                {isDone && !isActive && (
                  <svg width="14" height="14" viewBox="0 0 14 14" fill="none">
                    <circle cx="7" cy="7" r="5.5" stroke="#1e293b" strokeWidth="1"/>
                    <path d="M4.5 7l2 2 3-3" stroke="#34D399" strokeWidth="1.5" strokeLinecap="round" strokeLinejoin="round"/>
                  </svg>
                )}

                {/* Spinning loader */}
                {isActive && (
                  <div style={{
                    width: 14, height: 14, flexShrink: 0,
                    border:    `2px solid ${node.color}30`,
                    borderTop: `2px solid ${node.color}`,
                    borderRadius: '50%',
                    animation: 'v-spin 0.8s linear infinite',
                  }} />
                )}
              </div>

              {/* Description */}
              <p style={{
                fontSize: 11, margin: '5px 0 0 16px',
                color: isActive ? '#cbd5e1' : isDone ? '#94a3b8' : '#64748b',
                lineHeight: 1.5, transition: 'color 0.3s',
              }}>
                {node.desc}
              </p>

              {/* Sub-steps (e.g. Retriever internals) */}
              {node.subSteps && (
                <div style={{ marginTop: 10, marginLeft: 16, display: 'flex', flexDirection: 'column', gap: 5 }}>
                  {node.subSteps.map((step, si) => (
                    <div key={si} style={{
                      display: 'flex', alignItems: 'center', gap: 8,
                      padding: '6px 10px',
                      background: isActive ? step.color + '12' : isDone ? step.color + '0a' : '#0d1a2e',
                      border: `1px solid ${isActive ? step.color + '50' : isDone ? step.color + '40' : step.color + '15'}`,
                      borderLeft: `2px solid ${isActive ? step.color : isDone ? step.color + 'bb' : step.color + '30'}`,
                      borderRadius: 6,
                      transition: 'all 0.3s ease',
                    }}>
                      {isActive && (
                        <div style={{
                          width: 10, height: 10, flexShrink: 0,
                          border: `1.5px solid ${step.color}40`,
                          borderTop: `1.5px solid ${step.color}`,
                          borderRadius: '50%',
                          animation: `v-spin ${0.7 + si * 0.15}s linear infinite`,
                        }} />
                      )}
                      {isDone && (
                        <svg width="10" height="10" viewBox="0 0 10 10" fill="none" style={{ flexShrink: 0 }}>
                          <path d="M2 5l2.5 2.5 3.5-4" stroke="#34D399" strokeWidth="1.5" strokeLinecap="round" strokeLinejoin="round"/>
                        </svg>
                      )}
                      <div>
                        <span style={{ fontSize: 11, fontWeight: 600, color: isActive ? step.color : isDone ? step.color + 'dd' : '#64748b' }}>
                          {step.label}
                        </span>
                        <span style={{ fontSize: 10, color: isDone ? '#94a3b8' : '#64748b', marginLeft: 6 }}>{step.detail}</span>
                      </div>
                    </div>
                  ))}
                </div>
              )}
            </div>

            {/* Arrow connector between nodes */}
            {i < NODES.length - 1 && (
              <div style={{ display: 'flex', alignItems: 'center', height: 22, marginLeft: 15, position: 'relative' }}>
                <div style={{ width: 1, height: '100%', background: visited.has(node.id) ? '#475569' : '#1e3050' }} />
                {/* Retry path annotation after evaluator */}
                {node.id === 'evaluator' && (
                  <span style={{
                    position: 'absolute', left: 12,
                    fontSize: 10, fontWeight: 500, whiteSpace: 'nowrap',
                    color: '#F87171', background: '#F8717115',
                    border: '1px solid #F8717130',
                    padding: '1px 8px', borderRadius: 6,
                  }}>
                    ↩ retry path if insufficient
                  </span>
                )}
              </div>
            )}
          </div>
        )
      })}

      {/* Retry loop explainer */}
      <div style={{
        marginTop: 20, padding: '10px 12px',
        background: '#F8717110', border: '1px solid #F8717125',
        borderLeft: '3px solid #F87171', borderRadius: 8,
        fontSize: 11, color: '#64748b', lineHeight: 1.6,
      }}>
        <span style={{ color: '#F87171', fontWeight: 700 }}>Agentic Retry Loop — </span>
        Evaluator → Query Refiner → Retriever cycles up to{' '}
        <strong style={{ color: '#94a3b8' }}>3 times</strong> before the Psychologist
        responds with the best available context.
      </div>

      {/* Knowledge base note */}
      <div style={{
        marginTop: 8, padding: '10px 12px',
        background: '#34D39910', border: '1px solid #34D39925',
        borderLeft: '3px solid #34D399', borderRadius: 8,
        fontSize: 11, color: '#64748b', lineHeight: 1.6,
      }}>
        <span style={{ color: '#34D399', fontWeight: 700 }}>Knowledge Base — </span>
        7,351 chunks from 6 psychology books — all searched on every query via cosine similarity.
        Top 10 chunks returned and evaluated before generating a response.
      </div>
    </div>
  )
}

// ─────────────────────────────────────────────
// Tech Stack tab
// ─────────────────────────────────────────────
function StackTab() {
  return (
    <div>
      <p style={{ fontSize: 11, color: '#475569', marginBottom: 20, lineHeight: 1.65 }}>
        Full technology stack powering the PsycheNavigator agentic RAG pipeline.
      </p>
      {STACK_GROUPS.map(({ label, items }) => (
        <div key={label} style={{ marginBottom: 22 }}>
          <div style={{
            fontSize: 10, fontWeight: 700, letterSpacing: '0.12em',
            textTransform: 'uppercase', color: '#475569', marginBottom: 8,
          }}>
            {label}
          </div>
          <div style={{ display: 'flex', flexDirection: 'column', gap: 5 }}>
            {items.map(({ name, detail, color }) => (
              <div key={name} style={{
                display: 'flex', alignItems: 'center', gap: 10,
                padding: '9px 12px', background: '#0b1526',
                border: `1px solid ${color}25`,
                borderLeft: `3px solid ${color}`,
                borderRadius: 7,
              }}>
                <span style={{
                  width: 7, height: 7, borderRadius: '50%', flexShrink: 0,
                  background: color, boxShadow: `0 0 6px ${color}90`,
                }} />
                <div style={{ flex: 1 }}>
                  <div style={{ fontSize: 12, fontWeight: 600, color }}>{name}</div>
                  <div style={{ fontSize: 10, color: '#475569', marginTop: 1 }}>{detail}</div>
                </div>
              </div>
            ))}
          </div>
        </div>
      ))}
    </div>
  )
}
