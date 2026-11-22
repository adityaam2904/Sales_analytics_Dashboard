import { BrowserRouter, Routes, Route, NavLink } from "react-router-dom";
import Dashboard from "./pages/Dashboard";
import Customers from "./pages/Customers";
import Products from "./pages/Products";
import Orders from "./pages/Orders";
import Upload from "./pages/Upload";
import ETLMonitor from "./pages/ETLMonitor";
// import Chat        from "./pages/chat";
const navItems = [
  { path: "/", label: "📊 Dashboard" },
  { path: "/customers", label: "👥 Customers" },
  { path: "/products", label: "📦 Products" },
  { path: "/orders", label: "🧾 Orders" },
  { path: "/upload", label: "📁 Upload CSV" },
  { path: "/etl", label: "⚙️ ETL Monitor" },
  // { path: "/chat",        label: "💬 Chatbot"          }
];

export default function App() {
  return (
    <BrowserRouter>
      <div className="flex h-screen bg-gray-100">

        {/* Sidebar */}
        <aside className="w-64 bg-gray-900 text-white flex flex-col">
          <div className="p-6 border-b border-gray-700">
            <h1 className="text-xl font-bold text-white">Sales Analytics</h1>
            <p className="text-gray-400 text-sm mt-1">Platform</p>
          </div>
          <nav className="flex-1 p-4 space-y-1">
            {navItems.map((item) => (
              <NavLink
                key={item.path}
                to={item.path}
                end={item.path === "/"}
                className={({ isActive }) =>
                  `block px-4 py-2.5 rounded-lg text-sm font-medium transition-colors ${isActive
                    ? "bg-blue-600 text-white"
                    : "text-gray-300 hover:bg-gray-700"
                  }`
                }
              >
                {item.label}
              </NavLink>
            ))}
          </nav>
          <div className="p-4 border-t border-gray-700 text-xs text-gray-500">
            Sales Analytics Platform v1.0
          </div>
        </aside>

        {/* Main Content */}
        <main className="flex-1 overflow-auto">
          <Routes>
            <Route path="/" element={<Dashboard />} />
            <Route path="/customers" element={<Customers />} />
            <Route path="/products" element={<Products />} />
            <Route path="/orders" element={<Orders />} />
            <Route path="/upload" element={<Upload />} />
            <Route path="/etl" element={<ETLMonitor />} />
            {/* <Route path="/chat"       element={<Chat />}       /> */}
          </Routes>
        </main>

      </div>
    </BrowserRouter>
  );
}