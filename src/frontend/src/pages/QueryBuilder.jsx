import { useState, useRef, useCallback } from 'react';
import './QueryBuilder.css';

/**
 * REQ-F39 a F42: Construtor Visual de Queries Booleanas
 * Permite ao utilizador construir queries arrastando blocos de operadores e termos.
 */

const BLOCK_TYPES = [
  { type: 'term',  label: '🔤 Termo',    color: '#1d4ed8', bg: '#eff6ff', border: '#bfdbfe' },
  { type: 'AND',   label: '✅ AND',      color: '#065f46', bg: '#f0fdf4', border: '#bbf7d0' },
  { type: 'OR',    label: '🟡 OR',       color: '#92400e', bg: '#fffbeb', border: '#fde68a' },
  { type: 'NOT',   label: '🚫 NOT',      color: '#991b1b', bg: '#fef2f2', border: '#fecaca' },
  { type: 'phrase',label: '💬 Frase',    color: '#5b21b6', bg: '#f5f3ff', border: '#ddd6fe' },
];

let blockIdCounter = 0;
function newBlock(type) {
  blockIdCounter++;
  return {
    id: `block-${blockIdCounter}`,
    type,
    value: type === 'term' ? '' : (type === 'phrase' ? '' : type),
  };
}

function BlockChip({ block, onRemove, onChange, dragging, onDragStart, onDragEnd }) {
  const conf = BLOCK_TYPES.find(b => b.type === block.type) || BLOCK_TYPES[0];
  const isEditable = block.type === 'term' || block.type === 'phrase';

  return (
    <div
      id={`block-chip-${block.id}`}
      className={`block-chip ${dragging ? 'dragging' : ''}`}
      style={{ background: conf.bg, border: `2px solid ${conf.border}`, color: conf.color }}
      draggable
      onDragStart={onDragStart}
      onDragEnd={onDragEnd}
    >
      {isEditable ? (
        <input
          className="block-input"
          style={{ color: conf.color }}
          placeholder={block.type === 'phrase' ? 'frase exata...' : 'termo...'}
          value={block.value}
          onChange={(e) => onChange(block.id, e.target.value)}
          onClick={(e) => e.stopPropagation()}
        />
      ) : (
        <span className="block-label">{conf.label}</span>
      )}
      <button
        className="block-remove"
        onClick={() => onRemove(block.id)}
        title="Remover"
      >
        ×
      </button>
      <span className="drag-handle" title="Arrastar">⠿</span>
    </div>
  );
}

