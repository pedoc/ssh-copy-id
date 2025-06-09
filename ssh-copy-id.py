# -*- coding: utf-8 -*-
"""
Created on Fri Jan 06 16:12:44 2017

@author: Zhengyi
"""

import os
import sys
import argparse
from getpass import getuser, getpass

from fabric import Connection
from invoke import UnexpectedExit
from paramiko.ssh_exception import AuthenticationException
import paramiko

# import logging
# logging.basicConfig(level=logging.DEBUG)

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

    def ensure_ssh_rsa_key(self, ssh_dir, public_key_name='id_rsa.pub', private_key_name='id_rsa'):
        private_key_path = os.path.join(ssh_dir, private_key_name)
        public_key_path = os.path.join(ssh_dir, public_key_name)
        if os.path.exists(public_key_path):
            return
        os.makedirs(ssh_dir, exist_ok=True)
        key = paramiko.RSAKey.generate(bits=4096)
        key.write_private_key_file(private_key_path)
        os.chmod(private_key_path, 0o600)
        with open(public_key_path, "w") as pub_file:
            pub_file.write(f"{key.get_name()} {key.get_base64()}\n")
        print(f"SSH 密钥已生成：\n  - 私钥：{private_key_path}\n  - 公钥：{public_key_path}")

    def _get_default_local_key_path(self):
        ssh_dir = os.path.expanduser('~/.ssh')
        public_key_name = 'id_rsa.pub'
        private_key_name = 'id_rsa'
        result = os.path.join(ssh_dir, public_key_name)
        if not os.path.exists(result):
            self.ensure_ssh_rsa_key(ssh_dir, public_key_name, private_key_name)
        return result

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

    def try_connect_with_prompt(self):
        retry_count = 1
        while retry_count <= 3:
            try:
                conn = Connection(
                    host=self.hostname,
                    user=self.username,
                    port=self.port,
                    connect_kwargs={"password": self.password} if self.password else {}
                )
                print(conn.__class__)
                conn.open()
                return conn
            except AuthenticationException:
                self.password = getpass(f"[{retry_count}] {self.username}@{self.hostname}'s password: ")
                retry_count += 1
            except Exception as e:
                print(f"ERROR: {e}")
                sys.exit(1)

    def deploy_key(self):
        key = self._get_local_key()
        copied = 0
        conn = self.try_connect_with_prompt()
        try:
            print(f'Information:')
            conn.run('uname -a', hide=False)
            print()

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

# Patch built-in open function to default to UTF-8 encoding
def patch_builtins_open():
    import builtins
    original_open = builtins.open
    def utf8_open(*args, **kwargs):
        if 'encoding' not in kwargs:
            kwargs['encoding'] = 'utf-8'
        return original_open(*args, **kwargs)
    builtins.open = utf8_open

if __name__ == '__main__':
    patch_builtins_open()

    parser = argparse.ArgumentParser(description='ssh-copy-id by Zhengyi')
    parser.add_argument('hostname', help='[user@]machine')
    parser.add_argument('-i', nargs='?', dest='identity_file', default=None,
                        help='defaults to ~/.ssh/id_rsa.pub')
    parser.add_argument('-p', nargs='?', dest='port', type=int, default=22,
                        help='defaults to 22')
    parser.add_argument('-P', nargs='?', dest='password', type=str, default='',
                        help='password')
    args = parser.parse_args()

    hostname = args.hostname
    username = None
    if '@' in args.hostname:
        if args.hostname.count('@') > 1:
            print('ERROR: unrecognized [user@]machine %s ' % args.hostname)
            sys.exit(1)
        username, hostname = hostname.split('@')

    ssh_copy_id = DeployKey(hostname, username, password=args.password, port=args.port,
                            local_key_path=args.identity_file).deploy_key
    try:
        ssh_copy_id()
    except KeyboardInterrupt:
        print('\nKeyboardInterrupt')
    except SystemExit:
        print('\nSystemExit')
    except Exception as e:
        print('\nERROR: ', e)
