# Use an official Python runtime as a parent image
FROM python:3.8-slim

# Set the working directory to /app
WORKDIR /app

# Copy the current directory contents into the container at /app
COPY . /app

RUN sed 's/main/main non-free contrib/' < /etc/apt/sources.list > /tmp/apt; cp /tmp/apt /etc/apt/sources.list; apt-get update && DEBIAN_FRONTEND=noninteractive apt-get install --no-install-recommends -y locales imagemagick gnuplot-nox msttcorefonts

RUN sed -i -e 's/# en_US.UTF-8 UTF-8/en_US.UTF-8 UTF-8/' -e 's/# nl_NL.UTF-8 UTF-8/nl_NL.UTF-8 UTF-8/' /etc/locale.gen && \
    dpkg-reconfigure --frontend=noninteractive locales && \
    update-locale LANG=en_US.UTF-8 && \
    update-locale LANG=nl_NL.UTF-8

#RUN mkdir -p /home/tom/tmp && touch /home/tom/tmp/baro.dat && mkdir -p /home/tom/public_html/public

# Install any needed packages specified in requirements.txt
RUN DEBIAN_FRONTEND=noninteractive apt-get install -y gcc && \
    pip install --trusted-host pypi.python.org -r requirements.txt && \
    DEBIAN_FRONTEND=noninteractive apt-get purge -y gcc && \
    DEBIAN_FRONTEND=noninteractive apt-get -y auto-remove

# Define environment variable
ENV TZ "Europe/Amsterdam"
ENV NAME "Tom Home Automation"

# Run all.py when the container launches
CMD ["python", "-u", "all.py"]

