FROM python:3.9.7-slim-buster


RUN apt-get update && apt-get install -y \
    wget \
    curl \
    fontconfig \
    fonts-noto-cjk \
    git \
    unzip \
    # Next packages are for wkhtmltopdf
    libxrender1 \
    xfonts-75dpi \
    xfonts-base \
    libjpeg62-turbo

# Get and install needed fonts.
RUN cd /tmp \
    && git clone --depth 1 https://github.com/Bible-Translation-Tools/ScriptureAppBuilder-pipeline \
    && cp /tmp/ScriptureAppBuilder-pipeline/ContainerImage/home/fonts/*.ttf /usr/share/fonts/
# Refresh system font cache.
RUN fc-cache -f -v

# Install wkhtmltopdf
# Source: https://github.com/wkhtmltopdf/wkhtmltopdf/issues/2037
# Source: https://gist.github.com/lobermann/ca0e7bb2558b3b08923c6ae2c37a26ce
# How to get wkhtmltopdf - don't use what Debian provides as it can have
# headless display issues that mess with wkhtmltopdf.
ARG WKHTMLTOX_LOC=https://github.com/wkhtmltopdf/packaging/releases/download/0.12.6-1/wkhtmltox_0.12.6-1.buster_amd64.deb
RUN WKHTMLTOX_TEMP="$(mktemp)" && \
    wget -O "$WKHTMLTOX_TEMP" ${WKHTMLTOX_LOC} && \
    dpkg -i "$WKHTMLTOX_TEMP" && \
    rm -f "$WKHTMLTOX_TEMP"

# Make the output directory where resource asset files are cloned or
# downloaded and unzipped.
RUN mkdir -p /working/temp
# Make the output directory where generated HTML and PDFs are placed.
RUN mkdir -p /working/output
# Make the directory where logs are written to.
RUN mkdir -p /logs

COPY icon-tn.png .
COPY requirements.txt .
COPY requirements-dev.txt .

RUN pip install -r requirements.txt
RUN pip install -r requirements-dev.txt

COPY ./src/ /src/
RUN pip install -e /src
COPY ./tests /tests

# Note: for development, first install your app,
# pip install -e .
# before running your Docker commands, e.g., make unit-tests.

# Note: For production the requirements.in will be modified to include
# this project's remote git repo using the git+https pip-install
# format. See the entry in requirements.in for USFM-Tools as an example.

# Note: For development or production, you'll also need to provide the
# required environment variables as found in the .env file.
