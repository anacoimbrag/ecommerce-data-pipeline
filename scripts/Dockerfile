FROM python:3.11-slim
WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY load_ga4_customer_behavior.py ./
CMD ["python", "load_ga4_customer_behavior.py"]
