# Use an official Python runtime as a parent image
FROM python:3.7-slim

# Set the working directory to /app
WORKDIR /app

# Copy the current directory contents into the container at /app
COPY . /app

RUN apt-get update && DEBIAN_FRONTEND=noninteractive apt-get install -y locales imagemagick gnuplot

RUN sed -i -e 's/# en_US.UTF-8 UTF-8/en_US.UTF-8 UTF-8/' -e 's/# nl_NL.UTF-8 UTF-8/nl_NL.UTF-8 UTF-8/' /etc/locale.gen && \
    dpkg-reconfigure --frontend=noninteractive locales && \
    update-locale LANG=en_US.UTF-8 && \
    update-locale LANG=nl_NL.UTF-8

RUN mkdir -p /home/tom/tmp
RUN touch /home/tom/tmp/baro.dat
RUN mkdir -p /home/tom/public_html/public

# Install any needed packages specified in requirements.txt
RUN pip install --trusted-host pypi.python.org -r requirements.txt

# Make port 80 available to the world outside this container
#EXPOSE 80

# Define environment variable
ENV NAME "Tom Home Automation"

# Run all.py when the container launches
CMD ["python", "-u", "all.py"]

