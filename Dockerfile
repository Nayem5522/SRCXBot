FROM python:3.11-slim

RUN apt-get update && apt-get install -y \
    libgl1 \
    libxext6 \
    libxrender1 \
    libsm6 \
    ffmpeg \
    libgomp1 \          
    libfontconfig1 \    
    libxcb-randr0 \     
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app
COPY . .

# এটি এখন numpy<2.0.0 ইনস্টল করবে
RUN pip install --no-cache-dir -r requirements.txt

CMD ["python", "bot.py"]
