FROM keybaseio/client:6.0.2-slim
WORKDIR /app
# Copy in backup script
COPY backup-to-keybase.sh backup-to-keybase.sh
# Run 
# - updates
# - install git, make
# - create the repos directory
# - set executable bit for shell script
# In normal cases, this will be overwritten by a bind mount
RUN \ 
    apt -y update && \
    apt -y install git make && \
    mkdir -p /repos && \
    chmod +x backup-to-keybase.sh
# Tell keybase to not create autostart file
COPY autostart_created /home/keybase/.config/keybase/autostart_created
# Set ENV
ENV KEYBASE_SERVICE=1
# CMD
CMD /app/backup-to-keybase.sh
