import { useState, useCallback } from 'react'
import ChatWindow from './components/ChatWindow.jsx'
import AgentPipeline from './components/AgentPipeline.jsx'
import BookSidebar from './components/BookSidebar.jsx'
import HomePage from './components/HomePage.jsx'
import TechStackVisualizer from './components/TechStackVisualizer.jsx'

export default function App() {
  const [view, setView] = useState('home')
  const [messages, setMessages] = useState([])
  const [isLoading, setIsLoading] = useState(false)
  const [activeNode, setActiveNode] = useState(null)
  const [activeFrameworks, setActiveFrameworks] = useState([])
  const [retries, setRetries] = useState(0)

  const handleSend = useCallback(async (text) => {
    const userMsg = { role: 'user', content: text }
    setMessages(prev => [...prev, userMsg])
    setIsLoading(true)
    setActiveNode(null)
    setRetries(0)

    const history = [...messages, userMsg]

    try {
      const res = await fetch('/chat', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ messages: history }),
      })

      const reader = res.body.getReader()
      const decoder = new TextDecoder()
      let finalResponse = null, actionPlan = null, frameworks = [], followUpQuestion = null

      while (true) {
        const { done, value } = await reader.read()
        if (done) break
        const text = decoder.decode(value)
        for (const line of text.split('\n')) {
          if (!line.startsWith('data: ')) continue
          try {
            const event = JSON.parse(line.slice(6))
            const { node: nodeName, output } = event
            if (!nodeName || nodeName === '__end__') continue
            setActiveNode(nodeName)
            if (nodeName === 'query_builder') setRetries(r => r + 1)
            if (!output) continue
            if (output.final_response) finalResponse = output.final_response
            if (nodeName === 'psychologist') {
              frameworks = output.active_frameworks ?? []
              setActiveFrameworks(frameworks)
            }
            if (nodeName === 'action_planner') actionPlan = output.action_plan
            if (nodeName === 'follow_up' && output.follow_up_question) followUpQuestion = output.follow_up_question
          } catch { /* partial chunk */ }
        }
      }

      if (finalResponse) {
        setMessages(prev => [...prev, {
          role: 'assistant', content: finalResponse,
          actionPlan: actionPlan ?? [], sources: frameworks,
          followUpQuestion: followUpQuestion,
        }])
      }
    } catch {
      setMessages(prev => [...prev, {
        role: 'assistant',
        content: 'Something went wrong. Please check that the backend is running.',
      }])
    } finally {
      setIsLoading(false)
      setActiveNode(null)
    }
  }, [messages])

  return (
    <div className="h-screen flex flex-col overflow-hidden bg-warm-50">

      {/* ── Header ── */}
      <header className="flex-shrink-0 bg-warm-100 border-b border-warm-200 px-6 h-14 flex items-center justify-between shadow-warm-sm z-10">

        {/* Brand */}
        <button
          onClick={() => setView('home')}
          className="flex items-center gap-3 group"
        >
          <div className="w-8 h-8 bg-forest-500 rounded-lg flex items-center justify-center shadow-warm-sm group-hover:bg-forest-400 transition-colors">
            <svg width="16" height="16" viewBox="0 0 16 16" fill="none">
              <path d="M8 2C4.686 2 2 4.686 2 8s2.686 6 6 6 6-2.686 6-6-2.686-6-6-6zm0 2.5a1.5 1.5 0 1 1 0 3 1.5 1.5 0 0 1 0-3zm0 7.5a4.5 4.5 0 0 1-3.6-1.8c.018-.9 1.8-1.4 3.6-1.4 1.8 0 3.582.5 3.6 1.4A4.5 4.5 0 0 1 8 12z" fill="white"/>
            </svg>
          </div>
          <span className="font-serif text-lg text-warm-900 leading-none tracking-tight">MindMate Assistant</span>
        </button>

        {/* Right side */}
        <div className="flex items-center gap-3">
          {view === 'home' ? (
            <button
              onClick={() => setView('chat')}
              className="text-xs font-semibold bg-forest-500 hover:bg-forest-400 active:scale-95 text-white px-4 py-2 rounded-lg transition-all shadow-warm-sm"
            >
              Open Chat
            </button>
          ) : (
            <button
              onClick={() => setView('home')}
              className="text-xs font-medium text-warm-600 hover:text-forest-400 transition-colors flex items-center gap-1.5"
            >
              <svg width="14" height="14" viewBox="0 0 14 14" fill="none"><path d="M8.5 2.5L4 7l4.5 4.5" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round" strokeLinejoin="round"/></svg>
              Home
            </button>
          )}
        </div>
      </header>

      {/* ── Tech Stack Visualizer (presentation overlay) ── */}
      <TechStackVisualizer activeNode={activeNode} retries={retries} />

      {/* ── Views ── */}
      {view === 'home' ? (
        <div key="home" className="flex flex-col flex-1 overflow-hidden anim-fade-in">
          <HomePage onStart={() => setView('chat')} />
        </div>
      ) : (
        <div key="chat" className="flex flex-col flex-1 overflow-hidden anim-fade-in">
          <AgentPipeline activeNode={activeNode} retries={retries} />
          <div className="flex flex-1 overflow-hidden">
            <ChatWindow messages={messages} onSend={handleSend} isLoading={isLoading} />
            <BookSidebar activeFrameworks={activeFrameworks} />
          </div>
        </div>
      )}
    </div>
  )
}
