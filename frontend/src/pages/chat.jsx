// import { useState, useRef, useEffect } from "react";
// import ReactMarkdown from "react-markdown";
// import API from "../api/axios";

// export default function Chat() {
//   const [messages, setMessages] = useState([
//     {
//       sender: "ai",
//       text: "👋 Hi! I'm your **Sales Analytics AI Assistant**.\n\nAsk me anything about your revenue, top customers, popular products, or order statuses!",
//       time: new Date().toLocaleTimeString([], { hour: "2-digit", minute: "2-digit" }),
//     },
//   ]);
//   const [input, setInput] = useState("");
//   const [loading, setLoading] = useState(false);
//   const messagesEndRef = useRef(null);

//   const scrollToBottom = () => {
//     messagesEndRef.current?.scrollIntoView({ behavior: "smooth" });
//   };

//   useEffect(() => {
//     scrollToBottom();
//   }, [messages, loading]);

//   const handleSend = async (e) => {
//     e.preventDefault();
//     if (!input.trim() || loading) return;

//     const userQuestion = input.trim();
//     const currentTime = new Date().toLocaleTimeString([], {
//       hour: "2-digit",
//       minute: "2-digit",
//     });

//     setMessages((prev) => [
//       ...prev,
//       { sender: "user", text: userQuestion, time: currentTime },
//     ]);
//     setInput("");
//     setLoading(true);

//     try {
//       const res = await API.post("/chat/ask", { question: userQuestion });
//       setMessages((prev) => [
//         ...prev,
//         {
//           sender: "ai",
//           text: res.data.answer,
//           time: new Date().toLocaleTimeString([], {
//             hour: "2-digit",
//             minute: "2-digit",
//           }),
//         },
//       ]);
//     } catch (err) {
//       setMessages((prev) => [
//         ...prev,
//         {
//           sender: "ai",
//           text:
//             err.response?.data?.detail ||
//             "⚠️ Sorry, I encountered an issue querying the database. Please try again.",
//           time: new Date().toLocaleTimeString([], {
//             hour: "2-digit",
//             minute: "2-digit",
//           }),
//           isError: true,
//         },
//       ]);
//     } finally {
//       setLoading(false);
//     }
//   };

//   const handleChipClick = (suggestion) => {
//     setInput(suggestion);
//   };

//   return (
//     <div className="p-6 h-[calc(100vh-2rem)] flex flex-col space-y-4">
//       {/* Header */}
//       <div className="flex items-center justify-between border-b pb-3 border-gray-200">
//         <div>
//           <h1 className="text-2xl font-bold text-gray-800 flex items-center gap-2">
//             💬 AI Sales Assistant
//           </h1>
//           <p className="text-gray-500 text-sm">
//             Chat with Gemini connected directly to your PostgreSQL database
//           </p>
//         </div>
//         <span className="text-xs bg-emerald-50 text-emerald-700 font-semibold px-3 py-1 rounded-full border border-emerald-200 flex items-center gap-1.5">
//           <span className="w-2 h-2 rounded-full bg-emerald-500 animate-pulse"></span>
//           Connected to PostgreSQL
//         </span>
//       </div>

