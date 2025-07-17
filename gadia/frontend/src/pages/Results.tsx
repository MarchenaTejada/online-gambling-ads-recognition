import React, { useEffect, useState } from "react";

interface AnalysisResult {
  id: string;
  page_name: string;
  favicon_url: string;
  link: string;
}

function Results() {
  const [analyses, setAnalyses] = useState<AnalysisResult[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");

  useEffect(() => {
    fetch("http://localhost:8000/simple-analyses")
      .then((res) => {
        if (!res.ok) throw new Error("Error al obtener los análisis");
        return res.json();
      })
      .then((data) => setAnalyses(data))
      .catch((err) => setError(err.message))
      .finally(() => setLoading(false));
  }, []);

  return (
    <div style={{ maxWidth: 800, margin: "0 auto" }}>
      <h2>Resultados de análisis</h2>
      {loading && <div>Cargando...</div>}
      {error && <div style={{ color: "red" }}>{error}</div>}
      <table style={{ width: "100%", borderCollapse: "collapse" }}>
        <thead>
          <tr>
            <th style={{ border: "1px solid #ccc", padding: 8 }}>Favicon</th>
            <th style={{ border: "1px solid #ccc", padding: 8 }}>Nombre</th>
            <th style={{ border: "1px solid #ccc", padding: 8 }}>Link</th>
          </tr>
        </thead>
        <tbody>
          {analyses.map((item) => (
            <tr key={item.id}>
              <td style={{ border: "1px solid #ccc", padding: 8, textAlign: "center" }}>
                <img src={item.favicon_url} alt="favicon" width={24} height={24} />
              </td>
              <td style={{ border: "1px solid #ccc", padding: 8 }}>{item.page_name}</td>
              <td style={{ border: "1px solid #ccc", padding: 8 }}>
                <a href={item.link} target="_blank" rel="noopener noreferrer">
                  {item.link}
                </a>
              </td>
            </tr>
          ))}
        </tbody>
      </table>
      {(!loading && analyses.length === 0) && <div>No hay análisis realizados aún.</div>}
    </div>
  );
}

export default Results; 