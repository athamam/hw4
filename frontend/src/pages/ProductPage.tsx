import { useEffect, useState } from 'react'
import { Link, useParams } from 'react-router-dom'
import { fetchProduct, formatPrice, type ProductDetail } from '../api'

function stockLabel(qty: number) {
  if (qty === 0) return 'Sold out'
  if (qty <= 5) return `Only ${qty} left`
  return `${qty} in stock`
}

export default function ProductPage() {
  const { productId = '' } = useParams()
  const [product, setProduct] = useState<ProductDetail | null>(null)
  const [error, setError] = useState<string | null>(null)
  const [selected, setSelected] = useState<string | null>(null)

  useEffect(() => {
    setProduct(null)
    setError(null)
    setSelected(null)
    fetchProduct(productId).then(setProduct).catch((e: Error) => setError(e.message))
  }, [productId])

  if (error) {
    return (
      <section className="section">
        <p className="error">We couldn't find that product ({error}).</p>
        <Link to="/products" className="link">← Back to all products</Link>
      </section>
    )
  }
  if (!product) return <section className="section"><p className="muted">Loading…</p></section>

  const chosen = product.sizes.find((s) => s.size === selected)

  return (
    <section className="section">
      <Link to="/products" className="link">← Back to all products</Link>
      <div className="detail">
        <div className="detail-img">
          <img src={product.image_url} alt={product.name} />
        </div>
        <div className="detail-info">
          <div className="card-type">{product.garment_type}</div>
          <h1>{product.name}</h1>
          <div className="detail-price">{formatPrice(product.price)}</div>
          <p>{product.description}</p>

          <div className="detail-block">
            <div className="detail-label">Colors</div>
            <div className="chips">
              {product.colors.map((c) => <span key={c} className="chip">{c}</span>)}
            </div>
          </div>

          <div className="detail-block">
            <div className="detail-label">Sizes &amp; stock</div>
            <div className="sizes">
              {product.sizes.map((s) => (
                <button
                  key={s.size}
                  className={`size ${s.quantity === 0 ? 'size-out' : ''} ${selected === s.size ? 'size-on' : ''}`}
                  disabled={s.quantity === 0}
                  onClick={() => setSelected(s.size)}
                  title={stockLabel(s.quantity)}
                >
                  <span className="size-name">{s.size}</span>
                  <span className="size-qty">{s.quantity === 0 ? 'Sold out' : s.quantity}</span>
                </button>
              ))}
            </div>
            <p className="muted">
              {chosen
                ? `Size ${chosen.size}: ${stockLabel(chosen.quantity)}`
                : product.total_stock > 0
                  ? `${product.total_stock} total in stock. Pick a size.`
                  : 'This item is currently sold out in every size.'}
            </p>
          </div>

          <div className="detail-block">
            <div className="detail-label">Tags</div>
            <div className="chips">
              {product.search_tags.map((t) => <span key={t} className="chip chip-soft">{t}</span>)}
            </div>
          </div>
        </div>
      </div>
    </section>
  )
}
