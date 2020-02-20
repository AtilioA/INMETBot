# [INMETBot](https://t.me/INMETBot)
[@INMETBot](https://t.me/INMETBot) - Bot no Telegram para solicitar imagens de satélites e alertas recentes (não filiado ao INMET)

# About
This is a bot that scrapes INMET's website and makes information available through [Telegram](http://telegram.org/). It runs on Python 3 and uses MongoDB. You can [try it here](https://telegram.me/INMETBot).

# Running locally
First, clone the repository and create a virtual environment for the project (to ensure you won't have problems with your other libraries versions):

`pipenv install` - Create virtual environment and install dependencies

`pipenv shell` - Activate virtual environment

Some of the bot's functionality depends on being connected to a MongoDB database. If you wish to use with your own database, just set its URI connection string to a environment variable in a `.env` file (in this case, exit and then activate the virtual environment again) or in your environment variables.

With everything set, you can start the bot with

`python main.py`
