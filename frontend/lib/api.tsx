const BASE_URL = "http://localhost:8000/api/github";

export async function fetchFullReport(url: string) {
  const res = await fetch(`${BASE_URL}/full-report`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ url }),
  });
  if (!res.ok) {
    const err = await res.json();
    throw new Error(err.detail || "Request failed");
  }
  return res.json();
}
