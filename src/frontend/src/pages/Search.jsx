import { useState } from 'react';
import './Search.css';

export default function Search() {
  const [query, setQuery] = useState('');
  // Memória das configurações da Sidebar
  const [processing, setProcessing] = useState('stemming'); // Começa com stemming selecionado
  const [removeStopWords, setRemoveStopWords] = useState(true); // Começa a remover stop words
  const [language, setLanguage] = useState('all'); // Começa em Ambos
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

  // Paginação e Ordenação
  const [currentPage, setCurrentPage] = useState(1);
  const [sortOption, setSortOption] = useState('relevance');
  const resultsPerPage = 10; // Quantos resultados por página
  const [totalResults, setTotalResults] = useState(0); // Total de resultados da API

  // --- ESTADOS DAS AÇÕES DOS RESULTADOS ---
  const [expandedDocs, setExpandedDocs] = useState({}); // Controla quais os resumos que estão expandidos (usando ID do doc)
  const [savedDocs, setSavedDocs] = useState(() => {
    // Lê a memória do Chrome ao iniciar a página
    const saved = localStorage.getItem('repositorium_saved');
    return saved ? JSON.parse(saved) : [];
  });

  // --- FUNÇÕES DE AÇÃO NOS DOCUMENTOS ---

  // 1. Ver Resumo (Abre e fecha a caixa de texto completo usando o título ou URL como ID único)
  const toggleSummary = (docId) => {
    setExpandedDocs(prev => ({
      ...prev,
      [docId]: !prev[docId]
    }));
  };

  // 2. Guardar (Guarda no LocalStorage do Browser)
  const toggleSave = (doc) => {
    const docId = doc.url || doc.handle || doc.title; // Usa o link ou titulo como ID único
    const isSaved = savedDocs.some(d => (d.url || d.handle || d.title) === docId);

    let newSaved;
    if (isSaved) {
      newSaved = savedDocs.filter(d => (d.url || d.handle || d.title) !== docId); // Remove se já lá estiver
    } else {
      newSaved = [...savedDocs, doc]; // Adiciona se não estiver
    }

    setSavedDocs(newSaved);
    localStorage.setItem('repositorium_saved', JSON.stringify(newSaved)); // Grava no PC do utilizador
  };

  // 3. Exportar (Gera um ficheiro .txt com citação estilo APA e faz download)
  const handleExport = (doc) => {
    // Limpar o <b> do título que vem do backend para não ir para o ficheiro de texto
    const cleanTitle = (doc.title || "Sem título").replace(/<\/?b>/gi, '');
    const author = doc.authors ? (Array.isArray(doc.authors) ? doc.authors.join(', ') : doc.authors) : (doc.author || "Autor Desconhecido");
    const year = doc.date || doc.year || "S.d.";
    const url = doc.url || doc.link || doc.handle || "";

    const citation = `${author} (${year}). ${cleanTitle}. Recuperado de ${url}`;

    // Cria um ficheiro de texto falso e força o browser a fazer download
    const blob = new Blob([citation], { type: 'text/plain;charset=utf-8' });
    const link = document.createElement('a');
    link.href = URL.createObjectURL(blob);
    link.download = `citacao_${cleanTitle.substring(0, 20).replace(/[^a-z0-9]/gi, '_')}.txt`;
    link.click();
  };

  const executeSearch = async (page = 1, sort = sortOption) => {
    if (!query.trim()) return;

    setIsLoading(true);
    setError(null);

    try {
      const params = new URLSearchParams({
        q: query,
        lang: language,
        processing: processing,
        stop_words: removeStopWords,
        algo: algorithm,
        target: searchTarget,
        area: researchArea,
        author_mode: authorMode,
        sort_by: sort,
        page: page,
        page_size: resultsPerPage
      });

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
      setTotalResults(data.metadata?.total || 0);
      setCurrentPage(page);
      setSortOption(sort);
      setExpandedDocs({});

    } catch (err) {
      console.error("Erro na pesquisa:", err);
      // Feedback claro ao utilizador
      setError("Não foi possível ligar ao servidor. Verifica se a API está a correr na porta 8000.");
    } finally {
      setIsLoading(false); // Para o loading, quer tenha dado erro ou sucesso
    }
  };

  const handleSearch = async (e) => {
    e.preventDefault();
    executeSearch(1, sortOption);
  };

  // 1. Paginação Total (vinda do backend)
  const totalPages = Math.ceil(totalResults / resultsPerPage);
  const currentResults = results;

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
          {language !== 'all' && (
            <span style={{ background: '#fef2f2', color: '#AA192B', padding: '4px 12px', borderRadius: '20px', fontSize: '0.85rem', border: '1px solid #fecaca' }}>
              Idioma: <strong>{language === 'PT' ? 'Português' : 'Inglês'}</strong>
            </span>
          )}
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
                <option value="AI & Robotics">IA & Robótica</option>
                <option value="General Engineering">Engenharia Geral</option>
                <option value="Systems & Tech">Sistemas e Tecnologia</option>
                <option value="Education & Society">Educação e Sociedade</option>
                <option value="Data Science">Ciência de Dados</option>
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
                <option value="all">Ambos (PT/EN)</option>
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
              <strong>Cálculo de Semelhança:</strong><br />
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
            /* APRESENTAÇÃO DE RESULTADOS */
            <div className="results-container" style={{ width: '100%', textAlign: 'left' }}>

              {/* Contagem, Tempo e Ordenação */}
              <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', borderBottom: '2px solid #e5e7eb', paddingBottom: '10px', marginBottom: '20px' }}>
                <p style={{ color: '#4b5563', margin: 0, fontSize: '1.1rem' }}>
                  Encontrados <strong>{totalResults}</strong> resultados
                  {/* O tempo pode ser real se a Laura enviar, por agora metemos um placeholder estético */}
                  <span style={{ fontSize: '0.85em', color: '#9ca3af', marginLeft: '8px' }}> (0.24 segundos)</span>
                </p>

                <select
                  value={sortOption}
                  onChange={(e) => executeSearch(1, e.target.value)}
                  style={{ padding: '8px', borderRadius: '6px', border: '1px solid #d1d5db', outline: 'none' }}
                >
                  <option value="relevance">🌟 Ordenar por: Relevância</option>
                  <option value="date_desc">📅 Mais recentes primeiro</option>
                  <option value="date_asc">📅 Mais antigos primeiro</option>
                </select>
              </div>

              {/* A LISTA DE DOCUMENTOS */}
              <div className="display-results-list" style={{ display: 'flex', flexDirection: 'column', gap: '20px' }}>
                {currentResults.map((item, index) => {

                  // NOVO: Criar um ID Único para cada documento (resolve bugs de paginação)
                  const docUniqueId = item.url || item.title || index;

                  return (
                    <div key={docUniqueId} style={{ padding: '20px', background: '#fff', border: '1px solid #e5e7eb', borderRadius: '8px', boxShadow: '0 4px 6px -1px rgba(0, 0, 0, 0.05)' }}>

                      {/* Título (Clicável) e Score */}
                      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', marginBottom: '10px' }}>
                        <h3 style={{ margin: 0, fontSize: '1.25rem' }}>
                          {/* Usamos dangerouslySetInnerHTML para transformar as tags <b> (enviadas pelo backend) em HTML real */}
                          <a
                            href={item.url || item.link || item.handle || "#"}
                            target="_blank"
                            rel="noreferrer"
                            style={{ textDecoration: 'none', color: '#1d4ed8' }}
                            dangerouslySetInnerHTML={{ __html: item.title || "Documento sem título" }}
                          />
                        </h3>
                        <span style={{ background: '#ecfdf5', color: '#059669', padding: '4px 10px', borderRadius: '12px', fontSize: '0.85rem', fontWeight: 'bold', marginLeft: '15px' }}>
                          Score: {item.score ? Number(item.score).toFixed(4) : "N/A"}
                        </span>
                      </div>

                      {/* Autores e Data */}
                      <div style={{ color: '#059669', fontSize: '0.9rem', marginBottom: '12px', display: 'flex', gap: '20px', flexWrap: 'wrap' }}>
                        <span>👤 <strong>Autores:</strong> {item.authors ? (Array.isArray(item.authors) ? item.authors.join(', ') : item.authors) : (item.author || "Desconhecido")}</span>
                        <span>📅 <strong>Ano:</strong> {item.date || item.year || "N/D"}</span>
                      </div>

                      {/* F26 e F27: Snippet (recolhido) ou Resumo Completo (expandido) */}
                      <p
                        className="highlight-backend"
                        style={{
                          color: '#4b5563',
                          fontSize: '0.95rem',
                          lineHeight: '1.6',
                          marginBottom: '20px',
                          // Controla o número de linhas baseado no estado (expandido ou não)
                          display: expandedDocs[docUniqueId] ? 'block' : '-webkit-box',
                          WebkitLineClamp: expandedDocs[docUniqueId] ? 'unset' : 3,
                          WebkitBoxOrient: 'vertical',
                          overflow: expandedDocs[docUniqueId] ? 'visible' : 'hidden'
                        }}
                        dangerouslySetInnerHTML={{
                          __html: expandedDocs[docUniqueId]
                            ? (item.abstract || item.description || item.snippet || "Resumo completo não disponível.")
                            : (item.snippet || item.abstract || item.description || "Resumo não disponível.")
                        }}
                      />

                      {/* Ações nos Resultados */}
                      <div style={{ display: 'flex', gap: '10px', flexWrap: 'wrap' }}>

                        {/* Botão Ver Resumo (Alterna o texto usando o ID do documento) */}
                        <button
                          onClick={() => toggleSummary(docUniqueId)}
                          style={{ padding: '8px 16px', background: '#f3f4f6', color: '#374151', border: '1px solid #d1d5db', borderRadius: '6px', cursor: 'pointer', fontWeight: '500', transition: '0.2s' }}
                        >
                          {expandedDocs[docUniqueId] ? '🔼 Ocultar Resumo' : '👁️ Ver Resumo Completo'}
                        </button>

                        {/* Abrir PDF */}
                        <a href={item.url || item.link || item.handle || "#"} target="_blank" rel="noreferrer" style={{ padding: '8px 16px', background: '#fee2e2', color: '#b91c1c', border: '1px solid #fecaca', borderRadius: '6px', cursor: 'pointer', fontWeight: '500', textDecoration: 'none', display: 'inline-block' }}>
                          📥 Abrir PDF
                        </a>

                        {/* Botão Guardar (Muda de cor se estiver guardado) */}
                        <button
                          onClick={() => toggleSave(item)}
                          style={{
                            padding: '8px 16px',
                            background: savedDocs.some(d => (d.url || d.handle || d.title) === (item.url || item.handle || item.title)) ? '#fef08a' : '#f3f4f6',
                            color: savedDocs.some(d => (d.url || d.handle || d.title) === (item.url || item.handle || item.title)) ? '#854d0e' : '#374151',
                            border: savedDocs.some(d => (d.url || d.handle || d.title) === (item.url || item.handle || item.title)) ? '1px solid #fde047' : '1px solid #d1d5db',
                            borderRadius: '6px',
                            cursor: 'pointer',
                            fontWeight: '500',
                            transition: '0.2s'
                          }}
                        >
                          {savedDocs.some(d => (d.url || d.handle || d.title) === (item.url || item.handle || item.title)) ? '🌟 Guardado' : '⭐ Guardar'}
                        </button>

                        {/* Botão Exportar */}
                        <button
                          onClick={() => handleExport(item)}
                          style={{ padding: '8px 16px', background: '#f3f4f6', color: '#374151', border: '1px solid #d1d5db', borderRadius: '6px', cursor: 'pointer', fontWeight: '500' }}
                        >
                          📤 Exportar Citação
                        </button>
                      </div>
                    </div>
                  );
                })}
              </div>

              {/* Paginação */}
              {totalPages > 1 && (
                <div style={{ display: 'flex', justifyContent: 'center', alignItems: 'center', gap: '10px', marginTop: '40px' }}>
                  <button
                    onClick={() => executeSearch(Math.max(currentPage - 1, 1), sortOption)}
                    disabled={currentPage === 1}
                    style={{ padding: '8px 16px', borderRadius: '6px', border: '1px solid #d1d5db', background: currentPage === 1 ? '#f3f4f6' : '#fff', cursor: currentPage === 1 ? 'not-allowed' : 'pointer' }}
                  >
                    Anterior
                  </button>

                  <span style={{ color: '#4b5563', fontWeight: '500' }}>
                    Página {currentPage} de {totalPages}
                  </span>

                  <button
                    onClick={() => executeSearch(Math.min(currentPage + 1, totalPages), sortOption)}
                    disabled={currentPage === totalPages}
                    style={{ padding: '8px 16px', borderRadius: '6px', border: '1px solid #d1d5db', background: currentPage === totalPages ? '#f3f4f6' : '#fff', cursor: currentPage === totalPages ? 'not-allowed' : 'pointer' }}
                  >
                    Próxima
                  </button>
                </div>
              )}
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