export default function QueryBuilder({ onQueryReady }) {
  const [blocks, setBlocks] = useState([]);
  const [draggedId, setDraggedId] = useState(null);
  const [dragOverId, setDragOverId] = useState(null);
  const [previewQuery, setPreviewQuery] = useState('');
  const [error, setError] = useState('');
  const dropZoneRef = useRef(null);

  // Build the query string from blocks
  const buildQuery = useCallback((blks) => {
    const parts = blks.map(b => {
      if (b.type === 'phrase') return b.value ? `"${b.value}"` : '';
      if (b.type === 'term') return b.value.trim();
      return b.type; // AND, OR, NOT
    });
    return parts.filter(Boolean).join(' ');
  }, []);

  const updatePreview = useCallback((blks) => {
    setPreviewQuery(buildQuery(blks));
  }, [buildQuery]);

  const addBlock = (type) => {
    const b = newBlock(type);
    const newBlocks = [...blocks, b];
    setBlocks(newBlocks);
    updatePreview(newBlocks);
  };

  const removeBlock = (id) => {
    const newBlocks = blocks.filter(b => b.id !== id);
    setBlocks(newBlocks);
    updatePreview(newBlocks);
    setError('');
  };

  const changeBlockValue = (id, val) => {
    const newBlocks = blocks.map(b => b.id === id ? { ...b, value: val } : b);
    setBlocks(newBlocks);
    updatePreview(newBlocks);
  };

  const clearAll = () => {
    setBlocks([]);
    setPreviewQuery('');
    setError('');
  };

  // Drag & Drop reordering
  const handleDragStart = (id) => setDraggedId(id);
  const handleDragEnd = () => { setDraggedId(null); setDragOverId(null); };

  const handleDragOver = (e, id) => {
    e.preventDefault();
    if (id !== draggedId) setDragOverId(id);
  };

  const handleDrop = (e, targetId) => {
    e.preventDefault();
    if (!draggedId || draggedId === targetId) return;

    const fromIdx = blocks.findIndex(b => b.id === draggedId);
    const toIdx = blocks.findIndex(b => b.id === targetId);
    if (fromIdx === -1 || toIdx === -1) return;

    const newBlocks = [...blocks];
    const [moved] = newBlocks.splice(fromIdx, 1);
    newBlocks.splice(toIdx, 0, moved);
    setBlocks(newBlocks);
    updatePreview(newBlocks);
    setDraggedId(null);
    setDragOverId(null);
  };

  const handleDropOnZone = (e) => {
    e.preventDefault();
    // Dropped from palette to zone (type is stored as data-transfer)
    const type = e.dataTransfer.getData('block-type');
    if (type) {
      const b = newBlock(type);
      const newBlocks = [...blocks, b];
      setBlocks(newBlocks);
      updatePreview(newBlocks);
    }
  };

  const handleValidate = () => {
    const q = buildQuery(blocks);
    if (!q) { setError('A query está vazia!'); return; }

    // Basic validation: operators shouldn't be adjacent or at the start/end
    const operators = ['AND', 'OR', 'NOT'];
    const parts = q.split(/\s+/).filter(Boolean);
    const firstWord = parts[0]?.toUpperCase();
    const lastWord = parts[parts.length - 1]?.toUpperCase();

    if (['AND', 'OR'].includes(firstWord)) {
      setError('A query não pode começar com AND ou OR.');
      return;
    }
    if (['AND', 'OR', 'NOT'].includes(lastWord)) {
      setError('A query não pode terminar com um operador.');
      return;
    }

    setError('');
    if (onQueryReady) onQueryReady(q);
  };

  const handlePaletteItemDragStart = (e, type) => {
    e.dataTransfer.setData('block-type', type);
  };

  const templates = [
    { label: 'A AND B', blocks: [{ type: 'term', value: '' }, { type: 'AND', value: 'AND' }, { type: 'term', value: '' }] },
    { label: 'A OR B', blocks: [{ type: 'term', value: '' }, { type: 'OR', value: 'OR' }, { type: 'term', value: '' }] },
    { label: 'A AND NOT B', blocks: [{ type: 'term', value: '' }, { type: 'AND', value: 'AND' }, { type: 'NOT', value: 'NOT' }, { type: 'term', value: '' }] },
    { label: '(A OR B) AND C', blocks: [{ type: 'term', value: '' }, { type: 'OR', value: 'OR' }, { type: 'term', value: '' }, { type: 'AND', value: 'AND' }, { type: 'term', value: '' }] },
  ];

  const applyTemplate = (tmplBlocks) => {
    const newBlocks = tmplBlocks.map((b, i) => ({ ...newBlock(b.type), value: b.value, id: `tmpl-${Date.now()}-${i}` }));
    setBlocks(newBlocks);
    updatePreview(newBlocks);
  };

  return (
    <div className="qb-container">
      <div className="qb-header">
        <h3>🧩 Construtor Visual de Queries Booleanas</h3>
        <p>Arrasta os blocos para construir a tua query ou clica para adicionar.</p>
      </div>

      {/* Palette */}
      <div className="qb-palette">
        <span className="palette-label">Paleta de Blocos:</span>
        {BLOCK_TYPES.map(bt => (
          <div
            key={bt.type}
            className="palette-item"
            style={{ background: bt.bg, border: `2px solid ${bt.border}`, color: bt.color }}
            draggable
            onDragStart={(e) => handlePaletteItemDragStart(e, bt.type)}
            onClick={() => addBlock(bt.type)}
            title={`Adicionar bloco ${bt.label}`}
            id={`palette-${bt.type}`}
          >
            {bt.label}
          </div>
        ))}
      </div>

      {/* Templates */}
      <div className="qb-templates">
        <span className="palette-label">Templates:</span>
        {templates.map(t => (
          <button
            key={t.label}
            className="template-btn"
            onClick={() => applyTemplate(t.blocks)}
            id={`template-${t.label.replace(/\s/g, '-')}`}
          >
            {t.label}
          </button>
        ))}
      </div>

      {/* Drop Zone */}
      <div
        id="qb-drop-zone"
        className={`qb-drop-zone ${blocks.length === 0 ? 'empty' : ''}`}
        onDragOver={(e) => e.preventDefault()}
        onDrop={handleDropOnZone}
        ref={dropZoneRef}
      >
        {blocks.length === 0 ? (
          <div className="drop-hint">
            <span className="drop-icon">⬇️</span>
            <p>Arrasta blocos aqui ou clica na paleta acima para começar a construir a tua query.</p>
          </div>
        ) : (
          <div className="blocks-row">
            {blocks.map((block) => (
              <div
                key={block.id}
                className={`block-wrapper ${dragOverId === block.id ? 'drag-over' : ''}`}
                onDragOver={(e) => handleDragOver(e, block.id)}
                onDrop={(e) => handleDrop(e, block.id)}
              >
                <BlockChip
                  block={block}
                  onRemove={removeBlock}
                  onChange={changeBlockValue}
                  dragging={draggedId === block.id}
                  onDragStart={() => handleDragStart(block.id)}
                  onDragEnd={handleDragEnd}
                />
              </div>
            ))}
          </div>
        )}
      </div>

      {/* Preview & Controls */}
      <div className="qb-footer">
        <div className="qb-preview">
          <span className="preview-label">Query gerada:</span>
          <code className="preview-code">{previewQuery || '—'}</code>
        </div>

        {error && (
          <div className="qb-error">⚠️ {error}</div>
        )}

        <div className="qb-actions">
          <button className="qb-btn qb-clear" onClick={clearAll} id="qb-clear-btn">
            🗑️ Limpar
          </button>
          <button className="qb-btn qb-validate" onClick={handleValidate} id="qb-validate-btn" disabled={blocks.length === 0}>
            ✅ Usar esta Query
          </button>
        </div>
      </div>
    </div>
  );
}
