import { useEffect, useState } from "react";
import API from "../api/axios";

export default function Products() {
  const [products, setProducts] = useState([]);
  const [total, setTotal] = useState(0);
  const [page, setPage] = useState(1);
  const [pages, setPages] = useState(1);
  const [search, setSearch] = useState("");
  const [category, setCategory] = useState("");
  const [categories, setCategories] = useState([]);
  const [loading, setLoading] = useState(true);

  // Fetch category filter options
  useEffect(() => {
    API.get("/data/filters")
      .then((res) => setCategories(res.data.categories || []))
      .catch((err) => console.error("Error fetching filters:", err));
  }, []);

  // Fetch paginated products
  const fetchProducts = async () => {
    setLoading(true);
    try {
      const params = { page, limit: 10 };
      if (search.trim()) params.search = search.trim();
      if (category) params.category = category;

      const res = await API.get("/data/products", { params });
      setProducts(res.data.data);
      setTotal(res.data.total);
      setPages(res.data.pages || 1);
    } catch (err) {
      console.error("Failed to load products:", err);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchProducts();
  }, [page, category]);

  const handleSearchSubmit = (e) => {
    e.preventDefault();
    setPage(1);
    fetchProducts();
  };

  const fmt = (n) =>
    Number(n).toLocaleString("en-US", {
      minimumFractionDigits: 2,
      maximumFractionDigits: 2,
    });

  return (
    <div className="p-6 space-y-6">
      {/* Header */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
        <div>
          <h1 className="text-2xl font-bold text-gray-800">Products Catalog</h1>
          <p className="text-gray-500 text-sm mt-1">
            Product inventory, pricing, and revenue performance
          </p>
        </div>
        <span className="text-sm font-medium bg-emerald-50 text-emerald-700 px-3 py-1.5 rounded-full border border-emerald-200">
          Total Products: {total}
        </span>
      </div>

      {/* Search & Filter Bar */}
      <div className="bg-white p-4 rounded-xl shadow-sm border border-gray-200 flex flex-col md:flex-row gap-4 items-center justify-between">
        <form onSubmit={handleSearchSubmit} className="flex gap-2 w-full md:w-auto">
          <input
            type="text"
            placeholder="Search products by name..."
            value={search}
            onChange={(e) => setSearch(e.target.value)}
            className="border border-gray-300 rounded-lg px-3 py-2 text-sm w-full sm:w-64 focus:outline-none focus:ring-2 focus:ring-blue-500"
          />
          <button
            type="submit"
            className="bg-blue-600 hover:bg-blue-700 text-white px-4 py-2 rounded-lg text-sm font-medium transition-colors"
          >
            Search
          </button>
        </form>

        <div className="flex items-center gap-2 w-full md:w-auto">
          <label className="text-sm text-gray-600 font-medium whitespace-nowrap">
            Category:
          </label>
          <select
            value={category}
            onChange={(e) => {
              setCategory(e.target.value);
              setPage(1);
            }}
            className="border border-gray-300 rounded-lg px-3 py-2 text-sm bg-white focus:outline-none focus:ring-2 focus:ring-blue-500 w-full sm:w-48"
          >
            <option value="">All Categories</option>
            {categories.map((cat) => (
              <option key={cat} value={cat}>
                {cat}
              </option>
            ))}
          </select>
        </div>
      </div>

      {/* Products Table */}
      <div className="bg-white rounded-xl shadow-sm border border-gray-200 overflow-hidden">
        {loading ? (
          <div className="p-8 text-center text-gray-500">Loading products...</div>
        ) : products.length === 0 ? (
          <div className="p-8 text-center text-gray-500">No products found.</div>
        ) : (
          <div className="overflow-x-auto">
            <table className="w-full text-left border-collapse text-sm">
              <thead className="bg-gray-50 border-b border-gray-200 text-gray-600 uppercase text-xs">
                <tr>
                  <th className="py-3 px-4">Product ID</th>
                  <th className="py-3 px-4">Product Name</th>
                  <th className="py-3 px-4">Category</th>
                  <th className="py-3 px-4 text-right">Price</th>
                  <th className="py-3 px-4 text-center">Stock</th>
                  <th className="py-3 px-4 text-center">Units Sold</th>
                  <th className="py-3 px-4 text-right">Total Revenue</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-gray-100">
                {products.map((p) => (
                  <tr key={p.product_id} className="hover:bg-gray-50 transition-colors">
                    <td className="py-3 px-4 font-mono text-xs text-blue-600 font-semibold">
                      {p.product_id}
                    </td>
                    <td className="py-3 px-4 font-medium text-gray-800">{p.name}</td>
                    <td className="py-3 px-4">
                      <span className="bg-gray-100 text-gray-700 px-2 py-0.5 rounded text-xs">
                        {p.category}
                      </span>
                    </td>
                    <td className="py-3 px-4 text-right font-medium text-gray-800">
                      ${fmt(p.unit_price)}
                    </td>
                    <td className="py-3 px-4 text-center">
                      <span
                        className={`text-xs px-2 py-0.5 rounded font-medium ${
                          p.stock < 20
                            ? "bg-red-100 text-red-700"
                            : "bg-green-100 text-green-700"
                        }`}
                      >
                        {p.stock}
                      </span>
                    </td>
                    <td className="py-3 px-4 text-center font-medium text-gray-700">
                      {p.total_sold}
                    </td>
                    <td className="py-3 px-4 text-right font-bold text-gray-800">
                      ${fmt(p.total_revenue)}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}

        {/* Pagination */}
        <div className="p-4 border-t border-gray-200 flex items-center justify-between text-sm text-gray-600">
          <div>
            Page <span className="font-semibold text-gray-800">{page}</span> of{" "}
            <span className="font-semibold text-gray-800">{pages}</span>
          </div>
          <div className="flex gap-2">
            <button
              disabled={page <= 1}
              onClick={() => setPage((p) => Math.max(p - 1, 1))}
              className="px-3 py-1.5 border border-gray-300 rounded hover:bg-gray-50 disabled:opacity-50 disabled:cursor-not-allowed"
            >
              Previous
            </button>
            <button
              disabled={page >= pages}
              onClick={() => setPage((p) => Math.min(p + 1, pages))}
              className="px-3 py-1.5 border border-gray-300 rounded hover:bg-gray-50 disabled:opacity-50 disabled:cursor-not-allowed"
            >
              Next
            </button>
          </div>
        </div>
      </div>
    </div>
  );
}