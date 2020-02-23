# Plain strings for the bot

welcomeMessage = """🌥 @INMETBot
Olá! Este bot pode enviar imagens e informações úteis disponíveis pelo INMET diretamente pelo Telegram.

*COMANDOS DISPONÍVEIS*:
/start exibe esta mensagem de boas-vindas.
/help ou /ajuda exibe a mensagem de ajuda.
/nuvem ou /vpr exibe imagens de vapor de água realçado (vapor de água na média e alta atmosfera).
/nuvens ou /vpr\_gif exibe GIF feito do número de imagens fornecido.
Exemplo: `/nuvens 5`
/alertas ou /alertas\_brasil exibe alertas graves em vigor no Brasil.
`/alertas_CEP` exibe alertas graves em vigor para o CEP fornecido.
Exemplo: `/alertas_CEP 29075-910`
\* Você também pode simplesmente enviar sua localização para checar alertas em sua cidade.
/inscrever inscreve o chat para ser avisado automaticamente quando alertas incluírem regiões cadastradas. Para isso, adicione CEPs com `/inscrever 29075-910`, por exemplo.
/status exibe o status de inscrição do chat nos alertas e lista CEPs inscritos.
/mapa exibe imagem do mapa de alertas disponível pelo Alert-AS.
/acumulada exibe imagem de precipitação acumulada no intervalo de dias especificado (1, 3, 5, 10, 15, 30 ou 90) anteriores ao atual no Brasil.
Exemplo: `/acumulada 3`
/acumulada\_previsao exibe imagem de precipitação acumulada prevista para as próximas 24 horas no Brasil.
Para mais detalhes, clique em /help.

—
Não filiado ao INMET
Criado por @AtilioA
"""

helpMessage = """🌥 @INMETBot
Para utilizar o bot, envie alguns destes comandos:

🕹 *COMANDOS DISPONÍVEIS*
/start exibe a mensagem de boas-vindas.
/help ou /ajuda exibe esta mensagem de ajuda.
/nuvem ou /vpr exibe a última imagem do satélite de vapor de água realçado (vapor de água na média e alta atmosfera).
/nuvens ou /vpr\_gif exibe GIF feito do número de imagens fornecido.
Exemplo: `/nuvens 5` exibe um GIF com as últimas 5 imagens do satélite de vapor de água realçado.
/alertas ou /alertas\_brasil exibe alertas *graves* em vigor no Brasil.
`/alertas_CEP` exibe alertas *graves e moderados* em vigor para o CEP fornecido.
Exemplo: `/alertas_CEP 29075-910` exibe alertas graves e moderados para o CEP 29075-910.
\* Você também pode simplesmente enviar sua localização para checar alertas em sua cidade a qualquer momento.
/inscrever inscreve você ou o seu grupo para ser avisado automaticamente quando alertas incluírem sua região. Para isso, adicione CEPs com `/inscrever 29075-910`, por exemplo.
/status exibe o status de inscrição do chat nos alertas e lista CEPs inscritos.
/desinscrever desinscreve o chat e CEPs dos alertas.
/mapa ou /mapa\_alertas exibe imagem do mapa de alertas disponível pelo Alert-AS.
/acumulada exibe imagem de precipitação acumulada no intervalo de dias especificado (1, 3, 5, 10, 15, 30 ou 90) anteriores ao atual no Brasil.
Exemplo: `/acumulada 3` exibe o mapa de precipitação acumulada nas últimas 72h.
/acumulada\_previsao exibe imagem de precipitação acumulada prevista para as próximas 24 horas no Brasil.

📖 Bot open-source:
https://github.com/AtilioA/INMETBot

—
Não filiado ao INMET
Criado por @AtilioA
"""

instructions = "Instruções de uso: clique em /help ou /ajuda."
acumuladaError = "❌ Não foi possível identificar o intervalo de dias! Portanto, utilizarei 1 como valor.\nOs intervalos de dias permitidos são 1, 3, 5, 10, 15, 30 e 90 dias.\nExemplo:\n`/acumulada 3`"
alertsMapMessage = "⏳ Buscando imagem do mapa de alertas..."
sorrizoChegou = "É O *SORRIZO RONALDO* 😁 QUE CHEGOU..."
sorrizoQueen = "👊👊👏 *SORRIZ*.."
