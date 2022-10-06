# Backup to keybase git

Committing repositories to Keybase git

## Description

This Docker setup allows you to login to keybase and commit all accessible repositories to their respective keybase git repositories.
A changelog.md with all new, modified and deleted files will be generated inside the repository.
A mail with deleted files will be sent to the indicated user.

## Getting Started

### Installing

- Clone this repository
```
git clone git@github.com:unfoldingWord/keybase_git_backup
```

- Or pull the docker container from [here](https://hub.docker.com/r/unfoldingword/keybase_git_backup)
```
docker pull unfoldingword/keybase_git_backup
```

- Or build your own docker container with the help of the provided Dockerfile
```
docker build -t <dockerhub-username>/<repo-name> .
```

### Executing the docker container

```
docker run --env-file .env --rm -v /local/path/to/repos:/repos --name keybase-git unfoldingword/keybase_git_backup
```
where `local/path/to/repos` is the location where your git repos are stored.

#### Enviromnment variables
You need to provide the following environment variables, 
either through a .env file, or by setting them manually

##### Keybase settings
- `KEYBASE_USERNAME` *(your Keybase username)*
- `KEYBASE_PAPERKEY` *(a valid Keybase paper key)*
- `KEYBASE_SERVICE` *(should be 1, but you can omit it, as it has already been hardcoded in the build)*

##### Git settings
- `GIT_AUTHOR_NAME` *(Your Git username)*
- `GIT_AUTHOR_EMAIL` *(Your Git email address)*

##### Misc
- `PATHS_CHANGELOG` *A bash array with the path to each changelog, per repository. The given path MUST exist!*

##### Sendgrid settings.
- `SENDGRID_API_KEY` *(Your Sendgrid API key)*
- `TO_EMAIL` *(Where to send the email to)*
- `TO_NAME` *(Name of the addressee)*
- `FROM_EMAIL` *(Email of sender)*
- `FROM_NAME` *(Name of sender)*
- `REPLY_EMAIL` *(Reply email)*
- `REPLY_NAME` (*Name of sender)*

## Authors

- [yakob-aleksandrovich ](https://github.com/yakob-aleksandrovich)

## Version History

* 0.1
    * Initial Release

## License

This project is licensed under the MIT License
