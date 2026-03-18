import logging
from duckduckgo_search import DDGS
import re
from typing import Dict, Any, List

logger = logging.getLogger(__name__)

# --- Novas Constantes para Scoring e Busca de Personas ---

SENIORITY_SCORES = {
    "high": 3.0,
    "medium": 2.0,
    "low": 1.0,
}

SENIORITY_MAP = {
    "high": ["cmo", "chief marketing officer", "vp", "vice president", "head", "diretor", "director"],
    "medium": ["manager", "gerente", "leader", "líder", "lead"],
    "low": ["coordenador", "coordinator", "specialist", "analyst"],
}

KEYWORD_SCORES = {
    "performance": 1.0, "mídia paga": 1.0, "paid media": 1.0, "roi": 1.0,
    "aquisição": 1.0, "acquisition": 1.0, "growth": 1.0, "crescimento": 1.0,
    "marketing digital": 1.0, "digital marketing": 1.0, "demand generation": 1.0,
    "geração de demanda": 1.0,
}

TARGET_ROLES = [
    "CMO", "Chief Marketing Officer", "Head de Marketing", "Head of Marketing",
    "Diretor de Marketing", "Director of Marketing", "VP of Marketing",
    "Marketing Manager", "Gerente de Marketing", "Growth Manager", "Growth Lead",
    "Performance Marketing Manager", "Gerente de Mídia Paga", "Head of Growth",
    "Demand Generation Manager"
]

# Palavras que invalidam um "nome" extraído
BLACKLIST_NAMES = [
    'linkedin', 'google', 'facebook', 'about us', 'home', 'login',
    'see more', 'view all', 'sign in', 'sign up', 'people', 'company'
]

def _is_valid_name(name: str) -> bool:
    """Verifica se o texto extraído parece ser um nome de pessoa."""
    if not name or len(name) < 5 or len(name) > 50:
        return False
    if any(b in name.lower() for b in BLACKLIST_NAMES):
        return False
    # Nome deve ter pelo menos 2 palavras
    parts = name.split()
    if len(parts) < 2:
        return False
    return True

def _extract_name_from_title(title: str) -> str:
    """Extrai nome do formato típico de título LinkedIn."""
    patterns = [
        r'^([A-ZÀ-Ú][a-zà-ú]+(?:\s(?:de|da|do|dos|das|e)\s)?[A-ZÀ-Ú][a-zà-ú]+(?:\s[A-ZÀ-Ú]?[a-zà-ú]*)*)\s*[-–—|]',
        r'^([A-ZÀ-Ú][a-zà-ú]+\s[A-ZÀ-Ú][a-zà-ú]+(?:\s[A-ZÀ-Ú][a-zà-ú]+)*)\s*[-–—|,]',
    ]
    for pattern in patterns:
        match = re.search(pattern, title.strip())
        if match:
            return match.group(1).strip()
    return ""

def _score_persona(role: str, text: str) -> Dict[str, Any]:
    """
    Calcula um score de relevância para uma persona e extrai seus atributos.
    """
    score = 0.0
    role_lower = role.lower()
    text_lower = text.lower()
    full_text = f"{role_lower} {text_lower}"

    # 1. Score por senioridade
    seniority = "default"
    for level, titles in SENIORITY_MAP.items():
        if any(title in role_lower for title in titles):
            score += SENIORITY_SCORES.get(level, 0)
            seniority = level
            break

    # 2. Score por palavras-chave
    found_keywords = []
    for keyword, value in KEYWORD_SCORES.items():
        if keyword in full_text:
            score += value
            found_keywords.append(keyword)

    return {"score": score, "seniority": seniority, "keywords": found_keywords}

def find_target_personas(company_name: str) -> List[Dict]:
    """
    Retorna uma lista de possíveis personas com score de relevância.
    """
    logger.info(f"Buscando múltiplas personas de marketing para: {company_name}")
    found_personas = {}  # Usar um dict para deduplicar por nome

    for role_query in TARGET_ROLES:
        try:
            with DDGS() as ddgs:
                query = f'site:linkedin.com/in "{company_name}" "{role_query}"'
                results = list(ddgs.text(query, region="br-pt", max_results=5))
                

                for item in results:
                    title = item.get("title", "")
                    href = item.get("href", "")
                    body = item.get("body", "")
                    
                    # Tentar extrair nome do título
                    full_text = f"{title} {body}"

                    name = _extract_name_from_title(title)
                    
                    if not _is_valid_name(name):
                        # Tentar extrair do body com padrões flexíveis usando role_query
                        flex_patterns = [
                            rf'([A-ZÀ-Ú][a-zà-ú]+(?:\s[A-ZÀ-Ú][a-zà-ú]+)+)\s*[-–—,|]\s*{re.escape(role_query)}',
                            rf'{re.escape(role_query)}[:\s]+([A-ZÀ-Ú][a-zà-ú]+(?:\s[A-ZÀ-Ú][a-zà-ú]+)+)',
                        ]
                        for pattern in flex_patterns:
                            match = re.search(pattern, full_text, re.IGNORECASE)
                            if match:
                                potential_name = match.group(1).strip()
                                if _is_valid_name(potential_name):
                                    name = potential_name
                                    break
                                
                    if not _is_valid_name(name) or name.lower() in found_personas:
                        continue

                    # Extrai o cargo do título para maior precisão
                    role_match = re.search(r'-\s(.*?)\s(?:at|na|em|-|\|)', title, re.IGNORECASE)
                    role = role_match.group(1).strip() if role_match else role_query

                    scoring_info = _score_persona(role, full_text)

                    if scoring_info["score"] > 0:
                        persona_data = {
                            "name": name,
                            "role": role,
                            "seniority": scoring_info["seniority"],
                            "keywords": scoring_info["keywords"],
                            "linkedin_url": href if 'linkedin.com/in' in href else "Não encontrado",
                            "score": scoring_info["score"]
                        }
                        found_personas[name.lower()] = persona_data
                        logger.info(f"  -> Persona encontrada: {name} (Score: {scoring_info['score']:.1f})")

        except Exception as e:
            logger.warning(f"Erro ao buscar por '{role_query}': {e}")

    # Ordena as personas encontradas pelo score
    sorted_personas = sorted(found_personas.values(), key=lambda p: p["score"], reverse=True)

    # Fallback caso nenhuma persona seja encontrada
    if not sorted_personas:
        logger.warning(f"Nenhuma persona de marketing encontrada para {company_name}. Usando fallback.")
        return [{
            "name": "Responsável de Marketing",
            "role": "Marketing",
            "seniority": "N/A",
            "keywords": [],
            "linkedin_url": "Não encontrado",
            "score": 0.0
        }]

    return sorted_personas[:3]  # Retorna as top 3

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
    Classifica os dados REAIS coletados, focando em encontrar as melhores personas.
    """
    logger.info(f"Classificando dados coletados para {company_name}")
    
    # NOVA LÓGICA: Busca uma lista de personas ranqueadas
    target_personas = find_target_personas(company_name)
    # Mantém compatibilidade com código antigo selecionando a melhor persona
    best_person = target_personas[0]
    
    privileged_info = _select_best_privileged_info(company_name, news, posts)
    cpc_growth = {
        "percentage": None,
        "currency_brl": None
    }
    
    return {
        "company_name": company_name,
        "target_person": best_person,       # Mantido para compatibilidade
        "target_persons": target_personas,  # CAMPO ATUALIZADO
        "privileged_info": privileged_info,
        "cpc_growth": cpc_growth
    }