//       {/* Messages */}
//       <div className="flex-1 bg-white rounded-xl shadow-sm border border-gray-200 p-4 overflow-y-auto space-y-4">
//         {messages.map((m, i) => (
//           <div
//             key={i}
//             className={`flex flex-col ${
//               m.sender === "user" ? "items-end" : "items-start"
//             }`}
//           >
//             <div
//               className={`max-w-[80%] rounded-2xl px-5 py-3 text-sm leading-relaxed shadow-sm ${
//                 m.sender === "user"
//                   ? "bg-blue-600 text-white rounded-br-none"
//                   : m.isError
//                   ? "bg-red-50 text-red-700 border border-red-200 rounded-bl-none"
//                   : "bg-gray-100 text-gray-800 rounded-bl-none"
//               }`}
//             >
//               {m.sender === "user" ? (
//                 <p className="whitespace-pre-line">{m.text}</p>
//               ) : (
//                 <div className="prose prose-sm max-w-none text-gray-800 space-y-2">
//                   <ReactMarkdown
//                     components={{
//                       p: ({ node, ...props }) => <p className="mb-2 last:mb-0" {...props} />,
//                       ul: ({ node, ...props }) => <ul className="list-disc pl-5 space-y-1 mb-2" {...props} />,
//                       ol: ({ node, ...props }) => <ol className="list-decimal pl-5 space-y-1 mb-2" {...props} />,
//                       li: ({ node, ...props }) => <li className="leading-snug" {...props} />,
//                       strong: ({ node, ...props }) => <strong className="font-semibold text-gray-900" {...props} />,
//                     }}
//                   >
//                     {m.text}
//                   </ReactMarkdown>
//                 </div>
//               )}
//             </div>
//             <span className="text-[10px] text-gray-400 mt-1 px-1">
//               {m.sender === "user" ? "You" : "AI Assistant"} • {m.time}
//             </span>
//           </div>
//         ))}

//         {loading && (
//           <div className="flex items-start gap-2">
//             <div className="bg-gray-100 rounded-2xl rounded-bl-none px-4 py-3 text-sm text-gray-500 flex items-center gap-1.5 shadow-sm">
//               <span className="w-2 h-2 bg-gray-400 rounded-full animate-bounce"></span>
//               <span className="w-2 h-2 bg-gray-400 rounded-full animate-bounce [animation-delay:0.2s]"></span>
//               <span className="w-2 h-2 bg-gray-400 rounded-full animate-bounce [animation-delay:0.4s]"></span>
//               <span className="ml-2 text-xs text-gray-400">Analyzing live PostgreSQL data...</span>
//             </div>
//           </div>
//         )}
//         <div ref={messagesEndRef} />
//       </div>

//       {/* Suggestion Chips */}
//       <div className="flex gap-2 overflow-x-auto pb-1 text-xs">
//         <button
//           onClick={() => handleChipClick("Who is our top spending customer?")}
//           className="bg-white border border-gray-300 hover:border-blue-500 hover:text-blue-600 px-3 py-1.5 rounded-full transition-colors whitespace-nowrap text-gray-600"
//         >
//           🏆 Top customer?
//         </button>
//         <button
//           onClick={() => handleChipClick("Which product generated the highest revenue?")}
//           className="bg-white border border-gray-300 hover:border-blue-500 hover:text-blue-600 px-3 py-1.5 rounded-full transition-colors whitespace-nowrap text-gray-600"
//         >
//           📦 Best selling product?
//         </button>
//         <button
//           onClick={() => handleChipClick("Give me a quick executive summary of our business KPIs.")}
//           className="bg-white border border-gray-300 hover:border-blue-500 hover:text-blue-600 px-3 py-1.5 rounded-full transition-colors whitespace-nowrap text-gray-600"
//         >
//           📊 Executive KPI summary
//         </button>
//         <button
//           onClick={() => handleChipClick("What is our revenue breakdown by category?")}
//           className="bg-white border border-gray-300 hover:border-blue-500 hover:text-blue-600 px-3 py-1.5 rounded-full transition-colors whitespace-nowrap text-gray-600"
//         >
//           📂 Revenue by category?
//         </button>
//       </div>

//       {/* Input */}
//       <form onSubmit={handleSend} className="flex gap-2">
//         <input
//           type="text"
//           value={input}
//           onChange={(e) => setInput(e.target.value)}
//           placeholder="Ask a question about your sales, products, or customers..."
//           disabled={loading}
//           className="flex-1 border border-gray-300 rounded-xl px-4 py-3 text-sm focus:outline-none focus:ring-2 focus:ring-blue-500 bg-white"
//         />
//         <button
//           type="submit"
//           disabled={loading || !input.trim()}
//           className="bg-blue-600 hover:bg-blue-700 text-white font-medium px-6 py-3 rounded-xl text-sm transition-colors disabled:opacity-50 flex items-center gap-2"
//         >
//           Send 🚀
//         </button>
//       </form>
//     </div>
//   );
// }