###
# Dockerfile to build WorldsProject Recipe Database
###

# Set the base image to Ubuntu
FROM ubuntu

# Author Maintainer
MAINTAINER Tim Butram WorldsProject

# Install basic tools
RUN apt-get update && apt-get install -y \
tar \
git \
curl \
nano \
wget \
dialog \
net-tools \
build-essential \
libssl-dev \
libpq-dev \
python3 \ 
python3-dev

# Install correct version of pip
RUN wget https://raw.github.com/pypa/pip/master/contrib/get-pip.py
RUN python3 get-pip.py

# Clone the recipe database.
#RUN git clone https://github.com/worldsproject/recipe_database.git

#Copy from local dir for faster testing.
ADD ./ /recipe_database

# Add in the config file
COPY ./config.py /recipe_database/config.py

# Create the tmp directory for logging.
RUN mkdir recipe_database/tmp | echo

# Install all the pip requirements
RUN pip install -r recipe_database/requirements.txt #updated for cherrypy

# Expose 80 for webserver
EXPOSE 80

# Setup database
RUN /recipe_database/reset_db.sh #

# Add admin user
#RUN python3 /recipe_database/create_admin.py #

# Set the working directory to be recipe_database
WORKDIR /recipe_database

# Start the server
CMD python3 run.py #