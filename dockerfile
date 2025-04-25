FROM python:3.11-bullseye

WORKDIR /app

RUN apt-get update && apt-get install -y \
    build-essential \
    libffi-dev \
    curl \
    openjdk-17-jdk \
    libstdc++6 \
    libcurl4 \
    ca-certificates \
    libssl-dev \
    zlib1g \
    libasound2 \
    && rm -rf /var/lib/apt/lists/*

COPY ./malppot/requirements.txt ./malppot/requirements.txt
RUN pip install --no-cache-dir -r ./malppot/requirements.txt

COPY . .

EXPOSE 8000

CMD ["uvicorn", "malppot.main:app", "--host", "0.0.0.0", "--port", "8000"]