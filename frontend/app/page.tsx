"use client";

import { useState } from "react";
import Chat from "@/components/Chat";
import DocumentUpload from "@/components/DocumentUpload";
import DocumentList from "@/components/DocumentList";

export default function Home() {
  const [activeTab, setActiveTab] = useState<"chat" | "documents">("chat");

  return (
    <div className="min-h-screen bg-gray-50 dark:bg-gray-900">
      {/* Header */}
      <header className="bg-white dark:bg-gray-800 shadow">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-4">
          <h1 className="text-2xl font-bold text-gray-900 dark:text-white">
            AI Autonomous Platform
          </h1>
          <p className="text-sm text-gray-600 dark:text-gray-400 mt-1">
            Knowledge & Workflow Intelligence
          </p>
        </div>
      </header>

      {/* Navigation Tabs */}
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 mt-6">
        <div className="border-b border-gray-200 dark:border-gray-700">
          <nav className="-mb-px flex space-x-8">
            <button
              onClick={() => setActiveTab("chat")}
              className={`${
                activeTab === "chat"
                  ? "border-blue-500 text-blue-600 dark:text-blue-400"
                  : "border-transparent text-gray-500 hover:text-gray-700 hover:border-gray-300 dark:text-gray-400"
              } whitespace-nowrap py-4 px-1 border-b-2 font-medium text-sm`}
            >
              Chat
            </button>
            <button
              onClick={() => setActiveTab("documents")}
              className={`${
                activeTab === "documents"
                  ? "border-blue-500 text-blue-600 dark:text-blue-400"
                  : "border-transparent text-gray-500 hover:text-gray-700 hover:border-gray-300 dark:text-gray-400"
              } whitespace-nowrap py-4 px-1 border-b-2 font-medium text-sm`}
            >
              Documents
            </button>
          </nav>
        </div>
      </div>

      {/* Main Content */}
      <main className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        {activeTab === "chat" && <Chat />}
        {activeTab === "documents" && (
          <div className="grid grid-cols-1 lg:grid-cols-2 gap-8">
            <DocumentUpload />
            <DocumentList />
          </div>
        )}
      </main>
    </div>
  );
}
