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
invalidZipcode = "❌ CEP inválido/não existe!\nExemplo:\n`{textArgs} 29075-910`"
alertsMapMessage = "⏳ Buscando imagem do mapa de alertas..."
