import { useState, useEffect, useRef } from 'react'

const QUOTES = [
  { text: "You don't have to control your thoughts. You just have to stop letting them control you.", author: "Dan Millman" },
  { text: "Almost everything will work again if you unplug it for a few minutes — including you.", author: "Anne Lamott" },
  { text: "The greatest weapon against stress is our ability to choose one thought over another.", author: "William James" },
  { text: "Healing is not linear. Be patient with yourself.", author: "Unknown" },
  { text: "You are allowed to be both a masterpiece and a work in progress simultaneously.", author: "Sophia Bush" },
  { text: "What you are is what you have been. What you'll be is what you do now.", author: "Buddha" },
  { text: "Owning our story and loving ourselves through that process is the bravest thing we'll ever do.", author: "Brené Brown" },
  { text: "Between stimulus and response there is a space. In that space is our power to choose our response.", author: "Viktor Frankl" },
]

const COVER = isbn => `https://covers.openlibrary.org/b/isbn/${isbn}-M.jpg`

const BOOKS = [
  { title: "Feeling Good",             author: "David D. Burns",             tag: "CBT & Mood",             color: "from-blue-600 to-blue-800",    cover: COVER("9780380810338"), desc: "A foundational psychology book based on Cognitive Behavioral Therapy (CBT), the most scientifically validated psychotherapy for depression and anxiety, with 2,000+ peer-reviewed studies backing it." },
  { title: "Attached",                 author: "Amir Levine & Rachel Heller", tag: "Attachment",            color: "from-pink-600 to-pink-800",    cover: COVER("9781585429134"), desc: "A psychology book built on attachment theory, one of the most influential frameworks in relational psychology, explaining how your attachment style shapes every relationship you form." },
  { title: "The Body Keeps the Score", author: "Bessel van der Kolk",        tag: "Trauma & Healing",       color: "from-amber-600 to-amber-800",  cover: COVER("9780143127741"), desc: "A landmark psychology book by a leading trauma researcher, explaining how psychological trauma physically rewires the brain and nervous system, and why healing requires more than talk therapy alone." },
  { title: "Games People Play",        author: "Eric Berne",                  tag: "Social Psychology ", color: "from-violet-600 to-violet-800", cover: "/covers/games_people_play.jpg", desc: "A classic psychology book that introduced Transactional Analysis, a psychological framework for understanding the unconscious social scripts that drive human conflict and behavior." },
  { title: "Thinking, Fast and Slow",  author: "Daniel Kahneman",            tag: "Cognitive Science",      color: "from-teal-600 to-teal-800",    cover: COVER("9780374533557"), desc: "A Nobel Prize-winning behavioral psychology book that exposes the cognitive biases and psychological patterns (System 1 and System 2) behind our emotional and interpersonal decisions." },
  { title: "Nonviolent Communication", author: "Marshall B. Rosenberg",       tag: "Communication",          color: "from-emerald-600 to-emerald-800", cover: COVER("9781892005281"), desc: "A psychology-based communication book providing a 4-step framework (Observation, Feeling, Need, Request) used by therapists and mediators worldwide to resolve conflict without blame or judgment." },
]

const TIPS = [
  { icon: "🌬️", title: "Box Breathing",      body: "Inhale 4s · Hold 4s · Exhale 4s · Hold 4s. Repeat 4 times to reset your nervous system." },
  { icon: "📓", title: "Daily Journaling",    body: "Write 3 things you're grateful for each morning. Gratitude rewires your brain toward positivity." },
  { icon: "🚶", title: "Move Your Body",      body: "A 10-minute walk lowers cortisol and triggers mood-lifting endorphins. Motion changes emotion." },
  { icon: "📵", title: "Digital Boundaries",  body: "No screens an hour before bed. Blue light disrupts melatonin and degrades sleep quality." },
  { icon: "🤝", title: "Reach Out",           body: "Connection is the antidote to anxiety. Send one text today — it matters more than you think." },
  { icon: "⏸️", title: "The 90-Second Rule", body: "Emotions peak and dissolve in 90 seconds if you don't re-trigger them. Pause and let it pass." },
]

