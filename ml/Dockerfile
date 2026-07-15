FROM python:3.11-slim
WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY common ./common
COPY segmentation ./segmentation
COPY campaigns ./campaigns
COPY recommendations ./recommendations
COPY export_to_serving_store.py .
CMD ["python", "segmentation/train_kmeans.py"]
