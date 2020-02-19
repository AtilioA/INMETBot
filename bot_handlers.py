from telegram.ext import CommandHandler, Filters, MessageHandler

from bot_config import dispatcher, bot
import bot_functions

# Initialize handlers
start_handler = CommandHandler('start', bot_functions.cmd_start)
help_handler = CommandHandler(('help', 'ajuda'), bot_functions.cmd_help)

vpr_handler = CommandHandler(('vpr', 'vapor_de_agua', 'nuvem'), bot_functions.cmd_vpr)
vpr_gif_handler = CommandHandler(('vpr_gif', 'nuvens'), bot_functions.cmd_vpr_gif)

acumulada_handler = CommandHandler('acumulada', bot_functions.cmd_acumulada)
acumulada_previsao_24hrs_handler = CommandHandler('acumulada_previsao_24hrs', bot_functions.cmd_acumulada_previsao_24hrs)

alertas_brasil_handler = CommandHandler(('alertas', 'alertas_brasil', 'avisos'), bot_functions.cmd_alertas_brasil)
alertas_CEP_handler = CommandHandler('alertas_CEP', bot_functions.cmd_alertas_CEP)
alertas_location_handler = MessageHandler(Filters.location, bot_functions.alertas_location)
inscrever_alertas_handler = CommandHandler(('inscrever_alertas', 'alertas_inscrever', 'inscrever'), bot_functions.cmd_subscribe_alerts)
desinscrever_alertas_handler = CommandHandler(('desinscrever_alertas', 'alertas_desinscrever', 'desinscrever'), bot_functions.cmd_desinscrever_alertas)
inscrito_alertas_handler = CommandHandler(('inscrito', 'status'), bot_functions.cmd_inscrito_alertas)

sorrizoronaldo_handler = CommandHandler(('sorrizo', 'sorrizoronaldo', 'fodase'), bot_functions.cmd_sorrizoronaldo)
sorrizoronaldo_will_rock_you_handler = CommandHandler(('sorrizoronaldo_will_rock_you', 'sorrizorock', 'sorrizoqueen', 'queenfodase'), bot_functions.cmd_sorrizoronaldo_will_rock_you)

catch_all_if_not_group_handler = MessageHandler(Filters.text, bot_functions.catch_all_if_not_group)

# Add handlers to dispatcher
dispatcher.add_handler(start_handler)
dispatcher.add_handler(help_handler)

dispatcher.add_handler(vpr_handler)
dispatcher.add_handler(vpr_gif_handler)

dispatcher.add_handler(acumulada_handler)
dispatcher.add_handler(acumulada_previsao_24hrs_handler)

dispatcher.add_handler(alertas_brasil_handler)
dispatcher.add_handler(alertas_CEP_handler)
dispatcher.add_handler(inscrever_alertas_handler)
dispatcher.add_handler(desinscrever_alertas_handler)
dispatcher.add_handler(inscrito_alertas_handler)

dispatcher.add_handler(sorrizoronaldo_handler)
dispatcher.add_handler(sorrizoronaldo_will_rock_you_handler)

dispatcher.add_handler(alertas_location_handler)
dispatcher.add_handler(catch_all_if_not_group_handler)

dispatcher.add_error_handler(bot_functions.error)
