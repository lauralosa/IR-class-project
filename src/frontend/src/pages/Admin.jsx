import React, { useState, useEffect } from 'react';
import './Admin.css';

export default function Admin() {
  const [stats, setStats] = useState(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    fetch('http://localhost:8000/stats')
      .then(res => res.json())
      .then(data => {
        setStats(data);
        setLoading(false);
      })
      .catch(console.error);
  }, []);

  if (loading || !stats) {
    return <div className="admin-page" style={{ padding: '3rem', textAlign: 'center' }}><h3>A carregar métricas do sistema...</h3></div>;
  }

  // Helper para F58 (Categories chart)
  const categoryNames = Object.keys(stats.categories || {});
  const categoryValues = Object.values(stats.categories || {});
  const totalCategories = categoryValues.reduce((a, b) => a + b, 0);

  return (
    <div className="admin-page">
      <div className="admin-header">
        <h2>📈 Dashboard de Analytics</h2>
        <p>Monitorização em tempo real do estado do índice e do modelo de IA .</p>
        <span className="last-update">Última indexação: {stats.metadata?.last_updated || 'N/D'}</span>
      </div>

      {/* REQ-F55: Admin Dashboard - Collection Statistics */}
      <div className="admin-grid top-metrics">
        <div className="admin-card">
          <div className="card-icon">📄</div>
          <div className="card-value">{stats.num_docs}</div>
          <div className="card-label">Total de Documentos</div>
        </div>
        <div className="admin-card">
          <div className="card-icon">🔤</div>
          <div className="card-value">{stats.vocabulary_size?.stemming || stats.vocabulary_size || '0'}</div>
          <div className="card-label">Tamanho do Vocabulário</div>
        </div>
        <div className="admin-card">
          <div className="card-icon">👥</div>
          <div className="card-value">{stats.author_count}</div>
          <div className="card-label">Autores Registados</div>
        </div>
        <div className="admin-card">
          <div className="card-icon">⏱️</div>
          <div className="card-value">
            {stats.performance ? (stats.performance.stemming_time_sec + stats.performance.lemmatization_time_sec).toFixed(2) : 'N/D'}s
          </div>
          <div className="card-label">Tempo Total de Indexação<br/><span style={{fontSize:'0.8em'}}>(Stemming: {stats.performance?.stemming_time_sec?.toFixed(2)}s | Lematização: {stats.performance?.lemmatization_time_sec?.toFixed(2)}s)</span></div>
        </div>
      </div>

      <div className="admin-row">
        {/* REQ-F57: Most frequent queries and terms */}
        <div className="admin-panel half-panel">
          <h3>🏆 Top Termos Mais Frequentes</h3>
          <p className="panel-sub">Os termos com maior Document Frequency (DF) no Índice Invertido.</p>
          <ul className="top-terms-list">
            {stats.top_terms?.map((t, idx) => (
              <li key={t.term}>
                <span className="term-rank">#{idx + 1}</span>
                <span className="term-word">{t.term}</span>
                <span className="term-count">{t.df} docs</span>
              </li>
            ))}
          </ul>
        </div>

        {/* REQ-F58: Classification accuracy / Distribution */}
        <div className="admin-panel half-panel">
          <h3>🧠 Classificação Automática ML</h3>
          <p className="panel-sub">Distribuição da coleção pelas categorias previstas pelo modelo de Machine Learning.</p>
          <div className="categories-chart">
            {categoryNames.map(cat => {
              const perc = ((stats.categories[cat] / totalCategories) * 100).toFixed(1);
              return (
                <div className="cat-bar-container" key={cat}>
                  <div className="cat-info">
                    <span className="cat-name">{cat === 'General Engineering' ? 'Engenharia Geral' : cat === 'AI & Robotics' ? 'IA & Robótica' : cat === 'Data Science' ? 'Ciência de Dados' : cat === 'Education & Society' ? 'Educação & Sociedade' : cat === 'Systems & Tech' ? 'Sistemas & TI' : cat}</span>
                    <span className="cat-perc">{perc}%</span>
                  </div>
                  <div className="cat-track">
                    <div className="cat-fill" style={{ width: `${perc}%` }}></div>
                  </div>
                </div>
              )
            })}
          </div>
        </div>
      </div>

      {/* REQ-F56: Index growth over time */}
      <div className="admin-panel full-panel">
        <h3>📈 Crescimento do Índice</h3>
        <p className="panel-sub">Evolução simulada do tamanho do vocabulário e documentos processados (últimos 6 meses).</p>
        <div className="growth-chart">
          <div className="growth-col"><div className="g-bar" style={{ height: '30%' }}></div><span>Jan</span></div>
          <div className="growth-col"><div className="g-bar" style={{ height: '45%' }}></div><span>Fev</span></div>
          <div className="growth-col"><div className="g-bar" style={{ height: '50%' }}></div><span>Mar</span></div>
          <div className="growth-col"><div className="g-bar" style={{ height: '75%' }}></div><span>Abr</span></div>
          <div className="growth-col"><div className="g-bar" style={{ height: '90%' }}></div><span>Mai</span></div>
          <div className="growth-col"><div className="g-bar active-bar" style={{ height: '100%' }}></div><span style={{ fontWeight: 'bold', color: '#2563eb' }}>Atual</span></div>
        </div>
      </div>

    </div>
  );
}