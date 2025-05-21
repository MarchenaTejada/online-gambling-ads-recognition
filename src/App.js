import React, { useState } from 'react';
import {
  Container, Navbar, Form, Button, InputGroup,
  Modal, ProgressBar
} from 'react-bootstrap';
import { Clipboard } from 'react-bootstrap-icons';
import './App.css';
import 'bootstrap/dist/css/bootstrap.min.css';

function App() {
  const [url, setUrl] = useState('');
  const [loading, setLoading] = useState(false);
  const [progress, setProgress] = useState(0);
  const [showModal, setShowModal] = useState(false);
  const [result, setResult] = useState(null); // 'safe' o 'warning'
  const [pegado, setPegado] = useState(false);

  const handleAnalyze = () => {
    if (!esUrlValida(url)) return;

    setLoading(true);
    setProgress(0);
    let current = 0;

    const interval = setInterval(() => {
      current += 10;
      setProgress(current);

      if (current >= 100) {
        clearInterval(interval);
        setLoading(false);
        const isGambling = Math.random() > 0.5;
        setResult(isGambling ? 'warning' : 'safe');
        setShowModal(true);
      }
    }, 200);
  };

  const handlePaste = async () => {
    try {
      const text = await navigator.clipboard.readText();
      setUrl(text);
      setPegado(true);
      setTimeout(() => setPegado(false), 2000);
    } catch (err) {
      console.error("Error al pegar del portapapeles:", err);
    }
  };

  const esUrlValida = (texto) => {
    const pattern = /^(https?:\/\/)?([\w.-]+)\.([a-z]{2,})(\/\S*)?$/i;
    return pattern.test(texto);
  };

  return (
    <>
      <Navbar bg="success" variant="dark" className="px-4">
        <Navbar.Brand className="d-flex align-items-center">
          <img
            src=""
            width="32"
            height="32"
            className="me-2"
            alt="Logo"
          />
          <span className="fs-4 fw-semibold">GAnalysis</span>
        </Navbar.Brand>
      </Navbar>

      <Container className="my-5 text-center">
        <h2>Analiza los anuncios de la web</h2>
        <p className="mb-4">
          Mediante web scraping analizamos los anuncios de la web que elijas para prevenir que tenga anuncios referentes al gambling.
        </p>

        <InputGroup className="mb-3 w-75 mx-auto shadow-sm">
          <Form.Control
            placeholder="https://ejemplo.com"
            value={url}
            onChange={(e) => setUrl(e.target.value)}
          />
          <Button variant="outline-secondary" onClick={handlePaste}>
            <Clipboard />
          </Button>
        </InputGroup>
        {pegado && <small className="text-success">Pegado desde el portapapeles ✅</small>}

        <Button
          variant="success"
          onClick={handleAnalyze}
          disabled={!esUrlValida(url)}
        >
          ANALIZAR
        </Button>

        {loading && (
          <div className="w-75 mx-auto mt-4">
            <ProgressBar
              striped
              animated
              now={progress}
              label={`${progress}%`}
            />
          </div>
        )}
      </Container>

      <div className="info-box gambling-risk mt-4 p-4 rounded">
        <h5 className="fw-bold mb-2">🎯 ¿Por qué detectar anuncios de gambling?</h5>
        <p>
          Los anuncios relacionados con el gambling pueden representar un riesgo para la reputación y la ética de tu sitio web.
          Identificarlos a tiempo te ayuda a proteger a tus usuarios y a cumplir con regulaciones legales y estándares de calidad.
        </p>
      </div>

      <div className="info-box how-it-works mt-4 p-4 rounded">
        <h5 className="fw-bold mb-2">🔍 ¿Cómo funciona?</h5>
          <p>
            Utilizamos técnicas de web scraping para escanear el contenido en los anuncios de una página, y detectar posibles
            elementos que estén relacionados con apuestas, casinos, juegos de azar y promociones similares.
          </p>
      </div>

      <div className="info-box tips mt-4 p-4 rounded">
        <h5 className="fw-bold mb-2">✅ Nuestras intenciones con esta herramienta</h5>
        <p>
          Esta herramienta nace con la intención de ayudar a los usuarios, especialmente a quienes son sensibles al contenido relacionado con apuestas, a navegar de forma más segura en la web.
        </p>
        <p>
          Queremos hacer visible este tipo de contenido para que se comprenda mejor su impacto, y colaborar en el futuro con organizaciones reguladoras que busquen proteger a los usuarios frente a prácticas publicitarias engañosas o riesgosas.
        </p>
        <p>
          Creemos que con más información y prevención, podemos contribuir a una experiencia digital más segura y consciente para todos.
        </p>
      </div>

      <Modal show={showModal} onHide={() => setShowModal(false)} centered>
        <Modal.Body className="d-flex justify-content-center">
          {result === 'safe' ? (
            <div className="custom-alert custom-alert-success">
              <h4 className="mb-3">✔️ Análisis Completado</h4>
              No se ha detectado ningún tipo de anuncio referente al gambling en la página que proporcionaste.
            </div>
          ) : (
            <div className="custom-alert custom-alert-warning">
              <h4 className="mb-3">⚠️ Advertencia</h4>
              La página que proporcionaste posee anuncios que dan promoción al gambling.
            </div>
          )}
        </Modal.Body>
      </Modal>

      <footer className="text-center text-white bg-success py-3 mt-5">
        GAnalysis © 2025 | Desarrollado para detectar amenazas de anuncios relacionados con gambling
      </footer>
    </>
  );
}

export default App;
