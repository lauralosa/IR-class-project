import { useState, useEffect, useRef } from 'react';
import { useSearchParams } from 'react-router-dom';
import './Search.css';
import QueryBuilder from './QueryBuilder';

// REQ-F78: Cache de pesquisas em memória (evita chamadas repetidas à API)
const searchCache = new Map();

export default function Search() {
  // REQ-F81: URL routing para pesquisas partilháveis
  const [searchParams, setSearchParams] = useSearchParams();

  const [query, setQuery] = useState(() => searchParams.get('q') || '');

  // REQ-F63, F64: Memória das configurações da Sidebar (Guardadas no localStorage)
  const [processing, setProcessing] = useState(() => searchParams.get('processing') || localStorage.getItem('pref_processing') || 'lemmatization');
  const [removeStopWords, setRemoveStopWords] = useState(() => localStorage.getItem('pref_removeStopWords') !== 'false');
  const [language, setLanguage] = useState(() => searchParams.get('lang') || localStorage.getItem('pref_language') || 'all');
  const [algorithm, setAlgorithm] = useState(() => searchParams.get('algo') || localStorage.getItem('pref_algorithm') || 'custom');

  // Persistir as preferências acima automaticamente quando mudam
  useEffect(() => {
    localStorage.setItem('pref_processing', processing);
    localStorage.setItem('pref_removeStopWords', removeStopWords);
    localStorage.setItem('pref_language', language);
    localStorage.setItem('pref_algorithm', algorithm);
  }, [processing, removeStopWords, language, algorithm]);

  // Estados para o âmbito da pesquisa
  const [searchTarget, setSearchTarget] = useState('all');
  const [researchArea, setResearchArea] = useState('all');

  // REQ-F43 a F46: Filtros avançados
  const [yearStart, setYearStart] = useState('');
  const [yearEnd, setYearEnd] = useState('');
  const [docType, setDocType] = useState('all'); // REQ-F44
  const [selectedKeyword, setSelectedKeyword] = useState('all'); // REQ-F45
  const [facetsKeywords, setFacetsKeywords] = useState([]); // Guarda as keywords para facetas

  // REQ-F39 a F42: Construtor visual de queries
  const [showQueryBuilder, setShowQueryBuilder] = useState(false);

  // REQ-F59 a F62: Histórico e Pesquisas Guardadas
  const [showHistoryPanel, setShowHistoryPanel] = useState(false);
  const [searchHistory, setSearchHistory] = useState(() => JSON.parse(localStorage.getItem('repositorium_query_history') || '[]'));
  const [savedSearches, setSavedSearches] = useState(() => JSON.parse(localStorage.getItem('repositorium_saved_queries') || '[]'));

  // Painel de Documentos Guardados
  const [showSavedDocsPanel, setShowSavedDocsPanel] = useState(false);

  // Modo de pesquisa por autor
  const [authorMode, setAuthorMode] = useState(false);

  // REQ-F08, F10: Autocompletar & Validação
  const [queryError, setQueryError] = useState('');

  // REQ-F67, F69, F70: Páginas de ajuda e Tour Guiado
  const [showHelp, setShowHelp] = useState(() => localStorage.getItem('tour_done') !== 'true');

  const [suggestions, setSuggestions] = useState([]);
  const [showAutocomplete, setShowAutocomplete] = useState(false);
  const [activeIndex, setActiveIndex] = useState(-1); // REQ-F87: navegação por teclado
  const debounceRef = useRef(null); // REQ-F85: debounce timer

  const handleQueryChange = (e) => {
    const val = e.target.value;
    setQuery(val);
    setActiveIndex(-1);

    // REQ-F85: Debounce no autocomplete (300ms) para não atualizar em cada tecla
    clearTimeout(debounceRef.current);
    debounceRef.current = setTimeout(() => {
      if (val.trim().length > 1) {
        const matches = searchHistory
          .map(h => h.query)
          .filter(q => q.toLowerCase().includes(val.toLowerCase()) && q !== val)
          .filter((value, index, self) => self.indexOf(value) === index)
          .slice(0, 5);
        setSuggestions(matches);
        setShowAutocomplete(matches.length > 0);
      } else {
        setShowAutocomplete(false);
      }
    }, 300);

    // Validação Booleana em tempo real (F10) - sem debounce para feedback imediato
    let error = '';
    const openParens = (val.match(/\(/g) || []).length;
    const closeParens = (val.match(/\)/g) || []).length;
    if (openParens !== closeParens) {
      error = '⚠️ Erro de sintaxe: Parênteses desbalanceados.';
    } else if (/\b(AND|OR|NOT)\s*$/i.test(val)) {
      error = '⚠️ Expressão incompleta (termina num operador lógico).';
    } else if (/\b(AND|OR|NOT)\s+(AND|OR)\b/i.test(val)) {
      error = '⚠️ Operadores booleanos seguidos inválidos.';
    }
    setQueryError(error);
  };

  // REQ-F87: Navegar no dropdown com setas e selecionar com Enter
  const handleKeyDown = (e) => {
    if (!showAutocomplete) return;
    if (e.key === 'ArrowDown') {
      e.preventDefault();
      setActiveIndex(i => Math.min(i + 1, suggestions.length - 1));
    } else if (e.key === 'ArrowUp') {
      e.preventDefault();
      setActiveIndex(i => Math.max(i - 1, -1));
    } else if (e.key === 'Enter' && activeIndex >= 0) {
      e.preventDefault();
      setQuery(suggestions[activeIndex]);
      setShowAutocomplete(false);
      setActiveIndex(-1);
      setQueryError('');
    } else if (e.key === 'Escape') {
      setShowAutocomplete(false);
      setActiveIndex(-1);
    }
  };

  // Esquema de pesos alinhados com o algoritmo escolhido
  const [weightingScheme, setWeightingScheme] = useState('ltc');

  // API e Resultados
  const [results, setResults] = useState([]); // Vai guardar os documentos que vêm do Backend
  const [isLoading, setIsLoading] = useState(false); // Controla se mostramos "A carregar..."
  const [error, setError] = useState(null); // Guarda mensagens de erro se a API falhar

  // REQ-F65, F66: User Session e Preferências de Interface
  const [showPrefsModal, setShowPrefsModal] = useState(false);
  const [userPrefs, setUserPrefs] = useState(() => {
    return JSON.parse(localStorage.getItem('repositorium_user_prefs')) || {
      username: 'Convidado',
      compactMode: false,
      resultsPerPage: 10
    };
  });

  // Atualiza LocalStorage sempre que userPrefs mudar
  useEffect(() => {
    localStorage.setItem('repositorium_user_prefs', JSON.stringify(userPrefs));
  }, [userPrefs]);

  // REQ-F81: Se a página carregar com ?q=... na URL, dispara a pesquisa automaticamente
  useEffect(() => {
    const urlQuery = searchParams.get('q');
    if (urlQuery && urlQuery.trim()) {
      executeSearch(1, 'relevance');
    }
  // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []); // Só corre uma vez no mount

  // Paginação e Ordenação
  const [currentPage, setCurrentPage] = useState(1);
  const [sortOption, setSortOption] = useState('relevance');
  const [totalResults, setTotalResults] = useState(0); // Total de resultados da API
  const [searchTime, setSearchTime] = useState(null);  // Tempo real de pesquisa (vem da API)

  // --- ESTADOS DAS AÇÕES DOS RESULTADOS ---
  const [abstractModal, setAbstractModal] = useState(null); // { title, abstract, authors, year } ou null
  const [savedDocs, setSavedDocs] = useState(() => {
    // Lê a memória do Chrome ao iniciar a página
    const saved = localStorage.getItem('repositorium_saved');
    return saved ? JSON.parse(saved) : [];
  });

  // --- FUNÇÕES DE AÇÃO NOS DOCUMENTOS ---

  // 1. Ver Resumo — abre modal com o abstract completo
  const openAbstractModal = (doc) => {
    setAbstractModal(doc);
  };
  const closeAbstractModal = () => setAbstractModal(null);

  // Utilitário: Destaca os termos da query no texto (para quando o backend não enviou <b>)
  const highlightQuery = (text, q) => {
    if (!text || !q) return text || '';
    const rawTerms = q.split(/\W+/).filter(t => t && !['AND','OR','NOT'].includes(t.toUpperCase()));
    if (!rawTerms.length) return text;
    const pattern = new RegExp(`(${rawTerms.map(t => t.replace(/[.*+?^${}()|[\]\\]/g, '\\$&')).join('|')})`, 'gi');
    return text.replace(pattern, '<b>$1</b>');
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

    // REQ-F81: Atualiza a URL com os parâmetros da pesquisa (permite partilhar o link)
    setSearchParams({
      q: query,
      algo: algorithm,
      processing,
      lang: language,
      ...(page > 1 ? { page: String(page) } : {})
    });

    const params = new URLSearchParams({
      q: query,
      lang: language,
      processing: processing,
      stop_words: removeStopWords,
      algo: algorithm,
      target: searchTarget,
      area: researchArea,
      doc_type: docType,
      keyword: selectedKeyword,
      author_mode: authorMode,
      sort_by: sort,
      page: page,
      page_size: userPrefs.resultsPerPage
    });

    if (algorithm === 'custom') params.append('weights', weightingScheme);
    if (yearStart) params.append('year_start', yearStart);
    if (yearEnd) params.append('year_end', yearEnd);

    // REQ-F78: Verificar se já existe no cache antes de chamar a API
    const cacheKey = params.toString();
    if (searchCache.has(cacheKey)) {
      const cached = searchCache.get(cacheKey);
      setResults(cached.results || []);
      setTotalResults(cached.metadata?.total || 0);
      setSearchTime(cached.metadata?.time ?? null);
      setFacetsKeywords(cached.metadata?.facets?.keywords || []);
      setCurrentPage(page);
      setSortOption(sort);
      setIsLoading(false);
      return;
    }

    try {
      const response = await fetch(`http://localhost:8000/search?${cacheKey}`);
      if (!response.ok) throw new Error(`Erro do servidor: ${response.status}`);
      const data = await response.json();

      // Guardar no cache (máx. 50 entradas para não encher a memória)
      if (searchCache.size >= 50) searchCache.delete(searchCache.keys().next().value);
      searchCache.set(cacheKey, data);

      setResults(data.results || []);
      setTotalResults(data.metadata?.total || 0);
      setSearchTime(data.metadata?.time ?? null);
      setFacetsKeywords(data.metadata?.facets?.keywords || []);
      setCurrentPage(page);
      setSortOption(sort);

      // REQ-F59: Registar no histórico
      if (page === 1 && query.trim()) {
        const historyItem = { id: Date.now(), query, date: new Date().toLocaleString(), algorithm, docType, total: data.metadata?.total || 0 };
        const filteredHistory = searchHistory.filter(h => h.query !== query);
        const newHistory = [historyItem, ...filteredHistory].slice(0, 50);
        setSearchHistory(newHistory);
        localStorage.setItem('repositorium_query_history', JSON.stringify(newHistory));
      }

    } catch (err) {
      console.error('Erro na pesquisa:', err);
      setError('Não foi possível ligar ao servidor. Verifica se a API está a correr na porta 8000.');
    } finally {
      setIsLoading(false);
    }
  };

  // Funções REQ-F60, F61, F62
  const handleSaveSearch = (historyItem) => {
    const name = prompt("Atribui um nome a esta pesquisa (ex: IA na Saúde):", historyItem.query);
    if (!name) return;
    const collectionName = prompt("Em que coleção queres guardar? (ex: Tese, Pessoal, Geral)", "Geral");

    const newSaved = [...savedSearches, { ...historyItem, name, collection: collectionName || 'Geral' }];
    setSavedSearches(newSaved);
    localStorage.setItem('repositorium_saved_queries', JSON.stringify(newSaved));
    alert(`Pesquisa '${name}' guardada na coleção '${collectionName || 'Geral'}'!`);
  };

  const handleExportHistory = () => {
    const blob = new Blob([JSON.stringify(searchHistory, null, 2)], { type: 'application/json' });
    const link = document.createElement('a');
    link.href = URL.createObjectURL(blob);
    link.download = 'historico_pesquisas.json';
    link.click();
  };

  const loadSavedSearch = (savedItem) => {
    setQuery(savedItem.query);
    setAlgorithm(savedItem.algorithm || 'custom');
    setDocType(savedItem.docType || 'all');
    setShowHistoryPanel(false);
    // Dispara a pesquisa diretamente com os valores atualizados
    setTimeout(() => executeSearch(1, 'relevance'), 50);
  };

  const handleSearch = async (e) => {
    e.preventDefault();
    executeSearch(1, sortOption);
  };

  // 1. Paginação Total (vinda do backend)
  const totalPages = Math.ceil(totalResults / userPrefs.resultsPerPage);
  const currentResults = results;

  return (
    <div className="search-page">
      <div className="search-container">
        <h2>Pesquisar na Coleção <span style={{ fontSize: '1rem', color: '#6b7280', fontWeight: 'normal' }}>(Sessão: {userPrefs.username})</span></h2>
        <form onSubmit={handleSearch} className="search-form-wrapper">
          <div className="search-main-row">
            <div style={{ flex: 1, display: 'flex', flexDirection: 'column', position: 'relative' }}>
              <input
                id="search-query-input"
                type="text"
                className="search-input"
                placeholder="Ex: machine learning AND (health OR medicine)"
                value={query}
                onChange={handleQueryChange}
                onKeyDown={handleKeyDown}
                onFocus={() => { if (suggestions.length > 0) setShowAutocomplete(true); }}
                onBlur={() => setTimeout(() => setShowAutocomplete(false), 200)}
                style={{ width: '100%', borderColor: queryError ? '#f87171' : '#d1d5db', boxSizing: 'border-box' }}
                aria-label="Caixa de pesquisa de documentos"
                aria-autocomplete="list"
                aria-controls={showAutocomplete ? 'autocomplete-list' : undefined}
                aria-activedescendant={activeIndex >= 0 ? `suggestion-${activeIndex}` : undefined}
                aria-invalid={!!queryError}
                aria-describedby={queryError ? 'query-error-msg' : undefined}
                autoComplete="off"
              />

              {showAutocomplete && (
                <div
                  id="autocomplete-list"
                  role="listbox"
                  aria-label="Sugestões de pesquisa"
                  style={{ position: 'absolute', top: '100%', left: 0, right: 0, background: 'white', border: '1px solid #e5e7eb', borderRadius: '8px', boxShadow: '0 10px 15px -3px rgba(0,0,0,0.1)', zIndex: 50, marginTop: '5px', overflow: 'hidden' }}>
                  <ul style={{ listStyle: 'none', margin: 0, padding: 0, textAlign: 'left' }}>
                    {suggestions.map((sug, idx) => (
                      <li
                        id={`suggestion-${idx}`}
                        key={idx}
                        role="option"
                        aria-selected={activeIndex === idx}
                        onClick={() => { setQuery(sug); setShowAutocomplete(false); setActiveIndex(-1); setQueryError(''); }}
                        style={{ padding: '12px 20px', cursor: 'pointer', borderBottom: '1px solid #f3f4f6', color: '#374151', display: 'flex', alignItems: 'center', gap: '10px', background: activeIndex === idx ? '#eff6ff' : 'white' }}
                      >
                        <span style={{ color: '#9ca3af' }}>🕒</span> {sug}
                      </li>
                    ))}
                  </ul>
                </div>
              )}

              {queryError && (
                <span
                  id="query-error-msg"
                  role="alert"
                  aria-live="polite"
                  style={{ position: 'absolute', top: '100%', left: '15px', color: '#dc2626', fontSize: '0.8rem', marginTop: '4px', fontWeight: 'bold', zIndex: 10 }}>
                  {queryError}
                </span>
              )}
            </div>
            <button type="submit" className="search-button">Pesquisar</button>
          </div>

          <div className="search-actions-row">
            <button
              type="button"
              onClick={() => setShowQueryBuilder(v => !v)}
              style={{
                padding: '12px 18px', borderRadius: '25px',
                background: showQueryBuilder ? '#1d4ed8' : '#f3f4f6',
                color: showQueryBuilder ? 'white' : '#374151',
                border: '1px solid #d1d5db', cursor: 'pointer',
                fontWeight: '600', transition: '0.2s', fontSize: '0.9rem'
              }}
              title="Construtor Visual de Queries Booleanas"
            >
              🧩 Builder
            </button>
            <button
              type="button"
              onClick={() => setShowHistoryPanel(v => !v)}
              style={{
                padding: '12px 18px', borderRadius: '25px',
                background: showHistoryPanel ? '#10b981' : '#f3f4f6',
                color: showHistoryPanel ? 'white' : '#374151',
                border: '1px solid #d1d5db', cursor: 'pointer',
                fontWeight: '600', transition: '0.2s', fontSize: '0.9rem'
              }}
              title="Histórico e Pesquisas Guardadas"
            >
              🕒 Histórico
            </button>
            <button
              type="button"
              onClick={() => setShowSavedDocsPanel(v => !v)}
              style={{
                padding: '12px 18px', borderRadius: '25px',
                background: showSavedDocsPanel ? '#ec4899' : '#f3f4f6',
                color: showSavedDocsPanel ? 'white' : '#374151',
                border: '1px solid #d1d5db', cursor: 'pointer',
                fontWeight: '600', transition: '0.2s', fontSize: '0.9rem'
              }}
              title="Ver Documentos Guardados"
            >
              ⭐ Guardados
            </button>
            <button
              type="button"
              onClick={() => setShowPrefsModal(v => !v)}
              style={{
                padding: '12px 18px', borderRadius: '25px',
                background: showPrefsModal ? '#6366f1' : '#f3f4f6',
                color: showPrefsModal ? 'white' : '#374151',
                border: '1px solid #d1d5db', cursor: 'pointer',
                fontWeight: '600', transition: '0.2s', fontSize: '0.9rem'
              }}
              title="Preferências de Utilizador"
            >
              ⚙️ Configurações
            </button>
            <button
              type="button"
              onClick={() => setShowHelp(true)}
              style={{
                padding: '12px 18px', borderRadius: '25px',
                background: showHelp ? '#eab308' : '#f3f4f6',
                color: showHelp ? 'white' : '#374151',
                border: showHelp ? '1px solid #ca8a04' : '1px solid #d1d5db', cursor: 'pointer',
                fontWeight: '600', transition: '0.2s', fontSize: '0.9rem'
              }}
              title="Guia e Ajuda (Tour)"
            >
              📖 Ajuda
            </button>
          </div>
        </form>
        <div className="search-tips">
          <small><strong>Dica:</strong> Podes usar operadores booleanos como <code>AND</code>, <code>OR</code> e <code>NOT</code>. Usa o 🧩 Builder para construir visualmente.</small>
        </div>

        {/* REQ-F67, F69, F70: Help and Documentation (Guided Tour) */}
        {showHelp && (
          <div style={{ position: 'fixed', top: 0, left: 0, right: 0, bottom: 0, background: 'rgba(0,0,0,0.5)', display: 'flex', alignItems: 'center', justifyContent: 'center', zIndex: 1000 }}>
            <div style={{ background: 'white', padding: '2rem', borderRadius: '12px', maxWidth: '650px', maxHeight: '85vh', overflowY: 'auto', textAlign: 'left', boxShadow: '0 20px 25px -5px rgba(0, 0, 0, 0.1)' }}>
              <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '1.5rem', borderBottom: '2px solid #f3f4f6', paddingBottom: '1rem' }}>
                <h2 style={{ color: '#111827', margin: 0 }}>👋 Bem-vindo ao RepositóriUM Search!</h2>
                <button onClick={() => { setShowHelp(false); localStorage.setItem('tour_done', 'true'); }} style={{ background: 'none', border: 'none', fontSize: '1.5rem', cursor: 'pointer' }}>✕</button>
              </div>

              <p style={{ color: '#4b5563', fontSize: '1.05rem', marginBottom: '1.5rem' }}>Este sistema permite-te pesquisar documentos académicos de forma avançada usando técnicas de processamento de linguagem natural (NLP).</p>

              <h3 style={{ color: '#1d4ed8' }}>🔍 Estratégias de Pesquisa</h3>
              <ul style={{ lineHeight: '1.8', color: '#374151', marginBottom: '1.5rem' }}>
                <li><strong>Pesquisa Simples:</strong> Escreve termos como <em>machine learning</em> e o sistema usa o TF-IDF para ordenar os resultados por relevância semântica.</li>
                <li><strong>Pesquisa Booleana:</strong> Usa parênteses e operadores lógicos (AND, OR, NOT) escritos em maiúsculas para criar filtros rigorosos.<br />Exemplo: <code>data AND (blockchain OR iot)</code></li>
                <li><strong>Exclusão:</strong> Usa o NOT para excluir documentos que contenham certos termos. Exemplo: <code>health NOT medicine</code></li>
              </ul>

              <h3 style={{ color: '#059669' }}>💡 Dicas Avançadas da Interface</h3>
              <ul style={{ lineHeight: '1.8', color: '#374151' }}>
                <li>Usa o <strong>🧩 Builder</strong> se não souberes como escrever a query booleana! Ele ajuda-te visualmente.</li>
                <li>No painel lateral esquerdo, podes mudar o motor de pesquisa (TF-IDF Scikit-Learn vs Booleano vs Custom) e ajustar configurações de texto como o Stemming ou remoção de Stop Words.</li>
                <li>Passa o rato pelos ícones <strong>(?)</strong> na barra lateral para obteres ajuda contextual sobre o que cada opção faz.</li>
              </ul>

              <div style={{ textAlign: 'center', marginTop: '2rem' }}>
                <button
                  onClick={() => { setShowHelp(false); localStorage.setItem('tour_done', 'true'); }}
                  style={{ padding: '12px 24px', background: '#AA192B', color: 'white', border: 'none', borderRadius: '8px', fontSize: '1.1rem', cursor: 'pointer', fontWeight: 'bold', boxShadow: '0 4px 6px -1px rgba(170, 25, 43, 0.4)' }}
                >
                  Entendido, vamos pesquisar!
                </button>
              </div>
            </div>
          </div>
        )}

        {/* REQ-F39 a F42: Construtor Visual de Queries */}
        {showQueryBuilder && (
          <div style={{ marginTop: '1rem', textAlign: 'left' }}>
            <QueryBuilder
              onQueryReady={(q) => {
                setQuery(q);
                // Se o algoritmo não for booleano, mudar para booleano automaticamente
                if (algorithm !== 'boolean') setAlgorithm('boolean');
                setShowQueryBuilder(false);
              }}
            />
          </div>
        )}

        {/* REQ-F59 a F62: Painel de Histórico e Coleções */}
        {showHistoryPanel && (
          <div style={{ marginTop: '1rem', textAlign: 'left', background: 'white', padding: '1.5rem', borderRadius: '12px', border: '1px solid #e5e7eb', boxShadow: '0 4px 15px rgba(0,0,0,0.05)' }}>
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '1rem', borderBottom: '2px solid #f3f4f6', paddingBottom: '10px' }}>
              <h3 style={{ margin: 0, color: '#111827' }}>🕒 O teu Histórico & Coleções</h3>
              <button onClick={handleExportHistory} style={{ padding: '6px 12px', background: '#e0f2fe', color: '#0369a1', border: '1px solid #bae6fd', borderRadius: '6px', cursor: 'pointer', fontWeight: 'bold' }}>📤 Exportar Histórico (JSON)</button>
            </div>

            <div style={{ display: 'flex', gap: '2rem', flexWrap: 'wrap' }}>

              {/* Pesquisas Recentes (REQ-F59) */}
              <div style={{ flex: '1 1 300px' }}>
                <h4 style={{ color: '#4b5563', marginBottom: '10px' }}>Últimas Pesquisas</h4>
                {searchHistory.length === 0 ? <p style={{ fontSize: '0.9rem', color: '#9ca3af' }}>Nenhum histórico disponível.</p> : (
                  <ul style={{ listStyle: 'none', padding: 0, margin: 0, display: 'flex', flexDirection: 'column', gap: '8px' }}>
                    {searchHistory.slice(0, 5).map(h => (
                      <li key={h.id} style={{ background: '#f9fafb', padding: '10px', borderRadius: '8px', border: '1px solid #f3f4f6', display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                        <div>
                          <div style={{ fontWeight: '600', color: '#1f2937' }}>{h.query}</div>
                          <div style={{ fontSize: '0.8rem', color: '#6b7280' }}>{h.date} • {h.total} resultados</div>
                        </div>
                        <div style={{ display: 'flex', gap: '5px' }}>
                          <button onClick={() => loadSavedSearch(h)} style={{ padding: '4px 8px', background: '#dbeafe', color: '#1d4ed8', border: 'none', borderRadius: '4px', cursor: 'pointer', fontSize: '0.8rem' }}>🔄 Refazer</button>
                          <button onClick={() => handleSaveSearch(h)} style={{ padding: '4px 8px', background: '#fef08a', color: '#854d0e', border: 'none', borderRadius: '4px', cursor: 'pointer', fontSize: '0.8rem' }}>⭐ Guardar</button>
                        </div>
                      </li>
                    ))}
                  </ul>
                )}
              </div>

              {/* Coleções Guardadas (REQ-F60, F61) */}
              <div style={{ flex: '1 1 300px' }}>
                <h4 style={{ color: '#4b5563', marginBottom: '10px' }}>Coleções Pessoais (Guardadas)</h4>
                {savedSearches.length === 0 ? <p style={{ fontSize: '0.9rem', color: '#9ca3af' }}>Nenhuma pesquisa guardada ainda.</p> : (
                  <div style={{ display: 'flex', flexDirection: 'column', gap: '10px' }}>
                    {/* Agrupar por coleção */}
                    {Object.entries(savedSearches.reduce((acc, curr) => {
                      (acc[curr.collection] = acc[curr.collection] || []).push(curr);
                      return acc;
                    }, {})).map(([colName, items]) => (
                      <div key={colName} style={{ background: '#fdf4ff', padding: '10px', borderRadius: '8px', border: '1px solid #fce7f3' }}>
                        <div style={{ fontWeight: 'bold', color: '#9d174d', marginBottom: '5px', fontSize: '0.9rem' }}>📁 Coleção: {colName}</div>
                        <ul style={{ listStyle: 'none', padding: 0, margin: 0, display: 'flex', flexDirection: 'column', gap: '5px' }}>
                          {items.map(s => (
                            <li key={s.id} style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', background: 'white', padding: '6px 10px', borderRadius: '6px', border: '1px solid #fbcfe8' }}>
                              <div>
                                <div style={{ fontWeight: '600', color: '#831843', fontSize: '0.95rem' }}>{s.name}</div>
                                <div style={{ fontSize: '0.8rem', color: '#be185d' }}>Query: <em>{s.query}</em></div>
                              </div>
                              <button onClick={() => loadSavedSearch(s)} style={{ padding: '4px 8px', background: '#fbcfe8', color: '#9d174d', border: 'none', borderRadius: '4px', cursor: 'pointer', fontSize: '0.8rem' }}>🔄 Carregar</button>
                            </li>
                          ))}
                        </ul>
                      </div>
                    ))}
                  </div>
                )}
              </div>

            </div>
          </div>
        )}

        {/* Painel de Documentos Guardados */}
        {showSavedDocsPanel && (
          <div style={{ marginTop: '1rem', textAlign: 'left', background: 'white', padding: '1.5rem', borderRadius: '12px', border: '1px solid #e5e7eb', boxShadow: '0 4px 15px rgba(0,0,0,0.05)' }}>
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '1rem', borderBottom: '2px solid #f3f4f6', paddingBottom: '10px' }}>
              <h3 style={{ margin: 0, color: '#111827' }}>⭐ Os Teus Documentos Guardados</h3>
              <button onClick={() => {
                const blob = new Blob([JSON.stringify(savedDocs, null, 2)], { type: 'application/json' });
                const link = document.createElement('a'); link.href = URL.createObjectURL(blob); link.download = 'documentos_guardados.json'; link.click();
              }} style={{ padding: '6px 12px', background: '#fce7f3', color: '#be185d', border: '1px solid #fbcfe8', borderRadius: '6px', cursor: 'pointer', fontWeight: 'bold' }}>📤 Exportar (JSON)</button>
            </div>

            {savedDocs.length === 0 ? (
              <p style={{ color: '#6b7280' }}>Ainda não guardaste nenhum documento. Clica em "⭐ Guardar" nos resultados da pesquisa para os veres aqui!</p>
            ) : (
              <ul style={{ listStyle: 'none', padding: 0, margin: 0, display: 'flex', flexDirection: 'column', gap: '10px' }}>
                {savedDocs.map((doc, idx) => (
                  <li key={idx} style={{ background: '#f9fafb', padding: '15px', borderRadius: '8px', border: '1px solid #e5e7eb', display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start' }}>
                    <div>
                      <h4 style={{ margin: '0 0 8px 0', fontSize: '1.05rem' }}>
                        <a href={doc.url || doc.handle || "#"} target="_blank" rel="noreferrer" style={{ textDecoration: 'none', color: '#1d4ed8' }} dangerouslySetInnerHTML={{ __html: doc.title || 'Documento sem título' }} />
                      </h4>
                      <p style={{ margin: 0, fontSize: '0.85rem', color: '#4b5563' }}>👤 {doc.authors ? (Array.isArray(doc.authors) ? doc.authors.join(', ') : doc.authors) : doc.author} • 📅 {doc.date || doc.year}</p>
                    </div>
                    <button onClick={() => toggleSave(doc)} style={{ background: 'none', border: 'none', color: '#ef4444', cursor: 'pointer', fontSize: '1.2rem', padding: '5px' }} title="Remover dos guardados">✕</button>
                  </li>
                ))}
              </ul>
            )}
          </div>
        )}

        {/* REQ-F63 a F66: Painel de Preferências do Utilizador */}
        {showPrefsModal && (
          <div style={{ marginTop: '1rem', textAlign: 'left', background: 'white', padding: '1.5rem', borderRadius: '12px', border: '1px solid #e5e7eb', boxShadow: '0 4px 15px rgba(0,0,0,0.05)' }}>
            <div style={{ borderBottom: '2px solid #f3f4f6', paddingBottom: '10px', marginBottom: '15px' }}>
              <h3 style={{ margin: 0, color: '#111827' }}>⚙️ Preferências da Conta</h3>
            </div>

            <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(250px, 1fr))', gap: '20px' }}>

              {/* Sessão (REQ-F66) */}
              <div className="filter-group">
                <label className="filter-label">👤 Nome de Utilizador (Sessão)</label>
                <input
                  type="text"
                  value={userPrefs.username}
                  onChange={e => setUserPrefs({ ...userPrefs, username: e.target.value })}
                  className="filter-select"
                  style={{ width: '100%', boxSizing: 'border-box' }}
                />
              </div>

              {/* Display Options (REQ-F65) */}
              <div className="filter-group">
                <label className="filter-label">📄 Resultados por Página</label>
                <select
                  value={userPrefs.resultsPerPage}
                  onChange={e => setUserPrefs({ ...userPrefs, resultsPerPage: Number(e.target.value) })}
                  className="filter-select"
                  style={{ width: '100%' }}
                >
                  <option value={5}>5 Resultados</option>
                  <option value={10}>10 Resultados</option>
                  <option value={20}>20 Resultados</option>
                  <option value={50}>50 Resultados</option>
                </select>
              </div>

              <div className="filter-group" style={{ display: 'flex', alignItems: 'center' }}>
                <label className="checkbox-label" style={{ fontWeight: 'bold' }}>
                  <input
                    type="checkbox"
                    checked={userPrefs.compactMode}
                    onChange={e => setUserPrefs({ ...userPrefs, compactMode: e.target.checked })}
                  />
                  Modo de Visualização Compacta
                </label>
              </div>

              <div className="filter-group" style={{ display: 'flex', alignItems: 'center' }}>
                <p style={{ fontSize: '0.85rem', color: '#6b7280', margin: 0 }}>
                  <em>Nota: As tuas opções da Barra Lateral (Idioma, Stop Words, Algoritmo) também são guardadas automaticamente na tua sessão.</em>
                </p>
              </div>
            </div>
          </div>
        )}

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
              Área: <strong>{{
                'AI & Robotics': 'IA & Robótica',
                'General Engineering': 'Engenharia Geral',
                'Systems & Tech': 'Sistemas e Tecnologia',
                'Education & Society': 'Educação e Sociedade',
                'Data Science': 'Ciência de Dados'
              }[researchArea] || researchArea}</strong>
            </span>
          )}
          {docType !== 'all' && (
            <span style={{ background: '#f5f3ff', color: '#6d28d9', padding: '4px 12px', borderRadius: '20px', fontSize: '0.85rem', border: '1px solid #ddd6fe' }}>
              Tipo: <strong>{docType === 'phd' ? 'Tese (PhD)' : docType === 'msc' ? 'Dissertação (MSc)' : 'Artigo Científico'}</strong>
            </span>
          )}
          {selectedKeyword !== 'all' && (
            <span style={{ background: '#fdf4ff', color: '#a21caf', padding: '4px 12px', borderRadius: '20px', fontSize: '0.85rem', border: '1px solid #fbcfe8' }}>
              Keyword: <strong>{selectedKeyword}</strong>
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
          {(yearStart || yearEnd) && (
            <span style={{ background: '#eff6ff', color: '#1e40af', padding: '4px 12px', borderRadius: '20px', fontSize: '0.85rem', border: '1px solid #bfdbfe' }}>
              📅 <strong>{yearStart || '…'} – {yearEnd || '…'}</strong>
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
              <label className="filter-label">Área de Investigação: <span data-tooltip="Filtra resultados apenas para a área académica selecionada." className="tooltip-icon">?</span></label>
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

            {/* REQ-F44: Tipo de Documento */}
            <div className="filter-group">
              <label className="filter-label">Tipo de Documento: <span data-tooltip="Limita os resultados a teses, dissertações ou artigos." className="tooltip-icon">?</span></label>
              <select
                className="filter-select"
                value={docType}
                onChange={(e) => setDocType(e.target.value)}
              >
                <option value="all">Todos os Tipos</option>
                <option value="article">Artigo Científico</option>
                <option value="msc">Dissertação (MSc)</option>
                <option value="phd">Tese (PhD)</option>
              </select>
            </div>

            {/* REQ-F43 a F46: Filtro por intervalo de datas */}
            <div className="filter-group">
              <label className="filter-label">📅 Intervalo de Anos:</label>
              <div style={{ display: 'flex', gap: '8px', alignItems: 'center' }}>
                <input
                  id="year-start-input"
                  type="number"
                  className="filter-select"
                  style={{ width: '85px', padding: '8px' }}
                  placeholder="De"
                  min="1900"
                  max="2030"
                  value={yearStart}
                  onChange={(e) => setYearStart(e.target.value)}
                />
                <span style={{ color: '#9ca3af' }}>–</span>
                <input
                  id="year-end-input"
                  type="number"
                  className="filter-select"
                  style={{ width: '85px', padding: '8px' }}
                  placeholder="Até"
                  min="1900"
                  max="2030"
                  value={yearEnd}
                  onChange={(e) => setYearEnd(e.target.value)}
                />
                {(yearStart || yearEnd) && (
                  <button
                    onClick={() => { setYearStart(''); setYearEnd(''); }}
                    style={{ background: 'none', border: 'none', color: '#AA192B', cursor: 'pointer', fontSize: '1.1rem', padding: '0', lineHeight: 1 }}
                    title="Limpar filtro de datas"
                  >✕</button>
                )}
              </div>
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

          {/* SECÇÃO: Facetas (REQ-F45) */}
          <div className="sidebar-section">
            <h3>Palavras-Chave (Facetas)</h3>
            {facetsKeywords.length > 0 ? (
              <div style={{ display: 'flex', flexDirection: 'column', gap: '6px' }}>
                <button
                  onClick={() => setSelectedKeyword('all')}
                  style={{
                    textAlign: 'left',
                    background: selectedKeyword === 'all' ? '#f3f4f6' : 'transparent',
                    border: 'none',
                    padding: '4px 8px',
                    borderRadius: '4px',
                    cursor: 'pointer',
                    fontWeight: selectedKeyword === 'all' ? 'bold' : 'normal',
                    color: '#374151'
                  }}
                >
                  Todas as Keywords
                </button>
                {facetsKeywords.map((kw) => (
                  <button
                    key={kw.keyword}
                    onClick={() => setSelectedKeyword(kw.keyword)}
                    style={{
                      textAlign: 'left',
                      background: selectedKeyword === kw.keyword ? '#fdf4ff' : 'transparent',
                      border: 'none',
                      padding: '4px 8px',
                      borderRadius: '4px',
                      cursor: 'pointer',
                      display: 'flex',
                      justifyContent: 'space-between',
                      alignItems: 'center',
                      color: selectedKeyword === kw.keyword ? '#a21caf' : '#4b5563',
                      fontWeight: selectedKeyword === kw.keyword ? 'bold' : 'normal',
                    }}
                    title={kw.keyword}
                  >
                    <span style={{ textOverflow: 'ellipsis', overflow: 'hidden', whiteSpace: 'nowrap', maxWidth: '140px' }}>
                      {kw.keyword}
                    </span>
                    <span style={{ background: '#e5e7eb', padding: '2px 6px', borderRadius: '10px', fontSize: '0.75rem', color: '#374151' }}>
                      {kw.count}
                    </span>
                  </button>
                ))}
              </div>
            ) : (
              <p style={{ fontSize: '0.85rem', color: '#6b7280' }}>Faz uma pesquisa para ver as keywords.</p>
            )}
          </div>

          <hr className="sidebar-divider" />
          {/* SECÇÃO 1: Processamento de Texto */}
          <div className="sidebar-section">
            <h3>Processamento de Texto</h3>

            <div className="filter-group">
              <label className="filter-label">Idioma: <span data-tooltip="Processa apenas documentos do idioma selecionado." className="tooltip-icon">?</span></label>
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
              <label className="filter-label">Técnica: <span data-tooltip="Stemming corta as palavras pela raiz (mais rápido). Lematização usa dicionário para base correta." className="tooltip-icon">?</span></label>
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
                  <span style={{ fontSize: '0.85em', color: '#9ca3af', marginLeft: '8px' }}>
                    ({searchTime !== null ? `${searchTime.toFixed(3)} segundos` : '...'})
                  </span>
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
                    <div key={docUniqueId} style={{ padding: userPrefs.compactMode ? '10px' : '20px', background: '#fff', border: '1px solid #e5e7eb', borderRadius: '8px', boxShadow: '0 4px 6px -1px rgba(0, 0, 0, 0.05)' }}>

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
                        {item.doc_type && (
                          <span style={{ color: '#6d28d9', background: '#f5f3ff', padding: '2px 8px', borderRadius: '12px', fontSize: '0.8rem', border: '1px solid #ddd6fe' }}>
                            {item.doc_type === 'phd' ? '🎓 Tese (PhD)' : item.doc_type === 'msc' ? '🎓 Dissertação (MSc)' : '📄 Artigo Científico'}
                          </span>
                        )}
                      </div>

                      {/* Keywords */}
                      {item.keywords && item.keywords.length > 0 && (
                        <div style={{ marginBottom: '15px', display: 'flex', gap: '8px', flexWrap: 'wrap' }}>
                          {item.keywords.map(kw => (
                            <span key={kw} style={{ background: '#fdf4ff', color: '#a21caf', padding: '2px 8px', borderRadius: '12px', fontSize: '0.75rem', border: '1px solid #fbcfe8' }}>
                              {kw}
                            </span>
                          ))}
                        </div>
                      )}

                      {/* F26 e F27: Snippet com highlighting dos termos da query */}
                      <p
                        className="highlight-backend"
                        style={{
                          color: '#4b5563',
                          fontSize: '0.95rem',
                          lineHeight: '1.6',
                          marginBottom: '20px',
                          display: '-webkit-box',
                          WebkitLineClamp: 3,
                          WebkitBoxOrient: 'vertical',
                          overflow: 'hidden'
                        }}
                        dangerouslySetInnerHTML={{
                          __html: (() => {
                            const snippetHtml = item.snippet || item.description || '';
                            // Se o snippet já tem <b> (destacado pelo backend), usa-o diretamente
                            // Se não tem <b>, destaca no frontend com a query atual
                            if (snippetHtml.includes('<b>')) return snippetHtml;
                            return highlightQuery(snippetHtml, query);
                          })()
                        }}
                      />

                      {/* Ações nos Resultados */}
                      <div style={{ display: 'flex', gap: '10px', flexWrap: 'wrap' }}>

                        {/* Botão Ver Resumo — abre modal com abstract completo */}
                        <button
                          onClick={() => openAbstractModal(item)}
                          style={{ padding: '8px 16px', background: '#f3f4f6', color: '#374151', border: '1px solid #d1d5db', borderRadius: '6px', cursor: 'pointer', fontWeight: '500', transition: '0.2s' }}
                        >
                          👁️ Ver Resumo
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
          ) : query.trim() ? (
            /* Zero resultados após pesquisa */
            <div style={{ textAlign: 'center', color: '#6b7280', padding: '3rem' }}>
              <span style={{ fontSize: '3rem' }}>🔍</span>
              <p style={{ fontWeight: 'bold', fontSize: '1.2rem', marginTop: '1rem' }}>Nenhum resultado encontrado para <em>"{query}"</em>.</p>
              <p style={{ fontSize: '0.95rem' }}>Tenta mudar os filtros ou usa termos mais genéricos.</p>
            </div>
          ) : (
            /* Estado Vazio Inicial */
            <div style={{ textAlign: 'center', color: '#9ca3af' }}>
              <span style={{ fontSize: '3rem' }}>📚</span>
              <p style={{ marginTop: '1rem' }}>Faz uma pesquisa para veres os resultados aqui.</p>
            </div>
          )}
        </section>
      </div>

      {/* Modal de Resumo / Abstract */}
      {abstractModal && (
        <div
          onClick={closeAbstractModal}
          style={{
            position: 'fixed', top: 0, left: 0, right: 0, bottom: 0,
            background: 'rgba(0,0,0,0.55)', backdropFilter: 'blur(4px)',
            display: 'flex', alignItems: 'center', justifyContent: 'center',
            zIndex: 2000, padding: '1rem'
          }}
        >
          <div
            onClick={e => e.stopPropagation()}
            style={{
              background: 'white', borderRadius: '16px',
              boxShadow: '0 25px 50px -12px rgba(0,0,0,0.35)',
              maxWidth: '720px', width: '100%',
              maxHeight: '85vh', display: 'flex', flexDirection: 'column',
              overflow: 'hidden'
            }}
          >
            {/* Cabeçalho do modal */}
            <div style={{
              background: 'linear-gradient(135deg, #AA192B 0%, #7f1220 100%)',
              padding: '1.5rem 2rem',
              display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start',
              gap: '1rem'
            }}>
              <div style={{ flex: 1 }}>
                <div style={{ color: 'rgba(255,255,255,0.7)', fontSize: '0.8rem', fontWeight: '600', letterSpacing: '0.05em', textTransform: 'uppercase', marginBottom: '8px' }}>
                  📄 Resumo / Abstract
                </div>
                <h2
                  style={{ color: 'white', margin: 0, fontSize: '1.15rem', lineHeight: '1.5', fontWeight: '700' }}
                  dangerouslySetInnerHTML={{ __html: abstractModal.title || 'Documento sem título' }}
                />
                <div style={{ color: 'rgba(255,255,255,0.8)', fontSize: '0.88rem', marginTop: '10px', display: 'flex', gap: '16px', flexWrap: 'wrap' }}>
                  <span>👤 {abstractModal.authors ? (Array.isArray(abstractModal.authors) ? abstractModal.authors.join(', ') : abstractModal.authors) : 'Desconhecido'}</span>
                  <span>📅 {abstractModal.year || 'N/D'}</span>
                </div>
              </div>
              <button
                onClick={closeAbstractModal}
                style={{
                  background: 'rgba(255,255,255,0.15)', border: 'none',
                  color: 'white', borderRadius: '8px', cursor: 'pointer',
                  width: '36px', height: '36px', fontSize: '1.1rem',
                  display: 'flex', alignItems: 'center', justifyContent: 'center',
                  flexShrink: 0, transition: '0.2s'
                }}
                title="Fechar"
              >✕</button>
            </div>

            {/* Corpo do modal — abstract */}
            <div style={{ overflowY: 'auto', padding: '2rem', flex: 1 }}>
              {abstractModal.abstract ? (
                <p style={{
                  color: '#374151', fontSize: '0.98rem', lineHeight: '1.8',
                  margin: 0, textAlign: 'justify'
                }}>
                  {abstractModal.abstract}
                </p>
              ) : (
                <p style={{ color: '#9ca3af', fontStyle: 'italic' }}>
                  Resumo não disponível para este documento.
                </p>
              )}
            </div>

            {/* Rodapé do modal */}
            {(abstractModal.url && abstractModal.url !== 'N/A') && (
              <div style={{
                padding: '1rem 2rem',
                borderTop: '1px solid #f3f4f6',
                display: 'flex', justifyContent: 'flex-end', gap: '10px'
              }}>
                <a
                  href={abstractModal.url}
                  target="_blank"
                  rel="noreferrer"
                  style={{
                    padding: '8px 20px', background: '#AA192B', color: 'white',
                    border: 'none', borderRadius: '8px', cursor: 'pointer',
                    fontWeight: '600', textDecoration: 'none', fontSize: '0.95rem',
                    display: 'inline-flex', alignItems: 'center', gap: '6px'
                  }}
                >
                  📥 Abrir PDF
                </a>
              </div>
            )}
          </div>
        </div>
      )}
    </div>
  );
}