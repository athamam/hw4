import { useEffect, useMemo, useState } from 'react'
import { fetchProducts, type Product } from '../api'
import ProductCard from '../components/ProductCard'

// Group the catalogue's many inconsistent garment_type labels into a few broad,
// shopper-friendly categories for the filter.
function categoryOf(garmentType: string): string {
  const t = garmentType.toLowerCase()
  if (t.includes('hood')) return 'Hoodies'
  if (t.includes('crew')) return 'Crewnecks'
  if (t.includes('jacket') || t.includes('bomber')) return 'Jackets'
  if (t.includes('zip')) return 'Quarter-Zips'
  if (t.includes('sweater') || t.includes('fleece') || t.includes('mockneck')) return 'Sweaters & Fleece'
  if (t.includes('t-shirt') || t.includes('tee') || t.includes('shirt')) return 'T-Shirts'
  return 'Other'
}

type SortKey = 'featured' | 'price-asc' | 'price-desc' | 'name'

export default function Products() {
  const [products, setProducts] = useState<Product[] | null>(null)
  const [error, setError] = useState<string | null>(null)
  const [query, setQuery] = useState('')
  const [category, setCategory] = useState('All')
  const [sort, setSort] = useState<SortKey>('featured')
  const [inStockOnly, setInStockOnly] = useState(false)

  useEffect(() => {
    fetchProducts().then(setProducts).catch((e: Error) => setError(e.message))
  }, [])

  const categories = useMemo(() => {
    if (!products) return ['All']
    return ['All', ...Array.from(new Set(products.map((p) => categoryOf(p.garment_type)))).sort()]
  }, [products])

  const visible = useMemo(() => {
    if (!products) return []
    const q = query.trim().toLowerCase()
    let list = products.filter((p) => {
      if (category !== 'All' && categoryOf(p.garment_type) !== category) return false
      if (inStockOnly && p.total_stock <= 0) return false
      if (!q) return true
      return (
        p.name.toLowerCase().includes(q) ||
        p.description.toLowerCase().includes(q) ||
        p.colors.join(' ').toLowerCase().includes(q) ||
        p.garment_type.toLowerCase().includes(q)
      )
    })
    list = [...list]
    if (sort === 'price-asc') list.sort((a, b) => a.price - b.price)
    else if (sort === 'price-desc') list.sort((a, b) => b.price - a.price)
    else if (sort === 'name') list.sort((a, b) => a.name.localeCompare(b.name))
    return list
  }, [products, query, category, sort, inStockOnly])

  return (
    <section className="section">
      <div className="page-head">
        <h1>All products</h1>
        <p className="lead">Sweatshirts, quarter-zips, tees and more, all in true Bulldog style.</p>
      </div>

      {error && <p className="error">Couldn't load products ({error}). Is the backend running?</p>}
      {!products && !error && <p className="muted">Loading products…</p>}

      {products && (
        <>
          <div className="toolbar">
            <input
              className="toolbar-search"
              type="search"
              value={query}
              onChange={(e) => setQuery(e.target.value)}
              placeholder="Search products…"
              aria-label="Search products"
            />
            <select value={category} onChange={(e) => setCategory(e.target.value)} aria-label="Category">
              {categories.map((c) => <option key={c} value={c}>{c === 'All' ? 'All categories' : c}</option>)}
            </select>
            <select value={sort} onChange={(e) => setSort(e.target.value as SortKey)} aria-label="Sort by">
              <option value="featured">Sort: Featured</option>
              <option value="price-asc">Price: Low to High</option>
              <option value="price-desc">Price: High to Low</option>
              <option value="name">Name: A–Z</option>
            </select>
            <label className="toolbar-check">
              <input type="checkbox" checked={inStockOnly} onChange={(e) => setInStockOnly(e.target.checked)} />
              In stock only
            </label>
          </div>

          <p className="muted">
            Showing {visible.length} of {products.length} items
            {(query || category !== 'All' || inStockOnly) && (
              <button
                className="link toolbar-reset"
                onClick={() => { setQuery(''); setCategory('All'); setInStockOnly(false); setSort('featured') }}
              >
                Reset filters
              </button>
            )}
          </p>

          {visible.length === 0 ? (
            <p className="muted">No products match your filters. Try clearing them or searching something else.</p>
          ) : (
            <div className="grid">
              {visible.map((p) => <ProductCard key={p.product_id} product={p} />)}
            </div>
          )}
        </>
      )}
    </section>
  )
}
