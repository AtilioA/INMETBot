from telegram.ext import CommandHandler, Filters, MessageHandler

import bot_functions
from bot_config import dispatcher

# Initialize handlers
start_handler = CommandHandler(
    "start", bot_functions.cmd_start, filters=~Filters.update.edited_message
)
help_handler = CommandHandler(
    ("help", "ajuda"), bot_functions.cmd_help, filters=~Filters.update.edited_message
)

vpr_handler = CommandHandler(
    ("vpr", "vapor_de_agua", "nuvem"),
    bot_functions.cmd_vpr,
    filters=~Filters.update.edited_message,
)
vpr_gif_handler = CommandHandler(
    ("vpr_gif", "nuvens", "nuvems", "vprs"),
    bot_functions.cmd_vpr_gif,
    filters=~Filters.update.edited_message,
)

acumulada_handler = CommandHandler(
    "acumulada", bot_functions.cmd_acumulada, filters=~Filters.update.edited_message
)

alerts_brazil_handler = CommandHandler(
    ("alertas", "alertas_brasil", "avisos"),
    bot_functions.cmd_alerts_brazil,
    filters=~Filters.update.edited_message,
)
alerts_CEP_handler = CommandHandler(
    "alertas_CEP", bot_functions.cmd_alerts_CEP, filters=~Filters.update.edited_message
)
alerts_location_handler = MessageHandler(
    Filters.location & ~Filters.update.edited_message, bot_functions.alerts_location
)
alerts_map_handler = CommandHandler(
    ("mapa", "alertas_mapa", "mapa_alertas", "mapa_avisos"),
    bot_functions.cmd_alerts_map,
    filters=~Filters.update.edited_message,
)
chat_subscribe_alerts_handler = CommandHandler(
    ("inscrever_alertas", "alertas_inscrever", "inscrever"),
    bot_functions.cmd_chat_subscribe_alerts,
    filters=~Filters.update.edited_message,
)
chat_unsubscribe_alerts_handler = CommandHandler(
    ("desinscrever_alertas", "alertas_desinscrever", "desinscrever"),
    bot_functions.cmd_chat_unsubscribe_alerts,
    filters=~Filters.update.edited_message,
)
chat_subscription_status_handler = CommandHandler(
    ("inscrito", "status"),
    bot_functions.cmd_chat_subscription_status,
    filters=~Filters.update.edited_message,
)

forecast_handler = CommandHandler(
    ("previsao"),
    bot_functions.cmd_forecast,
    filters=~Filters.update.edited_message,
)

deactivate_handler = CommandHandler(("desativar"), bot_functions.cmd_chat_deactivate)
activate_handler = CommandHandler(("ativar"), bot_functions.cmd_chat_activate)
toggle_activated_handler = CommandHandler(
    ("alternar", "toggle"), bot_functions.cmd_chat_toggle_activated
)

sorrizoronaldo_handler = CommandHandler(
    ("sorrizo", "sorrizoronaldo", "fodase", "earte", "ead"),
    bot_functions.cmd_sorrizoronaldo,
    filters=~Filters.update.edited_message,
)
sorrizoronaldo_will_rock_you_handler = CommandHandler(
    (
        "sorrizoronaldo_will_rock_you",
        "sorrizorock",
        "sorrizoqueen",
        "queenfodase",
        "sorriz",
    ),
    bot_functions.cmd_sorrizoronaldo_will_rock_you,
    filters=~Filters.update.edited_message,
)

update_handler = CommandHandler(
    ("update"),
    bot_functions.cmd_update_alerts,
    filters=~Filters.update.edited_message,
)

catch_all_if_private_handler = MessageHandler(
    Filters.text & ~Filters.update.edited_message, bot_functions.catch_all_if_private
)

# Add handlers to dispatcher
dispatcher.add_handler(start_handler)
dispatcher.add_handler(help_handler)

dispatcher.add_handler(vpr_handler)
dispatcher.add_handler(vpr_gif_handler)

dispatcher.add_handler(acumulada_handler)

dispatcher.add_handler(alerts_brazil_handler)
dispatcher.add_handler(alerts_CEP_handler)
dispatcher.add_handler(alerts_map_handler)

dispatcher.add_handler(chat_subscribe_alerts_handler)
dispatcher.add_handler(chat_unsubscribe_alerts_handler)
dispatcher.add_handler(chat_subscription_status_handler)
dispatcher.add_handler(deactivate_handler)
dispatcher.add_handler(activate_handler)
dispatcher.add_handler(toggle_activated_handler)

dispatcher.add_handler(forecast_handler)

dispatcher.add_handler(sorrizoronaldo_handler)
dispatcher.add_handler(sorrizoronaldo_will_rock_you_handler)

dispatcher.add_handler(update_handler)

dispatcher.add_handler(alerts_location_handler)

dispatcher.add_error_handler(bot_functions.error)

dispatcher.add_handler(catch_all_if_private_handler)
