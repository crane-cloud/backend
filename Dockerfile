# use an official python runtime as the base image
FROM python:3.6

# set the (container) working directory
WORKDIR /app

# install netcat
RUN apt-get update && \
    apt-get install netcat-traditional -y

COPY requirements.txt /app/requirements.txt

# define environment variables
# ENV FLASK_APP app.py
# ENV FLASK_ENV production

# install dependencies
RUN pip install -r requirements.txt

# copy current (local) directory contents into the container
COPY . /app

# make port available to the world outside this container
EXPOSE 5000

# run when the container launches
CMD ["/app/scripts/start.sh"]