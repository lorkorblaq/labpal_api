# Use an official Python runtime as a parent image
FROM python:3.11
# docker build -t lorkorblaq/clinicalx_api:latest -f Dockerfile .
# Set the working directory to /api
WORKDIR /labpal_api/

# Copy the current directory contents into the container at /app
COPY . /labpal_api/

# Install any needed packages specified in requirements.txt
RUN pip install --no-cache-dir -r requirements.txt

EXPOSE 3000
ENV FLASK_APP=api.py

# Run app.py when the container launches
# CMD ["gunicorn", "-w", "2", "-b", "0.0.0.0:3000", "api:app"]
CMD ["gunicorn", "-w", "2", "-k", "gevent", "-b", "0.0.0.0:3000", "api:app"]
# CMD ["python3", "api.py"]
