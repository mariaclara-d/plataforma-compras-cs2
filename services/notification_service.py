import os
from twilio.rest import Client
from dotenv import load_dotenv
import logging
from datetime import datetime

load_dotenv()

class NotificationService:
    def __init__(self):
        try:
            self.client = Client(
                os.getenv('TWILIO_ACCOUNT_SID'),
                os.getenv('TWILIO_AUTH_TOKEN')
            )
            self.whatsapp_from = os.getenv('TWILIO_WHATSAPP_FROM')
            self.admin_whatsapp = os.getenv('TWILIO_WHATSAPP_TO')
            logging.info(" Twilio configurado com sucesso")
        except Exception as e:
            logging.error(f" Erro na configuração Twilio: {e}")
            self.client = None
    
    def enviar_notificacao_saque(self, usuario_nome, valor, metodo_pagamento, chave_pix):
        """Envia notificação WhatsApp para admin sobre solicitação de saque"""
        if not self.client:
            logging.error(" Cliente Twilio não configurado")
            return False
            
        try:
            mensagem = f""" *NOVA SOLICITAÇÃO DE SAQUE*

 *Usuário:* {usuario_nome}
 *Valor:* R$ {valor:.2f}
 *Método:* {metodo_pagamento}
 *Chave PIX:* {chave_pix}

⏰ *Data:* {datetime.now().strftime('%d/%m/%Y %H:%M')}

Acesse o painel admin para processar."""
            
            message = self.client.messages.create(
                body=mensagem,
                from_=self.whatsapp_from,
                to=self.admin_whatsapp
            )
            
            logging.info(f" Notificação WhatsApp enviada: {message.sid}")
            return True
            
        except Exception as e:
            logging.error(f" Erro ao enviar WhatsApp: {e}")
            return False
    
    def enviar_notificacao_trade_oferta(self, usuario_nome, valor_total, itens_count, offer_id):
        """Envia notificação sobre nova trade offer"""
        if not self.client:
            logging.error(" Cliente Twilio não configurado")
            return False
            
        try:
            mensagem = f""" *NOVA TRADE OFFER*

 *Usuário:* {usuario_nome}
 *Valor Total:* R$ {valor_total:.2f}
 *Itens:* {itens_count}
 *Oferta ID:* {offer_id}

⏰ *Data:* {datetime.now().strftime('%d/%m/%Y %H:%M')}

Verifique no painel admin."""
            
            message = self.client.messages.create(
                body=mensagem,
                from_=self.whatsapp_from,
                to=self.admin_whatsapp
            )
            
            logging.info(f" Notificação trade offer enviada: {message.sid}")
            return True
            
        except Exception as e:
            logging.error(f" Erro ao enviar WhatsApp: {e}")
            return False

# Instância global
notification_service = NotificationService()
