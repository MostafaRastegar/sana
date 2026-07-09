# Build stage
FROM cache.damavand.ir/docker/python:3.11-slim-bookworm AS base
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    UV_PROJECT_ENVIRONMENT=/usr/local
RUN rm -f /etc/apt/sources.list /etc/apt/sources.list.d/debian.sources
RUN printf "deb [trusted=yes] https://cache.damavand.ir/repository/debian-main/debian/ bookworm main contrib non-free non-free-firmware\ndeb [trusted=yes] https://cache.damavand.ir/repository/debian-main/debian/ bookworm-updates main contrib non-free\ndeb [trusted=yes] https://cache.damavand.ir/repository/debian-main/debian-security/ bookworm-security main contrib\n" > /etc/apt/sources.list.d/main.list
RUN printf "[global]\ntimeout=900\nno-cache-dir=true\ntrusted-host=cache.damavand.ir\nindex-url=https://cache.damavand.ir/repository/pypi/simple\n" > /etc/pip.conf
COPY root-ca.crt /usr/local/share/ca-certificates/root-ca.crt
# RUN echo "Acquire::Check-Valid-Until false;" | tee /etc/apt/apt.conf.d/99no-check-valid-until
RUN set -eux; \
    mkdir -p /etc/ssl/certs /etc/apt/apt.conf.d; \
    cat /usr/local/share/ca-certificates/root-ca.crt > /etc/ssl/certs/ca-certificates.crt; \
    printf 'Acquire::https::CaInfo "/etc/ssl/certs/ca-certificates.crt";\n' > /etc/apt/apt.conf.d/99custom-ca; \
    apt-get update; \
    apt-get install -y --no-install-recommends ca-certificates gawk openssl; \
    update-ca-certificates; \
    rm -f /etc/apt/apt.conf.d/99custom-ca; \
    rm -rf /var/lib/apt/lists/*
RUN pip install --upgrade pip

FROM base AS builder

WORKDIR /app

# Install uv and build dependencies

RUN apt-get update && apt-get install -y \
    build-essential \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Install uv
RUN pip install uv

# Copy pyproject.toml and install with uv
COPY pyproject.toml .
RUN uv export --no-dev | uv pip install --system -r -

# Production stage
FROM base

WORKDIR /app

# Install runtime dependencies
RUN apt-get update && apt-get install -y \
    libpq-dev \
    && rm -rf /var/lib/apt/lists/*


# Copy other binaries from builder
COPY --from=builder /usr/local/bin /usr/local/bin

# Copy installed packages from builder
COPY --from=builder /usr/local/lib/python3.11/site-packages /usr/local/lib/python3.11/site-packages

# Copy application code
COPY . .

# Run collectstatic during build
RUN python manage.py collectstatic --noinput --clear

# Expose port
EXPOSE 8000

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD python manage.py check --deploy

# Run application with gunicorn
CMD ["gunicorn", "--config", "gunicorn.conf.py", "damavand.wsgi:application"]
