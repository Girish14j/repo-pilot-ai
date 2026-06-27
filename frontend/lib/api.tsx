"use client";

import { useState, useEffect } from "react";

export default function Home() {
  const [backendStatus, setBackendStatus] = useState("Checking...");
  const [service, setService] = useState("");

  useEffect(() => {
    fetch("http://localhost:8000/health")
      .then((response) => response.json())
      .then((data) => {
        setBackendStatus(data.status);
        setService(data.service);
      })
      .catch((error) => {
        console.error("Error fetching backend status:", error);
        setBackendStatus("Backend is not running");
      });
  }, []);

  return (
    <main className="flex min-h-screen flex-col items-center justify-center bg-gray-950 text-white">
      <h1 className="text-4xl font-bold mb-6">🚀 RepoPilot AI</h1>

      <div className="bg-gray-900 p-6 rounded-xl shadow-lg w-96">
        <h2 className="text-xl font-semibold mb-4">Backend Status</h2>

        <p className="mb-2">
          <span className="font-semibold">Status:</span>{" "}
          <span
            className={
              backendStatus === "ok" ? "text-green-400" : "text-red-400"
            }
          >
            {backendStatus}
          </span>
        </p>

        <p>
          <span className="font-semibold">Service:</span> {service}
        </p>
      </div>
    </main>
  );
}