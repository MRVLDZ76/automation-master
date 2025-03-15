FROM python:3.11.9-bullseye
SHELL ["/bin/bash", "-c"]

ENV PIP_NO_CACHE_DIR off
ENV PIP_DISABLE_PIP_VERSION_CHECK on
ENV PYTHONUNBUFFERED 1
ENV PYTHONDONTWRITEBYTECODE 0

# Install necessary packages
RUN apt-get update \
 && apt-get install -y --force-yes \
 nano python3-pip gettext chrpath libssl-dev libxft-dev \
 libfreetype6 libfreetype6-dev libfontconfig1 libfontconfig1-dev \
 && rm -rf /var/lib/apt/lists/*

# Upgrade pip and install gunicorn
RUN pip install --upgrade pip && pip install gunicorn

# Set the working directory
WORKDIR /code/

# Copy requirements and install
COPY ./code/requirements.txt /code/
RUN pip install -r requirements.txt

# Copy application code
COPY ./code/ /code/

# Copy environment variables
COPY ./env/ /env/

# Ensure debug.log can be written by the user code
RUN touch /code/debug.log && chmod 666 /code/debug.log

# Perform any necessary command (optional)
RUN source /env/envs_export.sh && if [ -n "$BUILD_COMMAND" ]; then eval $BUILD_COMMAND; fi
RUN source /env/envs_export.sh && export && if [ -f "manage.py" ]; then if [ "$DISABLE_COLLECTSTATIC" == "1" ]; then echo "collect static disabled"; else echo "Found manage.py, running collectstatic" && python manage.py collectstatic --noinput; fi;  else echo "No manage.py found. Skipping collectstatic."; fi;

# Create a user and set to that user
RUN useradd -ms /bin/bash code
USER code

# Expose ports, etc., if necessary (optional)
# EXPOSE 8000  # Or whichever port your app runs on
