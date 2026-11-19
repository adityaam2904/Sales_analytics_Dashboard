import { useEffect, useState } from "react";
import API from "../api/axios";

export default function Orders() {
  const [orders, setOrders] = useState([]);
  const [total, setTotal] = useState(0);
  const [page, setPage] = useState(1);
  const [pages, setPages] = useState(1);
  const [status, setStatus] = useState("");
  const [statuses, setStatuses] = useState([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    API.get("/data/filters")
      .then((res) => setStatuses(res.data.statuses || []))
      .catch((err) => console.error("Error fetching filters:", err));
  }, []);

  const fetchOrders = async () => {
    setLoading(true);
    try {
      const params = { page, limit: 10 };
      if (status) params.status = status;

      const res = await API.get("/data/orders", { params });
      setOrders(res.data.data);
      setTotal(res.data.total);
      setPages(res.data.pages || 1);
    } catch (err) {
      console.error("Failed to load orders:", err);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchOrders();
  }, [page, status]);

  const fmt = (n) =>
    Number(n).toLocaleString("en-US", {
      minimumFractionDigits: 2,
      maximumFractionDigits: 2,
    });

  const getStatusBadge = (st) => {
    switch (st) {
      case "completed":
        return "bg-green-100 text-green-800 border-green-200";
      case "shipped":
        return "bg-blue-100 text-blue-800 border-blue-200";
      case "pending":
        return "bg-yellow-100 text-yellow-800 border-yellow-200";
      case "cancelled":
        return "bg-red-100 text-red-800 border-red-200";
      case "returned":
        return "bg-purple-100 text-purple-800 border-purple-200";
      default:
        return "bg-gray-100 text-gray-800 border-gray-200";
    }
  };

  return (
    <div className="p-6 space-y-6">
      {/* Header */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
        <div>
          <h1 className="text-2xl font-bold text-gray-800">Orders Explorer</h1>
          <p className="text-gray-500 text-sm mt-1">
            View detailed sales transactions, statuses, and pricing breakdowns
          </p>
        </div>
        <span className="text-sm font-medium bg-indigo-50 text-indigo-700 px-3 py-1.5 rounded-full border border-indigo-200">
          Total Orders: {total}
        </span>
      </div>

      {/* Filter Bar */}
      <div className="bg-white p-4 rounded-xl shadow-sm border border-gray-200 flex justify-between items-center">
        <div className="flex items-center gap-2">
          <label className="text-sm text-gray-600 font-medium">Filter by Status:</label>
          <select
            value={status}
            onChange={(e) => {
              setStatus(e.target.value);
              setPage(1);
            }}
            className="border border-gray-300 rounded-lg px-3 py-2 text-sm bg-white focus:outline-none focus:ring-2 focus:ring-blue-500"
          >
            <option value="">All Statuses</option>
            {statuses.map((s) => (
              <option key={s} value={s}>
                {s.toUpperCase()}
              </option>
            ))}
          </select>
        </div>
      </div>

      {/* Orders Table */}
      <div className="bg-white rounded-xl shadow-sm border border-gray-200 overflow-hidden">
        {loading ? (
          <div className="p-8 text-center text-gray-500">Loading orders...</div>
        ) : orders.length === 0 ? (
          <div className="p-8 text-center text-gray-500">No orders found.</div>
        ) : (
          <div className="overflow-x-auto">
            <table className="w-full text-left border-collapse text-sm">
              <thead className="bg-gray-50 border-b border-gray-200 text-gray-600 uppercase text-xs">
                <tr>
                  <th className="py-3 px-4">Order ID</th>
                  <th className="py-3 px-4">Date</th>
                  <th className="py-3 px-4">Customer</th>
                  <th className="py-3 px-4">Product</th>
                  <th className="py-3 px-4 text-center">Qty</th>
                  <th className="py-3 px-4 text-right">Unit Price</th>
                  <th className="py-3 px-4 text-center">Discount</th>
                  <th className="py-3 px-4 text-right">Total Amount</th>
                  <th className="py-3 px-4 text-center">Status</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-gray-100">
                {orders.map((o) => (
                  <tr key={o.order_id} className="hover:bg-gray-50 transition-colors">
                    <td className="py-3 px-4 font-mono text-xs text-blue-600 font-semibold">
                      {o.order_id}
                    </td>
                    <td className="py-3 px-4 text-gray-600 text-xs">
                      {new Date(o.order_date).toLocaleDateString()}
                    </td>
                    <td className="py-3 px-4 font-medium text-gray-800">
                      {o.customer_name}
                    </td>
                    <td className="py-3 px-4 text-gray-700">{o.product_name}</td>
                    <td className="py-3 px-4 text-center font-medium">{o.quantity}</td>
                    <td className="py-3 px-4 text-right text-gray-600">
                      ${fmt(o.unit_price)}
                    </td>
                    <td className="py-3 px-4 text-center text-xs text-gray-500">
                      {Number(o.discount_pct)}%
                    </td>
                    <td className="py-3 px-4 text-right font-bold text-gray-900">
                      ${fmt(o.total_amount)}
                    </td>
                    <td className="py-3 px-4 text-center">
                      <span
                        className={`text-xs capitalize font-semibold px-2.5 py-1 rounded-full border ${getStatusBadge(
                          o.status
                        )}`}
                      >
                        {o.status}
                      </span>
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