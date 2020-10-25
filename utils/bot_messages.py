# Plain strings for the bot

welcomeMessage = """🌥 @INMETBot
Olá! Este bot pode enviar imagens e informações úteis disponíveis pelo INMET diretamente pelo Telegram.

🕹 *COMANDOS DISPONÍVEIS*:
/start exibe esta mensagem de boas-vindas.
/help ou /ajuda exibe a mensagem de ajuda.
/alertas ou /alertas\_brasil exibe alertas graves em vigor no Brasil.
`/alertas_CEP` exibe alertas graves em vigor para o CEP fornecido.
Exemplo: `/alertas_CEP 29075-910`.
\* Você também pode simplesmente enviar sua localização para checar alertas em sua cidade.
/inscrever inscreve o chat para ser avisado automaticamente quando alertas incluírem regiões cadastradas. Para isso, adicione CEPs com `/inscrever 29075-910`, por exemplo.
/status exibe o status de inscrição do chat nos alertas e lista CEPs inscritos.
/desativar desativa as notificações de alertas para o chat (os CEPs continuam salvos). Para ativar novamente, basta usar o comando /ativar.
/mapa exibe imagem do mapa de alertas disponível pelo Alert-AS.
/nuvem ou /vpr exibe imagens de vapor de água realçado (vapor de água na média e alta atmosfera).
/nuvens ou /vpr\_gif exibe GIF feito do número de imagens fornecido.
Exemplo: `/nuvens 5`
/acumulada exibe imagem de precipitação acumulada no intervalo de dias especificado (1, 3, 5, 10, 15, 30 ou 90) anteriores ao atual no Brasil.
Exemplo: `/acumulada 3`
Para mais detalhes, clique em /help.

—
Não filiado ao INMET
✈️ Criado por @AtilioA
💰 Doações: PicPay @atilioa
"""

helpMessage = """🌥 @INMETBot
Para utilizar o bot, envie alguns destes comandos:

🕹 *COMANDOS DISPONÍVEIS*:
❔ -
/start exibe a mensagem de boas-vindas.
/help ou /ajuda exibe esta mensagem de ajuda.
⚠️ -
/alertas ou /alertas\_brasil exibe alertas *graves* (apenas laranjas e vermelhos) em vigor para o Brasil.
`/alertas_CEP` exibe alertas *graves e moderados* (todos) em vigor para o CEP fornecido.
Exemplo: `/alertas_CEP 29075-910` exibe alertas *graves e moderados* para o CEP 29075-910.
\* Você também pode simplesmente enviar sua localização para checar alertas em sua cidade a qualquer momento.
/inscrever inscreve você ou o seu grupo para ser avisado automaticamente quando alertas incluírem sua região. Para isso, adicione CEPs com `/inscrever 29075-910`, por exemplo.
/desinscrever desinscreve o chat e CEPs dos alertas.
/status exibe o status de inscrição do chat nos alertas e lista CEPs inscritos.
/desativar desativa as notificações de alertas para o chat (*os CEPs continuam salvos*). Para ativar novamente, basta usar o comando /ativar.
/mapa ou /mapa\_alertas exibe imagem do mapa de alertas disponível pelo Alert-AS.
🛰 -
/nuvem ou /vpr exibe a última imagem do satélite de vapor de água realçado (vapor de água na média e alta atmosfera).
/nuvens ou /vpr\_gif exibe GIF feito do número de imagens fornecido.
Exemplo: `/nuvens 5` exibe um GIF com as últimas 5 imagens do satélite de vapor de água realçado.
/acumulada exibe imagem de precipitação acumulada no intervalo de dias especificado (1, 3, 5, 10, 15, 30 ou 90) anteriores ao atual no Brasil.
Exemplo: `/acumulada 3` exibe o mapa de precipitação acumulada nas últimas 72h (3 dias).

📖 *Bot open-source*:
https://github.com/AtilioA/INMETBot

—
Não filiado ao INMET
✈️ Criado por @AtilioA
💰 Doações: PicPay @atilioa
"""

instructions = "Instruções de uso: clique em /help ou /ajuda."

