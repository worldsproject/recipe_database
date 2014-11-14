###
# Dockerfile to build WorldsProject Recipe Database
###

# Set the base image to Ubuntu
FROM ubuntu

# Author Maintainer
MAINTAINER Tim Butram WorldsProject

#Update sources list
RUN apt-get update -y
RUN apt-get upgrade -y

# Install basic tools
RUN apt-get install -y tar git curl nano wget dialog net-tools build-essential libssl-dev

# Basic python deps.
RUN apt-get install -y python python-dev python-distribute

# Install correct version of pip
RUN wget https://raw.github.com/pypa/pip/master/contrib/get-pip.py
RUN python get-pip.py

# Clone the recipe database.
RUN git clone https://github.com/worldsproject/recipe_database.git

# Add in the config file
ADD ./config.py /recipe_database/config.py

# Create the tmp directory for logging.
RUN mkdir recipe_database/tmp

# Install all the pip requirements
RUN pip install -r recipe_database/requirements.txt

RUN pip install cherrypy

# Expose 80 for webserver
EXPOSE 80

# Set the working directory to be recipe_database
WORKDIR /recipe_database

# Start the server
CMD python run.py