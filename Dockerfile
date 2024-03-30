# Use an official Python runtime as a parent image
FROM python:3.11

# Set the working directory to /api
WORKDIR /api/

# Copy the current directory contents into the container at /app
COPY . /api/

# Install any needed packages specified in requirements.txt
RUN pip install --no-cache-dir -r requirements.txt

EXPOSE 3000

ENV FLASK_APP=api.py

# Run app.py when the container launches
CMD ["gunicorn", "-w", "3", "-t", "3", "-b", "0.0.0.0:8080", "api:app"]
# CMD ["python3", "api.py"]