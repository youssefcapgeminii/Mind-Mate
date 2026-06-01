const BOOK_STYLES = {
  'Feeling Good':             'bg-blue-50    text-blue-700    border-blue-200',
  'Attached':                 'bg-pink-50    text-pink-700    border-pink-200',
  'The Body Keeps the Score': 'bg-amber-50   text-amber-700   border-amber-200',
  'Games People Play':        'bg-violet-50  text-violet-700  border-violet-200',
  'Thinking Fast and Slow':   'bg-teal-50    text-teal-700    border-teal-200',
  'Nonviolent Communication': 'bg-emerald-50 text-emerald-700 border-emerald-200',
}

export default function SourceChip({ book }) {
  const style = BOOK_STYLES[book] ?? 'bg-warm-50 text-warm-600 border-warm-200'
  return (
    <span className={`inline-flex items-center gap-1 px-2.5 py-1 rounded-full text-[11px] font-medium border ${style}`}>
      <span className="w-1 h-1 rounded-full bg-current opacity-60" />
      {book}
    </span>
  )
}
