"use client";

import { useState, useEffect } from "react";
import { listDocuments, deleteDocument, getIndexingStats } from "@/lib/api";

interface Document {
  document_id: number;
  filename: string;
  status: string;
  chunks_count: number;
  created_at: string;
  error_message?: string;
}

export default function DocumentList() {
  const [documents, setDocuments] = useState<Document[]>([]);
  const [stats, setStats] = useState<any>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");

  const loadData = async () => {
    try {
      const [docsResponse, statsResponse] = await Promise.all([
        listDocuments(),
        getIndexingStats(),
      ]);
      setDocuments(docsResponse.documents);
      setStats(statsResponse);
      setError("");
    } catch (err: any) {
      setError(err.response?.data?.detail || "Failed to load documents");
      console.error("Load error:", err);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadData();
    // Refresh every 5 seconds
    const interval = setInterval(loadData, 5000);
    return () => clearInterval(interval);
  }, []);

  const handleDelete = async (documentId: number) => {
    if (!confirm("Are you sure you want to delete this document?")) return;

    try {
      await deleteDocument(documentId);
      await loadData();
    } catch (err: any) {
      alert(err.response?.data?.detail || "Failed to delete document");
    }
  };

  const getStatusColor = (status: string) => {
    switch (status) {
      case "completed":
        return "bg-green-100 text-green-800 dark:bg-green-900/20 dark:text-green-400";
      case "processing":
        return "bg-blue-100 text-blue-800 dark:bg-blue-900/20 dark:text-blue-400";
      case "failed":
        return "bg-red-100 text-red-800 dark:bg-red-900/20 dark:text-red-400";
      default:
        return "bg-gray-100 text-gray-800 dark:bg-gray-700 dark:text-gray-400";
    }
  };

  if (loading) {
    return (
      <div className="bg-white dark:bg-gray-800 rounded-lg shadow-lg p-6">
        <p className="text-gray-600 dark:text-gray-400">Loading documents...</p>
      </div>
    );
  }

  return (
    <div className="bg-white dark:bg-gray-800 rounded-lg shadow-lg p-6">
      <div className="flex justify-between items-center mb-4">
        <h2 className="text-lg font-semibold text-gray-900 dark:text-white">
          Documents
        </h2>
        <button
          onClick={loadData}
          className="px-3 py-1 text-sm bg-gray-200 dark:bg-gray-700 text-gray-700 dark:text-gray-300 rounded hover:bg-gray-300 dark:hover:bg-gray-600"
        >
          Refresh
        </button>
      </div>

      {/* Stats */}
      {stats && (
        <div className="grid grid-cols-2 md:grid-cols-4 gap-4 mb-6">
          <div className="bg-gray-50 dark:bg-gray-700 rounded-lg p-3">
            <p className="text-xs text-gray-600 dark:text-gray-400">Total</p>
            <p className="text-2xl font-bold text-gray-900 dark:text-white">
              {stats.total_documents}
            </p>
          </div>
          <div className="bg-green-50 dark:bg-green-900/20 rounded-lg p-3">
            <p className="text-xs text-green-600 dark:text-green-400">
              Completed
            </p>
            <p className="text-2xl font-bold text-green-600 dark:text-green-400">
              {stats.completed}
            </p>
          </div>
          <div className="bg-blue-50 dark:bg-blue-900/20 rounded-lg p-3">
            <p className="text-xs text-blue-600 dark:text-blue-400">
              Processing
            </p>
            <p className="text-2xl font-bold text-blue-600 dark:text-blue-400">
              {stats.processing}
            </p>
          </div>
          <div className="bg-gray-50 dark:bg-gray-700 rounded-lg p-3">
            <p className="text-xs text-gray-600 dark:text-gray-400">Chunks</p>
            <p className="text-2xl font-bold text-gray-900 dark:text-white">
              {stats.total_chunks}
            </p>
          </div>
        </div>
      )}

      {error && (
        <div className="bg-red-50 dark:bg-red-900/20 border border-red-200 dark:border-red-800 rounded-lg px-4 py-3 mb-4">
          <p className="text-sm text-red-600 dark:text-red-400">{error}</p>
        </div>
      )}

      {/* Document List */}
      <div className="space-y-3 max-h-[400px] overflow-y-auto">
        {documents.length === 0 ? (
          <p className="text-gray-600 dark:text-gray-400 text-center py-8">
            No documents uploaded yet
          </p>
        ) : (
          documents.map((doc) => (
            <div
              key={doc.document_id}
              className="border border-gray-200 dark:border-gray-700 rounded-lg p-4 hover:bg-gray-50 dark:hover:bg-gray-700/50"
            >
              <div className="flex justify-between items-start">
                <div className="flex-1">
                  <h3 className="font-medium text-gray-900 dark:text-white">
                    {doc.filename}
                  </h3>
                  <div className="flex items-center space-x-2 mt-1">
                    <span
                      className={`text-xs px-2 py-1 rounded ${getStatusColor(
                        doc.status
                      )}`}
                    >
                      {doc.status}
                    </span>
                    <span className="text-xs text-gray-500 dark:text-gray-400">
                      {doc.chunks_count} chunks
                    </span>
                  </div>
                  {doc.error_message && (
                    <p className="text-xs text-red-600 dark:text-red-400 mt-1">
                      Error: {doc.error_message}
                    </p>
                  )}
                  <p className="text-xs text-gray-500 dark:text-gray-400 mt-1">
                    {new Date(doc.created_at).toLocaleString()}
                  </p>
                </div>
                <button
                  onClick={() => handleDelete(doc.document_id)}
                  className="ml-4 px-3 py-1 text-sm text-red-600 hover:bg-red-50 dark:hover:bg-red-900/20 rounded"
                >
                  Delete
                </button>
              </div>
            </div>
          ))
        )}
      </div>
    </div>
  );
}
