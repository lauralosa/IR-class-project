import { useState } from 'react';
import './Search.css';

export default function Search() {
  const [query, setQuery] = useState('');
  // Memória das configurações da Sidebar
  const [processing, setProcessing] = useState('stemming'); // Começa com stemming selecionado
  const [removeStopWords, setRemoveStopWords] = useState(true); // Começa a remover stop words
  const [language, setLanguage] = useState('PT'); // Começa em Português
  const [algorithm, setAlgorithm] = useState('custom'); // Começa com o TF-IDF da Laura

  const handleSearch = (e) => {
    e.preventDefault();
    console.log("A pesquisar por:", query);
    // Isto vai imprimir no inspecionar elemento as opções escolhidas
    console.log("Opções da Sidebar:", { processing, removeStopWords, language, algorithm });
  };

  return (
    <div className="search-page">
      <div className="search-container">
        <h2>Pesquisar no Acervo</h2>
        <form onSubmit={handleSearch} className="search-form">
          <input 
            type="text" 
            className="search-input"
            placeholder="Ex: machine learning AND (health OR medicine)"
            value={query}
            onChange={(e) => setQuery(e.target.value)} 
          /> 
          <button type="submit" className="search-button">Pesquisar</button>
        </form>
        <div className="search-tips">
          <small><strong>Dica:</strong> Podes usar operadores booleanos como <code>AND</code>, <code>OR</code> e <code>NOT</code>.</small>
        </div>
      </div>

      <div className="layout-grid">
        <aside className="sidebar">
  
          {/* SECÇÃO 1: Processamento de Texto */}
          <div className="sidebar-section">
            <h3>Processamento de Texto</h3>
            
            <div className="filter-group">
              <label className="filter-label">Idioma:</label>
              <select 
                className="filter-select" 
                value={language} 
                onChange={(e) => setLanguage(e.target.value)}
              >
                <option value="PT">Português (PT)</option>
                <option value="EN">Inglês (EN)</option>
              </select>
            </div>

            <div className="filter-group">
              <label className="filter-label">Técnica:</label>
              <div className="radio-options">
                <label>
                  <input 
                    type="radio" 
                    value="stemming" 
                    checked={processing === 'stemming'} 
                    onChange={(e) => setProcessing(e.target.value)} 
                  />
                  Stemming
                </label>
                <label>
                  <input 
                    type="radio" 
                    value="lemmatization" 
                    checked={processing === 'lemmatization'} 
                    onChange={(e) => setProcessing(e.target.value)} 
                  />
                  Lematização
                </label>
              </div>
            </div>

            <div className="filter-group">
              <label className="checkbox-label">
                <input 
                  type="checkbox" 
                  checked={removeStopWords} 
                  onChange={(e) => setRemoveStopWords(e.target.checked)} 
                />
                Remover Stop Words
              </label>
            </div>
          </div>

          <hr className="sidebar-divider" />

          {/* SECÇÃO 2: Algoritmo de Ordenação */}
          <div className="sidebar-section">
            <h3>Algoritmo de Ordenação</h3>
            <div className="radio-options vertical">
              <label>
                <input 
                  type="radio" 
                  value="custom" 
                  checked={algorithm === 'custom'} 
                  onChange={(e) => setAlgorithm(e.target.value)} 
                />
                TF-IDF (Customizado)
              </label>
              <label>
                <input 
                  type="radio" 
                  value="sklearn" 
                  checked={algorithm === 'sklearn'} 
                  onChange={(e) => setAlgorithm(e.target.value)} 
                />
                TF-IDF (Scikit-Learn)
              </label>
              <label>
                <input 
                  type="radio" 
                  value="boolean" 
                  checked={algorithm === 'boolean'} 
                  onChange={(e) => setAlgorithm(e.target.value)} 
                />
                Modelo Booleano
              </label>
            </div>
          </div>

        </aside>
        <section className="results-placeholder">
          <p>Resultados da pesquisa aparecerão aqui.</p>
        </section>
      </div>
    </div>
  );
}