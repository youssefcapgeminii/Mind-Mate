import ReactMarkdown from 'react-markdown'
import SourceChip from './SourceChip.jsx'

export default function MessageBubble({ message }) {
  const isUser = message.role === 'user'

  if (isUser) {
    return (
      <div className="flex justify-end mb-5">
        {/* WhatsApp sent bubble — light green */}
        <div className="max-w-[72%] rounded-2xl rounded-br-sm px-5 py-3.5 shadow-warm-sm" style={{ background: '#D9FDD3' }}>
          <p className="text-sm leading-relaxed font-light text-warm-900">{message.content}</p>
        </div>
      </div>
    )
  }

  return (
    <div className="flex justify-start mb-6">
      <div className="max-w-[86%] space-y-2.5">

        {/* Avatar row */}
        <div className="flex items-center gap-2">
          <div className="w-7 h-7 rounded-full bg-forest-500 flex items-center justify-center flex-shrink-0 shadow-warm-sm">
            <span className="font-serif text-sm text-white leading-none select-none">M</span>
          </div>
          <span className="text-xs font-semibold text-forest-600 tracking-wide">MindMate Assistant</span>
        </div>

        {/* Response card — WhatsApp received bubble: white */}
        <div className="bg-warm-100 rounded-2xl rounded-tl-sm px-6 py-5 shadow-warm-md border border-warm-200">
          <div className="prose prose-sm max-w-none text-warm-900
            prose-p:leading-relaxed prose-p:mb-3 prose-p:last:mb-0
            prose-strong:text-warm-900 prose-strong:font-semibold
            prose-em:not-italic prose-em:font-medium prose-em:text-forest-600 prose-em:bg-forest-50 prose-em:px-1 prose-em:rounded
            prose-ul:my-2 prose-li:my-0.5 prose-li:leading-relaxed
            prose-blockquote:border-l-2 prose-blockquote:border-forest-400 prose-blockquote:text-warm-500 prose-blockquote:bg-forest-50 prose-blockquote:rounded-r-lg prose-blockquote:py-1
          ">
            <ReactMarkdown>{message.content}</ReactMarkdown>
          </div>
        </div>

        {/* Action plan */}
        {message.actionPlan?.length > 0 && (
          <div className="bg-forest-950 rounded-2xl px-5 py-4 shadow-warm-sm">
            <div className="flex items-center gap-2 mb-3.5">
              <svg width="14" height="14" viewBox="0 0 14 14" fill="none">
                <rect x="1.5" y="1.5" width="11" height="11" rx="2" stroke="#25D366" strokeWidth="1.2"/>
                <path d="M4 7h6M4 4.5h6M4 9.5h4" stroke="#25D366" strokeWidth="1.2" strokeLinecap="round"/>
              </svg>
              <span className="text-xs font-semibold text-forest-300 uppercase tracking-widest">Action Plan</span>
            </div>
            <ol className="space-y-2.5">
              {message.actionPlan.map((step, i) => (
                <li key={i} className="flex gap-3 items-start">
                  <span className="flex-shrink-0 w-5 h-5 rounded-full bg-forest-500 text-white flex items-center justify-center text-[11px] font-bold mt-0.5">
                    {i + 1}
                  </span>
                  <span className="text-sm text-forest-100 leading-relaxed font-light">{step}</span>
                </li>
              ))}
            </ol>
          </div>
        )}

        {/* Sources */}
        {message.sources?.length > 0 && (
          <div className="flex flex-wrap gap-1.5 items-center pt-1">
            <span className="text-[11px] text-warm-500 font-medium mr-1">Sources</span>
            {message.sources.map((book, i) => <SourceChip key={i} book={book} />)}
          </div>
        )}

        {/* Follow-up question */}
        {message.followUpQuestion && (
          <div className="flex items-start gap-2.5 pt-1">
            <div className="w-5 h-5 rounded-full bg-forest-400 flex items-center justify-center flex-shrink-0 mt-0.5">
              <svg width="10" height="10" viewBox="0 0 10 10" fill="none">
                <circle cx="5" cy="3.5" r="1.5" fill="white"/>
                <path d="M5 6v2" stroke="white" strokeWidth="1.2" strokeLinecap="round"/>
              </svg>
            </div>
            <div className="bg-forest-50 border border-forest-200 rounded-2xl rounded-tl-sm px-4 py-3">
              <p className="text-xs font-semibold text-forest-600 uppercase tracking-widest mb-1">Follow-up</p>
              <p className="text-sm text-warm-800 leading-relaxed">{message.followUpQuestion}</p>
            </div>
          </div>
        )}
      </div>
    </div>
  )
}
