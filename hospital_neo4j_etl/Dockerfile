# Use an official lightweight Python image
FROM python:3.11-slim

# Set the working directory inside the container
WORKDIR /app

# Copy our source code and dependency list into the container
COPY ./src/ /app
COPY ./pyproject.toml /code/pyproject.toml

# Install the Python libraries inside the container
RUN pip install /code/.

# The command to run when the container starts
CMD ["sh", "entrypoint.sh"]