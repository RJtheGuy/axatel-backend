# FROM python:3.12-slim AS builder

# ENV PYTHONDONTWRITEBYTECODE=1 \
#     PYTHONUNBUFFERED=1

# WORKDIR /app

# USER root

# RUN apt-get update && apt-get install -y --no-install-recommends \
#     gcc \
#     libpq-dev \
#     libjpeg-dev \
#     zlib1g-dev \
#     libxml2-dev \
#     libxslt-dev \
#  && rm -rf /var/lib/apt/lists/*

# COPY requirements.txt .
# RUN pip install --upgrade pip \
#  && pip install --prefix=/install --no-cache-dir -r requirements.txt

#  RUN pip install --no-cache-dir torch --index-url https://download.pytorch.org/whl/cpu

# FROM python:3.12-slim AS runtime

# ENV PYTHONDONTWRITEBYTECODE=1 \
#     PYTHONUNBUFFERED=1 \
#     DJANGO_SETTINGS_MODULE=axatel.settings.production

# WORKDIR /app

# USER root

# RUN apt-get update && apt-get install -y --no-install-recommends \
#     gcc \
#     libpq-dev \
#     libjpeg-dev \
#     zlib1g-dev \
#     libxml2-dev \
#     libxslt-dev \
#     && rm -rf /var/lib/apt/lists/*

# COPY --from=builder /install /usr/local

# RUN addgroup --system django && adduser --system --ingroup django django \
#  && mkdir -p staticfiles media logs

# COPY . .

# RUN chown -R django:django /app

# RUN python manage.py collectstatic --noinput --clear

# USER django

# EXPOSE 8000

# ENTRYPOINT ["sh", "/app/docker/entrypoint.sh"]


FROM python:3.12-slim AS builder

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

WORKDIR /app

# Required: this environment does not default to root during build, so
# apt cannot write to /var/lib/apt/lists without it and fails with
# "Permission denied (13)".
USER root

# Build-time toolchain. Only needed here — the runtime stage receives
# pre-built artifacts and does not compile anything.
RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc \
    libpq-dev \
    libjpeg-dev \
    zlib1g-dev \
    libxml2-dev \
    libxslt-dev \
 && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .

# Single install pass, everything into /install so the runtime stage can
# copy it wholesale.
#
# WAS: requirements.txt pulled the default (CUDA) torch — ~2.5GB of
# nvidia wheels (cublas, cudnn, nccl, cusparselt, cusolver, …) — and a
# SECOND `RUN pip install torch --index-url .../cpu` tried to replace it.
# That second command was missing `--prefix=/install`, so CPU torch went
# to the builder's own /usr/local and was discarded with the stage. The
# runtime therefore shipped the CUDA build regardless, on a container
# with no GPU.
#
# torch is now declared explicitly in requirements.txt as
# `torch==2.13.0+cpu` against the PyTorch CPU index, so this single
# install pass resolves it correctly.
RUN pip install --upgrade pip \
 && pip install --prefix=/install --no-cache-dir -r requirements.txt


FROM python:3.12-slim AS runtime

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    DJANGO_SETTINGS_MODULE=axatel.settings.production

WORKDIR /app

# Same reason as the builder stage — needed before any apt call.
USER root

# Runtime needs only the shared libraries the compiled wheels link
# against — not gcc or the -dev headers, which were build-only. Dropping
# them removes roughly 250MB from the final image.
RUN apt-get update && apt-get install -y --no-install-recommends \
    libpq5 \
    libjpeg62-turbo \
    zlib1g \
    libxml2 \
    libxslt1.1 \
 && rm -rf /var/lib/apt/lists/*

COPY --from=builder /install /usr/local

RUN addgroup --system django && adduser --system --ingroup django django \
 && mkdir -p staticfiles media logs

COPY . .

RUN chown -R django:django /app

RUN python manage.py collectstatic --noinput --clear

USER django

EXPOSE 8000

ENTRYPOINT ["sh", "/app/docker/entrypoint.sh"]