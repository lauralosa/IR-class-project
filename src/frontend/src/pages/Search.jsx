import { useState } from 'react';
import './Search.css';

export default function Search() {
  const [query, setQuery] = useState('');
  // Memória das configurações da Sidebar
  const [processing, setProcessing] = useState('stemming'); // Começa com stemming selecionado
  const [removeStopWords, setRemoveStopWords] = useState(true); // Começa a remover stop words
  const [language, setLanguage] = useState('PT'); // Começa em Português
  const [algorithm, setAlgorithm] = useState('custom'); // Começa com o TF-IDF da Laura
  // Estados para o âmbito da pesquisa
  const [searchTarget, setSearchTarget] = useState('all');
  const [researchArea, setResearchArea] = useState('all');

  // Modo de pesquisa por autor
  const [authorMode, setAuthorMode] = useState(false);
  
  // Esquema de pesos alinhados com o algoritmo escolhido
  const [weightingScheme, setWeightingScheme] = useState('ltc');

  const handleSearch = (e) => {
    e.preventDefault();
    console.log("A pesquisar por:", query);
    // Isto vai imprimir no inspecionar elemento as opções escolhidas
    console.log("Opções da Sidebar:", { processing, removeStopWords, language, algorithm });
  };

  return (
    <div className="search-page">
      <div className="search-container">
        <h2>Pesquisar na Coleção</h2>
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
        {/* Mostrar configuração atual */}
        <div className="active-configs" style={{ marginTop: '15px', display: 'flex', gap: '10px', justifyContent: 'center', flexWrap: 'wrap' }}>
          <span style={{ background: '#fef2f2', color: '#AA192B', padding: '4px 12px', borderRadius: '20px', fontSize: '0.85rem', border: '1px solid #fecaca' }}>
            Idioma: <strong>{language}</strong>
          </span>
          <span style={{ background: '#fef2f2', color: '#AA192B', padding: '4px 12px', borderRadius: '20px', fontSize: '0.85rem', border: '1px solid #fecaca' }}>
            Técnica: <strong>{processing === 'stemming' ? 'Stemming' : 'Lematização'}</strong>
          </span>
          {removeStopWords && (
            <span style={{ background: '#fef2f2', color: '#AA192B', padding: '4px 12px', borderRadius: '20px', fontSize: '0.85rem', border: '1px solid #fecaca' }}>
              Sem Stop Words
            </span>
          )}
          <span style={{ background: '#f3f4f6', color: '#4b5563', padding: '4px 12px', borderRadius: '20px', fontSize: '0.85rem', border: '1px solid #e5e7eb' }}>
            Algoritmo: <strong>{algorithm === 'custom' ? 'TF-IDF Custom' : algorithm === 'sklearn' ? 'TF-IDF Sklearn' : 'Booleano'}</strong>
          </span>
          {researchArea !== 'all' && (
            <span style={{ background: '#eff6ff', color: '#1d4ed8', padding: '4px 12px', borderRadius: '20px', fontSize: '0.85rem', border: '1px solid #bfdbfe' }}>
              Área: <strong>{researchArea === 'health' ? 'Saúde' : researchArea === 'engineering' ? 'Engenharia' : researchArea === 'humanities' ? 'Humanidades' : 'Ciências Exatas'}</strong>
            </span>
          )}
          {searchTarget !== 'all' && (
            <span style={{ background: '#eff6ff', color: '#1d4ed8', padding: '4px 12px', borderRadius: '20px', fontSize: '0.85rem', border: '1px solid #bfdbfe' }}>
              Alvo: <strong>{searchTarget === 'title' ? 'Títulos' : searchTarget === 'abstract' ? 'Resumos' : 'Documento Completo'}</strong>
            </span>
          )}

          {authorMode && (
            <span style={{ background: '#fef08a', color: '#854d0e', padding: '4px 12px', borderRadius: '20px', fontSize: '0.85rem', border: '1px solid #fde047' }}>
              <strong>Modo Autor</strong>
            </span>
          )}
          {algorithm === 'custom' && (
            <span style={{ background: '#f3f4f6', color: '#4b5563', padding: '4px 12px', borderRadius: '20px', fontSize: '0.85rem', border: '1px solid #e5e7eb' }}>
              Pesos: <strong>{weightingScheme === 'ltc' ? 'TF-IDF (ltc)' : weightingScheme === 'lnc' ? 'Logarítmico (lnc)' : 'Natural (nnn)'}</strong>
            </span>
          )}
        </div>
      </div>

      <div className="layout-grid">
        <aside className="sidebar">
          {/* SECÇÃO: Âmbito da Pesquisa*/}
          <div className="sidebar-section">
            <h3>Âmbito da Pesquisa</h3>
            
            <div className="filter-group">
              <label className="filter-label">Área de Investigação:</label>
              <select 
                className="filter-select" 
                value={researchArea} 
                onChange={(e) => setResearchArea(e.target.value)}
              >
                <option value="all">Todas as Áreas</option>
                <option value="health">Ciências da Saúde</option>
                <option value="engineering">Engenharia</option>
                <option value="humanities">Humanidades</option>
                <option value="sciences">Ciências Exatas</option>
              </select>
            </div>

            <div className="filter-group">
              <label className="filter-label">Pesquisar em:</label>
              <div className="radio-options vertical">
                <label>
                  <input type="radio" value="all" checked={searchTarget === 'all'} onChange={(e) => setSearchTarget(e.target.value)} /> 
                  Todos os campos
                </label>
                <label>
                  <input type="radio" value="title" checked={searchTarget === 'title'} onChange={(e) => setSearchTarget(e.target.value)} /> 
                  Apenas Títulos
                </label>
                <label>
                  <input type="radio" value="abstract" checked={searchTarget === 'abstract'} onChange={(e) => setSearchTarget(e.target.value)} /> 
                  Apenas Resumos
                </label>
                <label>
                  <input type="radio" value="fulltext" checked={searchTarget === 'fulltext'} onChange={(e) => setSearchTarget(e.target.value)} /> 
                  Documento Completo
                </label>
              </div>
            </div>

            {/*Toggle de Autor*/}
            <div className="filter-group" style={{ marginTop: '15px', paddingTop: '15px', borderTop: '1px dashed #e5e7eb' }}>
              <label className="checkbox-label" style={{ fontWeight: 'bold', color: '#AA192B' }}>
                <input 
                  type="checkbox" 
                  checked={authorMode} 
                  onChange={(e) => setAuthorMode(e.target.checked)} 
                />
                Modo Pesquisa de Autor
              </label>
            </div>
          </div>

          <hr className="sidebar-divider" />
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

            {/* Esquema de Pesos*/}
            {algorithm === 'custom' && (
              <div className="filter-group" style={{ marginTop: '15px', padding: '10px', background: '#f9fafb', borderRadius: '6px' }}>
                <label className="filter-label">Esquema de Pesos:</label>
                <select 
                  className="filter-select" 
                  value={weightingScheme} 
                  onChange={(e) => setWeightingScheme(e.target.value)}
                >
                  <option value="ltc">TF-IDF Padrão (ltc)</option>
                  <option value="lnc">TF Logarítmico (lnc)</option>
                  <option value="nnn">Frequência Natural (nnn)</option>
                </select>
              </div>
            )}

            {/* REQ-F19: Mostrar cálculo de semelhança fixo */}
            <div style={{ marginTop: '15px', fontSize: '0.85rem', color: '#6b7280', lineHeight: '1.4', padding: '10px', background: '#f0fdf4', borderRadius: '6px', border: '1px solid #bbf7d0' }}>
              <strong>Cálculo de Semelhança:</strong><br/>
              <span style={{ color: '#166534' }}>Similaridade do Cosseno</span>
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