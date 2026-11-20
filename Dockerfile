# pull basic Python
FROM python:3.13 

# Copy the list for non default python packages
COPY requirements.txt ./

# Install the python dependencies
RUN apt update && apt install iproute2 iputils-ping locales -y && pip install --no-cache-dir -r requirements.txt && sed -i 's/^# *\(de_DE.UTF-8 UTF-8\)/\1/' /etc/locale.gen  && locale-gen

# Set the working directory
WORKDIR /workspace