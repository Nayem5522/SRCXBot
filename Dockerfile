FROM python:3.10-slim

RUN apt-get update && apt-get install -y libgl1 libxext6 libxrender1 libsm6 ffmpeg && apt-get clean

WORKDIR /app
COPY . .

RUN pip install --no-cache-dir -r requirements.txt

CMD ["python", "bot.py"]
