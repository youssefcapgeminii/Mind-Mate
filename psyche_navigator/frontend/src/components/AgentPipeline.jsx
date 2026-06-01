import { useState, useEffect, useRef } from 'react'

const NODES = [
  { id: 'guard',          label: 'Guard'      },
  { id: 'retriever',      label: 'Retrieve'   },
  { id: 'evaluator',      label: 'Evaluate'   },
  { id: 'query_builder',  label: 'Refine'     },
  { id: 'psychologist',   label: 'Respond'    },
  { id: 'action_planner', label: 'Plan'       },
  { id: 'follow_up',      label: 'Follow-up'  },
]

export default function AgentPipeline({ activeNode, retries }) {
  const [visited, setVisited] = useState(new Set())
  const prevRef = useRef(null)

  useEffect(() => {
    if (activeNode) {
      // null → first node of a new query: reset then add
      if (prevRef.current === null && visited.size > 0) {
        setVisited(new Set([activeNode]))
      } else {
        setVisited(prev => new Set([...prev, activeNode]))
      }
    }
    // activeNode → null: keep visited so the completed state stays visible
    prevRef.current = activeNode
  }, [activeNode])

  // hide only before the very first query
  if (!activeNode && visited.size === 0) return null

  const activeIndex  = NODES.findIndex(n => n.id === activeNode)
  const maxVisited   = NODES.reduce((max, n, i) => visited.has(n.id) ? i : max, -1)
  const progress     = activeNode
    ? Math.round(((activeIndex  + 1) / NODES.length) * 100)
    : Math.round(((maxVisited   + 1) / NODES.length) * 100)

  return (
    <div className="flex-shrink-0 bg-warm-100 border-b border-warm-200 px-6 py-2.5 anim-slide-down shadow-warm-sm">
      <div className="max-w-3xl mx-auto space-y-1.5">
        {/* Progress bar */}
        <div className="h-0.5 bg-warm-100 rounded-full overflow-hidden">
          <div
            className="h-full bg-forest-500 rounded-full transition-all duration-500"
            style={{ width: `${progress}%` }}
          />
        </div>
        {/* Node pills */}
        <div className="flex items-center gap-1 overflow-x-auto pb-0.5">
          {NODES.map((node, i) => {
            const isActive = activeNode === node.id
            const isDone   = visited.has(node.id) && !isActive
            const isRetry  = node.id === 'query_builder'

            return (
              <div key={node.id} className="flex items-center gap-1 flex-shrink-0">
                <span className={`
                  flex items-center gap-1 px-2 py-0.5 rounded text-[11px] font-medium transition-all duration-300
                  ${isActive ? 'text-forest-700 bg-forest-50'
                  : isDone   ? 'text-warm-500'
                  :            'text-warm-300'
                  }
                `}>
                  {isActive && (
                    <span className="w-1 h-1 rounded-full bg-forest-500 animate-pulse flex-shrink-0" />
                  )}
                  {isDone && (
                    <svg width="9" height="9" viewBox="0 0 9 9" fill="none" className="flex-shrink-0">
                      <path d="M1.5 4.5l2 2 4-4" stroke="#a99270" strokeWidth="1.5" strokeLinecap="round" strokeLinejoin="round"/>
                    </svg>
                  )}
                  {node.label}
                  {isRetry && retries > 0 && (
                    <span className="ml-0.5 text-copper-500 font-bold">×{retries}</span>
                  )}
                </span>
                {i < NODES.length - 1 && (
                  <span className={`text-[10px] flex-shrink-0 ${isDone ? 'text-warm-300' : 'text-warm-200'}`}>›</span>
                )}
              </div>
            )
          })}
        </div>
      </div>
    </div>
  )
}
