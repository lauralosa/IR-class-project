import React, { useState } from 'react';
import './Educational.css';

export default function Educational() {
  const [activeTab, setActiveTab] = useState('how-it-works');

  // Estado para a calculadora TF-IDF interativa
  const [tf, setTf] = useState(3);
  const [df, setDf] = useState(10);
  const totalDocs = 110;
  const idf = Math.log10(totalDocs / (df || 1)) + 1;
  const tfIdfScore = tf * idf;

  // Estado para a demonstração Booleana
  const [boolOp, setBoolOp] = useState('AND');
  const docSetA = [1, 2, 4, 5, 8];
  const docSetB = [2, 3, 5, 7, 9];
  let boolResult = [];
  if (boolOp === 'AND') boolResult = docSetA.filter(x => docSetB.includes(x));
  if (boolOp === 'OR') boolResult = [...new Set([...docSetA, ...docSetB])].sort();
  if (boolOp === 'NOT') boolResult = docSetA.filter(x => !docSetB.includes(x));

  return (
    <div className="edu-page">
      <div className="edu-header">
        <h2>📚 Centro Educativo (Como Funciona)</h2>
        <p>Aprende os conceitos de Recuperação de Informação por detrás do motor de busca RepositóriUM.</p>
      </div>

      <div className="edu-tabs">
        <button className={activeTab === 'how-it-works' ? 'active' : ''} onClick={() => setActiveTab('how-it-works')}>⚙️ Pipeline IR</button>
        <button className={activeTab === 'inverted-index' ? 'active' : ''} onClick={() => setActiveTab('inverted-index')}>📖 Índice Invertido</button>
        <button className={activeTab === 'tfidf' ? 'active' : ''} onClick={() => setActiveTab('tfidf')}>🧮 Cálculo TF-IDF</button>
        <button className={activeTab === 'boolean' ? 'active' : ''} onClick={() => setActiveTab('boolean')}>🟢 Lógica Booleana</button>
      </div>

      <div className="edu-content">
        
        {/* REQ-F47: How it works */}
        {activeTab === 'how-it-works' && (
          <div className="edu-section fade-in">
            <h3>Pipeline de Recuperação de Informação</h3>
            <p>Um motor de busca funciona através de uma sequência rigorosa de etapas. Eis como transformamos ficheiros PDF em respostas às tuas perguntas:</p>
            
            <div className="pipeline-steps">
              <div className="pipeline-card">
                <div className="step-number">1</div>
                <h4>Scraping & Extração</h4>
                <p>O sistema faz o download de PDFs do repositório, extrai o texto utilizando OCR e ferramentas de leitura, e recolhe os metadados (autores, ano, título).</p>
              </div>
              <div className="pipeline-arrow">➔</div>
              <div className="pipeline-card">
                <div className="step-number">2</div>
                <h4>Processamento (NLP)</h4>
                <p>O texto sofre uma limpeza: removemos as <i>stop words</i> (palavras vazias como "o", "de") e aplicamos <i>Stemming</i> (cortar as palavras na raiz) ou <i>Lematização</i>.</p>
              </div>
              <div className="pipeline-arrow">➔</div>
              <div className="pipeline-card">
                <div className="step-number">3</div>
                <h4>Indexação</h4>
                <p>Criamos um <strong>Índice Invertido</strong>. Em vez de percorrer cada documento sempre que pesquisas, criamos um "dicionário" que aponta cada palavra aos documentos onde aparece.</p>
              </div>
              <div className="pipeline-arrow">➔</div>
              <div className="pipeline-card">
                <div className="step-number">4</div>
                <h4>Pesquisa & Ordenação</h4>
                <p>Quando escreves uma query, usamos o Índice Invertido para encontrar os documentos e aplicamos fórmulas (como o TF-IDF) para colocar os mais relevantes no topo!</p>
              </div>
            </div>
          </div>
        )}

        {/* REQ-F48: Inverted Index */}
        {activeTab === 'inverted-index' && (
          <div className="edu-section fade-in">
            <h3>O que é um Índice Invertido?</h3>
            <p>Tal como o índice no final de um livro (que te diz em que páginas encontras um tema), um Índice Invertido diz ao computador em que <strong>documentos</strong> (e posições) uma <strong>palavra</strong> aparece. Isto evita que o sistema tenha de ler milhares de ficheiros sempre que pesquisas!</p>
            
            <div className="inverted-index-demo">
              <div className="docs-mockup">
                <div className="doc-mockup"><strong>Doc 1:</strong> "Machine learning in healthcare"</div>
                <div className="doc-mockup"><strong>Doc 2:</strong> "AI and machine learning ethics"</div>
                <div className="doc-mockup"><strong>Doc 3:</strong> "Healthcare data ethics"</div>
              </div>

              <div className="index-arrow">⬇️ Como é guardado na memória ⬇️</div>

              <table className="index-table">
                <thead>
                  <tr>
                    <th>Termo (Vocabulário)</th>
                    <th>Postings (Doc ID : Frequência)</th>
                  </tr>
                </thead>
                <tbody>
                  <tr><td>ai</td><td><span className="posting">[Doc 2: 1]</span></td></tr>
                  <tr><td>data</td><td><span className="posting">[Doc 3: 1]</span></td></tr>
                  <tr><td>ethics</td><td><span className="posting">[Doc 2: 1]</span> <span className="posting">[Doc 3: 1]</span></td></tr>
                  <tr><td>healthcare</td><td><span className="posting">[Doc 1: 1]</span> <span className="posting">[Doc 3: 1]</span></td></tr>
                  <tr><td>learning</td><td><span className="posting">[Doc 1: 1]</span> <span className="posting">[Doc 2: 1]</span></td></tr>
                  <tr><td>machine</td><td><span className="posting">[Doc 1: 1]</span> <span className="posting">[Doc 2: 1]</span></td></tr>
                </tbody>
              </table>
              <small>Nota: As Stop words (in, and) não são indexadas para poupar espaço e tempo de pesquisa!</small>
            </div>
          </div>
        )}

        {/* REQ-F49: TF-IDF Calculation */}
        {activeTab === 'tfidf' && (
          <div className="edu-section fade-in">
            <h3>Como calculamos a Relevância? (TF-IDF)</h3>
            <p>O <strong>Term Frequency-Inverse Document Frequency (TF-IDF)</strong> é a fórmula mágica que nos diz o quão importante uma palavra é para um documento específico dentro de uma coleção gigante.</p>
            
            <div className="tfidf-formula-box">
              <div className="formula-part">
                <strong>TF (Term Frequency)</strong>
                <p>Quantas vezes a palavra aparece neste documento?</p>
                <i>Mais aparições = Maior Peso</i>
              </div>
              <div className="formula-operator">✖️</div>
              <div className="formula-part">
                <strong>IDF (Inverse Document Freq)</strong>
                <p>Em quantos documentos diferentes a palavra aparece?</p>
                <i>Muito comum (ex: "estudo") = Menor Peso<br/>Rara (ex: "CRISPR") = Maior Peso</i>
              </div>
            </div>

            <div className="tfidf-interactive">
              <h4>🧮 Simulador Interativo</h4>
              <p>Experimenta mudar os valores para ver como o score da palavra afeta a ordenação do documento:</p>
              
              <div className="simulator-controls">
                <div className="control-group">
                  <label>Term Frequency (TF) no Documento:</label>
                  <input type="range" min="1" max="20" value={tf} onChange={(e) => setTf(Number(e.target.value))} />
                  <span className="val">{tf} ocorrências</span>
                </div>
                <div className="control-group">
                  <label>Document Frequency (DF) na Coleção (N={totalDocs}):</label>
                  <input type="range" min="1" max={totalDocs} value={df} onChange={(e) => setDf(Number(e.target.value))} />
                  <span className="val">{df} documentos</span>
                </div>
              </div>

              <div className="simulator-results">
                <div className="res-box">
                  <span>Cálculo do IDF:</span>
                  <code>log10({totalDocs} / {df}) + 1 = <strong>{idf.toFixed(3)}</strong></code>
                </div>
                <div className="res-box final">
                  <span>Score TF-IDF Final (TF × IDF):</span>
                  <code>{tf} × {idf.toFixed(3)} = <strong style={{fontSize: '1.5rem'}}>{tfIdfScore.toFixed(3)}</strong></code>
                </div>
              </div>
            </div>
          </div>
        )}

        {/* REQ-F50: Boolean Operations */}
        {activeTab === 'boolean' && (
          <div className="edu-section fade-in">
            <h3>Demonstração de Operadores Booleanos</h3>
            <p>As pesquisas booleanas usam teoria de conjuntos para juntar ou excluir resultados de forma precisa.</p>
            
            <div className="boolean-demo-container">
              <div className="boolean-sets">
                <div className="set-box">
                  <strong>Conjunto A</strong> (Termo: "Machine")
                  <div className="doc-list">Documentos: {docSetA.join(', ')}</div>
                </div>
                <div className="set-box">
                  <strong>Conjunto B</strong> (Termo: "Health")
                  <div className="doc-list">Documentos: {docSetB.join(', ')}</div>
                </div>
              </div>

              <div className="boolean-controls">
                <button className={boolOp === 'AND' ? 'active' : ''} onClick={() => setBoolOp('AND')}>A AND B (Interseção)</button>
                <button className={boolOp === 'OR' ? 'active' : ''} onClick={() => setBoolOp('OR')}>A OR B (União)</button>
                <button className={boolOp === 'NOT' ? 'active' : ''} onClick={() => setBoolOp('NOT')}>A NOT B (Diferença)</button>
              </div>

              <div className="boolean-result">
                <h4>Resultado da Operação: {boolOp}</h4>
                <div className="venn-illustration">
                  {boolOp === 'AND' && <div className="venn-desc">Retorna apenas documentos onde AMBAS as palavras estão presentes. Ideal para afunilar a pesquisa.</div>}
                  {boolOp === 'OR' && <div className="venn-desc">Retorna documentos que tenham pelo menos uma das palavras. Ideal para alargar a pesquisa com sinónimos.</div>}
                  {boolOp === 'NOT' && <div className="venn-desc">Retorna documentos do Conjunto A, desde que NÃO tenham a palavra do Conjunto B. Ideal para remover falsos positivos.</div>}
                </div>
                <div className="result-doc-list">
                  <strong>Documentos Finais: </strong> 
                  {boolResult.length > 0 ? (
                    boolResult.map(d => <span key={d} className="res-badge">Doc {d}</span>)
                  ) : (
                    <span>Nenhum documento satisfaz a condição.</span>
                  )}
                </div>
              </div>
            </div>
          </div>
        )}

      </div>
    </div>
  );
}
