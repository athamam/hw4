import { Link } from 'react-router-dom'
import { formatPrice, type Product } from '../api'

export default function ProductCard({ product }: { product: Product }) {
  return (
    <Link to={`/products/${product.product_id}`} className="card">
      <div className="card-img">
        <img src={product.image_url} alt={product.name} loading="lazy" />
        {product.total_stock === 0 && <span className="badge badge-out">Sold out</span>}
      </div>
      <div className="card-body">
        <div className="card-type">{product.garment_type}</div>
        <h3 className="card-name">{product.name}</h3>
        <p className="card-desc">{product.description}</p>
        <div className="card-price">{formatPrice(product.price)}</div>
      </div>
    </Link>
  )
}
