// Typed client for the Campus Customs FastAPI backend (proxied by Vite).

export interface Product {
  product_id: string
  name: string
  garment_type: string
  description: string
  colors: string[]
  price: number
  image_url: string
  total_stock: number
}

export interface SizeStock {
  size: string
  quantity: number
}

export interface ProductDetail extends Product {
  search_tags: string[]
  sizes: SizeStock[]
}

export interface ChatReply {
  reply: string
  products: Product[]
}

async function getJson<T>(url: string, init?: RequestInit): Promise<T> {
  const res = await fetch(url, init)
  if (!res.ok) throw new Error(`${res.status} ${res.statusText}`)
  return res.json() as Promise<T>
}

export const fetchProducts = () => getJson<Product[]>('/api/products')

export const fetchProduct = (id: string) =>
  getJson<ProductDetail>(`/api/products/${encodeURIComponent(id)}`)

export interface PageContext {
  product_id?: string | null
  path?: string | null
}

export interface ChatHistoryMessage {
  role: 'user' | 'assistant'
  content: string
  products: Product[]
}

// Send a chat message to the PydanticAI agent. Includes the auth token (if signed
// in) so the agent knows the customer and can persist history, and the page context
// so "do you have this in pink" resolves to the product being viewed.
export const sendChatMessage = (message: string, page?: PageContext, token?: string | null) =>
  getJson<ChatReply>('/api/chat', {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
      ...(token ? { Authorization: `Bearer ${token}` } : {}),
    },
    body: JSON.stringify({ message, page }),
  })

export const fetchChatHistory = (token: string) =>
  getJson<ChatHistoryMessage[]>('/api/chat/history', {
    headers: { Authorization: `Bearer ${token}` },
  })

export const clearChatHistory = (token: string) =>
  fetch('/api/chat/history', { method: 'DELETE', headers: { Authorization: `Bearer ${token}` } })

export const formatPrice = (price: number) => `$${price.toFixed(2)}`

// ---------- Auth ----------

export interface PublicUser {
  id: number
  first_name: string
  last_name: string
  email: string
}

export interface AuthResponse {
  token: string
  user: PublicUser
}

async function postAuth<T>(url: string, body: unknown): Promise<T> {
  const res = await fetch(url, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(body),
  })
  if (!res.ok) {
    let detail = `${res.status} ${res.statusText}`
    try {
      const data = await res.json()
      if (data?.detail) detail = typeof data.detail === 'string' ? data.detail : detail
    } catch {
      // keep the status-based message
    }
    throw new Error(detail)
  }
  return res.json() as Promise<T>
}

export interface SignupInput {
  first_name: string
  last_name: string
  email: string
  password: string
}

export const signup = (input: SignupInput) =>
  postAuth<AuthResponse>('/api/auth/signup', input)

export const login = (email: string, password: string) =>
  postAuth<AuthResponse>('/api/auth/login', { email, password })

export async function fetchMe(token: string): Promise<PublicUser> {
  const res = await fetch('/api/auth/me', { headers: { Authorization: `Bearer ${token}` } })
  if (!res.ok) throw new Error('session expired')
  return res.json() as Promise<PublicUser>
}
