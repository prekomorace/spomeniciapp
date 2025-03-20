FROM python:3.10-slim

WORKDIR /app

# Instalirajte potrebne biblioteke
RUN apt-get update && apt-get install -y \
    libgl1-mesa-glx \
    libglib2.0-0 \
    && rm -rf /var/lib/apt/lists/*

# Kopirajte requirements.txt i instalirajte Python pakete
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Kopirajte ostatak aplikacije
COPY . .

# Stvorite direktorij za uploadane slike
RUN mkdir -p static/uploadovane_slike

# Ekspozirajte port 
EXPOSE 10000

# Postavite varijable okruženja
ENV PYTHONUNBUFFERED=1

# Pokrenite aplikaciju koristeći gunicorn
CMD gunicorn --bind 0.0.0.0:10000 app:app