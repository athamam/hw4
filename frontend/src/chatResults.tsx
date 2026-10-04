import { createContext, useContext, useState, type ReactNode } from 'react'
import type { Product } from './api'

// Holds the products the chat agent most recently surfaced, so the page can show
// them as cards. Shared across the app so the floating chat (any route) can update
// a results section rendered in the main page area.
interface ChatResultsState {
  products: Product[]
  query: string | null
  setResults: (products: Product[], query: string) => void
  clear: () => void
}

const ChatResultsContext = createContext<ChatResultsState | null>(null)

export function ChatResultsProvider({ children }: { children: ReactNode }) {
  const [products, setProducts] = useState<Product[]>([])
  const [query, setQuery] = useState<string | null>(null)

  const setResults = (next: Product[], q: string) => {
    setProducts(next)
    setQuery(q)
  }
  const clear = () => {
    setProducts([])
    setQuery(null)
  }

  return (
    <ChatResultsContext.Provider value={{ products, query, setResults, clear }}>
      {children}
    </ChatResultsContext.Provider>
  )
}

export function useChatResults(): ChatResultsState {
  const ctx = useContext(ChatResultsContext)
  if (!ctx) throw new Error('useChatResults must be used within ChatResultsProvider')
  return ctx
}
