# Step 1: Base image
FROM python:3.11-slim

# Step 2: Env config
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

# Step 3: Workdir
WORKDIR /app

# Step 4: Install build dependencies
RUN apt-get update && apt-get install -y \
    build-essential \
    libglib2.0-0 \
    libgl1 \
    libpq-dev \
    git \
 && apt-get clean && rm -rf /var/lib/apt/lists/*

# Step 5: Install pip packages
COPY requirements.txt .
RUN pip install --upgrade pip && \
    pip install --no-cache-dir -r requirements.txt \
    -i https://pypi.tuna.tsinghua.edu.cn/simple --timeout 100

# Step 6: Copy source code
COPY . .

# Step 7: Expose port (docs only; Render uses $PORT internally)
EXPOSE 10000

# Step 8: Start app (use shell form so $PORT is expanded)
CMD uvicorn main:app --host 0.0.0.0 --port ${PORT:-10000}
