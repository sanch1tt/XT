# Base image with compatible Python
FROM python:3.10-slim

# Set timezone
ENV TZ=Asia/Kolkata

# Install required system packages
RUN apt-get update && \
    apt-get install -y tzdata gcc build-essential libffi-dev libssl-dev git bash && \
    ln -snf /usr/share/zoneinfo/$TZ /etc/localtime && echo $TZ > /etc/timezone && \
    apt-get clean && rm -rf /var/lib/apt/lists/*

# Create non-root user with UID 1000
RUN useradd -m -u 1000 user

# Set workdir and copy requirements separately for caching
WORKDIR /app
COPY requirements.txt ./

# Install Python dependencies
RUN pip install --upgrade pip && \
    pip install --no-cache-dir -r requirements.txt

# Copy rest of the app files
COPY . .

# Change ownership of the app directory to the non-root user
RUN chown -R user:user /app

# Switch to non-root user
USER user

# Update PATH for local binaries
ENV PATH="/home/user/.local/bin:$PATH"

# Ensure log file exists and is writable (by user)
RUN touch /app/userbot.log

# Make startup script executable
RUN chmod +x /app/startup

# Start the bot
CMD ["bash", "/app/startup"]
