FROM keybaseio/client:6.0.2-slim

# Run 
# - updates
# - install git 
# - create the repos directory
# In normal cases, this will be overwritten by a bind mount
RUN \ 
    apt -y update && \
    apt -y install git && \
    mkdir -p /repos

# Tell keybase to not create autostart file
COPY autostart_created /home/keybase/.config/keybase/autostart_created

# Configure our backup script
WORKDIR /app

COPY backup-to-keybase.sh backup-to-keybase.sh

RUN chmod +x backup-to-keybase.sh

ENV KEYBASE_SERVICE=1

CMD /app/backup-to-keybase.sh
