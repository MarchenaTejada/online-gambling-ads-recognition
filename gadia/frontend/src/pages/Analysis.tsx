import React, { useState } from "react";

interface AnalysisResult {
  id: string;
  page_name: string;
  favicon_url: string;
  link: string;
}

function Analysis() {
  const [url, setUrl] = useState("");
  const [result, setResult] = useState<AnalysisResult | null>(null);
  const [error, setError] = useState("");
  const [loading, setLoading] = useState(false);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setError("");
    setLoading(true);
    setResult(null);
    try {
      const response = await fetch("http://localhost:8000/simple-analyze", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ url }),
      });
      if (!response.ok) {
        const err = await response.json();
        throw new Error(err.detail || "Error en el análisis");
      }
      const data = await response.json();
      setResult(data);
    } catch (err: any) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div style={{ maxWidth: 500, margin: "0 auto" }}>
      <h2>Análisis de página web</h2>
      <form onSubmit={handleSubmit} style={{ marginBottom: 20 }}>
        <input
          type="url"
          value={url}
          onChange={(e) => setUrl(e.target.value)}
          placeholder="Introduce el link de la web"
          required
          style={{ width: "80%", padding: 8, marginRight: 8 }}
        />
        <button type="submit" disabled={loading} style={{ padding: 8 }}>
          {loading ? "Analizando..." : "Analizar"}
        </button>
      </form>
      {error && <div style={{ color: "red" }}>{error}</div>}
      {result && (
        <div style={{ border: "1px solid #ccc", padding: 16, borderRadius: 8 }}>
          <h3>Resultado:</h3>
          <img src={result.favicon_url} alt="favicon" width={32} height={32} style={{ verticalAlign: "middle" }} />
          <p><strong>Nombre:</strong> {result.page_name}</p>
          <p><strong>Link:</strong> <a href={result.link} target="_blank" rel="noopener noreferrer">{result.link}</a></p>
        </div>
      )}
    </div>
  );
}

export default Analysis; 