function useRevealOnScroll(ref) {
  useEffect(() => {
    const obs = new IntersectionObserver(
      entries => entries.forEach(e => { if (e.isIntersecting) { e.target.classList.add('in-view'); obs.unobserve(e.target) } }),
      { threshold: 0.1 }
    )
    ref.current?.querySelectorAll('.reveal').forEach(n => obs.observe(n))
    return () => obs.disconnect()
  }, [ref])
}

function QuoteCarousel() {
  const [idx, setIdx]         = useState(0)
  const [visible, setVisible] = useState(true)

  const goTo = i => { setVisible(false); setTimeout(() => { setIdx(i); setVisible(true) }, 320) }

  useEffect(() => {
    const t = setInterval(() => goTo((idx + 1) % QUOTES.length), 5500)
    return () => clearInterval(t)
  }, [idx])

  return (
    <div className="px-8 py-14">
      <div className="transition-all duration-300" style={{ opacity: visible ? 1 : 0, transform: visible ? 'translateY(0)' : 'translateY(8px)' }}>
        <div className="quote-box">
          <p className="quote-box-text">"{QUOTES[idx].text}"</p>
          <p className="quote-box-author">— {QUOTES[idx].author}</p>
        </div>
      </div>
      <div className="flex justify-center gap-2 mt-12">
        {QUOTES.map((_, i) => (
          <button key={i} onClick={() => goTo(i)}
            className={`h-1 rounded-full transition-all duration-300 ${i === idx ? 'bg-forest-500 w-8' : 'bg-warm-300 w-1 hover:bg-warm-400'}`}
          />
        ))}
      </div>
    </div>
  )
}

