FROM python:3.11-slim

# আপনার RUN কমান্ডটি নিম্নরূপ পরিবর্তন করুন:
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

RUN pip install --no-cache-dir -r requirements.txt

CMD ["python", "bot.py"]
