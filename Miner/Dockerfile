FROM python:3.10.5

# define working directory
WORKDIR /app

# Copying files
COPY . .

# Install dependencies
RUN pip3 install -r requirements.txt

# Keep the container running
ENTRYPOINT ["tail", "-f", "/dev/null"]