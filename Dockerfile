FROM python:3.12-slim

WORKDIR /frontend

COPY . .

RUN pip install --no-cache-dir -r requirements.txt --root-user-action=ignore

EXPOSE 8000

ENV FLASK_APP=frontend.py
ENV FLASK_RUN_PORT=8000

CMD ["python", "frontend.py"]
