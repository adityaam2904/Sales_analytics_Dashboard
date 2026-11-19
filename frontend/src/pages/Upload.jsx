import { useState, useEffect } from "react";
import API from "../api/axios";

export default function Upload() {
  const [file, setFile] = useState(null);
  const [entity, setEntity] = useState("customers");
  const [uploading, setUploading] = useState(false);
  const [alert, setAlert] = useState(null);
  const [uploadedFiles, setUploadedFiles] = useState([]);
  const [loadingHistory, setLoadingHistory] = useState(true);

  const fetchUploadedFiles = async () => {
    try {
      const res = await API.get("/upload/files");
      setUploadedFiles(res.data);
    } catch (err) {
      console.error("Failed to load upload history:", err);
    } finally {
      setLoadingHistory(false);
    }
  };

  useEffect(() => {
    fetchUploadedFiles();
  }, []);

  const handleFileChange = (e) => {
    if (e.target.files && e.target.files[0]) {
      setFile(e.target.files[0]);
      setAlert(null);
    }
  };

  const handleUpload = async (e) => {
    e.preventDefault();
    if (!file) {
      setAlert({ type: "error", message: "Please select a CSV file to upload." });
      return;
    }

    const formData = new FormData();
    formData.append("entity", entity);
    formData.append("file", file);

    setUploading(true);
    setAlert(null);

    try {
      const res = await API.post("/upload/", formData, {
        headers: { "Content-Type": "multipart/form-data" },
      });

      if (res.data.duplicate) {
        setAlert({
          type: "warning",
          message: `${res.data.message} (File ID: ${res.data.file_id})`,
        });
      } else {
        setAlert({
          type: "success",
          message: `${res.data.message} (Stored as: ${res.data.filename})`,
        });
        setFile(null);
        e.target.reset();
      }
      fetchUploadedFiles();
    } catch (err) {
      setAlert({
        type: "error",
        message: err.response?.data?.detail || "Upload failed. Please try again.",
      });
    } finally {
      setUploading(false);
    }
  };

  return (
    <div className="p-6 space-y-8">
      <div>
        <h1 className="text-2xl font-bold text-gray-800">CSV File Uploader</h1>
        <p className="text-gray-500 text-sm mt-1">
          Upload raw datasets for customers, products, or orders into the pipeline
        </p>
      </div>

      {alert && (
        <div
          className={`p-4 rounded-xl border text-sm font-medium ${
            alert.type === "success"
              ? "bg-green-50 text-green-800 border-green-200"
              : alert.type === "warning"
              ? "bg-amber-50 text-amber-800 border-amber-200"
              : "bg-red-50 text-red-800 border-red-200"
          }`}
        >
          {alert.message}
        </div>
      )}

      <div className="bg-white rounded-xl shadow-sm border border-gray-200 p-6 max-w-2xl">
        <form onSubmit={handleUpload} className="space-y-5">
          <div>
            <label className="block text-sm font-semibold text-gray-700 mb-1">
              Select Dataset Entity
            </label>
            <select
              value={entity}
              onChange={(e) => setEntity(e.target.value)}
              className="w-full border border-gray-300 rounded-lg px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-blue-500"
            >
              <option value="customers">Customers (customers.csv)</option>
              <option value="products">Products (products.csv)</option>
              <option value="orders">Orders (orders.csv)</option>
            </select>
          </div>

          <div>
            <label className="block text-sm font-semibold text-gray-700 mb-1">
              Choose CSV File
            </label>
            <input
              type="file"
              accept=".csv"
              onChange={handleFileChange}
              className="w-full border border-gray-300 rounded-lg p-2 text-sm text-gray-600 file:mr-4 file:py-1.5 file:px-4 file:rounded-md file:border-0 file:text-xs file:font-semibold file:bg-blue-50 file:text-blue-700 hover:file:bg-blue-100"
            />
          </div>

          <button
            type="submit"
            disabled={uploading}
            className="w-full bg-blue-600 hover:bg-blue-700 text-white font-medium py-2.5 rounded-lg text-sm transition-colors disabled:opacity-50"
          >
            {uploading ? "Uploading & Checking Duplicates..." : "Upload CSV to Staging"}
          </button>
        </form>
      </div>

      <div className="bg-white rounded-xl shadow-sm border border-gray-200 overflow-hidden">
        <div className="p-4 border-b border-gray-200 font-semibold text-gray-800">
          Upload Staging & History
        </div>
        {loadingHistory ? (
          <div className="p-8 text-center text-gray-500">Loading files...</div>
        ) : uploadedFiles.length === 0 ? (
          <div className="p-8 text-center text-gray-500">No files uploaded yet.</div>
        ) : (
          <div className="overflow-x-auto">
            <table className="w-full text-left border-collapse text-sm">
              <thead className="bg-gray-50 border-b border-gray-200 text-gray-600 uppercase text-xs">
                <tr>
                  <th className="py-3 px-4">File ID</th>
                  <th className="py-3 px-4">Entity</th>
                  <th className="py-3 px-4">Filename</th>
                  <th className="py-3 px-4">Size</th>
                  <th className="py-3 px-4 text-center">Status</th>
                  <th className="py-3 px-4 text-center">Uploaded At</th>
                  <th className="py-3 px-4 text-right">Rows Inserted / Rejected</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-gray-100">
                {uploadedFiles.map((f) => (
                  <tr key={f.file_id} className="hover:bg-gray-50 transition-colors">
                    <td className="py-3 px-4 font-mono text-xs text-blue-600 font-semibold">
                      #{f.file_id}
                    </td>
                    <td className="py-3 px-4 capitalize font-medium">{f.entity}</td>
                    <td className="py-3 px-4 text-gray-700">{f.original_name}</td>
                    <td className="py-3 px-4 text-xs text-gray-500">
                      {(f.size_bytes / 1024).toFixed(1)} KB
                    </td>
                    <td className="py-3 px-4 text-center">
                      <span
                        className={`text-xs px-2.5 py-0.5 rounded-full font-semibold uppercase ${
                          f.status === "processed"
                            ? "bg-green-100 text-green-700"
                            : f.status === "uploaded"
                            ? "bg-amber-100 text-amber-700"
                            : "bg-red-100 text-red-700"
                        }`}
                      >
                        {f.status}
                      </span>
                    </td>
                    <td className="py-3 px-4 text-center text-xs text-gray-500">
                      {new Date(f.uploaded_at).toLocaleString()}
                    </td>
                    <td className="py-3 px-4 text-right font-medium">
                      <span className="text-green-600">{f.rows_inserted} inserted</span>
                      {f.rows_rejected > 0 && (
                        <span className="text-red-500 ml-2">
                          ({f.rows_rejected} rejected)
                        </span>
                      )}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </div>
    </div>
  );
}