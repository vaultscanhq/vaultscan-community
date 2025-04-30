# Use official lightweight Python image
FROM python:3.11-slim

# Set working directory
WORKDIR /app

# Copy project files
COPY . .

# Install dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Run VaultScan CLI
ENTRYPOINT ["python", "-m", "vaultscan.main"]

# Developed by Pavan Gajjala – https://github.com/pavangajjala
# Licensed under Apache 2.0. Unauthorized removal of attribution is prohibited.