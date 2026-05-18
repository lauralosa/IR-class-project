import { useState, useEffect, useRef } from 'react';
import './Author.css';

// ─── Mini Bar Chart Component ───────────────────────────────────────────────
function TimelineChart({ data }) {
  if (!data || data.length === 0) return null;
  const maxCount = Math.max(...data.map(d => d.count), 1);

  return (
    <div className="timeline-chart">
      <div className="chart-bars">
        {data.map(({ year, count }) => (
          <div key={year} className="chart-bar-wrap">
            <span className="chart-count">{count}</span>
            <div
              className="chart-bar"
              style={{ height: `${(count / maxCount) * 100}%` }}
              title={`${year}: ${count} publicação(ões)`}
            />
            <span className="chart-year">{year}</span>
          </div>
        ))}
      </div>
    </div>
  );
}

// ─── Collaboration Network (Canvas-based) ────────────────────────────────────
function CollabNetwork({ author, collaborators }) {
  const canvasRef = useRef(null);

  useEffect(() => {
    const canvas = canvasRef.current;
    if (!canvas || !collaborators || collaborators.length === 0) return;
    const ctx = canvas.getContext('2d');
    const W = canvas.width;
    const H = canvas.height;
    ctx.clearRect(0, 0, W, H);

    const cx = W / 2;
    const cy = H / 2;
    const radius = Math.min(W, H) * 0.36;

    // Nodes: central author + top collaborators (max 12)
    const top = collaborators.slice(0, 12);
    const maxShared = top[0]?.shared_papers || 1;

    const nodeAngle = (2 * Math.PI) / top.length;

    // Draw edges first
    top.forEach((collab, i) => {
      const angle = i * nodeAngle - Math.PI / 2;
      const nx = cx + radius * Math.cos(angle);
      const ny = cy + radius * Math.sin(angle);
      const weight = collab.shared_papers / maxShared;

      ctx.beginPath();
      ctx.moveTo(cx, cy);
      ctx.lineTo(nx, ny);
      ctx.strokeStyle = `rgba(170,25,43,${0.15 + weight * 0.5})`;
      ctx.lineWidth = 1 + weight * 3;
      ctx.stroke();
    });

    // Draw peripheral nodes
    top.forEach((collab, i) => {
      const angle = i * nodeAngle - Math.PI / 2;
      const nx = cx + radius * Math.cos(angle);
      const ny = cy + radius * Math.sin(angle);
      const weight = collab.shared_papers / maxShared;
      const nodeR = 6 + weight * 10;

      ctx.beginPath();
      ctx.arc(nx, ny, nodeR, 0, 2 * Math.PI);
      ctx.fillStyle = `rgba(170,25,43,${0.35 + weight * 0.55})`;
      ctx.fill();
      ctx.strokeStyle = '#fff';
      ctx.lineWidth = 2;
      ctx.stroke();

      // Label
      ctx.fillStyle = '#374151';
      ctx.font = '11px Segoe UI, sans-serif';
      ctx.textAlign = 'center';
      const shortName = collab.name.split(' ').slice(-1)[0]; // Sobrenome
      ctx.fillText(shortName, nx, ny + nodeR + 14);
    });

    // Central node
    ctx.beginPath();
    ctx.arc(cx, cy, 22, 0, 2 * Math.PI);
    ctx.fillStyle = '#AA192B';
    ctx.fill();
    ctx.strokeStyle = '#fff';
    ctx.lineWidth = 3;
    ctx.stroke();

    ctx.fillStyle = '#fff';
    ctx.font = 'bold 11px Segoe UI, sans-serif';
    ctx.textAlign = 'center';
    ctx.textBaseline = 'middle';
    ctx.fillText('Autor', cx, cy);
    ctx.textBaseline = 'alphabetic';

  }, [author, collaborators]);

  if (!collaborators || collaborators.length === 0) {
    return <p className="no-data-msg">Sem dados de colaboração disponíveis.</p>;
  }

  return (
    <div style={{ display: 'flex', justifyContent: 'center' }}>
      <canvas ref={canvasRef} width={480} height={320} style={{ borderRadius: '12px', background: '#fafafa', border: '1px solid #e5e7eb' }} />
    </div>
  );
}

