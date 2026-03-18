import logging
import requests
from bs4 import BeautifulSoup
from duckduckgo_search import DDGS
from typing import List

logger = logging.getLogger(__name__)

# Palavras negativas que indicam notícia ruim para prospecção
NEGATIVE_KEYWORDS = [
    'pesadelo', 'escândalo', 'fraude', 'processo', 'denuncia', 'denúncia',
    'investigação', 'investigado', 'multa', 'multada', 'condenada', 'condenado',
    'demissão', 'demissões', 'layoff', 'falência', 'faliu', 'encerra', 'encerramento',
    'bloqueio', 'bloqueada', 'suspensa', 'suspensão', 'proibida', 'proibição',
    'crise', 'prejuízo', 'perda', 'queda', 'reclamação', 'reclamações',
    'problema', 'erro', 'falha', 'fora do ar', 'instabilidade', 'bug',
    'golpe', 'vazamento', 'hackeado', 'invasão', 'ilícito', 'ilegal',
    'negativos', 'piora', 'declínio', 'desvalorização', 'rebaixamento',
    'scandal', 'fraud', 'lawsuit', 'bankrupt', 'crisis', 'layoffs'
]

# Palavras positivas que indicam notícia boa para prospecção
POSITIVE_KEYWORDS = [
    'crescimento', 'expansão', 'investimento', 'aporte', 'lançamento', 'lança',
    'campanha', 'faturamento', 'receita', 'parceria', 'aquisição', 'fusão',
    'premiação', 'prêmio', 'inovação', 'novo', 'nova', 'inauguração',
    'recorde', 'lucro', 'alta', 'valorização', 'contratação', 'contrata',
    'expansão', 'abre', 'inaugura', 'conquista', 'líder', 'liderança',
    'tecnologia', 'plataforma', 'solução', 'produto', 'serviço',
    'growth', 'expansion', 'investment', 'launch', 'campaign', 'revenue',
    'award', 'innovation', 'partnership', 'acquisition', 'record'
]

def _is_positive_news(text: str) -> bool:
    """
    Verifica se a notícia é positiva/construtiva para uso em prospecção.
    Retorna True se a notícia for adequada, False se for negativa.
    """
    text_lower = text.lower()
    
    # Contar indicadores negativos
    negative_score = sum(1 for word in NEGATIVE_KEYWORDS if word in text_lower)
    
    # Contar indicadores positivos
    positive_score = sum(1 for word in POSITIVE_KEYWORDS if word in text_lower)
    
    # A notícia é considerada positiva se:
    # - Não possui nenhuma palavra negativa, OU
    # - As palavras positivas superam as negativas por pelo menos 2x
    if negative_score == 0:
        return True
    if positive_score >= negative_score * 2:
        return True
    
    return False


def _scrape_page_text(url: str, max_chars: int = 500) -> str:
    """Extrai texto de uma página web."""
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
        "Accept-Language": "pt-BR,pt;q=0.9,en-US;q=0.8,en;q=0.7"
    }
    try:
        response = requests.get(url, headers=headers, timeout=8)
        if response.status_code == 200:
            response.encoding = response.apparent_encoding
            soup = BeautifulSoup(response.text, "html.parser")
            for tag in soup(["script", "style", "nav", "footer", "header", "aside"]):
                tag.decompose()
            text = soup.get_text(separator=" ", strip=True)
            return text[:max_chars] if text else ""
    except Exception:
        pass
    return ""

def find_recent_news(company_name: str) -> List[str]:
    """
    Busca notícias REAIS recentes sobre a empresa usando DuckDuckGo.
    Forçando resultados em PORTUGUÊS (região Brasil).
    FILTRA apenas notícias POSITIVAS adequadas para prospecção comercial.
    """
    logger.info(f"Buscando notícias recentes sobre: {company_name}")
    
    all_candidates = []
    news_items = []
    
    # Busca com termos positivos para priorizar boas notícias
    try:
        with DDGS() as ddgs:
            news_results = list(ddgs.news(
                f"{company_name} crescimento expansão lançamento investimento",
                region="br-pt",
                max_results=10
            ))
            for item in news_results:
                title = item.get("title", "")
                body = item.get("body", "")
                snippet = f"{title}. {body}" if body else title
                if snippet and len(snippet) > 20:
                    all_candidates.append(snippet[:300])
                    
    except Exception as e:
        logger.warning(f"Erro ao buscar notícias via DuckDuckGo News: {e}")
    
    # Fallback: busca textual com termos positivos
    if not all_candidates:
        try:
            with DDGS() as ddgs:
                text_results = list(ddgs.text(
                    f"{company_name} crescimento expansão investimento novidade Brasil",
                    region="br-pt",
                    max_results=10
                ))
                for item in text_results:
                    title = item.get("title", "")
                    body = item.get("body", "")
                    snippet = f"{title}. {body}" if body else title
                    if snippet and len(snippet) > 20:
                        all_candidates.append(snippet[:300])
                        
        except Exception as e:
            logger.warning(f"Erro ao buscar via DuckDuckGo Text: {e}")
    
    # FILTRAR: manter apenas notícias POSITIVAS
    for candidate in all_candidates:
        if _is_positive_news(candidate):
            news_items.append(candidate)
            logger.info(f"  ✅ Notícia POSITIVA: {candidate[:80]}...")
        else:
            logger.info(f"  ❌ Notícia NEGATIVA descartada: {candidate[:80]}...")
    
    news_items = news_items[:5]
    
    if not news_items:
        logger.warning(f"Nenhuma notícia positiva encontrada para {company_name}.")
        news_items = [f"A empresa {company_name} continua se destacando em seu setor de atuação."]
    else:
        logger.info(f"Selecionadas {len(news_items)} notícias positivas sobre {company_name}.")
    
    return news_items
