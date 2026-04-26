import os
import requests
import fitz  # PyMuPDF
import json
import time

class PDFHandler:
    def __init__(self, base_path="data"):
        self.pdf_path = os.path.join(base_path, "pdfs")
        self.txt_path = os.path.join(base_path, "extracted_text")
        
        # Cria as pastas se não existirem
        os.makedirs(self.pdf_path, exist_ok=True)
        os.makedirs(self.txt_path, exist_ok=True)

    def process_pipeline(self, json_path):
        """Lê o JSON, baixa os PDFs, extrai para TXT e atualiza o JSON."""
        with open(json_path, 'r', encoding='utf-8') as f:
            data = json.load(f)

        count = 0
        print(f"---  Iniciando Download e Extração de PDFs (Alvo: 20) ---")

        for idx, item in enumerate(data):
            # Limpa lixo de tentativas antigas, se existir
            if 'full_content' in item:
                del item['full_content']

            if count >= 20: 
                item['has_full_text'] = False
                continue
            
            url = item.get('pdf_url', '')
            if url and ("bitstreams" in url or url.endswith('.pdf')):
                pdf_file = f"doc_{idx}.pdf"
                txt_file = f"doc_{idx}.txt"
                
                print(f"[{count+1}/20] A extrair: {item.get('title', 'Sem título')[:40]}...")
                
                try:
                    # 1. Download com timeout de 30s
                    res = requests.get(url, headers={'User-Agent': 'Mozilla/5.0'}, timeout=30)
                    if res.status_code == 200:
                        # Guardar PDF original na pasta data/pdfs
                        with open(os.path.join(self.pdf_path, pdf_file), 'wb') as f_pdf:
                            f_pdf.write(res.content)
                        
                        # 2. Extrair Texto do PDF
                        text = ""
                        with fitz.open(os.path.join(self.pdf_path, pdf_file)) as doc:
                            for page in doc:
                                text += page.get_text()
                        
                        # 3. Guardar em TXT na pasta data/extracted_text
                        if text.strip():
                            with open(os.path.join(self.txt_path, txt_file), 'w', encoding='utf-8') as f_txt:
                                f_txt.write(text)
                            
                            # 4. Atualizar o JSON apenas com a referência
                            item['has_full_text'] = True
                            item['text_file'] = txt_file
                            count += 1
                        else:
                            item['has_full_text'] = False
                    else:
                        print(f" Erro do servidor (Status {res.status_code}) em {url}")
                        item['has_full_text'] = False
                except requests.exceptions.Timeout:
                    print(f" Timeout a baixar o doc {idx}. A saltar para o próximo...")
                    item['has_full_text'] = False
                except Exception as e:
                    print(f" Erro no doc {idx}: {e}")
                    item['has_full_text'] = False
                
                # Pausa de 1.5 segundos para não sobrecarregar o RepositóriUM e evitar bloqueios
                time.sleep(1.5)
            else:
                item['has_full_text'] = False

        # 5. Guardar o JSON final limpinho
        with open(json_path, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=4, ensure_ascii=False)
        
        print(f"\n Concluído! {count} PDFs processados com sucesso. Ficheiros guardados na pasta 'data/'.")