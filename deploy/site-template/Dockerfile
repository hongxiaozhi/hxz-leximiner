FROM python:3.12-slim

ENV PYTHONUNBUFFERED=1

ARG PIP_INDEX_URL=https://pypi.tuna.tsinghua.edu.cn/simple
ARG APT_MIRROR=mirrors.tuna.tsinghua.edu.cn

RUN sed -i "s|deb.debian.org|${APT_MIRROR}|g" /etc/apt/sources.list.d/debian.sources \
	&& sed -i "s|security.debian.org|${APT_MIRROR}|g" /etc/apt/sources.list.d/debian.sources \
	&& apt-get update \
	&& apt-get install -y build-essential libffi-dev libssl-dev gcc \
	&& rm -rf /var/lib/apt/lists/*

WORKDIR /app

# install python deps
COPY backend/requirements.txt /app/requirements.txt
RUN python -m pip install \
	--no-cache-dir \
	--default-timeout=300 \
	--retries 10 \
	--index-url ${PIP_INDEX_URL} \
	-r requirements.txt

# copy application
COPY backend /app/backend
COPY frontend /app/frontend
COPY core /app/core
COPY data /app/data

WORKDIR /app/backend

EXPOSE 5000

CMD ["gunicorn", "--workers", "2", "--bind", "0.0.0.0:5000", "app:app"]