// ─── Main Author Page ────────────────────────────────────────────────────────
export default function Author() {
  const [searchQuery, setSearchQuery] = useState('');
  const [authorList, setAuthorList] = useState([]);
  const [isSearching, setIsSearching] = useState(false);
  const [totalAuthors, setTotalAuthors] = useState(0);

  // Profile state
  const [profile, setProfile] = useState(null);
  const [isLoadingProfile, setIsLoadingProfile] = useState(false);
  const [profileError, setProfileError] = useState(null);
  const [activeTab, setActiveTab] = useState('publications'); // publications | network | timeline

  // Initial load: top authors
  useEffect(() => {
    fetchAuthors('');
  }, []);

  const fetchAuthors = async (q) => {
    setIsSearching(true);
    try {
      const params = new URLSearchParams({ page_size: 30 });
      if (q) params.set('q', q);
      const res = await fetch(`http://localhost:8000/authors?${params}`);
      const data = await res.json();
      setAuthorList(data.authors || []);
      setTotalAuthors(data.total || 0);
    } catch {
      setAuthorList([]);
    } finally {
      setIsSearching(false);
    }
  };

  const handleSearch = (e) => {
    e.preventDefault();
    fetchAuthors(searchQuery);
  };

  const loadProfile = async (authorName) => {
    setIsLoadingProfile(true);
    setProfileError(null);
    setProfile(null);
    setActiveTab('publications');
    try {
      const res = await fetch(`http://localhost:8000/authors/${encodeURIComponent(authorName)}`);
      if (!res.ok) throw new Error(`Autor não encontrado (${res.status})`);
      const data = await res.json();
      setProfile(data);
    } catch (err) {
      setProfileError(err.message);
    } finally {
      setIsLoadingProfile(false);
    }
  };

  const getCategoryColor = (cat) => {
    const colors = {
      'AI & Robotics': '#7c3aed',
      'Data Science': '#0369a1',
      'Systems & Tech': '#0f766e',
      'Education & Society': '#92400e',
      'General Engineering': '#374151',
    };
    return colors[cat] || '#6b7280';
  };

  return (
    <div className="author-page">
      {/* ── Header ── */}
      <div className="author-header">
        <h2>🔬 Pesquisa de Autores</h2>
        <p>Explore perfis, redes de colaboração e timelines de publicação.</p>
      </div>

      <div className="author-layout">
        {/* ── Left Panel: Search + List ── */}
        <aside className="author-sidebar">
          <form onSubmit={handleSearch} className="author-search-form">
            <input
              id="author-search-input"
              type="text"
              className="author-search-input"
              placeholder="Procurar autor..."
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
            />
            <button type="submit" className="author-search-btn" id="author-search-submit">🔍</button>
          </form>

          {!isSearching && (
            <p className="author-list-count">
              {searchQuery ? `${authorList.length} resultado(s)` : `Top ${authorList.length} de ${totalAuthors} autores`}
            </p>
          )}

          <div className="author-list">
            {isSearching ? (
              <div className="author-loading"><div className="spinner-sm" /><span>A carregar...</span></div>
            ) : authorList.length === 0 ? (
              <p className="no-data-msg">Nenhum autor encontrado.</p>
            ) : (
              authorList.map((a) => (
                <button
                  key={a.name}
                  className={`author-list-item ${profile?.author === a.name ? 'active' : ''}`}
                  onClick={() => loadProfile(a.name)}
                  id={`author-item-${a.name.replace(/\s+/g, '-')}`}
                >
                  <span className="author-avatar">{a.name.charAt(0).toUpperCase()}</span>
                  <div className="author-item-info">
                    <strong>{a.name}</strong>
                    <span>{a.publication_count} publicação(ões)</span>
                  </div>
                  <span className="author-pub-badge">{a.publication_count}</span>
                </button>
              ))
            )}
          </div>
        </aside>

        {/* ── Right Panel: Profile ── */}
        <main className="author-profile-area">
          {isLoadingProfile ? (
            <div className="profile-loading">
              <div className="spinner" />
              <p>A carregar perfil...</p>
            </div>
          ) : profileError ? (
            <div className="profile-error">
              <span>⚠️</span>
              <p>{profileError}</p>
            </div>
          ) : profile ? (
            <div className="profile-card">
              {/* Profile Header */}
              <div className="profile-header">
                <div className="profile-avatar-large">{profile.author.charAt(0).toUpperCase()}</div>
                <div className="profile-meta">
                  <h2 className="profile-name">{profile.author}</h2>
                  <div className="profile-stats-row">
                    <div className="profile-stat">
                      <span className="stat-number">{profile.publication_count}</span>
                      <span className="stat-label">Publicações</span>
                    </div>
                    <div className="profile-stat">
                      <span className="stat-number">{profile.collaborators.length}</span>
                      <span className="stat-label">Colaboradores</span>
                    </div>
                    <div className="profile-stat">
                      <span className="stat-number">{profile.timeline.length}</span>
                      <span className="stat-label">Anos Ativos</span>
                    </div>
                    <div className="profile-stat">
                      <span className="stat-number">{Object.keys(profile.categories).length}</span>
                      <span className="stat-label">Áreas</span>
                    </div>
                  </div>

                  {/* Category badges */}
                  <div className="profile-categories">
                    {Object.entries(profile.categories).map(([cat, count]) => (
                      <span key={cat} className="category-badge" style={{ background: getCategoryColor(cat) + '18', color: getCategoryColor(cat), border: `1px solid ${getCategoryColor(cat)}40` }}>
                        {cat} ({count})
                      </span>
                    ))}
                  </div>
                </div>
              </div>

              {/* Tabs */}
              <div className="profile-tabs">
                <button
                  className={`tab-btn ${activeTab === 'publications' ? 'active' : ''}`}
                  onClick={() => setActiveTab('publications')}
                  id="tab-publications"
                >
                  📄 Publicações
                </button>
                <button
                  className={`tab-btn ${activeTab === 'network' ? 'active' : ''}`}
                  onClick={() => setActiveTab('network')}
                  id="tab-network"
                >
                  🕸️ Rede de Colaboração
                </button>
                <button
                  className={`tab-btn ${activeTab === 'timeline' ? 'active' : ''}`}
                  onClick={() => setActiveTab('timeline')}
                  id="tab-timeline"
                >
                  📅 Timeline
                </button>
              </div>

              {/* Tab Content */}
              <div className="tab-content">
                {/* Publications Tab */}
                {activeTab === 'publications' && (
                  <div className="publications-list">
                    {profile.publications.length === 0 ? (
                      <p className="no-data-msg">Sem publicações disponíveis.</p>
                    ) : (
                      profile.publications.map((pub) => (
                        <div key={pub.id} className="pub-card">
                          <div className="pub-card-top">
                            <span className="pub-year-badge">{pub.year || 'N/D'}</span>
                            <span className="pub-category-tag" style={{ color: getCategoryColor(pub.category) }}>
                              {pub.category}
                            </span>
                          </div>
                          <h4 className="pub-title">
                            {pub.url ? (
                              <a href={pub.url} target="_blank" rel="noreferrer">{pub.title}</a>
                            ) : pub.title}
                          </h4>
                          <p className="pub-authors">
                            👤 {pub.authors?.join(', ') || 'Autor desconhecido'}
                          </p>
                          {pub.snippet && (
                            <p className="pub-snippet">{pub.snippet}</p>
                          )}
                        </div>
                      ))
                    )}
                  </div>
                )}

                {/* Network Tab */}
                {activeTab === 'network' && (
                  <div className="network-panel">
                    <p className="network-desc">
                      Visualização das conexões de co-autoria de <strong>{profile.author}</strong>.
                      O tamanho e opacidade dos nós reflete o número de publicações partilhadas.
                    </p>
                    <CollabNetwork author={profile.author} collaborators={profile.collaborators} />
                    {profile.collaborators.length > 0 && (
                      <div className="collab-list">
                        <h4>Top Colaboradores</h4>
                        {profile.collaborators.slice(0, 10).map((c) => (
                          <div key={c.name} className="collab-item">
                            <button className="collab-name-btn" onClick={() => loadProfile(c.name)}>
                              {c.name}
                            </button>
                            <div className="collab-bar-wrap">
                              <div
                                className="collab-bar"
                                style={{ width: `${(c.shared_papers / (profile.collaborators[0]?.shared_papers || 1)) * 100}%` }}
                              />
                            </div>
                            <span className="collab-count">{c.shared_papers} paper(s)</span>
                          </div>
                        ))}
                      </div>
                    )}
                  </div>
                )}

                {/* Timeline Tab */}
                {activeTab === 'timeline' && (
                  <div className="timeline-panel">
                    <p className="network-desc">
                      Distribuição temporal das publicações de <strong>{profile.author}</strong>.
                    </p>
                    <TimelineChart data={profile.timeline} />
                    <div className="timeline-summary">
                      {profile.timeline.map(({ year, count }) => (
                        <div key={year} className="timeline-row">
                          <span className="tl-year">{year}</span>
                          <div className="tl-bar-wrap">
                            <div
                              className="tl-bar"
                              style={{ width: `${(count / Math.max(...profile.timeline.map(t => t.count))) * 100}%` }}
                            />
                          </div>
                          <span className="tl-count">{count} pub.</span>
                        </div>
                      ))}
                    </div>
                  </div>
                )}
              </div>
            </div>
          ) : (
            <div className="profile-empty">
              <div className="profile-empty-icon">👤</div>
              <h3>Seleciona um autor</h3>
              <p>Clica num autor da lista para ver o seu perfil completo, publicações e rede de colaboração.</p>
            </div>
          )}
        </main>
      </div>
    </div>
  );
}