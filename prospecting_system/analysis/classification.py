import logging
from duckduckgo_search import DDGS
import re
from typing import Dict, Any, List

logger = logging.getLogger(__name__)

def _search_marketing_contact(company_name: str) -> Dict[str, str]:
    """
    Busca REAL de um contato de marketing da empresa via DuckDuckGo.
    Usa múltiplas estratégias de extração para maximizar a chance de encontrar.
    """
    logger.info(f"Buscando contato de marketing para: {company_name}")
    
    target_roles = [
        "CMO", "Chief Marketing Officer",
        "Head de Marketing", "Head of Marketing",
        "Diretor de Marketing", "Director of Marketing", "Diretora de Marketing",
        "Marketing Manager", "Gerente de Marketing",
        "Growth Manager", "Growth Lead",
        "Media Manager", "Gerente de Mídia",
        "VP Marketing", "VP de Marketing",
        "Coordenador de Marketing", "Coordenadora de Marketing",
    ]
    
    # Palavras que invalidam um "nome" extraído
    blacklist = [
        'linkedin', 'google', 'facebook', 'about us', 'home', 'login',
        'see more', 'view all', 'sign in', 'sign up', 'people', 'company'
    ]
    
    def _is_valid_name(name: str) -> bool:
        """Verifica se o texto extraído parece ser um nome de pessoa."""
        if not name or len(name) < 5 or len(name) > 50:
            return False
        if name.lower() in blacklist:
            return False
        # Nome deve ter pelo menos 2 palavras
        parts = name.split()
        if len(parts) < 2:
            return False
        return True
    
    def _extract_name_from_title(title: str) -> str:
        """Extrai nome do formato típico de título LinkedIn."""
        # "Nome Sobrenome - Cargo - Empresa | LinkedIn"
        # "Nome Sobrenome – Cargo na Empresa"
        patterns = [
            r'^([A-ZÀ-Ú][a-zà-ú]+(?:\s(?:de|da|do|dos|das|e)\s)?[A-ZÀ-Ú][a-zà-ú]+(?:\s[A-ZÀ-Ú]?[a-zà-ú]*)*)\s*[-–—|]',
            r'^([A-ZÀ-Ú][a-zà-ú]+\s[A-ZÀ-Ú][a-zà-ú]+(?:\s[A-ZÀ-Ú][a-zà-ú]+)*)\s*[-–—|,]',
        ]
        for pattern in patterns:
            match = re.search(pattern, title.strip())
            if match:
                return match.group(1).strip()
        return ""
    
    # ========== ESTRATÉGIA 1: Buscar perfis LinkedIn ==========
    for role in target_roles:
        try:
            with DDGS() as ddgs:
                query = f'site:linkedin.com/in "{company_name}" "{role}"'
                results = list(ddgs.text(query, region="br-pt", max_results=5))
                
                for item in results:
                    title = item.get("title", "")
                    href = item.get("href", "")
                    body = item.get("body", "")
                    
                    # Tentar extrair nome do título
                    name = _extract_name_from_title(title)
                    if _is_valid_name(name):
                        linkedin_url = href if 'linkedin.com' in href else "Não encontrado"
                        logger.info(f"Encontrado: {name} - {role}")
                        return {"name": name, "role": role, "linkedin": linkedin_url}
                    
                    # Tentar extrair do body com padrões flexíveis
                    full_text = f"{title} {body}"
                    flex_patterns = [
                        rf'([A-ZÀ-Ú][a-zà-ú]+(?:\s[A-ZÀ-Ú][a-zà-ú]+)+)\s*[-–—,|]\s*{re.escape(role)}',
                        rf'{re.escape(role)}[:\s]+([A-ZÀ-Ú][a-zà-ú]+(?:\s[A-ZÀ-Ú][a-zà-ú]+)+)',
                    ]
                    for pattern in flex_patterns:
                        match = re.search(pattern, full_text, re.IGNORECASE)
                        if match:
                            name = match.group(1).strip()
                            if _is_valid_name(name):
                                linkedin_url = href if 'linkedin.com' in href else "Não encontrado"
                                logger.info(f"Encontrado: {name} - {role}")
                                return {"name": name, "role": role, "linkedin": linkedin_url}
                                
        except Exception as e:
            logger.warning(f"Erro ao buscar contato '{role}': {e}")
    
    # ========== ESTRATÉGIA 2: Busca genérica ampla ==========
    try:
        with DDGS() as ddgs:
            query = f'"{company_name}" marketing OR CMO OR "head de marketing" OR "gerente de marketing" LinkedIn'
            results = list(ddgs.text(query, region="br-pt", max_results=5))
            
            for item in results:
                title = item.get("title", "")
                href = item.get("href", "")
                
                name = _extract_name_from_title(title)
                if _is_valid_name(name):
                    detected_role = "Marketing"
                    for role in target_roles:
                        if role.lower() in title.lower():
                            detected_role = role
                            break
                    linkedin_url = href if 'linkedin.com' in href else "Não encontrado"
                    logger.info(f"Encontrado (busca ampla): {name} - {detected_role}")
                    return {"name": name, "role": detected_role, "linkedin": linkedin_url}
    except Exception as e:
        logger.warning(f"Erro na busca genérica: {e}")
    
    logger.warning(f"Não foi possível encontrar contato de marketing para {company_name}.")
    return {
        "name": "Responsável de Marketing",
        "role": "Marketing",
        "linkedin": "Não encontrado"
    }


