import { useEffect, useRef } from 'react'
import { useChatResults } from '../chatResults'
import ProductCard from './ProductCard'

// The on-page results section. When the chat agent finds products, they appear here
// as full product cards. These are the SAME ProductCard components used on the
// Products page, so clicking one opens the single-item detail view (Problem 3).
export default function ChatResults() {
  const { products, query, clear } = useChatResults()
  const ref = useRef<HTMLDivElement>(null)

  // Scroll the fresh results into view when they change.
  useEffect(() => {
    if (products.length) ref.current?.scrollIntoView({ behavior: 'smooth', block: 'start' })
  }, [products])

  if (products.length === 0) return null

  return (
    <section className="section chat-results" ref={ref}>
      <div className="section-head">
        <h2>
          From your chat <span className="muted">({products.length})</span>
          {query && <span className="chat-results-q"> · “{query}”</span>}
        </h2>
        <button className="link chat-results-clear" onClick={clear}>Clear</button>
      </div>
      <div className="grid">
        {products.map((p) => <ProductCard key={p.product_id} product={p} />)}
      </div>
    </section>
  )
}
