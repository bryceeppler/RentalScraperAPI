# Base image
FROM python:3.9-slim-buster


# Set working directory
WORKDIR /app

# Copy the requirements file into the container
COPY requirements.txt .

# Install requirements
RUN pip install --no-cache-dir -r requirements.txt
# playwright dependencies
RUN apt-get update && apt-get install -y libglib2.0-0 libnss3 libnss3-tools libatk-bridge2.0-0 libgtk-3-0 libx11-xcb1 libxcomposite1 libxdamage1 libxext6 libxfixes3 libxrandr2 libgbm1 libdrm2 libxcb-dri3-0 libxcb1 libxkbcommon0 libpango-1.0-0 libcairo2 libasound2

# Install Chromium browser dependencies
RUN apt-get update && \
    apt-get install -y wget gnupg ca-certificates && \
    wget -qO- https://playwright.dev/cli/sh | bash && \
    playwright install && \
    playwright install chromium



# Copy the application code into the container
COPY . .

# Set the command to run the application
CMD uvicorn main:app --host 0.0.0.0 --port $PORT