def _select_best_privileged_info(company_name: str, news: List[str], posts: List[str]) -> str:
    """
    Seleciona a informação mais relevante e recente dentre as coletadas.
    """
    all_info = news + posts
    
    priority_keywords = [
        'expansão', 'crescimento', 'investimento', 'aporte', 'lançamento',
        'campanha', 'faturamento', 'receita', 'parceria', 'aquisição',
        'premiação', 'prêmio', 'inovação', 'novo', 'nova', 'inauguração',
        'expansion', 'growth', 'investment', 'launch', 'campaign', 'revenue'
    ]
    
    # Palavras que indicam notícia negativa (EVITAR para prospecção)
    negative_keywords = [
        'pesadelo', 'escândalo', 'fraude', 'processo', 'denúncia',
        'investigação', 'multa', 'condenada', 'demissão', 'layoff',
        'falência', 'encerra', 'bloqueio', 'suspensa', 'crise',
        'prejuízo', 'perda', 'queda', 'reclamação', 'problema',
        'erro', 'falha', 'fora do ar', 'golpe', 'vazamento', 'ilícito'
    ]
    
    scored_items = []
    for item in all_info:
        score = 0
        item_lower = item.lower()
        # Pontuar positivamente
        for keyword in priority_keywords:
            if keyword in item_lower:
                score += 2
        # Penalizar fortemente notícias negativas
        for keyword in negative_keywords:
            if keyword in item_lower:
                score -= 10
        # Penalizar fallbacks genéricos
        if "não foram encontrad" in item_lower or "mantém presença" in item_lower or "é uma empresa" in item_lower:
            score -= 20
        scored_items.append((score, item))
    
    scored_items.sort(key=lambda x: x[0], reverse=True)
    
    # Só pegar itens com score positivo
    if scored_items and scored_items[0][0] > 0:
        return scored_items[0][1]
    elif all_info:
        # Se nenhum item é positivo, usar fallback genérico
        return f"A empresa {company_name} continua se destacando e inovando em seu setor de atuação."
    else:
        return f"A empresa {company_name} continua se destacando e inovando em seu setor de atuação."


def classify_company_data(company_name: str, news: List[str], posts: List[str]) -> Dict[str, Any]:
    """
    Classifica os dados REAIS coletados nas 4 categorias obrigatórias.
    """
    logger.info(f"Classificando dados coletados para {company_name}")
    
    company = company_name
    person = _search_marketing_contact(company_name)
    privileged_info = _select_best_privileged_info(company_name, news, posts)
    cpc_growth = {
        "percentage": None,
        "currency_brl": None
    }
    
    return {
        "company_name": company,
        "target_person": person,
        "privileged_info": privileged_info,
        "cpc_growth": cpc_growth
    }
