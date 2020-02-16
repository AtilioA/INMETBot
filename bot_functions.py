import requests
import scrap_satelites
import parse_alerts
import pycep_correios as pycep
import bot_utils
import bot_messages

@bot_utils.send_typing_action
def catch_all(update, context):
    """ Answer any message not handled if not sent in a group """

    update.message.reply_text('Instruções de uso: `/help` ou `/ajuda`', parse_mode="markdown")


def catch_all_if_not_group(update, context):
    if not bot_utils.is_group_or_channel(update.effective.chat_id):
        catch_all(update, context)


@bot_utils.send_typing_action
def cmd_help(update, context):
    """ Send the help message to the user. """

    update.message.reply_text(text=bot_messages.helpMessage, parse_mode="markdown", disable_web_page_preview=True)


@bot_utils.send_typing_action
def cmd_start(update, context):
    """ Send the help message to the user.  """

    update.message.reply_text(bot_messages.welcomeMessage, parse_mode="markdown")


@bot_utils.send_upload_photo_action
def cmd_vpr(update, context):
    """ Fetch and send latest VPR satellite image to the user """

    vprImageURL = scrap_satelites.get_vpr_last_image()
    # print(vprImageURL)
    context.bot.send_photo(chat_id=update.effective_chat.id, photo=vprImageURL)


@bot_utils.send_upload_document_action
def cmd_vpr_gif(update, context):
    """ TODO: Create and send GIF made of recent VPR satellite images to the user. """

    pass
    # scrap_satelites.scrap_page()
    # vprImageURL = "VPR.gif"
    # context.bot.send_document(chat_id=update.effective_chat.id, document=open(vprImageURL, 'rb'))


@bot_utils.send_upload_photo_action
def cmd_acumulada(update, context):
    """ Fetch and send accumulated precipitation within given interval satellite image to the user. """

    print("Getting acumulada images...")

    text = update.message.text
    try:
        interval = text.split(' ')[1]
    except IndexError:
        update.message.reply_text(text="❌ Não foi possível obter a imagem!\nOs intervalos de dias permitidos são 1, 3, 5, 10, 15, 30 e 90 dias.\nExemplo:\n/acumulada 3")
        return None
    print(interval)

    acumuladaImageURL = scrap_satelites.get_acumulada_last_image(interval)
    if acumuladaImageURL:
        context.bot.send_photo(chat_id=update.effective_chat.id, photo=acumuladaImageURL)
    else:
        update.message.reply_text(text="❌ Não foi possível obter a imagem!\nOs intervalos de dias permitidos são 1, 3, 5, 10, 15, 30 e 90 dias.\nExemplo:\n/acumulada 3")


@bot_utils.send_upload_photo_action
def cmd_acumulada_previsao_24hrs(update, context):
    """ Fetch and send accumulated precipitation satellite image forecast for the next 24 hours to the user. """

    print("Getting acumulada previsão images...")

    acumuladaPrevisaoImageURL = scrap_satelites.get_acumulada_previsao_24hrs()
    update.message.reply_text(text="Precipitação acumulada prevista para as próximas 24 horas:")
    context.bot.send_photo(chat_id=update.effective_chat.id, photo=acumuladaPrevisaoImageURL)


@bot_utils.send_typing_action
def cmd_alertas_brasil(update, context):
    """ Fetch and send active high-risk alerts for Brazil. """

    print("Getting alerts...")

    alerts = parse_alerts.parse_alerts(ignoreModerate=True)
    if alerts:
        alertMessage = ""
        for alert in alerts:
                alertMessage += bot_utils.get_alert_message(alert)
        alertMessage += "\nVeja os gráficos em http://www.inmet.gov.br/portal/alert-as/"
    else:
        alertMessage = "✅ Não há alertas graves para o Brasil no momento.\n\nVocê pode ver outros alertas menores em http://www.inmet.gov.br/portal/alert-as/"

    update.message.reply_text(text=alertMessage, parse_mode="markdown", disable_web_page_preview=True)


