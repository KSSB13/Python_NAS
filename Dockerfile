# Start with an official, lightweight Python image
FROM python:3.9-slim

# Set the working directory inside the container
WORKDIR /app

# Copy the requirements file first to leverage Docker's build cache
# This means Docker won't reinstall packages unless requirements.txt changes
COPY requirements.txt .

# Install the Python dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Copy the rest of the application code into the container
COPY . .

# Tell Docker that the container will listen on port 8080
EXPOSE 8080

# The command to run the application when the container starts
# We use Flask's built-in server here.
# --host=0.0.0.0 is crucial to make the server accessible from outside the container
CMD ["flask", "run", "--host=0.0.0.0", "--port=8080"]