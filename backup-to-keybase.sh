#!/usr/bin/env bash

# Warning: This file is piped out via Puppet, do not modify manually

# General settings
VAULTPATH=/repos
TMP_FILE=/tmp/current_changes.md

create_pipe () {
    local STATUS_PIPE=/tmp/status_pipe
    if [ ! -p ${STATUS_PIPE} ]; then
        mkfifo ${STATUS_PIPE} # named pipe
    fi
    
    echo ${STATUS_PIPE}
}

get_deleted_files () {
    # Setup the pipe
    STATUS_PIPE="$(create_pipe)"

    # Get status, replace prefixes, get only deleted files (D)
    git status -s | gawk '{ sub("?", "U", $1); sub("?", "", $1); sub("^ ", "", $0); print $0 } ' | grep "D " > ${STATUS_PIPE} &

    # Prefix with -, suffix with <br>
    while IFS=$'\n' read line; do
        my_file_list+="- ${line}<br>"
    done < ${STATUS_PIPE}

    echo ${my_file_list}
}

send_mail () {
    # Settings the subject
    # All other variables have to be set through ENV variables!!!
    SUBJECT="Files being deleted from Obsidian vault"
    SUBJECT+=" '`basename $PWD`'"

    file_list=$1

    BODY="<p>${file_list}</p>"

    MAILDATA='{"personalizations":[{"to":[{"email": "'${TO_EMAIL}'","name": "'${TO_NAME}'"}],"subject":"'${SUBJECT}'"}],"content": [{"type": "text/html", "value": "'${BODY}'"}],"from":{"email":"'${FROM_EMAIL}'","name":"'${FROM_NAME}'"},"reply_to":{"email":"'${REPLY_EMAIL}'","name":"'${REPLY_NAME}'"}}'

    #echo $MAILDATA

    curl --request POST \
        --url https://api.sendgrid.com/v3/mail/send \
        --header 'Authorization: Bearer '${SENDGRID_API_KEY} \
        --header 'Content-Type: application/json' \
        --data "${MAILDATA}"
}

for dir in $VAULTPATH/*
do
    # We can only commit when there is a .git directory available
    if [ -d $dir/.git ]; then
        cd $dir
        
        # See if there are any changes
        status=`git status -s`

        if [ "${status}" != "" ]; then
            # Find deleted_files
            file_list="$(get_deleted_files)"

            # Send mail if we have deleted files
            if [ "${file_list}" != "" ]; then
                send_mail "${file_list}"
            fi
        
            # Next, update changelog with all changes
            # 1) Build tmp file with all info
            date -u +\#\#\#\ %Y/%m/%d\ %H:%M:%S > $TMP_FILE
            git status -s | gawk '{ sub("?", "U", $1); sub("?", "", $1); sub("^ ", "", $0); print $0 } ' | while IFS=$'\n' read line; do
                echo "- $line" >> $TMP_FILE
            done
            echo >> $TMP_FILE

            # 2) Merge temporary file with changelog file, putting the most recent changes (tmp file) at the top
            changelog=changelog-$(basename $dir).md
            touch $changelog
            cat $TMP_FILE $changelog > /tmp/changelog_tmp.md && mv /tmp/changelog_tmp.md $changelog
            
            # 3) Remove clutter
            rm $TMP_FILE
            
            # Add, commit and push changes
            make commit > /tmp/commit.out

        fi
    fi
done
