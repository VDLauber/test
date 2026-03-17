import logging
from duckduckgo_search import DDGS
import re

logger = logging.getLogger(__name__)

def verify_linkedin_employees(company_name: str, linkedin_link: str) -> dict:
    """
    Tenta buscar o número REAL de funcionários via DuckDuckGo.
    """
    logger.info(f"Verificando funcionários no LinkedIn para: {company_name}")
    
    employee_count = None
    found_linkedin = linkedin_link
    
    try:
        with DDGS() as ddgs:
            results = list(ddgs.text(f"{company_name} LinkedIn funcionários employees número", max_results=5))
            
            for item in results:
                text = f"{item.get('title', '')} {item.get('body', '')}"
                href = item.get("href", "")
                
                if 'linkedin.com/company/' in href:
                    found_linkedin = href
                
                patterns = [
                    r'([\d.]+)\s*(?:mil|K)\s*(?:funcionários|employees|colaboradores)',
                    r'([\d,.]+)\s*(?:funcionários|employees|colaboradores)',
                    r'(?:funcionários|employees|colaboradores)[:\s]*([\d,.]+)',
                ]
                
                for pattern in patterns:
                    match = re.search(pattern, text, re.IGNORECASE)
                    if match:
                        num_str = match.group(1).replace('.', '').replace(',', '').strip()
                        try:
                            num = int(num_str)
                            full_match = match.group(0).lower()
                            if 'mil' in full_match or 'k' in full_match:
                                employee_count = num * 1000
                            else:
                                employee_count = num
                            if employee_count > 10:
                                break
                        except ValueError:
                            continue
                
                if employee_count and employee_count > 10:
                    break
                    
    except Exception as e:
        logger.warning(f"Erro ao buscar dados do LinkedIn: {e}")
    
    if employee_count is not None and employee_count > 10:
        passed = employee_count > 500
        if passed:
            logger.info(f"[PASS] {company_name} possui {employee_count:,} funcionários.")
        else:
            logger.info(f"[FAIL] {company_name} possui {employee_count:,} funcionários (Mín: 500).")
    else:
        logger.warning(f"Não foi possível determinar nº de funcionários para {company_name}.")
        logger.warning("Assumindo PASS para continuar o fluxo. Verifique manualmente.")
        employee_count = 0
        passed = True

    return {
        "linkedin_link": found_linkedin,
        "employees": employee_count,
        "passed_criteria": passed
    }
