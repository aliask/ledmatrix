FROM python:3.10-alpine as base

# Install Build dependencies for rpi_ws281x and Pillow
RUN apk --no-cache add python3-dev gcc libc-dev \
  tiff-dev jpeg-dev openjpeg-dev zlib-dev freetype-dev lcms2-dev \
  libwebp-dev tcl-dev tk-dev harfbuzz-dev fribidi-dev libimagequant-dev \
  libxcb-dev libpng-dev

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