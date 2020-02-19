import os
import requests
import logging
import scrap_satelites
import parse_alerts
import pycep_correios as pycep
import models
import bot_utils
import bot_messages

functionsLogger = logging.getLogger(__name__)
functionsLogger.setLevel(logging.DEBUG)

@bot_utils.send_typing_action
def send_instructions_message(update, context):
    """ Reply to the last message with the instructions message. """

    context.bot.send_message(chat_id=update.effective_chat.id, reply_to_message_id=update.message.message_id, text=bot_messages.instructions)


def catch_all_if_not_group(update, context):
    """ Reply to any message not handled (if not sent to a group/channel). """

    if not bot_utils.is_group_or_channel(update.effective_chat.id):
        functionsLogger.debug("catch_all: not group")
        return send_instructions_message(update, context)


@bot_utils.send_typing_action
def cmd_help(update, context):
    """ Send the help message to the user. """

    context.bot.send_message(chat_id=update.effective_chat.id, reply_to_message_id=update.message.message_id, text=bot_messages.helpMessage, parse_mode="markdown", disable_web_page_preview=True)


@bot_utils.send_typing_action
def cmd_start(update, context):
    """ Send the help message to the user.  """

    context.bot.send_message(chat_id=update.effective_chat.id, reply_to_message_id=update.message.message_id, text=bot_messages.welcomeMessage, parse_mode="markdown")


@bot_utils.send_upload_photo_action
def cmd_vpr(update, context):
    """ Fetch and send latest VPR satellite image to the user """

    vprImageURL = scrap_satelites.get_vpr_last_image()
    # functionsLogger.debug(vprImageURL)
    context.bot.send_photo(chat_id=update.effective_chat.id, reply_to_message_id=update.message.message_id, photo=vprImageURL)


@bot_utils.send_upload_video_action
def send_vpr_video(update, context, vprVideoPath):
    """ Send the .mp4 file to the user and delete it """

    context.bot.send_video(chat_id=update.effective_chat.id, reply_to_message_id=update.message.message_id, video=open(vprVideoPath, 'rb'))
    os.remove(vprVideoPath)
    functionsLogger.info(f"Deleted {vprVideoPath}.")


def get_n_images_input(update, context, text):
    """ Parse input for VPR gifs. Input must exist and be numeric.

        Return:
            Number of images if successful, None otherwise.
    """

    try:
        nImages = text.split(' ')[1]
        if nImages.isnumeric():
            nImages = int(nImages)
            if scrap_satelites.MAX_VPR_IMAGES < nImages:
                nImages = scrap_satelites.DEFAULT_VPR_IMAGES
                context.bot.send_message(chat_id=update.effective_chat.id, text=f"❕O número máximo de imagens é {scrap_satelites.MAX_VPR_IMAGES}! Utilizarei o padrão, que é {scrap_satelites.DEFAULT_VPR_IMAGES} (exibe 2 horas de imagens).", reply_to_message_id=update.message.message_id, parse_mode="markdown")
            elif scrap_satelites.MIN_VPR_IMAGES > nImages:
                nImages = scrap_satelites.DEFAULT_VPR_IMAGES
                context.bot.send_message(chat_id=update.effective_chat.id, text=f"❕O número mínimo de imagens é {scrap_satelites.MIN_VPR_IMAGES}! Utilizarei o padrão, que é {scrap_satelites.DEFAULT_VPR_IMAGES} (exibe 2 horas de imagens).", reply_to_message_id=update.message.message_id, parse_mode="markdown")
        else:
            context.bot.send_message(chat_id=update.effective_chat.id, text=f"❌ Não entendi!\nExemplo:\n`/vpr_gif 3` ou `/nuvens 3`", reply_to_message_id=update.message.message_id,  parse_mode="markdown")
            return None
    except IndexError as indexE:
        context.bot.send_message(chat_id=update.effective_chat.id, text=f"❕Não foi possível identificar o intervalo. Utilizarei o padrão, que é {scrap_satelites.DEFAULT_VPR_IMAGES} (exibe 2 horas de imagens).\nDica: você pode estipular quantas imagens buscar. Ex: `{text.split(' ')[0]} 4` buscará as 4 últimas imagens.", reply_to_message_id=update.message.message_id, parse_mode="markdown")
        functionsLogger.warning(f"{indexE} on cmd_vpr_gif. Message text: \"{text}\"")
        nImages = scrap_satelites.DEFAULT_VPR_IMAGES

    return nImages


