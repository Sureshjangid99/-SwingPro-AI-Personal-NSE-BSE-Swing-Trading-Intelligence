FROM python:3.11-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

# Create all required directories and placeholder files
RUN mkdir -p database static/css static/js templates && \
    echo "/* SwingPro AI */" > static/css/style.css && \
    echo "" > static/js/main.js && \
    chmod -R 777 /app/database && \
    chmod -R 755 /app/static && \
    chmod -R 755 /app/templates

EXPOSE 7860

CMD ["uvicorn", "app:app", "--host", "0.0.0.0", "--port", "7860", "--workers", "1"]
