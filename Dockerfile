FROM keybaseio/client:6.2.4-python
WORKDIR /app

# Copy in backup script
COPY backup-to-keybase.py backup-to-keybase.py
COPY requirements.txt requirements.txt

# Run
# - updates
# - install essential programs
# - create the /repos directory
#       In normal cases, this will be overwritten by a bind mount
# - set executable bit for Python program

RUN \
    apt -y update && \
    apt -y install git make gawk curl && \
    mkdir -p /repos && \
    chmod +x backup-to-keybase.py

# Install Python requirements
# Disable caching, to keep Docker image lean
RUN pip install --no-cache-dir -r requirements.txt

# Copy relevant user files
COPY autostart_created /home/keybase/.config/keybase/autostart_created
# Set ENV
ENV KEYBASE_SERVICE=1
# CMD
CMD /app/backup-to-keybase.py
