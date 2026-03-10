####################################################################################################

# [RFC 9051 - Internet Message Access Protocol (IMAP) - Version 4rev2](https://datatracker.ietf.org/doc/html/rfc9051)
# [RFC 2822 - Internet Message Format](https://datatracker.ietf.org/doc/html/rfc2822.html)

# [IMAPClient — IMAPClient 3.0.0 documentation](https://imapclient.readthedocs.io/en/3.0.0/index.html)
# [mjs/imapclient: An easy-to-use, Pythonic and complete IMAP client library](https://github.com/mjs/imapclient)

####################################################################################################

from dataclasses import dataclass
from icu import Collator, Locale  # To sort correctly latin and unicode
from pathlib import Path
from typing import Self, Callable
import argparse
import email
import logging

import imapclient

import yaml

from rich.console import Console

####################################################################################################

# logging.basicConfig(
#     format='%(asctime)s - %(levelname)s: %(message)s',
#     level=logging.DEBUG
# )

####################################################################################################

# Fixme:
collator = Collator.createInstance(Locale('fr_FR'))

####################################################################################################

def _humanize(size: int, binary: bool = False, number_of_digits: int = 1) -> str:  # ty:ignore[invalid-return-type]
    # if not size:
    #     return None
    BASE = 1024 if binary else 1000
    I_PREFIX = 'i' if binary else ''
    PREFIXES = ('', 'k', 'M', 'G', 'T', 'P')
    DOT_ZERO = '.' + '0'*number_of_digits
    remain: float = size
    for prefix in PREFIXES:
        next_remain = remain / BASE
        if int(next_remain) == 0 or prefix == PREFIXES[-1]:
            _ = str(round(remain, number_of_digits))
            # remove .000
            if _.endswith(DOT_ZERO):
                _ = _[:-len(DOT_ZERO)]
            return f'{_}{prefix}{I_PREFIX}B'
        remain = next_remain

def byte_humanize(size: int) -> str:
    return _humanize(size)

def ibyte_humanize(size: int) -> str:
    return _humanize(size, binary=True)

####################################################################################################

@dataclass
class ImapClientConfig:
    server: str
    user: str
    password: str

    ##############################################

    @classmethod
    def from_yaml(cls, path: Path, server: str) -> Self:
        _ = yaml.load(path.read_text(), Loader=yaml.SafeLoader)
        return cls(**_[server])

####################################################################################################

class Folder:

    ##############################################

    def __init__(self, name: str, parent: 'Folder' | None = None) -> None:
        self._name = name
        self._parent: Folder | None = parent
        self._childs: dict[str, Folder] = {}

    ##############################################

    @property
    def name(self) -> str:
        return self._name

    @property
    def full_name(self) -> str:
        # parts = [self._name]
        # parent = self
        # while True:
        #     parent = parent._parent
        #     if parent is None:
        #         break
        #     parts.append(parent._name)
        # return '/'.join(reversed(parts))
        if self._parent is not None:
            return self._parent.full_name + '/' + self._name
        else:
            return self._name

    def __str__(self) -> str:
        return self.full_name

    ##############################################

    def find_parent(self, folder: str) -> tuple['Folder' | None, str]:
        # It assumes parents are build before childs
        # print(f"find_parent '{folder}'")
        *parents, name = folder.split('/')
        if not parents and name == self._name:
            return None, name
        if parents.pop(0) != self._name:
            raise ValueError(f"Invalid root for {folder} should be {self._name}")
        parent = self
        for _ in parents:
            # print(f"  '{parent._name}' '{_}'")
            parent = parent._childs[_]
        return parent, name

    ##############################################

    def add(self, folder: str) -> 'Folder':
        parent, name = self.find_parent(folder)
        if parent is not None:
            child = Folder(name, parent)
            parent._childs[name] = child
            return child
        return self

    ##############################################

    def depth_first_search(self, callback: Callable, callback_data=None, level: int = 0) -> None:
        callback(self, callback_data, level)
        for name, child in sorted(self._childs.items(), key=lambda t: collator.getSortKey(t[0])):
            child.depth_first_search(callback, callback_data, level + 1)

