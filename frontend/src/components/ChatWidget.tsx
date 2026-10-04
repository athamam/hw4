import { useEffect, useRef, useState, type FormEvent } from 'react'
import { Link, useLocation } from 'react-router-dom'
import { fetchChatHistory, formatPrice, sendChatMessage, type Product } from '../api'
import { useChatResults } from '../chatResults'
import { useAuth, getToken } from '../auth'

interface Message {
  role: 'user' | 'assistant'
  content: string
  products?: Product[]
}

const GREETING: Message = {
  role: 'assistant',
  content: "Hi! I'm the Campus Customs helper. Ask me about hoodies, sizes, or gifts for the Yale family.",
}

export default function ChatWidget() {
  const [open, setOpen] = useState(false)
  const [messages, setMessages] = useState<Message[]>([GREETING])
  const [input, setInput] = useState('')
  const [sending, setSending] = useState(false)
  const endRef = useRef<HTMLDivElement>(null)
  const { setResults } = useChatResults()
  const { user } = useAuth()
  const location = useLocation()

  useEffect(() => {
    endRef.current?.scrollIntoView({ behavior: 'smooth' })
  }, [messages, open])

  // Reload saved history when a user logs in; reset to the greeting on logout.
  useEffect(() => {
    const token = getToken()
    if (user && token) {
      fetchChatHistory(token)
        .then((rows) => {
          if (rows.length === 0) {
            setMessages([{ ...GREETING, content: `Welcome back, ${user.first_name}! How can I help you today?` }])
          } else {
            setMessages([
              { ...GREETING, content: `Welcome back, ${user.first_name}! Here's where we left off.` },
              ...rows.map((r) => ({ role: r.role, content: r.content, products: r.products })),
            ])
          }
        })
        .catch(() => setMessages([GREETING]))
    } else {
      setMessages([GREETING])
    }
  }, [user])

  // Resolve the product being viewed, so "do you have this in pink" works.
  function currentPage() {
    const match = location.pathname.match(/^\/products\/(.+)$/)
    return { product_id: match ? decodeURIComponent(match[1]) : null, path: location.pathname }
  }

  async function send(text: string) {
    if (!text || sending) return
    setInput('')
    setMessages((m) => [...m, { role: 'user', content: text }])
    setSending(true)
    try {
      const res = await sendChatMessage(text, currentPage(), getToken())
      setMessages((m) => [...m, { role: 'assistant', content: res.reply, products: res.products }])
      // Surface any matches as product cards on the page (Problem 7).
      if (res.products && res.products.length > 0) setResults(res.products, text)
    } catch {
      setMessages((m) => [
        ...m,
        { role: 'assistant', content: "Sorry, I couldn't reach the shop right now. Please try again in a moment." },
      ])
    } finally {
      setSending(false)
    }
  }

  function handleSubmit(e: FormEvent) {
    e.preventDefault()
    send(input.trim())
  }

  // Starter prompts shown until the shopper sends their first message.
  const SUGGESTIONS = ['Show me Yale hoodies', 'Gifts for a Yale dad', 'Crewnecks under $60', "What's in stock in XL?"]
  const showSuggestions = !sending && !messages.some((m) => m.role === 'user')

  return (
    <div className="chat">
      {open && (
        <div className="chat-panel" role="dialog" aria-label="Campus Customs chat">
          <div className="chat-header">
            <div className="chat-avatar" aria-hidden="true">CC</div>
            <div className="chat-head-text">
              <div className="chat-title">Campus Customs Chat</div>
              <div className="chat-sub">Online · here to help you find your fit</div>
            </div>
            <button className="chat-close" onClick={() => setOpen(false)} aria-label="Close chat">×</button>
          </div>
          <div className="chat-messages">
            {messages.map((m, i) => (
              <div key={i} className={`chat-msg chat-${m.role}`}>
                <div className="chat-bubble">{m.content}</div>
                {m.products && m.products.length > 0 && (
                  <div className="chat-products">
                    {m.products.map((p) => (
                      <Link key={p.product_id} to={`/products/${p.product_id}`} className="chat-product">
                        <img src={p.image_url} alt={p.name} />
                        <span>{p.name}</span>
                        <b>{formatPrice(p.price)}</b>
                      </Link>
                    ))}
                  </div>
                )}
              </div>
            ))}
            {sending && (
              <div className="chat-msg chat-assistant">
                <div className="chat-bubble chat-typing" aria-label="Assistant is typing">
                  <span></span><span></span><span></span>
                </div>
              </div>
            )}
            {showSuggestions && (
              <div className="chat-suggestions">
                {SUGGESTIONS.map((s) => (
                  <button key={s} type="button" className="chat-chip" onClick={() => send(s)}>{s}</button>
                ))}
              </div>
            )}
            <div ref={endRef} />
          </div>
          <form className="chat-input" onSubmit={handleSubmit}>
            <input
              value={input}
              onChange={(e) => setInput(e.target.value)}
              placeholder="Ask about products, sizes, stock…"
              aria-label="Chat message"
              autoFocus
            />
            <button type="submit" className="btn" disabled={sending || !input.trim()}>Send</button>
          </form>
        </div>
      )}
      <button className="chat-toggle" onClick={() => setOpen((o) => !o)} aria-label={open ? 'Close chat' : 'Open chat'}>
        {open ? '×' : '💬'}
      </button>
    </div>
  )
}
