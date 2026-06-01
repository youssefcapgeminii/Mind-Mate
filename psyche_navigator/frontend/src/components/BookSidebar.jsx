const ALL_BOOKS = [
  { name: 'Feeling Good',             dot: 'bg-blue-400'   },
  { name: 'Attached',                 dot: 'bg-pink-400'   },
  { name: 'The Body Keeps the Score', dot: 'bg-amber-400'  },
  { name: 'Games People Play',        dot: 'bg-violet-400' },
  { name: 'Thinking Fast and Slow',   dot: 'bg-teal-400'   },
  { name: 'Nonviolent Communication', dot: 'bg-emerald-400'},
]

export default function BookSidebar({ activeFrameworks }) {
  return (
    <aside className="w-60 flex-shrink-0 bg-warm-100 border-l border-warm-200 flex flex-col overflow-hidden">

      {/* Header */}
      <div className="px-5 py-4 border-b border-warm-200">
        <h2 className="text-[11px] font-semibold text-warm-500 uppercase tracking-widest">Knowledge Base</h2>
      </div>

      {/* Book list */}
      <div className="flex-1 overflow-y-auto scrollbar-thin px-4 py-4 space-y-1.5">
        {ALL_BOOKS.map(({ name, dot }) => {
          const isActive = activeFrameworks?.includes(name)

          return (
            <div
              key={name}
              className={`
                flex items-center gap-2.5 px-3 py-2.5 rounded-xl text-xs transition-all duration-200
                ${isActive ? 'bg-forest-50 border border-forest-200 shadow-warm-sm' : ''}
              `}
            >
              <span className={`w-1.5 h-1.5 rounded-full flex-shrink-0 ${isActive ? dot : 'bg-warm-300'}`} />
              <span className={`leading-snug ${isActive ? 'font-semibold text-forest-800' : 'text-warm-500'}`}>
                {name}
              </span>
              {isActive && (
                <span className="ml-auto text-[9px] font-semibold text-forest-600 bg-forest-100 px-1.5 py-0.5 rounded-full uppercase tracking-wide">
                  Used
                </span>
              )}
            </div>
          )
        })}
      </div>

      {/* Footer note */}
      <div className="px-5 py-3 border-t border-warm-200">
        <p className="text-[11px] text-warm-500 leading-relaxed">
          Highlighted books were consulted to form the response above.
        </p>
      </div>
    </aside>
  )
}