####################################################################################################

class ImapClient:

    ##############################################

    def __init__(self, config: ImapClientConfig) -> None:
        self._config = config
        self._client = imapclient.IMAPClient(config.server, use_uid=True)
        _ = self._client.login(config.user, config.password)
        # _ == b'Logged in'

    ##############################################

    @property
    def config(self) -> ImapClientConfig:
        return self._config

    ##############################################

    @property
    def capabilities(self) -> list[str]:
        return [_.decode('ASCII') for _ in self._client.capabilities()]

    ##############################################

    @property
    def quota(self) -> list:  # .Quota ???
        # self._client.get_quota_root('INBOX')
        return self._client.get_quota(mailbox='INBOX')

    ##############################################

    def build_folder_tree(self) -> None:
        inbox = Folder('INBOX')
        for _ in self._client.list_folders():
            folder = _[2]
            if folder != 'INBOX':
                inbox.add(folder)
        self._inbox = inbox

    @property
    def inbox(self) -> Folder:
        return self._inbox

    ##############################################

    def select_folder(self, folder: Folder) -> dict:
        return self._client.select_folder(str(folder), readonly=True)

####################################################################################################

parser = argparse.ArgumentParser(
    prog='',
    description='',
    epilog='',
)
parser.add_argument(
    '--config',
    default='config.yaml'
)
parser.add_argument(
    '--imap',
    required=True,
)
args = parser.parse_args()

console = Console()

config_path = Path(args.config)
# config = yaml.load(config_path.read_text(), Loader=yaml.SafeLoader)
# console.print(config)
imap_config = ImapClientConfig.from_yaml(config_path, args.imap)
client = ImapClient(imap_config)
console.print(f"Logged to [green]{imap_config.server}")

# console.print("Server Capabilities:")
# for _ in client.capabilities:
#     console.print(f"  '{_}'")

console.print()
console.print("[yellow]Quota:")
for quota in client.quota:
    # console.print(quota)
    percent = round(100 * quota.usage / quota.limit)
    match quota.resource:
        case 'STORAGE':
            usage = byte_humanize(quota.usage*1024)
            limit = byte_humanize(quota.limit*1024)
            title = 'Storage'
            console.print(f"  {title:<20} {usage} / {limit} @{percent}%")
        case 'MESSAGE':
            title = 'Number of Messages'
            console.print(f"  {title:<20} {quota.usage:_} / {quota.limit:_} @{percent}%")

client.build_folder_tree()

@dataclass
class CallbackData:
    number_of_mails: int = 0
    number_of_folder: int = 0

def folder_callback(folder: Folder, callback_data, level: int) -> None:
    indent = ' '*level*4
    line = f'{indent}"{folder.name}"'
    line = f'{line:<40}'
    try:
        number_of_mails = client.select_folder(folder)[b'EXISTS']
        callback_data.number_of_mails += number_of_mails
        console.print(f'{line} {number_of_mails:>8_}')
    except:
        console.print(f'{line} [red]!!!')
    # console.print(f'"{folder}"')

console.print()
console.print("[yellow]Folders:")
callback_data= CallbackData()
client.inbox.depth_first_search(folder_callback, callback_data)
console.print(f"{' '*40} {callback_data.number_of_mails:>8_}")

# email_ids = server.search('ALL')
# console.print(email_ids)

# email_id = email_ids[0]
# _ = server.fetch(email_id, ['RFC822'])
# console.print(_)
# message_data = _[email_id]
# email_message = email.message_from_bytes(message_data[b"RFC822"])
# console.print(email_message.get('From'))

# # _ = server.fetch(email_id, '(BODY.PEEK[HEADER.FIELDS (MESSAGE-ID)])')
# console.print(_)
