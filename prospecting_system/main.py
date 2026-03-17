import logging
import json
import os
from typing import List, Dict, Any

from scraper.instagram_scraper import verify_instagram_followers
from scraper.linkedin_scraper import verify_linkedin_employees
from research.news_finder import find_recent_news
from research.post_analyzer import analyze_recent_posts
from analysis.classification import classify_company_data
from mailer.email_builder import build_personalized_email
from mailer.email_sender import EmailSender

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s [%(levelname)s] %(name)s - %(message)s',
    handlers=[logging.StreamHandler()]
)

logger = logging.getLogger("ProspectingSystem")

DATA_FILE = os.path.join(os.path.dirname(__file__), "data", "companies.json")

def load_data() -> List[Dict[str, Any]]:
    if not os.path.exists(DATA_FILE):
        return []
    with open(DATA_FILE, "r", encoding="utf-8") as file:
        return json.load(file)

def save_data(data: List[Dict[str, Any]]) -> None:
    os.makedirs(os.path.dirname(DATA_FILE), exist_ok=True)
    with open(DATA_FILE, "w", encoding="utf-8") as file:
        json.dump(data, file, ensure_ascii=False, indent=4)

def run_pipeline(companies_input: List[Dict[str, str]]):
    """
    Executa o fluxo completo (Etapas 1 a 6) para as empresas inseridas.
    """
    logger.info("INICIANDO PIPELINE DE PROSPECÇÃO B2B")
    all_company_records = load_data()
    
    sender = EmailSender(provider="smtp")

    for input_data in companies_input:
        company_name = input_data["nome"]
        instagram_link = input_data.get("instagram", f"https://instagram.com/{company_name}")
        linkedin_link = input_data.get("linkedin", f"https://linkedin.com/company/{company_name}")
        
        # Override do email destino para fins de teste
        target_email = "etedeloro.pt@gmail.com"

        logger.info(f"--- Processando Empresa: {company_name} ---")

        # ETAPA 1 - COLETA (e verificação)
        ig_status = verify_instagram_followers(company_name, instagram_link)
        in_status = verify_linkedin_employees(company_name, linkedin_link)
        
        if not (ig_status["passed_criteria"] and in_status["passed_criteria"]):
            logger.warning(f"Empresa '{company_name}' REJEITADA pelos critérios mínimos (>150k followers, >500 employees).")
            continue
            
        logger.info(f"Empresa '{company_name}' APROVADA na verificação inicial.")

        # ETAPA 2 - PESQUISA PROFUNDA
        recent_news = find_recent_news(company_name)
        recent_posts = analyze_recent_posts(company_name)
        
        # ETAPA 3 - CLASSIFICAÇÃO
        classified_data = classify_company_data(company_name, recent_news, recent_posts)
        
        # ETAPA 4 - VALIDAÇÃO & PAUSA PARA COMPLEMENTAÇÃO
        # O sistema precisa das informações manuais de CPC (Porcentagem e BRL)
        logger.info(f"=== REVISÃO MANUAL DE DADOS PARA: {company_name} ===")
        print(f"\nEmpresa: {company_name}")
        print(f"Pessoa Foco: {classified_data['target_person']['name']} ({classified_data['target_person']['role']})")
        print(f"Info Privilegiada: {classified_data['privileged_info']}")
        
        cpc_perc = input(f"Informe o aumento do CPC em % para {company_name} (ex: 25): ")
        cpc_brl = input(f"Informe o aumento do CPC em R$ para {company_name} (ex: 1.50): ")
        
        classified_data["cpc_growth"]["percentage"] = cpc_perc.strip() or "0"
        classified_data["cpc_growth"]["currency_brl"] = cpc_brl.strip() or "0"
        
        # Validar dados obrigatórios
        required_fields = [
            classified_data.get("company_name"),
            classified_data.get("target_person", {}).get("name"),
            classified_data.get("target_person", {}).get("role"),
            classified_data.get("privileged_info"),
            classified_data.get("cpc_growth", {}).get("percentage"),
            classified_data.get("cpc_growth", {}).get("currency_brl")
        ]
        
        if not all(required_fields):
            logger.error(f"DADOS INCOMPLETOS: Um ou mais campos obrigatórios faltam para {company_name}. Empresa marcada.")
            classified_data["status"] = "dados incompletos"
            all_company_records.append(classified_data)
            continue
        
        classified_data["status"] = "dados completos"
        
        # ETAPA 5 - MODELAGEM DO EMAIL PERSONALIZADO
        email_content = build_personalized_email(classified_data)
        
        # Confirmar antes de enviar
        print(f"\n--- PREVIEW DO EMAIL ---\nAssunto: {email_content['subject']}\n\n{email_content['body']}\n------------------------")
        confirm = input("Deseja enviar este email? (s/n): ")
        
        if confirm.lower() == 's':
            # ETAPA 6 - ENVIO DO EMAIL
            success = sender.send(target_email, email_content)
            classified_data["status"] = "enviado" if success else "erro_envio"
        else:
            logger.info("Envio cancelado pelo usuário.")
            classified_data["status"] = "cancelado"
            
        all_company_records.append(classified_data)
        
    # Salvar estado final
    save_data(all_company_records)
    logger.info("PIPELINE FINALIZADO. Dados gravados em companies.json.")

if __name__ == "__main__":
    print("------------------------------------------------")
    nome_empresa = input("Digite o nome da empresa que deseja pesquisar: ")
    print("------------------------------------------------\n")
    
    # Input baseado na entrada do usuário
    test_companies = [
        {
            "nome": nome_empresa,
            # Links e emails podem ser derivados ou buscados posteriormente
            "email": "contato@empresa.com", 
            "instagram": f"https://instagram.com/{nome_empresa.replace(' ', '').lower()}",
            "linkedin": f"https://linkedin.com/company/{nome_empresa.replace(' ', '').lower()}"
        }
    ]
    
    run_pipeline(test_companies)