acumuladaWarn = "❕ O intervalo não é válido! Portanto, utilizarei *{interval}* (valor mais próximo de {inputInterval}).\nOs intervalos de dias permitidos são: 1, 3, 5, 10, 15, 30 e 90 dias.\nExemplo:\n`/acumulada 3`"
acumuladaWarnMissing = "❕ Não foi possível identificar o intervalo de dias! Portanto, utilizarei *{interval}* como valor.\nOs intervalos de dias permitidos são: 1, 3, 5, 10, 15, 30 e 90 dias.\nExemplo:\n`/acumulada 3`"

sorrizoChegou = "É O *SORRIZO RONALDO* 😁 QUE CHEGOU..."
sorrizoQueen = "👊👊👏 *SORRIZ*.."

lastAvailableImageCaption = "Última imagem disponível"
waitMessageSearchGIF = "⏳ Buscando as últimas {nImages} imagens e criando GIF..."
failedFetchImage = "❌ Não foi possível obter a imagem!"
unavailableImage = "❌ Imagem indisponível."

moreInfoAlertAS = "\nMais informações em http://www.inmet.gov.br/portal/alert-as/"
noAlertsBrazil = "✅ Não há alertas graves para o Brasil no momento.\n\nVocê pode ver outros alertas menores em http://www.inmet.gov.br/portal/alert-as/"
noAlertsCity = "✅ Não há alertas para {city} no momento.\n\nVocê pode ver outros alertas em http://www.inmet.gov.br/portal/alert-as/"
locationOutsideBrazil = "❌ A localização indica uma região fora do Brasil."
unableCheckAlertsLocation = "❌ Não foi possível verificar a região 😔."
invalidZipCode = "❌ CEP inválido/não existe!\nExemplo:\n`{textArgs} 29075-910`"
alertsMapMessage = "⏳ Buscando imagem do mapa de alertas..."


def createForecastMessage(date, forecastDay):
    try:
        city = forecastDay["entidade"]
    except (KeyError, IndexError):
        city = forecastDay["manha"]["entidade"]

    forecastMessage = f"*PREVISÃO PARA {city} - {date}\n\n*".upper()

    print("Oi")
    try:
        forecastDayMorning = forecastDay["manha"]
        forecastDayAfternoon = forecastDay["tarde"]
        forecastDayEvening = forecastDay["noite"]

        if forecastDayMorning:
            forecastMessage += """🌄 *Manhã*:"""
            forecastMessage += forecastText(
                forecastDayMorning["cod_icone"],
                forecastDayMorning["resumo"],
                forecastDayMorning["temp_max"],
                forecastDayMorning["temp_min"],
                forecastDayMorning["umidade_max"],
                forecastDayMorning["umidade_min"],
                forecastDayMorning["dir_vento"],
                forecastDayMorning["int_vento"],
                forecastDayMorning["nascer"],
                forecastDayMorning["ocaso"],
            )
        if forecastDayAfternoon:
            forecastMessage += """\n🕑 *Tarde*:"""
            forecastMessage += forecastText(
                forecastDayAfternoon["cod_icone"],
                forecastDayAfternoon["resumo"],
                forecastDayAfternoon["temp_max"],
                forecastDayAfternoon["temp_min"],
                forecastDayAfternoon["umidade_max"],
                forecastDayAfternoon["umidade_min"],
                forecastDayAfternoon["dir_vento"],
                forecastDayAfternoon["int_vento"],
                forecastDayAfternoon["nascer"],
                forecastDayAfternoon["ocaso"],
            )
        if forecastDayEvening:
            forecastMessage += """\n🌌 *Noite*:"""
            forecastMessage += forecastText(
                forecastDayEvening["cod_icone"],
                forecastDayEvening["resumo"],
                forecastDayEvening["temp_max"],
                forecastDayEvening["temp_min"],
                forecastDayEvening["umidade_max"],
                forecastDayEvening["umidade_min"],
                forecastDayEvening["dir_vento"],
                forecastDayEvening["int_vento"],
                forecastDayEvening["nascer"],
                forecastDayEvening["ocaso"],
            )

    except (KeyError, IndexError):
        forecastMessage += forecastText(
            forecastDay["cod_icone"],
            forecastDay["resumo"],
            forecastDay["temp_max"],
            forecastDay["temp_min"],
            forecastDay["umidade_max"],
            forecastDay["umidade_min"],
            forecastDay["dir_vento"],
            forecastDay["int_vento"],
            forecastDay["nascer"],
            forecastDay["ocaso"],
            isWholeDay=True,
        )

    forecastMessage += "\nFonte: INMET - PrevMet"

    return forecastMessage


