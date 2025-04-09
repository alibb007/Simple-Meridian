FROM python:3.11-slim

# Install system dependencies needed to build some Python packages
RUN apt-get update && apt-get install -y \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

# Set the working directory in the container
WORKDIR /app

# Copy the requirements file and install the Python packages
COPY requirements.txt .
RUN pip install --upgrade pip && pip install -r requirements.txt

# Copy the rest of your application code (including run_meridian.sh)
COPY . .

CMD ["streamlit", "run", "app.py", "--server.address=0.0.0.0", "--browser.serverAddress=localhost"]