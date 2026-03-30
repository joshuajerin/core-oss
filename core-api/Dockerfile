FROM python:3.12-slim

WORKDIR /app

# Install uv for fast dependency management
RUN pip install uv

# Copy dependency files first for caching
COPY requirements.txt requirements-dev.txt ./

# Install dependencies
RUN uv pip install --system -r requirements-dev.txt

# Copy source code
COPY . .

EXPOSE 8000

CMD ["python", "dev.py"]
