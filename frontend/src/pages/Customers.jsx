import { useEffect, useState } from "react";
import API from "../api/axios";

export default function Customers() {
  const [customers, setCustomers] = useState([]);
  const [total, setTotal] = useState(0);
  const [page, setPage] = useState(1);
  const [pages, setPages] = useState(1);
  const [search, setSearch] = useState("");
  const [country, setCountry] = useState("");
  const [countries, setCountries] = useState([]);
  const [loading, setLoading] = useState(true);
  const [selectedCustomer, setSelectedCustomer] = useState(null);
  const [customerOrders, setCustomerOrders] = useState([]);
  const [modalLoading, setModalLoading] = useState(false);

  // Fetch filter dropdown options (countries)
  useEffect(() => {
    API.get("/data/filters")
      .then((res) => setCountries(res.data.countries || []))
      .catch((err) => console.error("Error fetching filters:", err));
  }, []);

  // Fetch paginated customer records
  const fetchCustomers = async () => {
    setLoading(true);
    try {
      const params = { page, limit: 10 };
      if (search.trim()) params.search = search.trim();
      if (country) params.country = country;

      const res = await API.get("/data/customers", { params });
      setCustomers(res.data.data);
      setTotal(res.data.total);
      setPages(res.data.pages || 1);
    } catch (err) {
      console.error("Failed to load customers:", err);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchCustomers();
  }, [page, country]);

  const handleSearchSubmit = (e) => {
    e.preventDefault();
    setPage(1);
    fetchCustomers();
  };

  // Open customer details modal
  const viewCustomerDetails = async (customerId) => {
    setModalLoading(true);
    setSelectedCustomer(null);
    try {
      const res = await API.get(`/data/customers/${customerId}`);
      setSelectedCustomer(res.data.customer);
      setCustomerOrders(res.data.orders);
    } catch (err) {
      console.error("Failed to fetch customer details:", err);
    } finally {
      setModalLoading(false);
    }
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
          <h1 className="text-2xl font-bold text-gray-800">Customers</h1>
          <p className="text-gray-500 text-sm mt-1">
            Browse and search customer records and order histories
          </p>
        </div>
        <span className="text-sm font-medium bg-blue-50 text-blue-700 px-3 py-1.5 rounded-full border border-blue-200">
          Total Customers: {total}
        </span>
      </div>

      {/* Search & Filter Bar */}
      <div className="bg-white p-4 rounded-xl shadow-sm border border-gray-200 flex flex-col md:flex-row gap-4 items-center justify-between">
        <form onSubmit={handleSearchSubmit} className="flex gap-2 w-full md:w-auto">
          <input
            type="text"
            placeholder="Search by name or email..."
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
            Filter Country:
          </label>
          <select
            value={country}
            onChange={(e) => {
              setCountry(e.target.value);
              setPage(1);
            }}
            className="border border-gray-300 rounded-lg px-3 py-2 text-sm bg-white focus:outline-none focus:ring-2 focus:ring-blue-500 w-full sm:w-48"
          >
            <option value="">All Countries</option>
            {countries.map((c) => (
              <option key={c} value={c}>
                {c}
              </option>
            ))}
          </select>
        </div>
      </div>

      {/* Customer Data Table */}
      <div className="bg-white rounded-xl shadow-sm border border-gray-200 overflow-hidden">
        {loading ? (
          <div className="p-8 text-center text-gray-500">Loading customers...</div>
        ) : customers.length === 0 ? (
          <div className="p-8 text-center text-gray-500">No customers found.</div>
        ) : (
          <div className="overflow-x-auto">
            <table className="w-full text-left border-collapse text-sm">
              <thead className="bg-gray-50 border-b border-gray-200 text-gray-600 uppercase text-xs">
                <tr>
                  <th className="py-3 px-4">Customer ID</th>
                  <th className="py-3 px-4">Name</th>
                  <th className="py-3 px-4">Email</th>
                  <th className="py-3 px-4">Location</th>
                  <th className="py-3 px-4 text-center">Orders</th>
                  <th className="py-3 px-4 text-right">Total Spent</th>
                  <th className="py-3 px-4 text-center">Actions</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-gray-100">
                {customers.map((c) => (
                  <tr key={c.customer_id} className="hover:bg-gray-50 transition-colors">
                    <td className="py-3 px-4 font-mono text-xs text-blue-600 font-semibold">
                      {c.customer_id}
                    </td>
                    <td className="py-3 px-4 font-medium text-gray-800">{c.name}</td>
                    <td className="py-3 px-4 text-gray-600">{c.email}</td>
                    <td className="py-3 px-4 text-gray-600">
                      {c.city}, {c.country}
                    </td>
                    <td className="py-3 px-4 text-center font-medium text-gray-700">
                      {c.total_orders}
                    </td>
                    <td className="py-3 px-4 text-right font-semibold text-gray-800">
                      ${fmt(c.total_spent)}
                    </td>
                    <td className="py-3 px-4 text-center">
                      <button
                        onClick={() => viewCustomerDetails(c.customer_id)}
                        className="text-xs font-semibold text-blue-600 hover:text-blue-800 bg-blue-50 hover:bg-blue-100 px-3 py-1 rounded"
                      >
                        View Orders
                      </button>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}

        {/* Pagination Controls */}
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

      {/* Modal: Customer Order History */}
      {(selectedCustomer || modalLoading) && (
        <div className="fixed inset-0 bg-black/50 flex items-center justify-center p-4 z-50">
          <div className="bg-white rounded-xl shadow-xl max-w-2xl w-full p-6 space-y-4 max-h-[85vh] overflow-y-auto">
            {modalLoading ? (
              <p className="text-center py-6 text-gray-500">Loading details...</p>
            ) : (
              <>
                <div className="flex justify-between items-start border-b pb-3">
                  <div>
                    <h2 className="text-lg font-bold text-gray-800">
                      {selectedCustomer.name}
                    </h2>
                    <p className="text-xs text-gray-500">
                      {selectedCustomer.email} • {selectedCustomer.city},{" "}
                      {selectedCustomer.country}
                    </p>
                  </div>
                  <button
                    onClick={() => setSelectedCustomer(null)}
                    className="text-gray-400 hover:text-gray-600 text-lg font-bold"
                  >
                    ✕
                  </button>
                </div>

                <div className="grid grid-cols-2 gap-4 bg-gray-50 p-3 rounded-lg text-sm">
                  <div>
                    <span className="text-gray-500">Total Spent:</span>{" "}
                    <span className="font-bold text-gray-800">
                      ${fmt(selectedCustomer.total_spent)}
                    </span>
                  </div>
                  <div>
                    <span className="text-gray-500">Orders Placed:</span>{" "}
                    <span className="font-bold text-gray-800">
                      {selectedCustomer.total_orders}
                    </span>
                  </div>
                </div>

                <div>
                  <h3 className="font-semibold text-gray-700 text-sm mb-2">Order History</h3>
                  {customerOrders.length === 0 ? (
                    <p className="text-xs text-gray-400 italic">No orders found.</p>
                  ) : (
                    <div className="border rounded-lg overflow-hidden text-xs">
                      <table className="w-full text-left">
                        <thead className="bg-gray-100 text-gray-600">
                          <tr>
                            <th className="p-2">Order ID</th>
                            <th className="p-2">Product</th>
                            <th className="p-2 text-center">Qty</th>
                            <th className="p-2 text-right">Amount</th>
                            <th className="p-2 text-center">Status</th>
                          </tr>
                        </thead>
                        <tbody className="divide-y divide-gray-100">
                          {customerOrders.map((o) => (
                            <tr key={o.order_id}>
                              <td className="p-2 font-mono text-blue-600 font-semibold">
                                {o.order_id}
                              </td>
                              <td className="p-2">{o.product_name}</td>
                              <td className="p-2 text-center">{o.quantity}</td>
                              <td className="p-2 text-right font-medium">
                                ${fmt(o.total_amount)}
                              </td>
                              <td className="p-2 text-center">
                                <span className="capitalize px-2 py-0.5 rounded text-[10px] font-semibold bg-gray-100 text-gray-700">
                                  {o.status}
                                </span>
                              </td>
                            </tr>
                          ))}
                        </tbody>
                      </table>
                    </div>
                  )}
                </div>
              </>
            )}
          </div>
        </div>
      )}
    </div>
  );
}