import { useEffect, useState } from 'react'
import { Link, NavLink, useNavigate } from 'react-router-dom'
import { useAuth } from '../auth'

const links = [
  { to: '/', label: 'Home', end: true },
  { to: '/products', label: 'Products' },
  { to: '/about', label: 'About Us' },
]

const ANNOUNCE = 'Proud New Haven outfitters · Officially licensed Yale apparel · Visit us at 57 Broadway · '

export default function NavBar() {
  const { user, logout } = useAuth()
  const navigate = useNavigate()
  const [scrolled, setScrolled] = useState(false)

  useEffect(() => {
    const onScroll = () => setScrolled(window.scrollY > 8)
    onScroll()
    window.addEventListener('scroll', onScroll, { passive: true })
    return () => window.removeEventListener('scroll', onScroll)
  }, [])

  function handleLogout() {
    logout()
    navigate('/')
  }

  return (
    <header className={`navbar${scrolled ? ' scrolled' : ''}`}>
      <div className="announce"><span>{ANNOUNCE.repeat(2)}</span></div>
      <nav className="nav-inner">
        <Link to="/" className="brand">
          <span className="brand-mark">CC</span>
          <span className="brand-text">Campus Customs</span>
        </Link>
        <div className="nav-links">
          {links.map((l) => (
            <NavLink key={l.to} to={l.to} end={l.end} className="nav-link">
              {l.label}
            </NavLink>
          ))}
        </div>
        <div className="nav-account">
          {user ? (
            <>
              <span className="nav-greeting">Hi, {user.first_name}</span>
              <button className="btn btn-small btn-ghost" onClick={handleLogout}>Log out</button>
            </>
          ) : (
            <>
              <NavLink to="/login" className="nav-link">Log in</NavLink>
              <NavLink to="/create-account" className="btn btn-small">Create account</NavLink>
            </>
          )}
        </div>
      </nav>
    </header>
  )
}