@bot_utils.send_typing_action
def cmd_vpr_gif(update, context):
    """ Create and send GIF made of recent VPR satellite images to the user. """

    text = update.message.text

    nImages = get_n_images_input(update, context, text)
    if nImages:
        context.bot.send_message(chat_id=update.effective_chat.id, text=f"⏳ Buscando as últimas {nImages} imagens e criando GIF...", parse_mode="markdown")

        vprVideoPath = scrap_satelites.get_vpr_gif(nImages)

        return send_vpr_video(update, context, vprVideoPath)


@bot_utils.send_upload_photo_action
def cmd_acumulada(update, context):
    """ Fetch and send accumulated precipitation within given interval satellite image to the user. """

    functionsLogger.debug("Getting acumulada images...")

    text = update.message.text
    try:
        interval = text.split(' ')[1]
    except IndexError as indexE:
        functionsLogger.warning(f"{indexE} on cmd_acumulada. Message text: \"{text}\"")
        context.bot.send_message(chat_id=update.effective_chat.id, reply_to_message_id=update.message.message_id, text="❌ Não foi possível identificar o intervalo! Portanto, utilizarei 1 como valor.\nOs intervalos de dias permitidos são 1, 3, 5, 10, 15, 30 e 90 dias.\nExemplo:\n`/acumulada 3`", parse_mode="markdown")
        interval = 1

    acumuladaImageURL = scrap_satelites.get_acumulada_last_image(interval)
    if acumuladaImageURL:
        context.bot.send_photo(chat_id=update.effective_chat.id, reply_to_message_id=update.message.message_id, photo=acumuladaImageURL)
    else:
        context.bot.send_message(chat_id=update.effective_chat.id, reply_to_message_id=update.message.message_id, text="❌ Não foi possível obter a imagem!", parse_mode="markdown")


@bot_utils.send_upload_photo_action
def cmd_acumulada_previsao_24hrs(update, context):
    """ Fetch and send accumulated precipitation satellite image forecast for the next 24 hours to the user. """

    functionsLogger.debug("Getting acumulada previsão images...")

    acumuladaPrevisaoImageURL = scrap_satelites.get_acumulada_previsao_24hrs()

    context.bot.send_message(chat_id=update.effective_chat.id, text="Precipitação acumulada prevista para as próximas 24 horas:", parse_mode="markdown")

    context.bot.send_photo(chat_id=update.effective_chat.id, reply_to_message_id=update.message.message_id, photo=acumuladaPrevisaoImageURL)


@bot_utils.send_typing_action
def cmd_alertas_brasil(update, context):
    """ Fetch and send active high-risk alerts for Brazil. """

    functionsLogger.debug("Getting alerts for Brazil...")

    alerts = parse_alerts.parse_alerts(ignoreModerate=True)
    if alerts:
        alertMessage = ""
        for alert in alerts:
                alertMessage += bot_utils.get_alert_message_object(alert)
        alertMessage += "\nVeja os gráficos em http://www.inmet.gov.br/portal/alert-as/"
    else:
        alertMessage = "✅ Não há alertas graves para o Brasil no momento.\n\nVocê pode ver outros alertas menores em http://www.inmet.gov.br/portal/alert-as/"

    context.bot.send_message(chat_id=update.effective_chat.id, reply_to_message_id=update.message.message_id, text=alertMessage, parse_mode="markdown", disable_web_page_preview=True)


