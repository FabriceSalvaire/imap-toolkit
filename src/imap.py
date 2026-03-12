####################################################################################################

# [RFC 9051 - Internet Message Access Protocol (IMAP) - Version 4rev2](https://datatracker.ietf.org/doc/html/rfc9051)
# [RFC 2822 - Internet Message Format](https://datatracker.ietf.org/doc/html/rfc2822.html)

# [IMAPClient — IMAPClient 3.0.0 documentation](https://imapclient.readthedocs.io/en/3.0.0/index.html)
# [mjs/imapclient: An easy-to-use, Pythonic and complete IMAP client library](https://github.com/mjs/imapclient)

####################################################################################################

from dataclasses import dataclass
from pathlib import Path
from typing import Self, Callable
import argparse
import email as py_email
import email.header as py_email_header
import email.iterators as py_email_iterators
import email.policy as py_email_policy
import email.utils as py_email_utils
import logging
import mailbox

import icu
# from icu import Collator, Locale  # To sort correctly latin and unicode

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
collator = icu.Collator.createInstance(icu.Locale('fr_FR'))  # ty:ignore[unresolved-attribute]

####################################################################################################

def _humanize(
    size: int,
    binary: bool = False,
    number_of_digits: int = 1,
    prefix_space: bool = True,
) -> str:  # ty:ignore[invalid-return-type]
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
            if prefix_space:
                return f'{_}{prefix:>2}{I_PREFIX}B'
            else:
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

class Email:

    ##############################################

    def __init__(
        self,
        folder: 'Folder',
        id: int,
        data: bytes,
    ):
        # Fixme: slot ?
        self._folder = folder
        self._id = id
        self._data = data
        self._email = None

    ##############################################

    @property
    def folder(self) -> 'Folder':
        return self._folder

    @property
    def id(self) -> int:
        return self._id

    @property
    def data(self) -> bytes:
        return self._data

    @property
    def size(self) -> int:
        return len(self._data)

    ##############################################

    def _decode(self, value: str) -> str:
        # print(value)
        parts = py_email_header.decode_header(value)
        # print(parts)
        new_value = ''
        for decoded_bytes, encoding in parts:
            if encoding is None:
                if isinstance(decoded_bytes, bytes):
                    _ = decoded_bytes.decode()
                else:
                    _ = decoded_bytes
            else:
                try:
                    _ = decoded_bytes.decode(encoding)
                except LookupError:
                    # unknown-8bit
                    # raise NameError(f'Encoding {value}')
                    return value
            new_value += _
        return new_value

    def _parse(self) -> None:
        # py_email_utils.decode_rfc2231
        if self._email is None:
            self._email = py_email.message_from_bytes(self.data, policy=py_email_policy.default)
            for key, value in self._email.items():
                key = key.lower()
                match key:
                    case 'cc':
                        self._cc = value
                    case 'date':
                        self._date = py_email_utils.parsedate_to_datetime(value)
                    case 'from':
                        self._from = value
                    case 'subject':
                        self._subject = value
                    case 'to':
                        self._to = value

    @property
    def from_(self) -> str:
        self._parse()
        return self._from

    @property
    def date(self) -> str:
        self._parse()
        return self._date

    @property
    def to(self) -> str:
        self._parse()
        return self._to

    @property
    def subject(self) -> str:
        self._parse()
        return self._subject

    ##############################################

    def structure(self) -> None:
        py_email_iterators._structure(self._email, level=4)

####################################################################################################

