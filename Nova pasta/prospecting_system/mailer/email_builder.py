import logging
from typing import Dict, Any

logger = logging.getLogger(__name__)

def build_personalized_email(data: Dict[str, Any]) -> dict:
    """
    Gera um email altamente personalizado e profissional para a Protentional.
    Tom: corporativo, consultivo, direto.
    """
    logger.info(f"Gerando email para {data['target_person']['name']} da empresa {data['company_name']}")
    
    company = data["company_name"]
    person_name = data["target_person"]["name"]
    person_role = data["target_person"]["role"]
    info = data["privileged_info"]
    cpc_perc = data["cpc_growth"]["percentage"]
    cpc_brl = data["cpc_growth"]["currency_brl"]
    
    subject = f"{company} — Oportunidade de otimização de investimento em mídia digital"
    
    body = f"""Oi {person_name},

Vi que a {company} está avançando em {info}.

Movimentos como esse normalmente vêm acompanhados de aumento em investimento de mídia — e é exatamente aí que começa o problema invisível.

Hoje, o CPC médio na sua vertical subiu cerca de {cpc_perc}% (≈ R$ {cpc_brl} a mais por clique). Parte relevante disso não vem de competição real, mas de tráfego inválido, bots e cliques fraudulentos.

Ou seja: uma parcela do orçamento pode estar sendo consumida sem gerar nenhum retorno.

A Protentional atua exatamente nesse ponto — identificando e bloqueando esse tipo de tráfego antes que ele impacte suas campanhas.

Já vimos empresas no mesmo momento que a {company} recuperarem eficiência rapidamente só eliminando esse desperdício invisível.

A pergunta é: faz sentido continuar investindo sem ter controle total sobre isso?

Se quiser, te mostro em 15 minutos como isso aparece na prática.

Victor Lauber  
Protentional
"""
    return {"subject": subject, "body": body}
