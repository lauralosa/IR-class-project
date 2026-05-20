import React, { useState, useEffect } from 'react';
import './Compare.css';

export default function Compare() {
  const [query, setQuery] = useState('');

  // Defaults para demonstrar F52 (Stemming vs Lematização)
  const [configA, setConfigA] = useState({ processing: 'stemming', removeStopWords: true });
  const [configB, setConfigB] = useState({ processing: 'lemmatization', removeStopWords: true });

  const [resultsA, setResultsA] = useState(null);
  const [resultsB, setResultsB] = useState(null);
  const [isLoading, setIsLoading] = useState(false);
  const [stats, setStats] = useState(null);

  useEffect(() => {
    // Busca métricas do índice para F53 (Indexing time)
    fetch('http://localhost:8000/stats')
      .then(res => res.json())
      .then(data => setStats(data))
      .catch(console.error);
  }, []);

  const handleCompare = async () => {
    if (!query.trim()) return;
    setIsLoading(true);

    const fetchConfig = async (conf) => {
      const params = new URLSearchParams({
        q: query,
        processing: conf.processing,
        stop_words: conf.removeStopWords,
        algo: 'custom',
        page_size: 5 // Top 5 para comparação
      });
      const res = await fetch(`http://localhost:8000/search?${params.toString()}`);
      if (!res.ok) throw new Error("Erro na API");
      return res.json();
    };

    try {
      const [resA, resB] = await Promise.all([fetchConfig(configA), fetchConfig(configB)]);
      setResultsA(resA);
      setResultsB(resB);
    } catch (e) {
      console.error(e);
      alert("Erro ao executar a comparação.");
    }
    setIsLoading(false);
  };

  return (
    <div className="compare-page">
      <div className="compare-header">
        <h2>⚖️ Comparador de Performance</h2>
        <p>Compara lado a lado o impacto de diferentes configurações de Processamento de Linguagem Natural (NLP) na velocidade e qualidade dos resultados.</p>
      </div>

      {/* REQ-F53: Tempo de Indexação Global */}
      {stats && stats.performance && (
        <div className="indexing-stats">
          <strong>⏱️ Tempos de Indexação: </strong>
          <span style={{ marginLeft: '10px', background: '#fef2f2', color: '#AA192B', padding: '2px 8px', borderRadius: '12px', fontSize: '0.9em' }}>
            <strong>Stemming:</strong> {stats.performance.stemming_time_sec ? Number(stats.performance.stemming_time_sec).toFixed(2) : "N/D"}s
          </span>
          <span style={{ marginLeft: '10px', background: '#fef2f2', color: '#AA192B', padding: '2px 8px', borderRadius: '12px', fontSize: '0.9em' }}>
            <strong>Lematização:</strong> {stats.performance.lemmatization_time_sec ? Number(stats.performance.lemmatization_time_sec).toFixed(2) : "N/D"}s
          </span>
          <span style={{ marginLeft: '10px', color: '#6b7280', fontSize: '0.9em' }}>
            (para {stats.num_docs} documentos)
          </span>
        </div>
      )}

      <div className="compare-controls">
        <div className="search-bar-wrapper">
          <input
            type="text"
            placeholder="Insere uma query (ex: health data ethics)..."
            value={query}
            onChange={(e) => setQuery(e.target.value)}
            onKeyDown={(e) => e.key === 'Enter' && handleCompare()}
          />
          <button onClick={handleCompare} disabled={isLoading || !query.trim()}>
            {isLoading ? 'A comparar...' : 'Comparar Configurações'}
          </button>
        </div>

        <div className="config-panels">
          <div className="config-panel panel-a">
            <h3>Sistema A</h3>
            <label>Técnica NLP:</label>
            <select value={configA.processing} onChange={e => setConfigA({ ...configA, processing: e.target.value })}>
              <option value="none">Nenhum (Tokens Exatos)</option>
              <option value="stemming">Stemming (Corte da raiz)</option>
              <option value="lemmatization">Lematização (Dicionário)</option>
            </select>
            <label style={{ marginTop: '10px', display: 'flex', alignItems: 'center', gap: '8px', cursor: 'pointer' }}>
              <input type="checkbox" checked={configA.removeStopWords} onChange={e => setConfigA({ ...configA, removeStopWords: e.target.checked })} />
              Remover Stop Words
            </label>
          </div>

          <div className="config-vs">VS</div>

          <div className="config-panel panel-b">
            <h3>Sistema B</h3>
            <label>Técnica NLP:</label>
            <select value={configB.processing} onChange={e => setConfigB({ ...configB, processing: e.target.value })}>
              <option value="none">Nenhum (Tokens Exatos)</option>
              <option value="stemming">Stemming (Corte da raiz)</option>
              <option value="lemmatization">Lematização (Dicionário)</option>
            </select>
            <label style={{ marginTop: '10px', display: 'flex', alignItems: 'center', gap: '8px', cursor: 'pointer' }}>
              <input type="checkbox" checked={configB.removeStopWords} onChange={e => setConfigB({ ...configB, removeStopWords: e.target.checked })} />
              Remover Stop Words
            </label>
          </div>
        </div>
      </div>

      {resultsA && resultsB && (
        <div className="compare-results">

          {/* REQ-F54: Gráficos de Comparação de Performance */}
          <div className="charts-section">
            <h3>📊 Relatório de Performance (REQ-F54)</h3>
            <div className="charts-grid">

              <div className="chart-box">
                <h4>Tempo de Pesquisa (segundos)</h4>
                <div className="bar-chart">
                  <div className="bar-row">
                    <span className="bar-label">Sistema A</span>
                    <div className="bar-track">
                      <div className="bar fill-a" style={{ width: `${Math.max(10, (resultsA.metadata.time / Math.max(resultsA.metadata.time, resultsB.metadata.time)) * 100)}%` }}></div>
                    </div>
                    <span className="bar-value">{resultsA.metadata.time.toFixed(4)}s</span>
                  </div>
                  <div className="bar-row">
                    <span className="bar-label">Sistema B</span>
                    <div className="bar-track">
                      <div className="bar fill-b" style={{ width: `${Math.max(10, (resultsB.metadata.time / Math.max(resultsA.metadata.time, resultsB.metadata.time)) * 100)}%` }}></div>
                    </div>
                    <span className="bar-value">{resultsB.metadata.time.toFixed(4)}s</span>
                  </div>
                </div>
              </div>

              <div className="chart-box">
                <h4>Total de Resultados Encontrados (Recall)</h4>
                <div className="bar-chart">
                  <div className="bar-row">
                    <span className="bar-label">Sistema A</span>
                    <div className="bar-track">
                      <div className="bar fill-a" style={{ width: `${Math.max(10, (resultsA.metadata.total / (Math.max(resultsA.metadata.total, resultsB.metadata.total) || 1)) * 100)}%` }}></div>
                    </div>
                    <span className="bar-value">{resultsA.metadata.total} docs</span>
                  </div>
                  <div className="bar-row">
                    <span className="bar-label">Sistema B</span>
                    <div className="bar-track">
                      <div className="bar fill-b" style={{ width: `${Math.max(10, (resultsB.metadata.total / (Math.max(resultsA.metadata.total, resultsB.metadata.total) || 1)) * 100)}%` }}></div>
                    </div>
                    <span className="bar-value">{resultsB.metadata.total} docs</span>
                  </div>
                </div>
              </div>

            </div>
          </div>

          {/* REQ-F51: Ranking Lado a Lado */}
          <div className="side-by-side">
            <div className="results-column col-a">
              <h3>Top 5 - Sistema A</h3>
              {resultsA.results.length === 0 && <p className="no-res">Nenhum resultado.</p>}
              {resultsA.results.map((doc, idx) => (
                <div key={doc.id} className="compare-card">
                  <div className="card-rank">#{idx + 1}</div>
                  <div className="card-content">
                    <h5 dangerouslySetInnerHTML={{ __html: doc.title }} />
                    <span className="card-score">Score: {doc.score}</span>
                    <p dangerouslySetInnerHTML={{ __html: doc.snippet }} />
                  </div>
                </div>
              ))}
            </div>

            <div className="results-column col-b">
              <h3>Top 5 - Sistema B</h3>
              {resultsB.results.length === 0 && <p className="no-res">Nenhum resultado.</p>}
              {resultsB.results.map((doc, idx) => (
                <div key={doc.id} className="compare-card">
                  <div className="card-rank">#{idx + 1}</div>
                  <div className="card-content">
                    <h5 dangerouslySetInnerHTML={{ __html: doc.title }} />
                    <span className="card-score">Score: {doc.score}</span>
                    <p dangerouslySetInnerHTML={{ __html: doc.snippet }} />
                  </div>
                </div>
              ))}
            </div>
          </div>

        </div>
      )}
    </div>
  );
}