def forecastText(
    forecastIcon,
    summary,
    maxTemperature,
    minTemperature,
    maxHumidity,
    minHumidity,
    windDirection,
    windIntensity,
    sunriseTime,
    sunsetTime,
    isWholeDay=False,
):
    forecastIconDict = {
        46: "🌧",
        60: "⛈",
        87: "⛈",
        88: "🌥⛈",
        34: "⛅️🌥",
    }

    if not isWholeDay:
        """
    🔥 Temperatura máxima: *{maxTemperature}°C*
    ❄️ Temperatura mínima: *{minTemperature}°C*

    💦 Umidade máxima: *{maxHumidity}%*
    💧 Umidade mínima: *{minHumidity}%*

    🧭 Direção dos ventos: {windDirection}
    💨 Intensidade dos ventos: {windIntensity}

    🌅 Nascer do sol: \t{sunriseTime}
    🌇 Pôr do sol: \t{sunsetTime}
        """

    forecastMessage = f"""
    \t*{forecastIconDict.get(int(forecastIcon), "")} {summary}*
    """

    if isWholeDay:
        """
    🔥 Temperatura máxima: *{maxTemperature}°C*
    ❄️ Temperatura mínima: *{minTemperature}°C*

    💦 Umidade máxima: *{maxHumidity}%*
    💧 Umidade mínima: *{minHumidity}%*

    🧭 Direção dos ventos: {windDirection}
    💨 Intensidade dos ventos: {windIntensity}

    🌅 Nascer do sol: \t{sunriseTime}
    🌇 Pôr do sol: \t{sunsetTime}
        """

    return forecastMessage


# forecastMessage = """
# 🌄 Manhã:

#     {forecastIconDict.get(forecastIcon)}{summaryMorning}

#     🔥 Temperatura máxima: {maxTemperatureMorning}
#     ❄️ Temperatura mínima: {minTemperatureMorning}

#     💦 Umidade máxima: {maxHumidityMorning}
#     💧 Umidade mínima: {minHumidityMorning}

#     🧭 Direção dos ventos: {windDirectionMorning}
#     📶 ou 💪 ou 💨 Intensidade dos ventos: {windIntensityMorning}

#     🌅 Nascer do sol: {sunriseTimeMorning}
#     🌇 Pôr do sol: {sunsetTimeMorning}

# —
# 🕑 Tarde:

#     {forecastIconDict.get(forecastIcon)}{summaryAfternoon}

#     🔥 Temperatura máxima: {maxTemperatureAfternoon}
#     ❄️ Temperatura mínima: {minTemperatureAfternoon}

#     💦 Umidade máxima: {maxHumidityAfternoon}
#     💧 Umidade mínima: {minHumidityAfternoon}

#     🧭 Direção dos ventos: {windDirectionAfternoon}
#     📶 ou 💪 ou 💨 Intensidade dos ventos: {windIntensityAfternoon}

#     🌅 Nascer do sol: {sunriseTimeAfternoon}
#     🌇 Pôr do sol: {sunsetTimeAfternoon}

# —
# 🌌 Noite:
#     {forecastIconDict.get(forecastIcon)}{summaryEvening}

#     🔥 Temperatura máxima: {maxTemperatureEvening}
#     ❄️ Temperatura mínima: {minTemperatureEvening}

#     💦 Umidade máxima: {maxHumidityEvening}
#     💧 Umidade mínima: {minHumidityEvening}

#     🧭 Direção dos ventos: {windDirectionEvening}
#     📶 ou 💪 ou 💨 Intensidade dos ventos: {windIntensityEvening}

#     🌅 Nascer do sol: {sunriseTimeEvening}
#     🌇 Pôr do sol: {sunsetTimeEvening}

# Fonte: INMET - PrevMet
# """
