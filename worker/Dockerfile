FROM python:3.12-slim

WORKDIR /worker

COPY worker/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY app/config.py ./config.py
COPY app/models.py ./models.py
COPY app/logger.py ./logger.py
COPY worker/main.py .

CMD ["python", "main.py"]
