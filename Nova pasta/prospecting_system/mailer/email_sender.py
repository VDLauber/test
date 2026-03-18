import logging
import os
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from typing import Dict
from dotenv import load_dotenv

logger = logging.getLogger(__name__)

class EmailSender:
    def __init__(self, provider: str = "mock"):
        """
        Modular email sender. Can be extended to use SMTP, Gmail API, or Outlook API.
        provider: 'mock', 'smtp', 'gmail', 'outlook'
        """
        self.provider = provider
        load_dotenv()  # Load environment variables once at initialization
        logger.info(f"EmailSender inicializado usando provedor: {provider}")

    def send(self, to_email: str, email_content: Dict[str, str]) -> bool:
        """
        Sends the email using the configured provider.
        """
        logger.info(f"Iniciando envio via provedor {self.provider} para {to_email}...")
        
        subject = email_content.get("subject", "")
        body = email_content.get("body", "")
        
        if self.provider == "mock":
            return self._send_mock(to_email, subject, body)
        elif self.provider == "smtp":
            return self._send_smtp(to_email, subject, body)
        elif self.provider in ["gmail", "outlook"]:
            logger.error(f"Provedor {self.provider} ainda não implementado.")
            return False
        else:
            logger.error(f"Provedor {self.provider} desconhecido.")
            return False

    def _send_mock(self, to_email: str, subject: str, body: str) -> bool:
        logger.info(f"--- [MOCK EMAIL ENVIADO] ---")
        logger.info(f"Para: {to_email}")
        logger.info(f"Assunto: {subject}")
        logger.info(f"Corpo:\n{body}")
        logger.info("----------------------------")
        return True

    def _send_smtp(self, to_email: str, subject: str, body: str) -> bool:
        smtp_server = os.environ.get("SMTP_SERVER", "smtp.gmail.com")
        smtp_port = int(os.environ.get("SMTP_PORT", 587))
        smtp_user = os.environ.get("SMTP_USER")
        smtp_password = os.environ.get("SMTP_PASSWORD")
        
        if not smtp_user or not smtp_password:
            logger.error("\n[ERRO SMTP] Credenciais de email não encontradas!")
            logger.error("Crie um arquivo '.env' na raiz do projeto com:")
            logger.error("SMTP_USER=seu_email@gmail.com")
            logger.error("SMTP_PASSWORD=sua_senha_de_app_aqui\n")
            return False
            
        try:
            msg = MIMEMultipart()
            msg['From'] = smtp_user
            msg['To'] = to_email
            msg['Subject'] = subject
            
            msg.attach(MIMEText(body, 'plain', 'utf-8'))
            
            logger.info("Conectando ao servidor SMTP...")
            
            # Use context manager to ensure connection is closed properly
            with smtplib.SMTP(smtp_server, smtp_port) as server:
                server.starttls()
                server.login(smtp_user, smtp_password)
                server.send_message(msg)
            
            logger.info(f"--- [EMAIL REAL ENVIADO] ---")
            logger.info(f"Enviado para: {to_email}")
            return True
        except Exception as e:
            logger.error(f"Erro ao enviar email via SMTP: {e}")
            return False
