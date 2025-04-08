# -*- coding: utf-8 -*-
"""
Created on Fri Jan 06 16:12:44 2017

@author: Zhengyi
"""

import os
import sys
import argparse
from getpass import getuser

from fabric import Connection
from invoke import UnexpectedExit


class DeployKey():

    def __init__(self, hostname, username=None, password=None, port=22,
                 local_key_path=None, remote_key_path=None):
        self.hostname = hostname

        if username is None:
            self.username = getuser()
        else:
            self.username = username

        self.password = password
        self.port = port

        if local_key_path is None:
            self.local_key_path = self._get_default_local_key_path()
        else:
            self.local_key_path = os.path.abspath(local_key_path)
        if remote_key_path is None:
            self.remote_key_path = self._get_default_remote_key_path()
        else:
            self.remote_key_path = remote_key_path

    def _get_default_local_key_path(self):
        home = os.path.expanduser('~')
        return os.path.join(home, '.ssh', 'id_rsa.pub')

    def _get_default_remote_key_path(self):
        return '~/.ssh/authorized_keys'

    def _get_local_key(self):
        try:
            key = open(self.local_key_path).read().strip()
        except Exception:
            print("ERROR: key file '%s' could not be opened." %
                  self.local_key_path)
            sys.exit(1)
        return key

    def deploy_key(self):
        key = self._get_local_key()
        copied = 0
        conn = Connection(
            host=self.hostname,
            user=self.username,
            port=self.port,
            connect_kwargs={"password": self.password} if self.password else {}
        )
        try:
            if conn.run(f'[ -f {self.remote_key_path} ] && echo 1 || echo 0', hide=True).stdout.strip() == '1':
                authorized_keys = conn.run(f'cat {self.remote_key_path}', hide=True).stdout
                if key not in authorized_keys:
                    conn.run(f'echo >> {self.remote_key_path}', hide=True)
                    conn.run(f'echo "{key}" >> {self.remote_key_path}', hide=True)
                    copied += 1
                else:
                    print(f"WARNING: ssh public key already exists in '{self.remote_key_path}'")
            else:
                dirpath, filename = os.path.split(self.remote_key_path)
                conn.run(f'mkdir -p {dirpath}', hide=True)
                conn.run(f'echo "{key}" > {self.remote_key_path}', hide=True)
                conn.run(f'chmod 600 {self.remote_key_path}', hide=True)
                copied += 1
            print()
            print('Number of keys copied: ', copied)
            print(f"Now try logging into the machine with: 'ssh {self.username}@{self.hostname}'")
        except UnexpectedExit as e:
            print(f"ERROR: Command failed: {e.result.command}")
            print(e.result.stderr)
            sys.exit(1)


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='ssh-copy-id by Zhengyi')
    parser.add_argument('hostname', help='[user@]machine')
    parser.add_argument('-i', nargs='?', dest='identity_file', default=None,
                        help='defaults to ~/.ssh/id_rsa.pub')
    parser.add_argument('-p', nargs='?', dest='port', type=int, default=22,
                        help='defaults to 22')
    args = parser.parse_args()

    hostname = args.hostname
    username = None
    if '@' in args.hostname:
        if args.hostname.count('@') > 1:
            print('ERROR: unrecognized [user@]machine %s ' % args.hostname)
            sys.exit(1)
        username, hostname = hostname.split('@')

    ssh_copy_id = DeployKey(hostname, username, port=args.port,
                            local_key_path=args.identity_file).deploy_key
    try:
        ssh_copy_id()
    except KeyboardInterrupt:
        print('\nKeyboardInterrupt')
    except SystemExit:
        print('\nSystemExit')
    except Exception as e:
        print('\nERROR: ', e)

