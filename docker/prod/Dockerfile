FROM python:3.6

WORKDIR /app

COPY requirements.txt /app/requirements.txt


RUN pip install -r requirements.txt

COPY . .

RUN chmod +x /app/scripts/start-prod.sh

CMD ["/app/scripts/start-prod.sh"]

