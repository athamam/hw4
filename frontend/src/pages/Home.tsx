import { useEffect, useState } from 'react'
import { Link } from 'react-router-dom'
import { fetchProducts, type Product } from '../api'
import ProductCard from '../components/ProductCard'

const FEATURED_IDS = [
  'basic-hoodie-big-yale',
  'champion-reverse-weave-crewneck',
  '2025-yale-vs-harvard-t-shirt',
  'yale-mom-hoodie',
]

export default function Home() {
  const [featured, setFeatured] = useState<Product[]>([])

  useEffect(() => {
    fetchProducts()
      .then((all) => setFeatured(FEATURED_IDS.map((id) => all.find((p) => p.product_id === id)).filter((p): p is Product => !!p)))
      .catch(() => setFeatured([]))
  }, [])

  return (
    <>
      <section className="hero">
        <div className="hero-text">
          <p className="eyebrow">Officially licensed Yale apparel</p>
          <h1>Easygoing comfort, <em>all-in Bulldog pride.</em></h1>
          <p className="lead">
            Hoodies for late-night problem sets, crewnecks for game day, and tees for every
            residential college, sport, and school. Campus Customs dresses the whole Yale family.
          </p>
          <div className="hero-actions">
            <Link to="/products" className="btn">Shop all products</Link>
            <Link to="/about" className="btn btn-ghost">Our story</Link>
          </div>
        </div>
      </section>

      <section className="section">
        <div className="section-head">
          <h2>Crowd favorites</h2>
          <Link to="/products" className="link">View all →</Link>
        </div>
        <div className="grid">
          {featured.map((p) => <ProductCard key={p.product_id} product={p} />)}
        </div>
      </section>

      <section className="section">
        <div className="perks">
          <div className="perk">
            <h3>Rep your college</h3>
            <p>From Branford to Pierson, there's a piece for every residential college crest.</p>
          </div>
          <div className="perk">
            <h3>Gear for the whole family</h3>
            <p>Mom, Dad, Grandpa, Aunt: everyone gets to show off their favorite Bulldog.</p>
          </div>
          <div className="perk">
            <h3>Need a hand?</h3>
            <p>Tap the chat bubble to ask about sizes, stock, or gift ideas.</p>
          </div>
        </div>
      </section>
    </>
  )
}
