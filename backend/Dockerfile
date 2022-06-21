FROM python:3.8

WORKDIR /app

# https://docs.python.org/3/using/cmdline.html#envvar-PYTHONDONTWRITEBYTECODE
# Preventing Python from writing .pyc to disk...
ENV PYTHONDONTWRITEBYTECODE 1
# Send Python output straight to terminal
# https://docs.python.org/3/using/cmdline.html#cmdoption-u
ENV PYTHONBUFFERED 1

# Install Poetry
RUN curl -sSL https://raw.githubusercontent.com/python-poetry/poetry/master/get-poetry.py | POETRY_HOME=/opt/poetry python && \
    cd /usr/local/bin && \
    ln -s /opt/poetry/bin/poetry && \
    poetry config virtualenvs.create false

# Copy pyproject.toml, poetry.lock* and run.sh too app folder
COPY ./pyproject.toml ./poetry.lock* ./run.sh /app/
# Allow installing dev dependencies to run tests
ARG INSTALL_DEV=true
# Installing project's dependencies
RUN bash -c "if [ $INSTALL_DEV == 'true' ] ; then poetry install --no-root ; else poetry install --no-root --no-dev ; fi"

COPY ./app /app
RUN chmod +x run.sh
ENV PYTHONPATH=/app
