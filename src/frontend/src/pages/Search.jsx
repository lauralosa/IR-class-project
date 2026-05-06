import { useState } from 'react';
import './Search.css';

export default function Search() {
  const [query, setQuery] = useState('');

  const handleSearch = (e) => {
    e.preventDefault();
    console.log("A pesquisar por:", query);
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
        <aside className="sidebar-placeholder">
          <p>Sidebar de Filtros (Em breve)</p>
        </aside>
        <section className="results-placeholder">
          <p>Resultados da pesquisa aparecerão aqui.</p>
        </section>
      </div>
    </div>
  );
}