FROM python:3.7

WORKDIR /usr/src/app

COPY requirements.txt ./

RUN pip install --default-timeout=100 --no-cache-dir -r requirements.txt

COPY . .

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]