class Folder:

    ##############################################

    def __init__(
        self,
        name: str,
        parent: 'Folder' | None = None,
        client: 'ImapClient' | None = None,
    ) -> None:
        self._name = name
        self._parent: Folder | None = parent
        self._childs: dict[str, Folder] = {}
        self._client = client
        self._selected: bool = False

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

    def find(self, folder: str) -> 'Folder':
        parts = folder.split('/')
        if parts.pop(0) != self._name:
            raise ValueError(f"Invalid root for {folder} should be {self._name}")
        parent = self
        for _ in parts:
            parent = parent._childs[_]
        return parent
 
    ##############################################

    def add(self, folder: str) -> 'Folder':
        parent, name = self.find_parent(folder)
        if parent is not None:
            child = Folder(name, parent, self._client)
            parent._childs[name] = child
            return child
        return self

    ##############################################

    def depth_first_search(self, callback: Callable, callback_data=None, level: int = 0) -> None:
        callback(self, callback_data, level)
        for name, child in sorted(self._childs.items(), key=lambda t: collator.getSortKey(t[0])):
            child.depth_first_search(callback, callback_data, level + 1)

    ##############################################

    def _check_client(self) -> None:
        if self._client is None:
            raise NameError('Client is None')

    def select(self) -> dict:
        self._check_client()
        _ = self._client.select_folder(self.full_name)  # ty:ignore[unresolved-attribute]
        self._selected = True
        return _

    def close(self) -> str:
        if self._selected:
            self._check_client()
            _ = self._client.close_folder()  # ty:ignore[unresolved-attribute]
            self._selected = False
            return _
        else:
            raise NameError(f"Folder {self} is not selected")

    @property
    def size(self) -> int:
        self._check_client()
        return self._client.folder_size(self.full_name)  # ty:ignore[unresolved-attribute]

    @property
    def number_of_mails(self) -> int:
        _ = self.select()
        self._client.close_folder()  # ty:ignore[unresolved-attribute]
        return _[b'EXISTS']

    ##############################################

    def ids(self, sorting: str = 'recent') -> list[int]:
        self.select()
        return self._client.folder_ids(sorting)  # ty:ignore[unresolved-attribute]

    def fetch(self, email_id: int) -> Email:
        self.select()
        data = self._client.fetch(email_id)  # ty:ignore[unresolved-attribute]
        return Email(self, email_id, data)

####################################################################################################

class ImapClient:

    ##############################################

    def __init__(self, config: ImapClientConfig) -> None:
        self._config = config
        self._client = imapclient.IMAPClient(config.server, use_uid=True)
        _ = self._client.login(config.user, config.password)
        # _ == b'Logged in'
        self._inbox: Folder | None = None

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

    @property
    def size(self) -> int:
        for quota in client.quota:
            match quota.resource:
                case 'STORAGE':
                    return quota.usage*1024
        raise NotImplementedError

    ##############################################

    def build_folder_tree(self) -> None:
        if self._inbox is not None:
            return
        inbox = Folder('INBOX', client=self)
        for _ in self._client.list_folders():
            folder = _[2]
            if folder != 'INBOX':
                inbox.add(folder)
        self._inbox = inbox

    @property
    def inbox(self) -> Folder:
        if self._inbox is None:
            self.build_folder_tree()
        return self._inbox  # ty:ignore[invalid-return-type]

    ##############################################

    def folder_size(self, folder: Folder | str) -> int:
        _ = self._client.folder_status(str(folder), what=('SIZE'))
        return _[b'SIZE']

    ##############################################

    def select_folder(self, folder: Folder | str) -> dict:
        return self._client.select_folder(str(folder), readonly=True)

    def close_folder(self) -> str:
        return self._client.close_folder()

    ##############################################

    # def folder_ids(self, folder: Folder | str) -> list[int]:
    #     self.select_folder(folder)
    def folder_ids(self, sorting: str = '') -> list[int]:
        # ARRIVAL CC FROM SIZE SUBJECT TO
        match sorting:
            case 'from':
                return self._client.sort(['FROM'])
            case 'subject':
                return self._client.sort(['SUBJECT'])
            case 'recent':
                return self._client.sort(['REVERSE DATE'])
            case 'size':
                return self._client.sort(['REVERSE SIZE'])
            case _:
                return self._client.search('ALL')

    def fetch(self, email_id: int) -> bytes:
        _ = self._client.fetch(email_id, ['RFC822'])
        return _[email_id][b'RFC822']

