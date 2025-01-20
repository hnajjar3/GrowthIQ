FROM python:3.10-slim

# Install Poetry using pip
RUN pip install poetry

# Verify Poetry installation
RUN poetry --version

# Set the working directory in the container
WORKDIR /app

# Copy poetry files and install dependencies
COPY pyproject.toml poetry.lock /app/
RUN poetry install --only main --no-root

# Copy the rest of the app
COPY . /app

# Expose the port for Streamlit
EXPOSE 8501

# Run the Streamlit app
CMD ["poetry", "run", "streamlit", "run", "growthiq/growth_dashboard.py"]
