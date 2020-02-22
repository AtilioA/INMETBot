from telegram.ext import CommandHandler, Filters, MessageHandler

from bot_config import dispatcher
import bot_functions

# Initialize handlers
start_handler = CommandHandler('start', bot_functions.cmd_start)
help_handler = CommandHandler(('help', 'ajuda'), bot_functions.cmd_help)

vpr_handler = CommandHandler(('vpr', 'vapor_de_agua', 'nuvem'), bot_functions.cmd_vpr)
vpr_gif_handler = CommandHandler(('vpr_gif', 'nuvens'), bot_functions.cmd_vpr_gif)

acumulada_handler = CommandHandler('acumulada', bot_functions.cmd_acumulada)
acumulada_previsao_24hrs_handler = CommandHandler('acumulada_previsao_24hrs', bot_functions.cmd_acumulada_previsao_24hrs)

alerts_brazil_handler = CommandHandler(('alertas', 'alertas_brasil', 'avisos'), bot_functions.cmd_alerts_brasil)
alerts_CEP_handler = CommandHandler('alertas_CEP', bot_functions.cmd_alerts_CEP)
alerts_location_handler = MessageHandler(Filters.location, bot_functions.alerts_location)
alerts_map_handler = CommandHandler(('mapa', 'alertas_mapa', 'mapa_alertas', 'mapa_avisos'), bot_functions.cmd_alerts_map)
subscribe_alerts_handler = CommandHandler(('inscrever_alertas', 'alertas_inscrever', 'inscrever'), bot_functions.cmd_subscribe_alerts)
unsubscribe_alerts_handler = CommandHandler(('desinscrever_alertas', 'alertas_desinscrever', 'desinscrever'), bot_functions.cmd_unsubscribe_alerts)
cmd_subscription_status_handler = CommandHandler(('inscrito', 'status'), bot_functions.cmd_subscription_status)

sorrizoronaldo_handler = CommandHandler(('sorrizo', 'sorrizoronaldo', 'fodase'), bot_functions.cmd_sorrizoronaldo)
sorrizoronaldo_will_rock_you_handler = CommandHandler(('sorrizoronaldo_will_rock_you', 'sorrizorock', 'sorrizoqueen', 'queenfodase'), bot_functions.cmd_sorrizoronaldo_will_rock_you)

catch_all_if_private_handler = MessageHandler(Filters.text, bot_functions.catch_all_if_private)

# Add handlers to dispatcher
dispatcher.add_handler(start_handler)
dispatcher.add_handler(help_handler)

dispatcher.add_handler(vpr_handler)
dispatcher.add_handler(vpr_gif_handler)

dispatcher.add_handler(acumulada_handler)
dispatcher.add_handler(acumulada_previsao_24hrs_handler)

dispatcher.add_handler(alerts_brazil_handler)
dispatcher.add_handler(alerts_CEP_handler)
dispatcher.add_handler(alerts_map_handler)
dispatcher.add_handler(subscribe_alerts_handler)
dispatcher.add_handler(unsubscribe_alerts_handler)
dispatcher.add_handler(cmd_subscription_status_handler)

dispatcher.add_handler(sorrizoronaldo_handler)
dispatcher.add_handler(sorrizoronaldo_will_rock_you_handler)

dispatcher.add_handler(alerts_location_handler)

dispatcher.add_error_handler(bot_functions.error)

dispatcher.add_handler(catch_all_if_private_handler)