####################################################################################################

@dataclass
class CallbackData:
    show_full_name: bool = False
    number_of_mails: int = 0
    number_of_folders: int = 0
    size: int = 0
    size2: int = 0

def folder_callback(folder: Folder, callback_data, level: int) -> None:
    indent = ' '*level*4
    line = f'{indent}"{folder.name}"'
    line = f'{line:<40}'
    try:
        callback_data.number_of_folders += 1
        number_of_mails = folder.number_of_mails
        callback_data.number_of_mails += number_of_mails
        size = folder.size
        percent = 100 * size / callback_data.size
        if percent < 1:
            percent_str = '  <  '
        elif percent > 5:
            percent_str = f'{round(percent):>3}  '
        else:
            percent_str = f'{percent:5.1f}'
        callback_data.size2 += size
        _ = byte_humanize(size)
        console.print(f'{line} {number_of_mails:>8_} {_:>10} {percent_str} %')
        if callback_data.show_full_name:
            indent = ''
            console.print(f'{indent}[blue]"{folder.full_name}"')
    except Exception as e:
        # print(e)
        console.print(f'{line} [red]!!!')
    # console.print(f'"{folder}"')

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
parser.add_argument(
    '--capabilities',
    action='store_true',
)
parser.add_argument(
    '--quota',
    action='store_true',
)
parser.add_argument(
    '--folders',
    action='store_true',
)
parser.add_argument(
    '--folders-full-name',
    action='store_true',
)
args = parser.parse_args()

console = Console()

config_path = Path(args.config)
# config = yaml.load(config_path.read_text(), Loader=yaml.SafeLoader)
# console.print(config)
imap_config = ImapClientConfig.from_yaml(config_path, args.imap)
client = ImapClient(imap_config)
console.print(f"Logged to [green]{imap_config.server}")

if args.capabilities:
    console.print("Server Capabilities:")
    for _ in client.capabilities:
        console.print(f"  '{_}'")

if args.quota:
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
                console.print(f"  {title:<20} {usage} / {limit} @{percent} %")
            case 'MESSAGE':
                title = 'Number of Messages'
                console.print(f"  {title:<20} {quota.usage:_} / {quota.limit:_} @{percent} %")

if args.folders:
    console.print()
    console.print("[yellow]Folders:")
    size1 = client.size
    # print(f"Size {byte_humanize(size1)}")
    callback_data= CallbackData(size=size1, show_full_name=args.folders_full_name)
    client.inbox.depth_first_search(folder_callback, callback_data)
    size = byte_humanize(callback_data.size2)
    console.print(f"  #folders {callback_data.number_of_folders}")
    console.print(f"{' '*40} {callback_data.number_of_mails:>8_} {size:>8}")

folder_name = 'INBOX/Compte Site Web'
# client.select_folder(folder_name)
# email_ids = client.folder_ids()
# email_id = email_ids[0]
# _ = client.fetch(email_id)

folder = client.inbox.find(folder_name)
# email_ids = folder.ids
# email_id = email_ids[0]
# _ = folder.fetch(email_id)
# console.print(_.data)
# headers = set()
mbox = mailbox.mbox('csw.mbox')
for email_id in folder.ids('size')[:100]:
    email = folder.fetch(email_id)
    size = byte_humanize(email.size)
    console.print(f"{email_id:6} {size:>8}")
    # headers |= set(email_message.keys())
    indent = ' '*10
    console.print(f"{indent}{email.date}")
    console.print(f"{indent}{email.from_}")
    console.print(f"{indent}{email.subject}")
    email.structure()
    mbox.add(email.data)
# console.print(sorted(headers))

# # _ = server.fetch(email_id, '(BODY.PEEK[HEADER.FIELDS (MESSAGE-ID)])')
# console.print(_)
