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

  // API e Resultados
  const [results, setResults] = useState([]); // Vai guardar os documentos que vêm do Backend
  const [isLoading, setIsLoading] = useState(false); // Controla se mostramos "A carregar..."
  const [error, setError] = useState(null); // Guarda mensagens de erro se a API falhar

  const handleSearch = async (e) => {
    e.preventDefault();
    if (!query.trim()) return; // Não pesquisa se a barra estiver vazia

    setIsLoading(true); // Começa o estado de loading
    setError(null); // Limpa erros de pesquisas anteriores

    try {
      // Sincronizar UI com backend. Vamos construir os parâmetros do URL dinamicamente!
      const params = new URLSearchParams({
        q: query,
        lang: language,
        processing: processing,
        stop_words: removeStopWords,
        algo: algorithm,
        target: searchTarget,
        area: researchArea,
        author_mode: authorMode
      });

      // Só envia o esquema de pesos se o algoritmo for o customizado
      if (algorithm === 'custom') {
        params.append('weights', weightingScheme);
      }

      // Comunicação API RESTful
      // Fazemos o fetch à porta 8000 do Backend
      const response = await fetch(`http://localhost:8000/search?${params.toString()}`);

      // Tratamento de erros do servidor (ex: erro 500 ou 404)
      if (!response.ok) {
        throw new Error(`Erro do servidor: ${response.status}`);
      }

      const data = await response.json();
      
      
      setResults(data.results || []); 

    } catch (err) {
      console.error("Erro na pesquisa:", err);
      // Feedback claro ao utilizador
      setError("Não foi possível ligar ao servidor. Verifica se a API está a correr na porta 8000."); 
    } finally {
      setIsLoading(false); // Para o loading, quer tenha dado erro ou sucesso
    }
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

            {/* Mostrar cálculo de semelhança fixo */}
            <div style={{ marginTop: '15px', fontSize: '0.85rem', color: '#6b7280', lineHeight: '1.4', padding: '10px', background: '#f0fdf4', borderRadius: '6px', border: '1px solid #bbf7d0' }}>
              <strong>Cálculo de Semelhança:</strong><br/>
              <span style={{ color: '#166534' }}>Similaridade do Cosseno</span>
            </div>
          </div>

        </aside>
        <section className="results-placeholder" style={{ flexDirection: 'column' }}>
          {/* Estado de Loading */}
          {isLoading ? (
            <div className="loading-state">
              <div className="spinner"></div>
              <p>A procurar no RepositóriUM...</p>
            </div>
          ) : error ? (
            /* Estado de Erro */
            <div className="error-state" style={{ color: '#AA192B', textAlign: 'center', maxWidth: '400px' }}>
              <span style={{ fontSize: '2rem' }}>⚠️</span>
              <p style={{ fontWeight: 'bold', marginTop: '10px' }}>Oops! Algo correu mal.</p>
              <p style={{ fontSize: '0.9rem' }}>{error}</p>
            </div>
          ) : results.length > 0 ? (
            /* Estado de Sucesso (Será formatado na Fase 5) */
            <div className="results-success" style={{ width: '100%', textAlign: 'left' }}>
              <p style={{ color: '#16a34a', fontWeight: 'bold' }}>✅ Ligação bem-sucedida! Recebemos {results.length} resultados.</p>
              <pre style={{ background: '#f3f4f6', padding: '15px', borderRadius: '8px', marginTop: '10px', fontSize: '0.8rem', overflowX: 'auto' }}>
                {JSON.stringify(results, null, 2)}
              </pre>
            </div>
          ) : (
            /* Estado Vazio Inicial */
            <p>Resultados da pesquisa aparecerão aqui.</p>
          )}
        </section>
      </div>
    </div>
  );
}