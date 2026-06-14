FROM python:3.11-slim

WORKDIR /app

COPY app/requirements.txt .
RUN pip install -r requirements.txt

COPY app/app.py .

EXPOSE 5000

CMD ["python", "app.py"]
