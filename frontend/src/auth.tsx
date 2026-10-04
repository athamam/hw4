import { createContext, useContext, useEffect, useState, type ReactNode } from 'react'
import { fetchMe, login as apiLogin, signup as apiSignup, type PublicUser, type SignupInput } from './api'

interface AuthState {
  user: PublicUser | null
  loading: boolean
  login: (email: string, password: string) => Promise<void>
  signup: (input: SignupInput) => Promise<void>
  logout: () => void
}

const AuthContext = createContext<AuthState | null>(null)
const TOKEN_KEY = 'cc_token'

export function AuthProvider({ children }: { children: ReactNode }) {
  const [user, setUser] = useState<PublicUser | null>(null)
  const [loading, setLoading] = useState(true)

  // On load, restore a session from a saved token.
  useEffect(() => {
    const token = localStorage.getItem(TOKEN_KEY)
    if (!token) {
      setLoading(false)
      return
    }
    fetchMe(token)
      .then(setUser)
      .catch(() => localStorage.removeItem(TOKEN_KEY))
      .finally(() => setLoading(false))
  }, [])

  async function login(email: string, password: string) {
    const res = await apiLogin(email, password)
    localStorage.setItem(TOKEN_KEY, res.token)
    setUser(res.user)
  }

  async function signup(input: SignupInput) {
    const res = await apiSignup(input)
    localStorage.setItem(TOKEN_KEY, res.token)
    setUser(res.user)
  }

  function logout() {
    localStorage.removeItem(TOKEN_KEY)
    setUser(null)
  }

  return (
    <AuthContext.Provider value={{ user, loading, login, signup, logout }}>
      {children}
    </AuthContext.Provider>
  )
}

export function getToken(): string | null {
  return localStorage.getItem(TOKEN_KEY)
}

export function useAuth(): AuthState {
  const ctx = useContext(AuthContext)
  if (!ctx) throw new Error('useAuth must be used within AuthProvider')
  return ctx
}
