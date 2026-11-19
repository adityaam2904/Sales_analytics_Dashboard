import { useEffect, useState } from "react";
import API from "../api/axios";

export default function ETLMonitor() {
  const [runs, setRuns] = useState([]);
  const [selectedRun, setSelectedRun] = useState(null);
  const [logs, setLogs] = useState([]);
  const [rejectedRecords, setRejectedRecords] = useState([]);
  const [activeTab, setActiveTab] = useState("runs");
  const [triggering, setTriggering] = useState(false);
  const [mode, setMode] = useState("incremental");
  const [loadingLogs, setLoadingLogs] = useState(false);
  const [statusMessage, setStatusMessage] = useState(null);

  const fetchRuns = async () => {
    try {
      const res = await API.get("/etl/runs");
      setRuns(res.data);
      if (res.data.length > 0 && !selectedRun) {
        viewLogs(res.data[0].run_id);
      }
    } catch (err) {
      console.error("Failed to fetch runs:", err);
    }
  };

  const fetchRejected = async () => {
    try {
      const res = await API.get("/etl/rejected");
      setRejectedRecords(res.data);
    } catch (err) {
      console.error("Failed to fetch rejected records:", err);
    }
  };

  useEffect(() => {
    fetchRuns();
    fetchRejected();
  }, []);

  const triggerETL = async () => {
    setTriggering(true);
    setStatusMessage(null);
    try {
      const res = await API.post(`/etl/run?mode=${mode}`);
      setStatusMessage({
        type: "success",
        text: `Run #${res.data.run_id} finished: ${res.data.rows_inserted} inserted, ${res.data.rows_rejected} rejected.`,
      });
      fetchRuns();
      fetchRejected();
      viewLogs(res.data.run_id);
    } catch (err) {
      setStatusMessage({
        type: "error",
        text: err.response?.data?.detail || "ETL trigger failed.",
      });
    } finally {
      setTriggering(false);
    }
  };

  const viewLogs = async (runId) => {
    setSelectedRun(runId);
    setLoadingLogs(true);
    try {
      const res = await API.get(`/etl/runs/${runId}/logs`);
      setLogs(res.data);
    } catch (err) {
      console.error("Failed to fetch logs:", err);
    } finally {
      setLoadingLogs(false);
    }
  };

  return (
    <div className="p-6 space-y-6">
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
        <div>
          <h1 className="text-2xl font-bold text-gray-800">ETL Execution Monitor</h1>
          <p className="text-gray-500 text-sm mt-1">
            Trigger pipelines, inspect runtime logs, and analyze rejected data
          </p>
        </div>

        <div className="flex items-center gap-3">
          <select
            value={mode}
            onChange={(e) => setMode(e.target.value)}
            className="border border-gray-300 rounded-lg px-3 py-2 text-sm bg-white focus:outline-none focus:ring-2 focus:ring-blue-500"
          >
            <option value="incremental">Incremental Mode</option>
            <option value="full_reload">Full Reload Mode</option>
          </select>
          <button
            onClick={triggerETL}
            disabled={triggering}
            className="bg-indigo-600 hover:bg-indigo-700 text-white font-medium px-5 py-2 rounded-lg text-sm transition-colors disabled:opacity-50 flex items-center gap-2"
          >
            {triggering ? "Running ETL Pipeline..." : "🚀 Trigger Pipeline"}
          </button>
        </div>
      </div>

      {statusMessage && (
        <div
          className={`p-4 rounded-xl border text-sm font-medium ${
            statusMessage.type === "success"
              ? "bg-green-50 text-green-800 border-green-200"
              : "bg-red-50 text-red-800 border-red-200"
          }`}
        >
          {statusMessage.text}
        </div>
      )}

      <div className="flex border-b border-gray-200 gap-6">
        <button
          onClick={() => setActiveTab("runs")}
          className={`pb-3 font-semibold text-sm border-b-2 transition-colors ${
            activeTab === "runs"
              ? "border-blue-600 text-blue-600"
              : "border-transparent text-gray-500 hover:text-gray-700"
          }`}
        >
          Execution History & Logs ({runs.length})
        </button>
        <button
          onClick={() => setActiveTab("rejected")}
          className={`pb-3 font-semibold text-sm border-b-2 transition-colors ${
            activeTab === "rejected"
              ? "border-blue-600 text-blue-600"
              : "border-transparent text-gray-500 hover:text-gray-700"
          }`}
        >
          Quarantined Rejected Records ({rejectedRecords.length})
        </button>
      </div>

      {activeTab === "runs" ? (
        <div className="grid grid-cols-1 lg:grid-cols-12 gap-6">
          <div className="lg:col-span-5 bg-white rounded-xl shadow-sm border border-gray-200 overflow-hidden">
            <div className="p-4 border-b border-gray-200 font-semibold text-gray-700 text-sm">
              Runs History
            </div>
            {runs.length === 0 ? (
              <p className="p-6 text-gray-500 text-sm text-center">No runs executed yet.</p>
            ) : (
              <div className="divide-y divide-gray-100 max-h-[550px] overflow-y-auto">
                {runs.map((r) => (
                  <div
                    key={r.run_id}
                    onClick={() => viewLogs(r.run_id)}
                    className={`p-4 cursor-pointer hover:bg-gray-50 transition-colors ${
                      selectedRun === r.run_id ? "bg-blue-50/70 border-l-4 border-blue-600" : ""
                    }`}
                  >
                    <div className="flex items-center justify-between">
                      <span className="font-bold text-gray-800 text-sm">
                        Run #{r.run_id} ({r.mode})
                      </span>
                      <span
                        className={`text-xs px-2 py-0.5 rounded font-semibold uppercase ${
                          r.status === "success"
                            ? "bg-green-100 text-green-700"
                            : r.status === "partial"
                            ? "bg-amber-100 text-amber-700"
                            : "bg-red-100 text-red-700"
                        }`}
                      >
                        {r.status}
                      </span>
                    </div>
                    <div className="text-xs text-gray-500 mt-2 flex justify-between">
                      <span>{new Date(r.started_at).toLocaleString()}</span>
                      <span>{r.duration_seconds || 0}s duration</span>
                    </div>
                    <div className="text-xs text-gray-600 mt-2 flex gap-3">
                      <span className="text-green-600">+{r.rows_inserted} inserted</span>
                      <span className="text-blue-600">~{r.rows_updated} updated</span>
                      <span className="text-red-500">✕ {r.rows_rejected} rejected</span>
                    </div>
                  </div>
                ))}
              </div>
            )}
          </div>

          <div className="lg:col-span-7 bg-gray-900 text-gray-100 rounded-xl shadow-sm border border-gray-800 p-5 font-mono text-xs flex flex-col h-[600px]">
            <div className="pb-3 border-b border-gray-800 flex justify-between items-center text-gray-400">
              <span>Logs for Run #{selectedRun || "—"}</span>
              <button
                onClick={() => selectedRun && viewLogs(selectedRun)}
                className="hover:text-white"
              >
                ↻ Refresh Logs
              </button>
            </div>
            <div className="flex-1 overflow-y-auto space-y-2 pt-4">
              {loadingLogs ? (
                <div className="text-gray-500 text-center py-10">Fetching logs...</div>
              ) : logs.length === 0 ? (
                <div className="text-gray-500 text-center py-10">No logs for this run.</div>
              ) : (
                logs.map((l) => (
                  <div key={l.log_id} className="leading-relaxed">
                    <span className="text-gray-500 mr-2">
                      {new Date(l.created_at).toLocaleTimeString()}
                    </span>
                    <span
                      className={`font-semibold mr-2 ${
                        l.level === "ERROR"
                          ? "text-red-400"
                          : l.level === "WARNING"
                          ? "text-amber-400"
                          : "text-green-400"
                      }`}
                    >
                      [{l.level}]
                    </span>
                    <span className="text-gray-200">{l.message}</span>
                  </div>
                ))
              )}
            </div>
          </div>
        </div>
      ) : (
        <div className="bg-white rounded-xl shadow-sm border border-gray-200 overflow-hidden">
          {rejectedRecords.length === 0 ? (
            <p className="p-8 text-center text-gray-500">
              No rejected records! All rows passed validation.
            </p>
          ) : (
            <div className="overflow-x-auto">
              <table className="w-full text-left border-collapse text-sm">
                <thead className="bg-gray-50 border-b border-gray-200 text-gray-600 uppercase text-xs">
                  <tr>
                    <th className="py-3 px-4">Entity</th>
                    <th className="py-3 px-4">Row #</th>
                    <th className="py-3 px-4">Reason for Rejection</th>
                    <th className="py-3 px-4">Raw Input Data</th>
                    <th className="py-3 px-4 text-center">Timestamp</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-gray-100">
                  {rejectedRecords.map((rj) => (
                    <tr key={rj.reject_id} className="hover:bg-gray-50">
                      <td className="py-3 px-4 font-bold capitalize text-gray-700">
                        {rj.entity}
                      </td>
                      <td className="py-3 px-4 font-mono text-xs">{rj.row_number}</td>
                      <td className="py-3 px-4 text-red-600 font-medium">
                        {rj.reason}
                      </td>
                      <td className="py-3 px-4">
                        <pre className="text-[11px] bg-gray-50 p-2 rounded border border-gray-200 font-mono max-w-md overflow-x-auto">
                          {typeof rj.raw_data === "string"
                            ? rj.raw_data
                            : JSON.stringify(rj.raw_data, null, 2)}
                        </pre>
                      </td>
                      <td className="py-3 px-4 text-center text-xs text-gray-500">
                        {new Date(rj.created_at).toLocaleTimeString()}
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          )}
        </div>
      )}
    </div>
  );
}