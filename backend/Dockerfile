FROM python:3.11-slim

WORKDIR /app

RUN mkdir -p /data

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

EXPOSE 5000

ENV FLASK_APP=run.py
ENV FLASK_ENV=production
ENV DATABASE_URL=sqlite:////data/access_review.db

CMD ["python", "run.py"]
