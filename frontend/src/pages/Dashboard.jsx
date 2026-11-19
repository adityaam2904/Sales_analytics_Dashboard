import { useEffect, useState } from "react";
import API from "../api/axios";
import {
  LineChart, Line, BarChart, Bar, PieChart, Pie, Cell,
  XAxis, YAxis, CartesianGrid, Tooltip, Legend, ResponsiveContainer
} from "recharts";

// ─── KPI CARD ───────────────────────────────
function KPICard({ title, value, subtitle, color }) {
  return (
    <div className={`bg-white rounded-xl shadow p-6 border-l-4 ${color}`}>
      <p className="text-sm text-gray-500 font-medium">{title}</p>
      <p className="text-3xl font-bold text-gray-800 mt-1">{value}</p>
      {subtitle && <p className="text-xs text-gray-400 mt-1">{subtitle}</p>}
    </div>
  );
}

const PIE_COLORS = ["#3b82f6","#10b981","#f59e0b","#ef4444","#8b5cf6","#06b6d4"];

// ─── MAIN DASHBOARD ─────────────────────────
export default function Dashboard() {
  const [kpis,       setKpis]       = useState(null);
  const [monthly,    setMonthly]    = useState([]);
  const [categories, setCategories] = useState([]);
  const [topProducts,setTopProducts]= useState([]);
  const [orderStatus,setOrderStatus]= useState([]);
  const [loading,    setLoading]    = useState(true);
  const [error,      setError]      = useState(null);

  useEffect(() => {
    const fetchAll = async () => {
      try {
        const [k, m, c, p, s] = await Promise.all([
          API.get("/dashboard/kpis"),
          API.get("/dashboard/monthly-revenue"),
          API.get("/dashboard/revenue-by-category"),
          API.get("/dashboard/top-products?limit=5"),
          API.get("/dashboard/order-status"),
        ]);
        setKpis(k.data);
        setMonthly(m.data);
        setCategories(c.data);
        setTopProducts(p.data);
        setOrderStatus(s.data);
      } catch (err) {
        setError("Failed to load dashboard data.");
      } finally {
        setLoading(false);
      }
    };
    fetchAll();
  }, []);

  if (loading) return (
    <div className="flex items-center justify-center h-full">
      <p className="text-gray-500 text-lg">Loading dashboard...</p>
    </div>
  );

  if (error) return (
    <div className="flex items-center justify-center h-full">
      <p className="text-red-500 text-lg">{error}</p>
    </div>
  );

  const fmt = (n) => Number(n).toLocaleString("en-US", {
    minimumFractionDigits: 2, maximumFractionDigits: 2
  });

  return (
    <div className="p-6 space-y-6">

      {/* Header */}
      <div>
        <h1 className="text-2xl font-bold text-gray-800">Dashboard Overview</h1>
        <p className="text-gray-500 text-sm mt-1">Real-time sales analytics</p>
      </div>

      {/* KPI Cards */}
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
        <KPICard
          title="Total Revenue"
          value={`$${fmt(kpis.total_revenue)}`}
          subtitle="Completed & shipped orders"
          color="border-blue-500"
        />
        <KPICard
          title="Total Orders"
          value={Number(kpis.total_orders).toLocaleString()}
          subtitle={`${kpis.cancelled_orders} cancelled · ${kpis.returned_orders} returned`}
          color="border-green-500"
        />
        <KPICard
          title="Total Customers"
          value={Number(kpis.total_customers).toLocaleString()}
          subtitle={`${kpis.active_customers} with orders`}
          color="border-yellow-500"
        />
        <KPICard
          title="Avg Order Value"
          value={`$${fmt(kpis.avg_order_value)}`}
          subtitle="Completed & shipped only"
          color="border-purple-500"
        />
      </div>

      {/* Monthly Revenue Chart */}
      <div className="bg-white rounded-xl shadow p-6">
        <h2 className="text-lg font-semibold text-gray-700 mb-4">
          Monthly Revenue (Last 12 Months)
        </h2>
        {monthly.length === 0 ? (
          <p className="text-gray-400 text-center py-8">No data available</p>
        ) : (
          <ResponsiveContainer width="100%" height={300}>
            <LineChart data={monthly}>
              <CartesianGrid strokeDasharray="3 3" />
              <XAxis dataKey="month" tick={{ fontSize: 12 }} />
              <YAxis tick={{ fontSize: 12 }} />
              <Tooltip formatter={(v) => `$${fmt(v)}`} />
              <Legend />
              <Line
                type="monotone"
                dataKey="revenue"
                stroke="#3b82f6"
                strokeWidth={2}
                dot={{ r: 4 }}
                name="Revenue ($)"
              />
            </LineChart>
          </ResponsiveContainer>
        )}
      </div>

      {/* Bottom Row: Category Pie + Top Products Bar */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">

        {/* Revenue by Category */}
        <div className="bg-white rounded-xl shadow p-6">
          <h2 className="text-lg font-semibold text-gray-700 mb-4">
            Revenue by Category
          </h2>
          {categories.length === 0 ? (
            <p className="text-gray-400 text-center py-8">No data available</p>
          ) : (
            <ResponsiveContainer width="100%" height={260}>
              <PieChart>
                <Pie
                  data={categories}
                  dataKey="revenue"
                  nameKey="category"
                  cx="50%"
                  cy="50%"
                  outerRadius={90}
                  label={({ category, revenue_pct }) =>
                    `${category} ${revenue_pct}%`
                  }
                >
                  {categories.map((_, i) => (
                    <Cell key={i} fill={PIE_COLORS[i % PIE_COLORS.length]} />
                  ))}
                </Pie>
                <Tooltip formatter={(v) => `$${fmt(v)}`} />
              </PieChart>
            </ResponsiveContainer>
          )}
        </div>

        {/* Top 5 Products */}
        <div className="bg-white rounded-xl shadow p-6">
          <h2 className="text-lg font-semibold text-gray-700 mb-4">
            Top 5 Products by Revenue
          </h2>
          {topProducts.length === 0 ? (
            <p className="text-gray-400 text-center py-8">No data available</p>
          ) : (
            <ResponsiveContainer width="100%" height={260}>
              <BarChart data={topProducts} layout="vertical">
                <CartesianGrid strokeDasharray="3 3" />
                <XAxis type="number" tick={{ fontSize: 11 }} />
                <YAxis
                  type="category"
                  dataKey="product_name"
                  tick={{ fontSize: 11 }}
                  width={130}
                />
                <Tooltip formatter={(v) => `$${fmt(v)}`} />
                <Bar dataKey="total_revenue" fill="#3b82f6" name="Revenue ($)" />
              </BarChart>
            </ResponsiveContainer>
          )}
        </div>

      </div>

      {/* Order Status */}
      <div className="bg-white rounded-xl shadow p-6">
        <h2 className="text-lg font-semibold text-gray-700 mb-4">
          Order Status Breakdown
        </h2>
        <div className="grid grid-cols-2 sm:grid-cols-3 lg:grid-cols-5 gap-4">
          {orderStatus.map((s, i) => (
            <div key={i} className="text-center bg-gray-50 rounded-lg p-4">
              <p className="text-2xl font-bold text-gray-800">{s.total_orders}</p>
              <p className="text-sm capitalize text-gray-500 mt-1">{s.status}</p>
              <p className="text-xs text-gray-400">{s.percentage}%</p>
            </div>
          ))}
        </div>
      </div>

    </div>
  );
}