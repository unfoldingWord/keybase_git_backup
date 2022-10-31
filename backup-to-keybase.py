#!/usr/bin/env python3
import os
from dotenv import load_dotenv
from git import Repo
import logging
import sendgrid
import datetime
from sendgrid.helpers.mail import Mail, Email, To, Content
import subprocess


class BackupToKeybase:
    def __init__(self):
        # Init logger
        self.logger = self.__init_logger()

    def __init_logger(self):
        if os.getenv('STAGE', False) == 'dev':
            log_level = logging.DEBUG
        else:
            log_level = logging.INFO

        logging.basicConfig(
            format='%(asctime)s %(levelname)-8s %(message)s',
            level=log_level,
            datefmt='%Y-%m-%d %H:%M:%S'
        )

        this_logger = logging.getLogger()
        return this_logger

    def __send_mail(self, reponame, lst_deleted_files):
        if len(lst_deleted_files) == 0:
            return False

        lst_deleted_files = [' '.join(item) for item in lst_deleted_files]
        html_deleted_files = '<ul><li>' + '<li>'.join(lst_deleted_files) + '</ul>'

        sg = sendgrid.SendGridAPIClient(api_key=self.__get_env('SENDGRID_API_KEY'))
        from_email = Email(email=self.__get_env('FROM_EMAIL'), name=self.__get_env('FROM_NAME'))
        to_email = To(email=self.__get_env('TO_EMAIL'), name=self.__get_env('TO_NAME'))
        subject = 'Files being deleted from Obsidian vault \'{}\''.format(reponame)
        content = Content("text/html", html_deleted_files)
        mail = Mail(from_email, to_email, subject, content)
        response = sg.client.mail.send.post(request_body=mail.get())

        if response.status_code == 202:
            return True

        return False

    def __get_changelog_file(self, full_repo_path):
        reponame = self.__get_repo_from_path(full_repo_path)
        lst_changelogs = eval(self.__get_env('PATHS_CHANGELOG_PY'))
        for path in lst_changelogs:
            if reponame in path:
                changelog_file = full_repo_path + path.replace(reponame, '') + '/changelog-' + reponame + '.md'
                return changelog_file

        return None

    def __get_clean_status_list(self, repo):
        # Cutting and cleaning up git status list for actual usage
        lst_tmp = [item.replace('"', '').lstrip().split(' ') for item in repo.git.status('--porcelain').split('\n')]

        idx = 0
        for item in lst_tmp:
            # ?? means Untracked, so we replace that with U
            if item[0] == '??':
                item[0] = 'U'

            # More than 2 elements means we have a filename with spaces, so we're going to fix that
            if len(item) > 2:
                lst_tmp[idx] = [item[0], ' '.join(item[1:])]
            idx += 1

        # Remove the changelog from the list of changes. Otherwise, we are stuck
        # in a loop updating our changelog with changes to itself!
        lst_tmp = [item for item in lst_tmp if item[1].find('changelog') == -1]

        self.logger.debug("Clean status list: " + str(lst_tmp))

        return lst_tmp

    def __set_git_config(self, repo):
        repo.git.config('user.name', self.__get_env('GIT_AUTHOR_NAME'))
        repo.git.config('user.email', self.__get_env('GIT_AUTHOR_EMAIL'))

    def __get_env(self, key):
        env = os.getenv(key)
        if not env:
            raise EnvironmentError("Environment variable {} not set".format(key))

        return env

    def __get_repo_from_path(self, full_repo_path):
        return full_repo_path.split('/')[-1]

    def __update_changelog(self, full_repo_path, changes):
        changelog_file = self.__get_changelog_file(full_repo_path)

        if not changelog_file:
            logging.warning('Changelog file could not be determined for {}'.format(full_repo_path))
            raise FileNotFoundError('Changelog file not found in repo \'{}\' '.format(full_repo_path))

        # If file does not exist, create first!
        if not os.path.exists(changelog_file):
            logging.info('Changelog file {} created.'.format(changelog_file))
            fp = open(changelog_file, 'x')
            fp.close()

        # Write our changes!
        logging.debug('Writing changes: {} to \'{}\''.format(changes.replace('\n', ' '), changelog_file))
        with open(changelog_file, 'r+') as f:
            lines = f.readlines()  # read old content
            f.seek(0)  # go back to the beginning of the file
            f.write(changes)  # write new content at the beginning
            for line in lines:  # write old content after new
                f.write(line)
            f.close()
            # Code taken from https://stackoverflow.com/a/11230429/18159860

    def run(self):
        vault_path = self.__get_env('VAULT_PATH')

        directories = os.listdir(vault_path)

        if len(directories) == 0:
            self.logger.warning('No directories found in vault path {}'.format(vault_path))

        for reponame in directories:
            full_repo_path = vault_path + "/" + reponame
            # Only non-hidden dirs
            if os.path.isdir(full_repo_path) and not reponame.startswith('.'):
                # Only when it is a git repo
                if os.path.exists(full_repo_path + '/.git'):
                    repo = Repo(full_repo_path)

                    if repo.is_dirty(untracked_files=True):
                        self.logger.debug('Repo \'{}\' has changes and needs a commit'.format(reponame))

                        lst_status = self.__get_clean_status_list(repo)

                        # It is possible to have a 'dirty' repository, but no changed files.
                        # We will not commit anything then. It will be taken care of at the
                        # next commit.
                        if len(lst_status) > 0:

                            self.logger.info('Changes to {} file(s) will be committed'.format(len(lst_status)))

                            # Send mail about deleted files
                            lst_deleted = [item for item in lst_status if item[0] == 'D']
                            if len(lst_deleted) > 0:
                                # Send a mail with deleted files
                                if self.__send_mail(reponame, lst_deleted) is False:
                                    self.logger.warning('Email about deleted files could not be sent')

                            # Current changes
                            date_header = datetime.datetime.now().strftime('### %Y/%m/%d %H:%M:%S')
                            lst_status = [' '.join(item) for item in lst_status]
                            md_status = '- ' + '\n- '.join(lst_status)

                            self.__set_git_config(repo)

                            # Primary commit, for the real changes
                            subprocess.run('cd {} && make commit'.format(full_repo_path),
                                           stdout=subprocess.PIPE, shell=True)

                            # Fetch git hash for just executed commit
                            git_hash = subprocess.Popen('cd {} && git log -1 --format=format:%H'.format(full_repo_path),
                                                        stdout=subprocess.PIPE, shell=True).communicate()[0]

                            # Update changelog
                            changes = \
                                date_header + '\n' + \
                                md_status + '\n\n' + \
                                'Commit hash: ' + git_hash.decode('utf-8') + '\n\n'
                            self.__update_changelog(full_repo_path, changes)

                            # Secondary commit, for the changelog file itself
                            cl_file = self.__get_changelog_file(full_repo_path).replace(' ', r'\ ')
                            cmd = 'cd {} && git add {} && git commit -m "Changelog update" && git push origin master'. \
                                format(full_repo_path, cl_file)
                            self.logger.debug('Changelog commit: {}'.format(cmd))
                            subprocess.run(cmd, stdout=subprocess.PIPE, shell=True)


load_dotenv()
obj_btk = BackupToKeybase()
obj_btk.run()
