import { useRef, useEffect, useState } from 'react'
import MessageBubble from './MessageBubble.jsx'

const SUGGESTIONS = [
  'My manager keeps dismissing my ideas in meetings',
  "I'm struggling with self-doubt and low confidence",
  'My partner and I keep having the same argument',
]

export default function ChatWindow({ messages, onSend, isLoading }) {
  const [input, setInput] = useState('')
  const bottomRef   = useRef(null)
  const textareaRef = useRef(null)

  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: 'smooth' })
  }, [messages, isLoading])

  const submit = (e) => {
    e?.preventDefault()
    const trimmed = input.trim()
    if (!trimmed || isLoading) return
    onSend(trimmed)
    setInput('')
    if (textareaRef.current) textareaRef.current.style.height = 'auto'
  }

  const onKey = (e) => {
    if (e.key === 'Enter' && !e.shiftKey) { e.preventDefault(); submit() }
  }

  const onInput = (e) => {
    setInput(e.target.value)
    e.target.style.height = 'auto'
    e.target.style.height = Math.min(e.target.scrollHeight, 140) + 'px'
  }

  return (
    <div className="flex flex-col flex-1 overflow-hidden">

      {/* Messages — WhatsApp chat wallpaper */}
      <div className="flex-1 overflow-y-auto px-4 md:px-10 py-8 scrollbar-thin" style={{ background: '#EFEAE2' }}>
        <div className="max-w-2xl mx-auto">

          {messages.length === 0 && (
            <div className="flex flex-col items-center justify-center text-center py-16 anim-fade-in">
              <div className="w-16 h-16 rounded-full bg-forest-500 flex items-center justify-center mb-5 shadow-warm-lg ring-4 ring-forest-100">
                <span className="font-serif text-2xl text-white leading-none select-none">M</span>
              </div>
              <h2 className="font-serif text-2xl text-warm-900 mb-2">How can I help you today?</h2>
              <p className="text-sm text-warm-500 max-w-sm leading-relaxed mb-8">
                Describe a personal challenge or conflict. I'll draw on six psychology books to give you empathetic, actionable guidance.
              </p>
              <div className="w-full max-w-sm space-y-2">
                {SUGGESTIONS.map(s => (
                  <button
                    key={s}
                    onClick={() => onSend(s)}
                    className="w-full text-left text-sm text-forest-600 bg-warm-100 hover:bg-warm-200 border border-warm-200 hover:border-forest-300 px-4 py-3 rounded-xl transition-all shadow-warm-sm"
                  >
                    "{s}"
                  </button>
                ))}
              </div>
            </div>
          )}

          {messages.map((msg, i) => (
            <div key={i} className={msg.role === 'user' ? 'anim-slide-right' : 'anim-slide-left'}>
              <MessageBubble message={msg} />
            </div>
          ))}

          {isLoading && (
            <div className="flex justify-start mb-6 anim-slide-left">
              <div className="flex items-start gap-2.5">
                <div className="w-7 h-7 rounded-full bg-forest-500 flex items-center justify-center flex-shrink-0 mt-0.5 shadow-warm-sm">
                  <span className="font-serif text-sm text-white leading-none select-none">M</span>
                </div>
                <div className="bg-warm-100 rounded-2xl rounded-tl-sm px-5 py-4 border border-warm-200 shadow-warm-sm">
                  <div className="flex items-center gap-1.5">
                    {[0, 150, 300].map(delay => (
                      <span key={delay} className="w-1.5 h-1.5 bg-forest-500 rounded-full animate-bounce" style={{ animationDelay: `${delay}ms` }} />
                    ))}
                  </div>
                </div>
              </div>
            </div>
          )}

          <div ref={bottomRef} />
        </div>
      </div>

      {/* Input bar */}
      <div className="flex-shrink-0 bg-warm-50 border-t border-warm-200 px-4 md:px-10 py-3">
        <form onSubmit={submit} className="max-w-2xl mx-auto">
          <div className="flex gap-3 items-end bg-warm-100 border border-warm-200 rounded-2xl px-4 py-3 focus-within:border-forest-500 focus-within:ring-2 focus-within:ring-forest-100 transition-all shadow-warm-sm">
            <textarea
              ref={textareaRef}
              value={input}
              onChange={onInput}
              onKeyDown={onKey}
              disabled={isLoading}
              placeholder="Describe your situation…"
              rows={1}
              className="flex-1 resize-none bg-transparent text-sm text-warm-900 placeholder:text-warm-400 focus:outline-none disabled:opacity-50 leading-relaxed"
              style={{ minHeight: '24px', maxHeight: '140px' }}
            />
            <button
              type="submit"
              disabled={!input.trim() || isLoading}
              className="flex-shrink-0 w-8 h-8 bg-forest-500 hover:bg-forest-400 disabled:opacity-30 text-white rounded-xl flex items-center justify-center transition-all active:scale-95 shadow-warm-sm"
            >
              <svg width="14" height="14" viewBox="0 0 14 14" fill="none">
                <path d="M2 7h10M8 3l4 4-4 4" stroke="white" strokeWidth="1.5" strokeLinecap="round" strokeLinejoin="round"/>
              </svg>
            </button>
          </div>
          <p className="text-center text-[11px] text-warm-400 mt-2">
            Answers draw exclusively from 6 psychology books · Enter to send
          </p>
        </form>
      </div>
    </div>
  )
}
