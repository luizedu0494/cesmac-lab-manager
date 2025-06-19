from flask import render_template
from flask_mail import Message
from . import mail

def send_email(to, subject, template, **kwargs):
    """
    Função para enviar e-mails de forma assíncrona.
    
    :param to: Destinatário ou lista de destinatários.
    :param subject: Assunto do e-mail.
    :param template: Caminho para o template Jinja2 do e-mail.
    :param kwargs: Argumentos para passar para o template.
    """
    # Se 'to' não for uma lista, transforma em uma
    recipients = [to] if not isinstance(to, list) else to
    
    msg = Message(
        subject,
        recipients=recipients,
        html=render_template(template, **kwargs)
    )
    try:
        mail.send(msg)
        print(f"E-mail enviado com sucesso para: {recipients}")
    except Exception as e:
        print(f"Falha ao enviar e-mail: {e}")