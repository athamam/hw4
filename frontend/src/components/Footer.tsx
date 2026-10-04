import { Link } from 'react-router-dom'

export default function Footer() {
  return (
    <footer className="footer">
      <div className="footer-inner">
        <div>
          <div className="footer-brand">Campus Customs</div>
          <p>Bulldog spirit, comfy enough to live in.</p>
        </div>
        <div>
          <div className="footer-head">Shop</div>
          <Link to="/products">All products</Link>
          <Link to="/about">About us</Link>
        </div>
        <div>
          <div className="footer-head">Visit</div>
          <p>57 Broadway<br />New Haven, CT 06511</p>
        </div>
      </div>
      <div className="footer-note">© {new Date().getFullYear()} Campus Customs · MGT 409 HW4 demo site</div>
    </footer>
  )
}
