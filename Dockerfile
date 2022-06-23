FROM keybaseio/client:6.0.2
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
    apt -y install git make gawk curl && \
    mkdir -p /repos && \
    chmod +x backup-to-keybase.sh
# Copy relevant user files
COPY autostart_created /home/keybase/.config/keybase/autostart_created
COPY .gitconfig /home/keybase/.gitconfig
# Set ENV
ENV KEYBASE_SERVICE=1
# CMD
CMD /app/backup-to-keybase.sh
