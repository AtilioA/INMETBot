<h1 align="center">
  <a href="https://t.me/INMETBot">🛰 INMETBot</a>
</h1>

<h4 align="center"><a href="https://t.me/INMETBot">@INMETBot</a> - Bot no Telegram para solicitar imagens de satélites e alertas recentes (não filiado ao INMET).

Telegram bot to fetch satellite images and recent alerts (not affiliated to INMET).

<p align="center">
  <a href="#-about">About</a>&nbsp;&nbsp;&nbsp;|&nbsp;&nbsp;
  <a href="#-examples">Examples</a>&nbsp;&nbsp;&nbsp;|&nbsp;&nbsp;
  <a href="#-running-locally">Running locally</a>
</p>

</h4>

<h5 align="center">

[![Telegram bot](https://img.shields.io/badge/Telegram-bot-0088CC)](https://t.me/INMETBot) [![License: GPL v3](https://img.shields.io/badge/License-GPLv3-orange.svg)](https://www.gnu.org/licenses/gpl-3.0) ![GitHub code size in bytes](https://img.shields.io/github/languages/code-size/atilioa/inmetbot)

</h5>

# ℹ About

Telegram bot that scrapes INMET's website/consumes its API and makes information available through a [Telegram](http://telegram.org/) bot. It runs on Python 3 and uses MongoDB to store chat preferences. You can [try it here](https://telegram.me/INMETBot) (only available in pt-BR), or [learn to run a local instance](#-running-locally).

# 📖 Examples

The screenshots are slightly outdated, but can still convey the functionality:

- Creating GIF made of the last **10** images from the enhanced water vapor satellite:

  ![/nuvens command](.github/vpr.png)

- Subscribing to be notified about alerts affecting subscribed CEPs (Brazilian postal code):

  ![/inscrever command](.github/subscribe.png)

- Getting the alerts map from Alert-AS:

  ![/mapa command](.github/map.png)

You can learn more with the **`/help`** command.

# 🏡 Running locally

First, clone the repository and [make sure you have Docker installed](https://docs.docker.com/get-docker/). Inside the repository directory, build the local Docker image for INMETBot:

```bash
git clone https://github.com/AtilioA/INMETBot
cd INMETBot
docker build . -t inmetbot
```

Some of the bot's functionalities depend on being connected to a MongoDB database. If you wish to use your own database, just set the `INMETBOT_MONGO_URI` environment variable in the `.env.example` file to your URI connection string and rename the `.env.example` file to `.env` or, alternatively, set `INMETBOT_MONGO_URI` as an environment variable of the system hosting the bot. Using local databases have not been tested.

Finally, start the container while passing environment variables directly to Docker:

```bash
docker run -t --name inmetbot \
              -e TELEGRAM_INMETBOT_APIKEY=t.me/BotFather \
              -e INMETBOT_MONGO_URI='mongodb+srv://<user>:<password>@cluster0-fcm5r.mongodb.net/<collection>?retryWrites=true&w=majority' \
              inmetbot
```

Alternatively, again, you can rename `.env.example` to `.env` and fill the variables there, since they'll be copied over to the Docker container. This way, you can create the container by simply running `docker run -t --name inmetbot inmetbot`.

Running the bot without Docker is trickier, but possible. Create a virtual environment with Python, install dependencies with `pip install -r requirements.txt` and get a Selenium driver (currently using the chromedriver) set in your `PATH`. With everything done, you can start the bot with `python main.py`.