@bot_utils.send_typing_action
def cmd_alertas_CEP(update, context):
    """ Fetch and send active high-risk alerts for given CEP (zip code). """

    functionsLogger.debug("Getting alerts by CEP (zip code)...")

    text = update.message.text
    try:
        cep = text.split(' ')[1]  # Get string after "/alertas_CEP"
    except IndexError as indexE:  # No number after /alertas_CEP
        functionsLogger.error(f"{indexE} on cmd_alertas_CEP. Message text: \"{text}\"")
        context.bot.send_message(chat_id=update.effective_chat.id, reply_to_message_id=update.message.message_id, text="❌ CEP não informado!\nExemplo:\n`/alertas_CEP 29075-910`", parse_mode="markdown")
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
                    # functionsLogger.debug(alert.cities)
                    if city in alert.cities:
                        cityWarned = True
                        alertMessage += bot_utils.get_alert_message_object(alert, city)

                alertMessage += "\nVeja os gráficos em http://www.inmet.gov.br/portal/alert-as/"
                if not cityWarned:
                    alertMessage = f"✅ Não há alertas para {city} no momento.\n\nVocê pode ver outros alertas em http://www.inmet.gov.br/portal/alert-as/"
            else:
                alertMessage = "✅ Não há alertas para o Brasil no momento."

            context.bot.send_message(chat_id=update.effective_chat.id, reply_to_message_id=update.message.message_id, text=alertMessage, parse_mode="markdown", disable_web_page_preview=True)
        else:
            context.bot.send_message(chat_id=update.effective_chat.id, reply_to_message_id=update.message.message_id, text="❌ CEP inválido/não existe!\nExemplo:\n`/alertas_CEP 29075-910`", parse_mode="markdown")
    except pycep.excecoes.ExcecaoPyCEPCorreios as zipError:  # Invalid zip code
        functionsLogger.error(f"{zipError} on cmd_alertas_cep. Message text: \"{text}\"")
        context.bot.send_message(chat_id=update.effective_chat.id, reply_to_message_id=update.message.message_id, text="❌ CEP inválido/não existe!\nExemplo:\n`/alertas_CEP 29075-910`", parse_mode="markdown")
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
            functionsLogger.info("Successful GET request to reverse geocoding API!")
            json = reverseGeocode.json()
            functionsLogger.debug(f"reverseGeocode json: {json}")
            state = json["nearest"]["state"]
            if state == "BR":
                city = json["nearest"]["region"]
                cityWarned = False

                alerts = parse_alerts.parse_alerts(ignoreModerate=False)
                if alerts:
                    alertMessage = ""
                    for alert in alerts:
                        # functionsLogger.debug(alert.cities)
                        if city in alert.cities:
                            cityWarned = True
                            alertMessage += bot_utils.get_alert_message_object(alert, city)

                    alertMessage += "\nVeja os gráficos em http://www.inmet.gov.br/portal/alert-as/"

                    if not cityWarned:
                        alertMessage = f"✅ Não há alertas para {city} no momento.\n\nVocê pode ver outros alertas em http://www.inmet.gov.br/portal/alert-as/"
                else:
                    alertMessage = "✅ Não há alertas para o Brasil no momento."

                context.bot.send_message(chat_id=update.effective_chat.id,  reply_to_message_id=update.message.message_id, text=alertMessage, parse_mode="markdown", disable_web_page_preview=True)

            else:
                context.bot.send_message(chat_id=update.effective_chat.id,  reply_to_message_id=update.message.message_id, text="❌ A localização indica uma região fora do Brasil.", parse_mode="markdown")

        else:
            functionsLogger.error("Failed GET request to reverse geocoding API.")
            context.bot.send_message(chat_id=update.effective_chat.id,  reply_to_message_id=update.message.message_id, text="❌ Não foi possível verificar a região 😔", parse_mode="markdown")


@bot_utils.send_typing_action
def cmd_inscrito_alertas(update, context):
    statusMessage = ""
    isGroupOrChannel = bot_utils.is_group_or_channel(update.effective_chat.id)

    if models.is_subscribed(update.effective_chat.id):
        if isGroupOrChannel:
            statusMessage += "O grupo está inscrito nos alertas.\n\n"
        else:
            statusMessage += "Você está inscrito nos alertas.\n\n"
        CEPs = models.get_CEPs(update.effective_chat.id)
        if CEPs:
            statusMessage += "CEPs inscritos:\n"
            for cep in CEPs:
                statusMessage += f"{cep}\n"
        else:
            statusMessage += "Não há CEPs inscritos."
    else:
        if isGroupOrChannel:
            statusMessage += "O grupo não está inscrito nos alertas."
        else:
            statusMessage += "Você não está inscrito nos alertas."
    context.bot.send_message(chat_id=update.effective_chat.id, reply_to_message_id=update.message.message_id, text=statusMessage, parse_mode="markdown")



