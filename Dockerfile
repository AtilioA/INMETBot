# Alternative: debian:11 (don't use alpine)
FROM python:3.8

# Update package list and install dependencies
RUN apt-get update && apt-get install -y \
    # Download and install Selenium driver
    unzip \
    wget \
    # # Python and dependencies
    # python3 \
    # python3-setuptools \
    # python3-pip \
    # Python wheel dependency (cryptography)
    libssl-dev

WORKDIR /app
ADD . /app

# - Selenium webdriver
# Install google chrome
RUN wget -q -O - https://dl-ssl.google.com/linux/linux_signing_key.pub | apt-key add - \
    && sh -c 'echo "deb [arch=amd64] http://dl.google.com/linux/chrome/deb/ stable main" >> /etc/apt/sources.list.d/google-chrome.list' \
    && apt-get -y update \
    && apt-get install -y google-chrome-stable

# Install chromedriver and set it to PATH
RUN wget -O /tmp/chromedriver.zip http://chromedriver.storage.googleapis.com/`curl -sS chromedriver.storage.googleapis.com/LATEST_RELEASE`/chromedriver_linux64.zip
RUN unzip /tmp/chromedriver.zip chromedriver -d /usr/local/bin/
ENV CHROMEDRIVER_PATH="/usr/local/bin/chromedriver"

RUN pip3 install --user -U pip \
    && pip3 install --no-warn-script-location --user --trusted-host pypi.python.org -r requirements.txt

# Start the bot (README.md for more details)
CMD ["python3", "main.py"]

