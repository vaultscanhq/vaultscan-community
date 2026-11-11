FROM python:3.12-slim

LABEL org.opencontainers.image.source="https://github.com/vaultscanhq/vaultscan-community" \
      org.opencontainers.image.licenses="Apache-2.0" \
      org.opencontainers.image.authors="Pavan Gajjala"

WORKDIR /opt/vaultscan
COPY pyproject.toml README.md LICENSE ./
COPY vaultscan ./vaultscan
RUN pip install --no-cache-dir . && useradd --create-home --uid 10001 scanner

USER scanner
WORKDIR /repo
ENTRYPOINT ["vaultscan"]
CMD ["gate", "--path", "/repo"]