@bot_utils.send_typing_action
def cmd_desinscrever_alertas(update, context):
    text = update.message.text

    # Parse input
    try:
        cep = text.split(' ')[1].replace("-", "")  # Get string after "/alertas_CEP"
    except IndexError as indexE:  # No number after /alertas_CEP
        functionsLogger.warning(f"{indexE} on cmd_subscribe_alerts. Message text: \"{text}\"")
        cep = None
    else:
        if not pycep.validar_cep(cep):
            context.bot.send_message(chat_id=update.effective_chat.id, reply_to_message_id=update.message.message_id, text=f"❌ CEP inválido/não existe!\nExemplo:\n`{text.split(' ')[0]} 29075-910`", parse_mode="markdown")
            return None

    # Check if is subscribed and cep was given
    if models.is_subscribed(update.effective_chat.id) and not cep:
        models.unsubscribe_chat(update.effective_chat.id, cep)
        if bot_utils.is_group_or_channel(update.effective_chat.id):
            unsubscribed = models.unsubscribe_chat(update.effective_chat.id, cep)
            context.bot.send_message(chat_id=update.effective_chat.id, reply_to_message_id=update.message.message_id, text="🔕 O grupo foi desinscrito dos alertas.\nInscreva o grupo com /inscrever.", parse_mode="markdown")
        else:
            unsubscribed = models.unsubscribe_chat(update.effective_chat.id, cep)
            context.bot.send_message(chat_id=update.effective_chat.id, reply_to_message_id=update.message.message_id, text="🔕 Você foi desinscrito dos alertas.\nInscreva-se com /inscrever.", parse_mode="markdown")
    elif models.is_subscribed(update.effective_chat.id) and cep:
        unsubscribed = models.unsubscribe_chat(update.effective_chat.id, cep)
        if unsubscribed:
            context.bot.send_message(chat_id=update.effective_chat.id, reply_to_message_id=update.message.message_id, text=f"🔕 Desinscrevi o CEP {cep}.", parse_mode="markdown")
        else:
            context.bot.send_message(chat_id=update.effective_chat.id, reply_to_message_id=update.message.message_id, text=f"❌ O CEP {cep} não está inscrito.\nAdicione CEPs: `/inscrever {cep}`", parse_mode="markdown")
    else:
        if bot_utils.is_group_or_channel(update.effective_chat.id):
            context.bot.send_message(chat_id=update.effective_chat.id, reply_to_message_id=update.message.message_id, text="❌ O grupo não está inscrito nos alertas.\nInscreva-o com /inscrever.", parse_mode="markdown")
        else:
            context.bot.send_message(chat_id=update.effective_chat.id, reply_to_message_id=update.message.message_id, text="❌ Você não está inscrito nos alertas.\nInscreva-se com /inscrever.", parse_mode="markdown")