@bot_utils.send_typing_action
def cmd_alertas_CEP(update, context):
    """ Fetch and send active high-risk alerts for given CEP (zip code). """

    print("Getting alerts by CEP (zip code)...")

    text = update.message.text
    try:
        cep = text.split(' ')[1]  # Get string after "/alertas_CEP"
    except IndexError:  # No number after /alertas_CEP
        update.message.reply_text(text="❌ CEP não informado!\nExemplo:\n/alertas_CEP 29075-910")
        return None

    try:
        if pycep.validar_cep(cep):
            cepJSON = pycep.consultar_cep(cep)
            city = cepJSON["cidade"]
            cityWarned = False

            alerts = parse_alerts.parse_alerts(ignoreModerate=False)
            if alerts:
                alertMessage = ""
                for alert in alerts:
                    # print(alert.cities)
                    if city in alert.cities:
                        cityWarned = True
                        alertMessage += bot_utils.get_alert_message(alert, city)

                alertMessage += "\nVeja os gráficos em http://www.inmet.gov.br/portal/alert-as/"
                if not cityWarned:
                    alertMessage = f"✅ Não há alertas para {city} no momento.\n\nVocê pode ver outros alertas em http://www.inmet.gov.br/portal/alert-as/"
            else:
                alertMessage = "✅ Não há alertas para o Brasil no momento."

            update.message.reply_text(text=alertMessage, parse_mode="markdown", disable_web_page_preview=True)

        else:
            update.message.reply_text(text="❌ Não foi possível verificar a região - CEP inválido!\nExemplo:\n/alertas_CEP 29075-910")

    except pycep.excecoes.ExcecaoPyCEPCorreios:  # Invalid zip code
        update.message.reply_text(text="❌ Não foi possível verificar a região - CEP inválido/não existe!\nExemplo:\n/alertas_CEP 29075-910")
        return None


@bot_utils.send_typing_action
def alertas_location(update, context):
    """ Handle location messages by checking for alerts in that region.

        Send message with current alerts, if any.
    """

    location = update.message
    if location:
        latitude = location['location']['latitude']
        longitude = location['location']['longitude']

        reverseGeocode = requests.get(f"https://api.3geonames.org/{latitude},{longitude}.json")
        if reverseGeocode.status_code == 200:
            print("Successful GET request to reverse geocoding API!")
            json = reverseGeocode.json()
            print(json)
            state = json["nearest"]["state"]
            if state == "BR":
                city = json["nearest"]["region"]
                cityWarned = False

                alerts = parse_alerts.parse_alerts(ignoreModerate=False)
                if alerts:
                    alertMessage = ""
                    for alert in alerts:
                        # print(alert.cities)
                        if city in alert.cities:
                            cityWarned = True
                            alertMessage += bot_utils.get_alert_message(alert, city)

                    alertMessage += "\nVeja os gráficos em http://www.inmet.gov.br/portal/alert-as/"

                    if not cityWarned:
                        alertMessage = f"✅ Não há alertas para {city} no momento.\n\nVocê pode ver outros alertas em http://www.inmet.gov.br/portal/alert-as/"
                else:
                    alertMessage = "✅ Não há alertas para o Brasil no momento."

                update.message.reply_text(text=alertMessage, parse_mode="markdown", disable_web_page_preview=True)
            else:
                update.message.reply_text(text="❌ A localização indica uma região fora do Brasil.")
        else:
            print("Failed GET request to reverse geocoding API.")
            update.message.reply_text(text="❌ Não foi possível verificar a região 😔")


@bot_utils.send_upload_video_action
def cmd_sorrizoronaldo(update, context):
    """ Send default Sorrizo Ronaldo video. """

    update.message.reply_text(text=bot_messages.sorrizoChegou, parse_mode="markdown")
    context.bot.send_video(chat_id=update.effective_chat.id, video="BAACAgEAAxkBAAPmXkSUcBDsVM300QABV4Oerb9PcUx3AAL8AAODXihGe5y1jndyb80YBA")

@bot_utils.send_upload_video_action
def cmd_sorrizoronaldo_will_rock_you(update, context):
    """ Send "We Will Rock You" Sorrizo Ronaldo video variation. """

    update.message.reply_text(text=bot_messages.sorrizoQueen, parse_mode="markdown")
    context.bot.send_video(chat_id=update.effective_chat.id, video="BAACAgEAAxkBAAICZ15HDelLB1IH1i3hTB8DaKwWlyPMAAJ8AAPfLzhG0hgf8dxd_zQYBA")
