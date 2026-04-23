from src.search.processor import TextProcessor

class QueryEngine:
    def __init__(self, index_obj):
        self.index_obj = index_obj
        self.processor = TextProcessor()

    def execute_boolean_query(self, query_str, operator="AND"):
        """
        Interpreta a query e executa a operação booleana (AND, OR, NOT).
        """
        # 1. Processar a query (os termos de busca têm de sofrer o mesmo stemming)
        query_terms = self.processor.process_text(query_str, use_stemming=True)
        
        if not query_terms:
            return []

        # 2. Obter as listas de postings (e skips) para os termos
        # Para simplificar o projeto, vamos focar em operações entre os dois primeiros termos
        if len(query_terms) < 2 and operator != "NOT":
            return self.index_obj.get_postings(query_terms[0])[0]

        term1_postings, term1_skips = self.index_obj.get_postings(query_terms[0])
        term2_postings, term2_skips = self.index_obj.get_postings(query_terms[1])

        # 3. Executar o algoritmo correspondente
        if operator.upper() == "AND":
            return self.intersect_with_skips(term1_postings, term1_skips, term2_postings, term2_skips)
        elif operator.upper() == "OR":
            return self.union(term1_postings, term2_postings)
        elif operator.upper() == "NOT":
            # Retorna documentos que têm o termo 1 mas NÃO têm o termo 2
            return self.difference(term1_postings, term2_postings)
        
        return []

    def intersect_with_skips(self, p1, s1, p2, s2):
        """
        Algoritmo de Interseção (AND) otimizado com Skip Pointers.
        """
        answer = []
        i, j = 0, 0
        
        while i < len(p1) and j < len(p2):
            if p1[i] == p2[j]:
                answer.append(p1[i])
                i += 1
                j += 1
            elif p1[i] < p2[j]:
                # Tentar saltar na lista p1
                # Se i está numa posição de skip e o destino do salto ainda é <= p2[j]
                skip_index = self._get_skip_target_index(i, s1, p1)
                if skip_index and p1[skip_index] <= p2[j]:
                    while skip_index and p1[skip_index] <= p2[j]:
                        i = skip_index
                        skip_index = self._get_skip_target_index(i, s1, p1)
                else:
                    i += 1
            else:
                # Tentar saltar na lista p2
                skip_index = self._get_skip_target_index(j, s2, p2)
                if skip_index and p2[skip_index] <= p1[i]:
                    while skip_index and p2[skip_index] <= p1[i]:
                        j = skip_index
                        skip_index = self._get_skip_target_index(j, s2, p2)
                else:
                    j += 1
        return answer

    def _get_skip_target_index(self, current_pos, skips, postings):
        """Auxiliar para encontrar o próximo destino de um salto."""
        if current_pos in skips:
            # Encontrar o próximo índice de skip
            idx_in_skips = skips.index(current_pos)
            if idx_in_skips + 1 < len(skips):
                return skips[idx_in_skips + 1]
        return None

    def union(self, p1, p2):
        """Operação OR: Une as duas listas sem duplicados."""
        return sorted(list(set(p1) | set(p2)))

    def difference(self, p1, p2):
        """Operação NOT: Documentos em p1 que não estão em p2."""
        return [doc_id for doc_id in p1 if doc_id not in p2]