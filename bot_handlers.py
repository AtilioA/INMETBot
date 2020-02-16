from telegram.ext import CommandHandler, Filters, MessageHandler

from bot_config import dispatcher, bot
from bot_functions import *

# Initialize handlers
start_handler = CommandHandler('start', start)
help_handler = CommandHandler(('help', 'ajuda'), help_msg)

vpr_handler = CommandHandler(('vpr', 'vapor_de_agua', 'nuvens'), vpr)
vpr_gif_handler = CommandHandler('vpr_gif', vpr_gif)

acumulada_handler = CommandHandler('acumulada', acumulada)
acumulada_previsao_24hrs_handler = CommandHandler('acumulada_previsao_24hrs', acumulada_previsao_24hrs)

alertas_brasil_handler = CommandHandler(('alertas', 'alertas_brasil', 'avisos'), alertas_brasil)
alertas_CEP_handler = CommandHandler('alertas_CEP', alertas_CEP)

sorrizoronaldo_handler = CommandHandler(('sorrizo', 'sorrizoronaldo', 'fodase'), sorrizoronaldo)
sorrizoronaldo_will_rock_you_handler = CommandHandler(('sorrizoronaldo_will_rock_you', 'sorrizorock', 'sorrizoqueen', 'queenfodase'), sorrizoronaldo_will_rock_you)

# Add handlers to dispatcher
dispatcher.add_handler(start_handler)
dispatcher.add_handler(help_handler)

dispatcher.add_handler(vpr_handler)
dispatcher.add_handler(vpr_gif_handler)

dispatcher.add_handler(acumulada_handler)
dispatcher.add_handler(acumulada_previsao_24hrs_handler)

dispatcher.add_handler(alertas_brasil_handler)
dispatcher.add_handler(alertas_CEP_handler)
dispatcher.add_handler(MessageHandler(Filters.location, alertas_location))

dispatcher.add_handler(sorrizoronaldo_handler)
dispatcher.add_handler(sorrizoronaldo_will_rock_you_handler)
dispatcher.add_handler(sorrizoronaldo_will_rock_you_handler)

dispatcher.add_handler(MessageHandler(Filters.text, catch_all_if_not_group))