@bot_utils.send_typing_action
def cmd_subscribe_alerts(update, context):
    text = update.message.text

    # Parse input
    try:
        cep = text.split(' ')[1].replace("-", "")  # Get string after "/alertas_CEP"
    except IndexError as indexE:  # No number after /alertas_CEP
        functionsLogger.warning(f"{indexE} on cmd_subscribe_alerts. Message text: \"{text}\"")
        cep = None
    else:
        if not pycep.validar_cep(cep):
            context.bot.send_message(chat_id=update.effective_chat.id, reply_to_message_id=update.message.message_id, text=f"❌ CEP inválido/não existe!\nExemplo:\n`{text.split(' ')[0]} 29075-910`", parse_mode="markdown")
            return None

    # Check if is subscribed and cep was given
    if models.is_subscribed(update.effective_chat.id) and not cep:
        if bot_utils.is_group_or_channel(update.effective_chat.id):
            context.bot.send_message(chat_id=update.effective_chat.id, reply_to_message_id=update.message.message_id, text="❕O grupo já está inscrito.\nAdicione CEPs: `/inscrever 29075-910`.\nDesinscreva o grupo com /desinscrever.", parse_mode="markdown")
        else:
            context.bot.send_message(chat_id=update.effective_chat.id, reply_to_message_id=update.message.message_id, text="❕Você já está inscrito.\nAdicione CEPs: `/inscrever 29075-910`.\nDesinscreva-se com /desinscrever.", parse_mode="markdown")
    elif models.is_subscribed(update.effective_chat.id) and cep:
        subscribed = models.subscribe_chat(update.effective_chat.id, cep)
        if subscribed:
            context.bot.send_message(chat_id=update.effective_chat.id, reply_to_message_id=update.message.message_id, text=f"🔔 Inscrevi o CEP {cep}.\nDesinscreva CEPs: `/desinscrever {cep}`.", parse_mode="markdown")
        else:
            context.bot.send_message(chat_id=update.effective_chat.id, reply_to_message_id=update.message.message_id, text=f"❕O CEP {cep} já está inscrito.\nDesinscreva CEPs: `/desinscrever {cep}`.\nDesinscreva o grupo com /desinscrever.", parse_mode="markdown")

    elif not models.is_subscribed(update.effective_chat.id) and cep:
        if bot_utils.is_group_or_channel(update.effective_chat.id):
            functionsLogger.debug("Inscrevendo grupo")
            models.subscribe_chat(update.effective_chat.id, cep)
            context.bot.send_message(chat_id=update.effective_chat.id, reply_to_message_id=update.message.message_id, text=f"🔔 Inscrevi o grupo e o CEP {cep}.\nDesinscreva o grupo com /desinscrever.", parse_mode="markdown")
        else:
            functionsLogger.debug("Inscrevendo privado")
            models.subscribe_chat(update.effective_chat.id, cep)
            context.bot.send_message(chat_id=update.effective_chat.id, reply_to_message_id=update.message.message_id, text=f"🔔 Inscrevi você e o CEP {cep}.\nDesinscreva-se com /desinscrever.", parse_mode="markdown")
    else:  # Not subscribed and cep not given
        if bot_utils.is_group_or_channel(update.effective_chat.id):
            functionsLogger.debug("Inscrevendo grupo")
            models.subscribe_chat(update.effective_chat.id, cep)
            context.bot.send_message(chat_id=update.effective_chat.id, reply_to_message_id=update.message.message_id, text="🔔 Inscrevi o grupo.\nAdicione CEPs: `/inscrever 29075-910`.\nDesinscreva o grupo com /desinscrever.", parse_mode="markdown")
        else:
            functionsLogger.debug("Inscrevendo privado")
            models.subscribe_chat(update.effective_chat.id, cep)
            context.bot.send_message(chat_id=update.effective_chat.id, reply_to_message_id=update.message.message_id, text="🔔 Inscrevi você.\nAdicione CEPs: `/inscrever 29075-910`.\nDesinscreva-se com /desinscrever.", parse_mode="markdown")


@bot_utils.send_upload_video_action
def cmd_sorrizoronaldo(update, context):
    """ Send default Sorrizo Ronaldo video. """

    context.bot.send_message(chat_id=update.effective_chat.id,  reply_to_message_id=update.message.message_id, text=bot_messages.sorrizoChegou, parse_mode="markdown")
    context.bot.send_video(chat_id=update.effective_chat.id, video="BAACAgEAAxkBAAPmXkSUcBDsVM300QABV4Oerb9PcUx3AAL8AAODXihGe5y1jndyb80YBA")


@bot_utils.send_upload_video_action
def cmd_sorrizoronaldo_will_rock_you(update, context):
    """ Send "We Will Rock You" Sorrizo Ronaldo video variation. """

    context.bot.send_message(chat_id=update.effective_chat.id,  reply_to_message_id=update.message.message_id, text=bot_messages.sorrizoQueen, parse_mode="markdown")
    context.bot.send_video(chat_id=update.effective_chat.id, video="BAACAgEAAxkBAAICZ15HDelLB1IH1i3hTB8DaKwWlyPMAAJ8AAPfLzhG0hgf8dxd_zQYBA")


def error(update, context):
    """ Log errors caused by Updates. """

    functionsLogger.warning('Update "%s" caused error "%s"', update, context.error)
