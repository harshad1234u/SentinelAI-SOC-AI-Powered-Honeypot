FROM python:3.11-slim AS builder
# Install dependencies into /install
COPY requirements.txt .
RUN pip install --prefix=/install --no-cache-dir -r requirements.txt

FROM python:3.11-slim
COPY --from=builder /install /usr/local
COPY . /app
WORKDIR /app
RUN adduser --disabled-password --no-create-home appuser
USER appuser
ENV PORT=8000
EXPOSE $PORT
CMD ["sh", "docker/entrypoint.sh"]
