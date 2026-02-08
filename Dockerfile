FROM python:3.11-slim

WORKDIR /app

# Install system dependencies for Playwright and minimal build tools
RUN apt-get update && apt-get install -y \
    build-essential \
    curl \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Install Playwright browsers (chromium only for AgentBay/Browser Use usually suffices, but safe to install deps)
RUN playwright install --with-deps chromium

COPY . .

# Expose port
EXPOSE 8000

# Command
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
