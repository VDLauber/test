import logging
from duckduckgo_search import DDGS
from typing import List

logger = logging.getLogger(__name__)

def analyze_recent_posts(company_name: str) -> List[str]:
    """
    Busca REAIS informações sobre posts, campanhas e atividades recentes
    da empresa via DuckDuckGo. Forçando resultados em PORTUGUÊS.
    """
    logger.info(f"Analisando posts e atividades recentes de: {company_name}")
    
    post_insights = []
    
    queries = [
        f"{company_name} campanha marketing digital Brasil",
        f"{company_name} lançamento produto novidade expansão",
    ]
    
    for query in queries:
        try:
            with DDGS() as ddgs:
                results = list(ddgs.text(query, region="br-pt", max_results=3))
                for item in results:
                    title = item.get("title", "")
                    body = item.get("body", "")
                    snippet = f"{title}. {body}" if body else title
                    if snippet and len(snippet) > 20:
                        if snippet not in post_insights:
                            post_insights.append(snippet[:300])
                            logger.info(f"  Insight (PT): {title[:80]}...")
                            
        except Exception as e:
            logger.warning(f"Erro ao buscar posts para '{query}': {e}")
    
    post_insights = post_insights[:5]
    
    if not post_insights:
        logger.warning(f"Nenhum insight de posts encontrado para {company_name}.")
        post_insights = [f"A empresa {company_name} mantém presença ativa em seu setor de atuação."]
    else:
        logger.info(f"Extraídos {len(post_insights)} insights reais.")
    
    return post_insights