export default function HomePage({ onStart }) {
  const tipsRef  = useRef(null)
  const booksRef = useRef(null)
  useRevealOnScroll(tipsRef)
  useRevealOnScroll(booksRef)

  return (
    <div className="flex-1 overflow-y-auto scrollbar-thin bg-warm-50">

      {/* ── Hero ── */}
      <section className="relative overflow-hidden text-white px-6 pt-20 pb-24"
        style={{ background: 'linear-gradient(135deg, #0a1f14 0%, #0d2b1a 40%, #0f3320 70%, #082010 100%)' }}
      >
        {/* Dot grid */}
        <div className="absolute inset-0 opacity-10"
          style={{ backgroundImage: 'radial-gradient(circle at 1px 1px, #25D366 1px, transparent 0)', backgroundSize: '28px 28px' }}
        />
        {/* Glowing orbs */}
        <div className="absolute -top-24 -left-24 w-80 h-80 rounded-full opacity-20 blur-3xl pointer-events-none"
          style={{ background: 'radial-gradient(circle, #00A884, transparent 70%)' }}
        />
        <div className="absolute -bottom-16 -right-16 w-72 h-72 rounded-full opacity-15 blur-3xl pointer-events-none"
          style={{ background: 'radial-gradient(circle, #25D366, transparent 70%)' }}
        />
        <div className="absolute top-1/2 left-1/2 -translate-x-1/2 -translate-y-1/2 w-[600px] h-40 opacity-10 blur-3xl pointer-events-none"
          style={{ background: 'radial-gradient(ellipse, #00A884, transparent 70%)' }}
        />

        <div className="relative max-w-2xl mx-auto text-center">
          {/* Badge */}
          <div className="anim-scale-in inline-flex items-center gap-2 border text-xs font-medium px-4 py-1.5 rounded-full mb-7"
            style={{ background: 'rgba(0,168,132,0.15)', borderColor: 'rgba(0,168,132,0.4)', color: '#6bcb77' }}
          >
            <span className="w-1.5 h-1.5 rounded-full bg-forest-400 animate-pulse" />
            6 psychology books · Agentic RAG · LangGraph
          </div>

          {/* Heading */}
          <h1 className="anim-fade-in-up font-serif leading-tight mb-5"
            style={{ fontSize: 'clamp(2.2rem, 5vw, 3.2rem)', animationDelay: '80ms' }}
          >
            Your safe space to think,
            <br />
            <span style={{ color: '#25D366', fontStyle: 'italic' }}>reflect, and grow.</span>
          </h1>

          {/* Sub */}
          <p className="anim-fade-in-up text-base leading-relaxed max-w-md mx-auto mb-10"
            style={{ color: '#7eb58d', animationDelay: '160ms' }}
          >
            MindMate Assistant helps you understand emotions, relationships, and yourself.
          </p>

          {/* CTA */}
          <div className="anim-fade-in-up flex flex-col sm:flex-row items-center justify-center gap-3" style={{ animationDelay: '240ms' }}>
            <button
              onClick={onStart}
              className="inline-flex items-center gap-2 text-white text-sm font-semibold px-7 py-3.5 rounded-xl transition-all active:scale-95 hover:scale-105"
              style={{ background: '#00A884', boxShadow: '0 4px 20px rgba(0,168,132,0.45)' }}
            >
              Start a conversation
              <svg width="14" height="14" viewBox="0 0 14 14" fill="none">
                <path d="M3 7h8M7.5 3.5L11 7l-3.5 3.5" stroke="white" strokeWidth="1.5" strokeLinecap="round" strokeLinejoin="round"/>
              </svg>
            </button>
          </div>

        </div>
      </section>

      {/* ── Quote carousel ── */}
      <section className="bg-warm-100 border-y border-warm-200 anim-fade-in" style={{ animationDelay: '300ms' }}>
        <QuoteCarousel />
      </section>

      {/* ── Tips ── */}
      <section className="px-6 py-14 max-w-4xl mx-auto" ref={tipsRef}>
        <div className="reveal mb-8" style={{ animationDelay: '0ms' }}>
          <p className="text-[11px] font-semibold text-warm-400 uppercase tracking-widest mb-1">Wellbeing</p>
          <h2 className="font-serif text-2xl text-warm-900">Daily mental health practices</h2>
        </div>
        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-4">
          {TIPS.map((tip, i) => (
            <div
              key={tip.title}
              className="reveal bg-warm-100 rounded-2xl border border-warm-200 p-5 shadow-warm-sm hover:shadow-warm-md hover:-translate-y-1 transition-all duration-200"
              style={{ animationDelay: `${i * 70}ms` }}
            >
              <div className="text-2xl mb-3">{tip.icon}</div>
              <h3 className="text-sm font-semibold text-warm-900 mb-1.5">{tip.title}</h3>
              <p className="text-xs text-warm-500 leading-relaxed">{tip.body}</p>
            </div>
          ))}
        </div>
      </section>

      {/* ── Books ── */}
      <section className="px-6 pb-16 max-w-4xl mx-auto" ref={booksRef}>
        <div className="reveal mb-8" style={{ animationDelay: '0ms' }}>
          <p className="text-[11px] font-semibold text-warm-400 uppercase tracking-widest mb-1">Library</p>
          <h2 className="font-serif text-2xl text-warm-900">Books powering the knowledge base</h2>
        </div>
        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-4">
          {BOOKS.map((book, i) => (
            <div
              key={book.title}
              className="reveal bg-warm-100 rounded-2xl border border-warm-200 shadow-warm-sm hover:shadow-warm-md hover:-translate-y-1 transition-all duration-200 flex gap-4 p-4"
              style={{ animationDelay: `${i * 70}ms` }}
            >
              {/* Cover */}
              <div className="flex-shrink-0 w-[68px]">
                <img
                  src={book.cover}
                  alt={book.title}
                  className="w-[68px] h-24 object-cover rounded-lg shadow-warm-sm bg-warm-100"
                  onError={e => { e.target.style.display = 'none'; e.target.nextSibling.style.display = 'flex' }}
                />
                <div className={`w-[68px] h-24 rounded-lg bg-gradient-to-br ${book.color} hidden items-center justify-center text-white text-[10px] font-bold text-center px-1.5 leading-tight`}>
                  {book.title}
                </div>
              </div>
              {/* Info */}
              <div className="flex flex-col justify-between min-w-0 py-0.5">
                <div>
                  <span className="text-[10px] font-semibold text-forest-600 bg-forest-50 border border-forest-200 px-2 py-0.5 rounded-full uppercase tracking-wide">
                    {book.tag}
                  </span>
                  <h3 className="text-sm font-semibold text-warm-900 mt-1.5 mb-0.5 leading-snug">{book.title}</h3>
                  <p className="text-[11px] text-warm-400 mb-2">{book.author}</p>
                </div>
                <p className="text-[11px] text-warm-500 leading-relaxed">{book.desc}</p>
              </div>
            </div>
          ))}
        </div>
      </section>

    </div>
  )
}
