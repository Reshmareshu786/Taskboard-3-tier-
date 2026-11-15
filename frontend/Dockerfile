# Base Image
FROM python:3.12-slim

# Working Directory
WORKDIR /app

# COPY dependencies
COPY requirements.txt .

# Install dependencies
RUN pip install --no-cache-dir -r requirements.txt 

# Copy frontend source code
COPY . .

# Application Port
EXPOSE 8080

# Start frontend
CMD ["gunicorn", "-b", "0.0.0.0:8080", "-w", "2", "app:app"]

# Build image
# docker build -t taskboard-frontend:1.0 ./frontend

# Run 
#docker run -d --name taskboard-frontend -p 8080:8080 --env-file .env taskboard-frontend:1.0