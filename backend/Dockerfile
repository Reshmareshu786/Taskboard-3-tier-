# Base Image
FROM python:3.12-slim

# Setting Work Directory
WORKDIR /app

# Copying Dependency File
COPY requirements.txt .

# Installing Python Dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Copying Application Source Code
COPY . .

# Application Port
EXPOSE 5000

# Start Flask Application using Gunicorn
CMD ["gunicorn", "-b", "0.0.0.0:5000", "-w", "2", "app:app"]

# Build docker image
#docker build -t taskboard-backend:tag ./backend

# Run 
# docker run -d --name taskboard-backend -p 5000:5000 --env-file .env taskboard-backend:1.0

# without env
#docker run -d --name taskboard-backend -p 5000:5000 taskboard-backend:1.0