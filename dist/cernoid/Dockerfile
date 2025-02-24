FROM condaforge/mambaforge:latest
WORKDIR /app

# Create Conda environment with dlib pre-installed
RUN mamba create -n myenv -c conda-forge python=3.10 dlib numpy pip -y

# Initialize conda in bash config
RUN conda init bash && \
    echo "conda activate myenv" >> ~/.bashrc

# Make RUN commands use the conda env
SHELL ["/bin/bash", "--login", "-c"]

# Copy project files
COPY . .

# Create necessary directories
RUN mkdir -p /app/face_encodings

# Install Python packages
RUN pip install --no-cache-dir -r requirements.txt

# Set permissions
RUN chmod -R 755 /app

# Set environment variables
ENV PYTHONPATH=/app
ENV PORT=8000

# Expose port
EXPOSE 8000

# Run the application
SHELL ["/bin/bash", "--login", "-c"]
CMD ["python", "-m", "uvicorn", "src.main:app", "--host", "0.0.0.0", "--port", "8000"]
