import React from 'react';
import { BrowserRouter, Routes, Route, Link } from 'react-router-dom';
import Search from './pages/Search';
import Author from './pages/Author';
import Admin from './pages/Admin';
import './App.css';

import logoUM from './assets/logo_um.png'; // Importa o logo


function App() {
  return (
    <BrowserRouter>
      <div className="app-container">
        <header className="header">
          <div className="logo-area" style={{ display: 'flex', alignItems: 'center', gap: '15px' }}>
            <img src={logoUM} alt="Logo UMinho" style={{ height: '40px' }} />
            <div>
              <h1>RepositóriUM Search</h1>
              <p>Universidade do Minho | Projeto de PRI</p>
            </div>
          </div>
          <nav className="nav-links">
            <Link to="/">Pesquisa</Link>
            <Link to="/author">Autores</Link>
            <Link to="/admin">Estatísticas</Link>
          </nav>
        </header>

        <main className="main-content">
          <Routes>
            <Route path="/" element={<Search />} />
            <Route path="/author" element={<Author />} />
            <Route path="/admin" element={<Admin />} />
          </Routes>
        </main>
      </div>
    </BrowserRouter>
  );
}

export default App;