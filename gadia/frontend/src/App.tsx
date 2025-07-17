import React, { useState } from "react";

interface AnalysisResult {
  id: string;
  page_name: string;
  favicon_url: string;
  link: string;
  has_gambling_ads: string;
  gambling_image_url?: string;
  frames_analysis?: { url: string; is_gambling: boolean }[];
}

function App() {
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
      setUrl("");
    } catch (err: any) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div style={{ minHeight: '100vh', background: 'none', display: 'flex', flexDirection: 'column', position: 'relative', zIndex: 1 }}>
      {/* Elementos decorativos de fondo */}
      <div className="body-decor blob1" />
      <div className="body-decor blob2" />
      <div className="body-decor blob3" />
      {/* Header minimalista */}
      <header style={{ background: '#1a2236', color: '#fff', padding: '18px 0 12px 0', textAlign: 'left', boxShadow: '0 2px 8px rgba(0,0,0,0.05)', zIndex: 2, position: 'relative' }}>
        <div style={{ maxWidth: 1200, margin: '0 auto', paddingLeft: 32, fontSize: 28, fontWeight: 700, letterSpacing: 2 }}>
          GADIA
        </div>
      </header>

      <main style={{ flex: 1, display: 'flex', flexDirection: 'column', alignItems: 'center', justifyContent: 'flex-start', padding: '32px 8px 0 8px' }}>
        {/* ¿Qué es GADIA? */}
        <section style={{ width: '100%', maxWidth: 700, background: '#fff', borderRadius: 16, boxShadow: '0 2px 12px rgba(0,0,0,0.07)', padding: 32, marginBottom: 32 }}>
          <h2 style={{ fontSize: 26, color: '#1a2236', marginBottom: 10 }}>¿Qué es GADIA?</h2>
          <p style={{ color: '#444', fontSize: 17, marginBottom: 10 }}>
            <strong>GADIA</strong> significa <strong>Gambling Advertisement Detection & Intelligence Analyzer</strong>.
          </p>
          <p style={{ color: '#444', fontSize: 16, marginBottom: 0 }}>
            Es una herramienta que analiza cualquier página web para detectar anuncios de apuestas y juegos de azar en imágenes y banners usando inteligencia artificial. Su objetivo es ayudar a la sociedad a identificar y comprender la presencia de este tipo de publicidad en el entorno digital.
          </p>
        </section>

        {/* Análisis */}
        <section style={{ width: '100%', maxWidth: 600, background: '#fff', borderRadius: 16, boxShadow: '0 2px 12px rgba(0,0,0,0.07)', padding: 32, marginBottom: 32 }}>
          <h3 style={{ fontSize: 22, marginBottom: 18, color: '#1a2236' }}>Analizar una página web</h3>
          <form onSubmit={handleSubmit} style={{ marginBottom: 20, display: 'flex', gap: 8 }}>
            <input
              type="url"
              value={url}
              onChange={(e) => setUrl(e.target.value)}
              placeholder="Introduce el link de la web"
              required
              style={{ flex: 1, padding: 10, borderRadius: 6, border: '1px solid #b0b8d1', fontSize: 16 }}
            />
            <button type="submit" disabled={loading} style={{ padding: '10px 24px', borderRadius: 6, background: '#ff4d4f', color: '#fff', border: 'none', fontWeight: 600, fontSize: 16, cursor: 'pointer', boxShadow: '0 1px 4px rgba(0,0,0,0.04)' }}>
              {loading ? "Analizando..." : "Analizar"}
            </button>
          </form>
          {error && <div style={{ color: "#ff4d4f", marginBottom: 12 }}>{error}</div>}
          {result && (
            <div style={{ border: "1px solid #e0e6f7", background: '#f9fafc', padding: 24, borderRadius: 12, marginTop: 16 }}>
              <h4 style={{ fontSize: 20, marginBottom: 12, color: '#1a2236' }}>Resultado:</h4>
              <div style={{ display: 'flex', alignItems: 'center', gap: 12, marginBottom: 8 }}>
                <img src={result.favicon_url} alt="favicon" width={40} height={40} style={{ verticalAlign: "middle", borderRadius: 8, background: '#fff', border: '1px solid #e0e6f7' }} />
                <span style={{ fontWeight: 700, fontSize: 18, color: '#1a2236' }}>{result.page_name}</span>
              </div>
              <p style={{ margin: '8px 0 4px 0', fontSize: 15 }}><strong>Link:</strong> <a href={result.link} target="_blank" rel="noopener noreferrer" style={{ color: '#2d6cdf', wordBreak: 'break-all' }}>{result.link}</a></p>
              <p style={{ margin: '8px 0 4px 0', fontSize: 15 }}><strong>¿Contiene anuncios de gambling?:</strong> <span style={{ color: result.has_gambling_ads === 'Sí' ? '#ff4d4f' : '#52c41a', fontWeight: 600 }}>{result.has_gambling_ads}</span></p>
              {result.gambling_image_url && (
                <div style={{ marginTop: 16 }}>
                  <strong>Imagen/frame detectado como gambling:</strong><br />
                  <img src={result.gambling_image_url} alt="Gambling ad" style={{ maxWidth: 220, border: '3px solid #ff4d4f', borderRadius: 8, marginTop: 6, background: '#fff' }} />
                </div>
              )}
              {/* Listado de frames/imágenes analizados */}
              {result.frames_analysis && result.frames_analysis.length > 0 && (
                <div style={{ marginTop: 32 }}>
                  <h4 style={{ fontSize: 17, color: '#1a2236', marginBottom: 10 }}>Listado de imágenes/frames analizados:</h4>
                  <table style={{ width: '100%', borderCollapse: 'collapse', fontSize: 14, background: '#fff', borderRadius: 8, overflow: 'hidden', boxShadow: '0 1px 4px rgba(0,0,0,0.03)' }}>
                    <thead>
                      <tr style={{ background: '#f4f6fa' }}>
                        <th style={{ border: '1px solid #e0e6f7', padding: 7 }}>Miniatura</th>
                        <th style={{ border: '1px solid #e0e6f7', padding: 7 }}>URL</th>
                        <th style={{ border: '1px solid #e0e6f7', padding: 7 }}>¿Gambling?</th>
                      </tr>
                    </thead>
                    <tbody>
                      {result.frames_analysis.map((frame, idx) => (
                        <tr key={idx}>
                          <td style={{ border: '1px solid #e0e6f7', padding: 7, textAlign: 'center', background: '#f9fafc' }}>
                            <img src={frame.url} alt={`frame-${idx}`} style={{ maxWidth: 60, maxHeight: 40, border: frame.is_gambling ? '2px solid #ff4d4f' : '1px solid #b0b8d1', borderRadius: 4, background: '#fff' }} />
                          </td>
                          <td style={{ border: '1px solid #e0e6f7', padding: 7, wordBreak: 'break-all', background: '#f9fafc' }}>
                            <a href={frame.url} target="_blank" rel="noopener noreferrer" style={{ color: '#2d6cdf' }}>{frame.url}</a>
                          </td>
                          <td style={{ border: '1px solid #e0e6f7', padding: 7, color: frame.is_gambling ? '#ff4d4f' : '#52c41a', fontWeight: 'bold', background: '#f9fafc' }}>
                            {frame.is_gambling ? 'Sí' : 'No'}
                          </td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>
              )}
            </div>
          )}
        </section>

        {/* Objetivo, métodos y propósito educativo */}
        <section style={{ width: '100%', maxWidth: 700, background: '#fff', borderRadius: 16, boxShadow: '0 2px 12px rgba(0,0,0,0.07)', padding: 32, marginBottom: 32 }}>
          <h3 style={{ color: '#ff4d4f', fontSize: 22, marginBottom: 10 }}>Sobre el proyecto</h3>
          <p style={{ color: '#1a2236', fontSize: 16, marginBottom: 12 }}>
            <strong>Objetivo:</strong> GADIA nace con la misión de ayudar a la sociedad a identificar y comprender la presencia de anuncios de apuestas y juegos de azar en la web. Queremos empoderar a las personas para que sean conscientes del impacto de este tipo de publicidad, especialmente en entornos digitales donde puede pasar desapercibida.
          </p>
          <p style={{ color: '#1a2236', fontSize: 16, marginBottom: 12 }}>
            <strong>Métodos:</strong> Utilizamos inteligencia artificial y técnicas avanzadas de visión por computadora para analizar imágenes y banners en páginas web. Nuestro sistema combina modelos de aprendizaje profundo con filtros contextuales y análisis de palabras clave para ofrecer resultados precisos y transparentes.
          </p>
          <p style={{ color: '#1a2236', fontSize: 16, marginBottom: 12 }}>
            <strong>Propósito educativo:</strong> Este proyecto busca fomentar el conocimiento sobre el sector de las apuestas online y su presencia en la vida cotidiana. Creemos que la información es la mejor herramienta para la toma de decisiones responsables y la protección de los usuarios, especialmente los más jóvenes.
          </p>
          <p style={{ color: '#444', fontSize: 15, marginTop: 18, marginBottom: 0 }}>
            Si tienes dudas, sugerencias o deseas colaborar, ¡no dudes en contactarnos!
          </p>
        </section>
      </main>

      <footer style={{ background: '#151a2b', color: '#fff', textAlign: 'center', padding: '18px 0 12px 0', fontSize: 16, letterSpacing: 1, marginTop: 'auto', zIndex: 2, position: 'relative' }}>
        Hecho por Eros y Taichi
      </footer>
    </div>
  );
}

export default App;
