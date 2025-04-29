# from twilio.rest import Client
# import config

# def enviar_pdf_whatsapp(numero_whatsapp, pdf_path):
#     client = Client(config.TWILIO_ACCOUNT_SID, config.TWILIO_AUTH_TOKEN)

#     from_whatsapp_number = 'whatsapp:+1415XXXXXXX'  # Seu número Twilio
#     to_whatsapp_number = f'whatsapp:+{numero_whatsapp}'

#     message = client.messages.create(
#         body="Aqui está a NFE que você solicitou!",
#         from_=from_whatsapp_number,
#         to=to_whatsapp_number,
#         media_url=[pdf_path]
#     )

#     print(f"PDF enviado para {numero_whatsapp} com sucesso!")
