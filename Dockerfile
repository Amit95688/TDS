# --------------------------------------------------------------------------------
# Stage 1: Base Image and System Setup
# Use a Python slim image for a smaller final container size.
# Replace with nvidia/cuda-xx.x-cudnn-x-runtime if you require GPU access.
FROM python:3.10-slim

# Set up the application port. Hugging Face Spaces defaults to 7860.
# Ensure this matches the 'app_port' value in your README.md if you change it.
ARG APP_PORT=7860
ENV PORT=${APP_PORT}

# Install necessary system dependencies (e.g., C/C++ compilers for libraries like llama-cpp-python)
# If you are using a pure PyTorch/Transformer model, you can skip the build dependencies.
# If you run a model like Llama 3.2 via llama_cpp_python, these are essential.
USER root
RUN apt-get update && \
    apt-get install -y --no-install-recommends \
    gcc \
    g++ \
    cmake \
    git \
    && apt-get clean && \
    rm -rf /var/lib/apt/lists/*
    
# --------------------------------------------------------------------------------
# Stage 2: User Setup and Environment Security
# Create a non-root user for security best practice on Hugging Face Spaces.
RUN useradd -m -u 1000 user
USER user

# Set environment variables for the user
ENV HOME=/home/user
ENV PATH="${HOME}/.local/bin:${PATH}"

# Set the working directory for the application
WORKDIR /app

# --------------------------------------------------------------------------------
# Stage 3: Python Dependencies and Model Loading
# Copy requirements.txt first to leverage Docker layer caching
COPY --chown=user requirements.txt .

# Install dependencies using --no-cache-dir for faster builds and smaller layers
# You may need to add --extra-index-url if using custom package repositories
RUN pip install --no-cache-dir -r requirements.txt

# If you are downloading a large model, this is where you would do it.
# E.g., via huggingface_hub or cloning a repo.

# --------------------------------------------------------------------------------
# Stage 4: Application Code and Startup
# Copy the application code (FastAPI/Flask app) and necessary files
# --chown=user ensures the non-root user owns these files.
COPY --chown=user . .

# Expose the application port (matching the ENV PORT above and the README.md)
EXPOSE ${APP_PORT}

# Define the command to run the application (assuming your entry file is main.py)
# This example uses Uvicorn to run a FastAPI app named 'app' in main.py.
# Replace 'main:app' with 'your_file_name:app' if your entry file is different.
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "7860"]