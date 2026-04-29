FROM python:3.11-slim

# System dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    ffmpeg \
    git \
    curl \
    libmagic1 \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Install Python dependencies first (cache layer)
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy source code
COPY . .

# Create directories
RUN mkdir -p logs cache/thumbnails assets/fonts

# Download Poppins fonts
RUN curl -sL "https://github.com/google/fonts/raw/main/ofl/poppins/Poppins-Bold.ttf" \
    -o assets/fonts/Poppins-Bold.ttf && \
    curl -sL "https://github.com/google/fonts/raw/main/ofl/poppins/Poppins-Regular.ttf" \
    -o assets/fonts/Poppins-Regular.ttf

EXPOSE 8080

CMD ["python3", "-m", "musicbot"]
