FROM python:3.11-slim

WORKDIR /app

# Copy requirements first (better caching)
COPY ./requirements.txt /app/requirements.txt
RUN pip install --no-cache-dir -r /app/requirements.txt

# Copy the whole chatbot_api folder
COPY . /app/chatbot_api

EXPOSE 8000

CMD ["uvicorn", "chatbot_api.src.api:app", "--host", "0.0.0.0", "--port", "8000"]
