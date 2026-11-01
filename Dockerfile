FROM python:3.12-slim
ENV PYTHONUNBUFFERED=1
WORKDIR /srv
COPY requirements.txt .
RUN pip install --no-cache-dir fastapi "uvicorn[standard]" prometheus-client psutil
COPY app ./app
RUN mkdir -p data
EXPOSE 8000
HEALTHCHECK --interval=15s --timeout=3s CMD python -c "import urllib.request;urllib.request.urlopen('http://localhost:8000/')" || exit 1
# ONE worker on purpose: metrics/rate-limit state is in-process memory
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000", "--workers", "1"]
