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
    
    body = f"""Prezado(a) {person_name},

Meu nome é Victor Lauber, e faço parte da equipe comercial da Protentional, empresa especializada em proteção de marca e combate a tráfego fraudulento em campanhas de mídia digital.

Tenho acompanhado de perto as movimentações estratégicas da {company} e, recentemente, chamou a minha atenção o seguinte: {info}

Esse tipo de contexto evidencia o momento de crescimento e relevância da {company}, e reforça a importância de garantir que cada real investido em mídia paga esteja gerando retorno qualificado.

Nesse sentido, dados recentes do setor indicam que o CPC médio na sua vertical teve um aumento de aproximadamente {cpc_perc}%, o que representa cerca de R$ {cpc_brl} a mais por clique. Nossa análise aponta que uma parcela significativa desse aumento pode estar associada a cliques inválidos, bots e tráfego fraudulento — fatores que comprometem diretamente o ROI das campanhas digitais.

A Protentional atua exatamente nesse ponto: nossa tecnologia identifica e bloqueia tráfego inválido em tempo real, antes que ele impacte o orçamento da sua operação. Entre os benefícios diretos para a {company}:

• Redução imediata do desperdício de verba com cliques fraudulentos
• Melhoria nos indicadores de performance (CPC, CPA, ROAS)
• Maior confiabilidade nos dados de campanha para tomada de decisão

Gostaria de propor uma conversa breve de 15 minutos para apresentar como podemos apoiar a {company} nessa frente. Posso me adequar à sua agenda ao longo da próxima semana.

Fico à disposição e agradeço pela atenção.

Atenciosamente,

Victor Lauber
Executivo Comercial — Protentional
Proteção de Marca e Combate à Fraude Digital
www.protentional.com.br
"""
    return {"subject": subject, "body": body}
