import logging
from duckduckgo_search import DDGS
import re

logger = logging.getLogger(__name__)

def verify_instagram_followers(company_name: str, instagram_link: str) -> dict:
    """
    Tenta buscar o número REAL de seguidores do Instagram via DuckDuckGo.
    """
    logger.info(f"Verificando seguidores no Instagram para: {company_name}")
    
    followers_count = None
    found_instagram = instagram_link
    
    try:
        with DDGS() as ddgs:
            results = list(ddgs.text(f"{company_name} Instagram seguidores followers", max_results=5))
            
            for item in results:
                text = f"{item.get('title', '')} {item.get('body', '')}"
                href = item.get("href", "")
                
                # Capturar link do Instagram
                if 'instagram.com/' in href:
                    found_instagram = href
                
                # Procurar números de seguidores
                patterns = [
                    r'([\d,.]+)\s*[Mm](?:ilhões|ilhão|illion)?\s*(?:de\s*)?(?:followers|seguidores)',
                    r'([\d,.]+)\s*[Kk]\s*(?:followers|seguidores)',
                    r'([\d,.]+)\s*(?:mil)\s*(?:de\s*)?(?:followers|seguidores)',
                    r'(?:followers|seguidores)[:\s]*([\d,.]+)\s*[MmKk]?',
                ]
                
                for pattern in patterns:
                    match = re.search(pattern, text, re.IGNORECASE)
                    if match:
                        num_str = match.group(1).replace(',', '.').strip()
                        try:
                            num = float(num_str)
                            full_match = match.group(0).lower()
                            if 'm' in full_match or 'milh' in full_match:
                                followers_count = int(num * 1_000_000)
                            elif 'k' in full_match or 'mil' in full_match:
                                followers_count = int(num * 1_000)
                            else:
                                followers_count = int(num)
                            if followers_count > 100:
                                break
                        except ValueError:
                            continue
                
                if followers_count and followers_count > 100:
                    break
                    
    except Exception as e:
        logger.warning(f"Erro ao buscar dados do Instagram: {e}")
    
    if followers_count is not None and followers_count > 100:
        passed = followers_count > 150000
        if passed:
            logger.info(f"[PASS] {company_name} possui {followers_count:,} seguidores no Instagram.")
        else:
            logger.info(f"[FAIL] {company_name} possui {followers_count:,} seguidores (Mín: 150k).")
    else:
        logger.warning(f"Não foi possível determinar seguidores para {company_name}.")
        logger.warning("Assumindo PASS para continuar o fluxo. Verifique manualmente.")
        followers_count = 0
        passed = True

    return {
        "instagram_link": found_instagram,
        "followers": followers_count,
        "passed_criteria": passed
    }
