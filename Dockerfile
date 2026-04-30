# pull basic Python
FROM python:3.13 

# Copy the list for non default python packages
COPY requirements.txt ./

# Install the python dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Set the working directory
WORKDIR /workspace