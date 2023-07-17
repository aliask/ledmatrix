FROM python:3.10-slim as base

# Install Build dependencies for rpi_ws281x and Pillow
RUN apt-get update && apt-get install -y --no-install-recommends \
        build-essential libffi-dev libxml2-dev libxslt1-dev \
        libtiff-dev libjpeg62-turbo-dev zlib1g-dev libfreetype6-dev \
        liblcms2-dev libwebp-dev \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Install Python dependencies
COPY requirements.txt /app
RUN pip3 install -r requirements.txt

COPY ledmatrix /app/ledmatrix
COPY main.py /app
COPY pattern.png /app

FROM base AS test
COPY test-requirements.txt /app
RUN pip3 install -r test-requirements.txt

COPY tests /app/tests
CMD [ "pytest", "tests" ]

FROM base AS prod
CMD [ "python3", "main.py" ]
