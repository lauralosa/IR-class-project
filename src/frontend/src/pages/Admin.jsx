import './Admin.css';

export default function Admin() {
  return (
    <div className="admin-page">
      <div className="admin-header">
        <h2>Dashboard de Analytics</h2>
        <p>Estatísticas do sistema e da coleção de documentos.</p>
      </div>
      <div className="admin-grid">
        <div className="admin-card">Total de Documentos</div>
        <div className="admin-card">Termos Mais Pesquisados</div>
        <div className="admin-card">Tamanho do Índice</div>
      </div>
    </div>
  );
}