####################################################################################################
#
# imap-tool -
# Copyright (C) 2026 Fabrice SALVAIRE
# SPDX-License-Identifier: GPL-3.0-or-later
#
####################################################################################################

__all__ = [
    'add_logging_to_imaplib',
    'Folder',
    'ImapClient',
    'ImapExtensionError',
]

####################################################################################################

import mailbox
from collections.abc import Callable, Iterator
from pathlib import Path

from rich.console import Console

import imapclient

from ImapTool.unicode import collator

from .config import ImapClientConfig
from .email import Email

####################################################################################################

type PathStr = Path | str

####################################################################################################

class ImapExtensionError(NameError):
    pass

####################################################################################################

def add_logging_to_imaplib(console: Console) -> None:
    import imaplib

    cls = imaplib.IMAP4
    py_read = cls.read
    py_readline = cls.readline
    py_send = cls.send

    COMMANDS = list(imaplib.Commands.keys())
    RESPONSES = ('OK', 'NO', 'BAD', 'PREAUTH', 'BYE')

    COMMAND_IDS: list[str] = []

    def split(text: str) -> tuple[int, int]:
        s1 = text.find(' ')
        if s1 == -1:
            raise ValueError
        s2 = text.find(' ', s1+1)
        if s2 == -1:
            s2 = text.find('\r', s1+1)
        return s1, s2

    def log(func: str, data: bytes) -> bytes:
        try:
            text = data.decode('ASCII')
            if text != '\r\n':
                if func.startswith('send'):
                    s1, s2 = split(text)
                    command_id = text[:s1]
                    COMMAND_IDS.append(command_id)
                    command = text[s1+1:s2]
                    args = text[s2+1:]
                    if command not in COMMANDS:
                        raise ValueError
                    text = f'[imap_cmd_id]{command_id}[/] [imap_cmd]{command}[/] [imap_args]{args}[/]'
                else:
                    s1, s2 = split(text)
                    p1 = text[:s1]
                    p2 = text[s1+1:s2]
                    p3 = text[s2:]
                    if p1 in COMMAND_IDS and p2 in RESPONSES:
                        COMMAND_IDS.remove(p1)
                        text = f'[imap_cmd_id]{p1}[/] [imap_ok]{p2}[/] [imap_args]{p3}[/]'
                    elif p1 in '*-' and p2 in RESPONSES:
                        text = f'[imap_star]{p1}[/] [imap_ok]{p2}[/] [imap_args]{p3}[/]'
                    elif p1 in '*-':
                        text = f'[imap_star]{p1}[/] [imap_args]{p2} {p3}[/]'
            text = text.replace('\r\n', ' [imap_rn]\\r\\n[/]')
            console.print(f'[debug]DEBUG:[/] [func]IMAP4.{func:8}[/] {text}')
        except Exception as e:
            console.print(f'{func} {data}')
            # console.print(e)
            raise e
        return data

    def read(self, size):
        return log('read', py_read(self, size))

    def readline(self):
        return log('readline', py_readline(self))

    def send(self, data):
        py_send(self, log('send', data))

    cls.read = read
    cls.readline = readline
    cls.send = send

####################################################################################################

class Folder:

    ##############################################

    def __init__(
        self,
        name: str,
        parent: Folder | None = None,
        client: ImapClient | None = None,
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
    def is_root(self) -> bool:
        return not self._name

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
        if not self.is_root:
            if self._parent.is_root:
                return self._name
            else:
                return self._parent.full_name + '/' + self._name
        else:
            raise NameError("Folder is root")

    def __str__(self) -> str:
        return self.full_name

    ##############################################

    def find_parent(self, folder: str) -> tuple[Folder | None, str]:
        # It assumes parents are build before childs
        # print(f"find_parent '{folder}'")
        *parents, name = folder.split('/')
        if not parents:
            return self, name
        parent = self
        for _ in parents:
            # print(f"  '{parent._name}' '{_}'")
            parent = parent._childs[_]
        return parent, name

    def find(self, folder: str) -> Folder:
        parts = folder.split('/')
        parent = self
        for _ in parts:
            parent = parent._childs[_]
        return parent

    ##############################################

    @property
    def has_childs(self) -> bool:
        return bool(self._childs)

    # @property
    # def childs(self) -> list[str]:
    #     return list(self._childs.keys())

    @property
    def childs(self) -> Iterator[Folder]:
        return self._childs.values()

    ##############################################

    def add(self, folder: str) -> Folder:
        parent, name = self.find_parent(folder)
        if parent is not None:
            child = Folder(name, parent, self._client)
            parent._childs[name] = child
            return child
        return self

    ##############################################

    def depth_first_search(self, callback: Callable, callback_data=None, level: int = 0) -> None:
        if not self.is_root:
            callback(self, callback_data, level)
        for _, child in sorted(self._childs.items(), key=lambda t: collator.getSortKey(t[0])):
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

    ##############################################

    def save(self, path: PathStr, sorting='recent', limit: int = -1) -> None:
        path = Path(path)
        if not path.exists():
            mbox = mailbox.mbox(path)
            for email_id in self.ids(sorting)[:limit]:
                email = self.fetch(email_id)
                mbox.add(email.data)
        else:
            raise NameError(f"Mbox {path} exists")

####################################################################################################

class ImapClient:

    ##############################################

    def __init__(self, config: ImapClientConfig, debug: bool = False) -> None:
        self._config = config
        if debug:
            import imaplib
            imaplib.Debug = 100
            # __debug__ is a global
        self._client = imapclient.IMAPClient(config.server, use_uid=True)
        _ = self._client.login(config.user, config.password)
        # _ == b'Logged in'
        self._root: Folder | None = None
        self._get_capabilities()

    ##############################################

    @property
    def welcome(self) -> str:
        return self._client.welcome.decode('ascii')

    ##############################################

    def _get_capabilities(self) -> list[str]:
        self._capabilities = [_.decode('ASCII') for _ in self._client.capabilities()]
        # self._has_status_size = self.has_capability('STATUS=SIZE')
        self._has_status_size = 'STATUS=SIZE' in self._capabilities

    @property
    def capabilities(self) -> list[str]:
        return self._capabilities

    def has_capability(self, capability: str) -> bool:
        return self._client.has_capability(capability)

    ##############################################

    @property
    def config(self) -> ImapClientConfig:
        return self._config

    ##############################################

    @property
    def quota(self) -> list:  # .Quota ???
        # OVH
        #   (MailboxQuotaRoots(mailbox='INBOX', quota_roots=['']),
        #    [Quota(quota_root='', resource='STORAGE', usage=4882231, limit=5242880)])
        #    [Quota(quota_root='', resource='STORAGE', usage=4882231, limit=5242880)]
        # Orange
        #   (MailboxQuotaRoots(mailbox='INBOX', quota_roots=['userquota']),
        #    [Quota(quota_root='userquota', resource='STORAGE', usage=8843043, limit=10485760),
        #     Quota(quota_root='userquota', resource='MESSAGE', usage=140251, limit=1048576)])
        #    [Quota(quota_root='userquota', resource='STORAGE', usage=8843043, limit=10485760),
        #     Quota(quota_root='userquota', resource='MESSAGE', usage=140251, limit=1048576)]
        # Fixme: INBOX
        # _ = self._client.get_quota_root('INBOX')
        return self._client.get_quota(mailbox="INBOX")

    ##############################################

    @property
    def size(self) -> int:
        for quota in self.quota:
            match quota.resource:
                case 'STORAGE':
                    # Fixme: 1024 or 1000
                    return quota.usage * 1000
        raise NotImplementedError

    ##############################################

    def build_folder_tree(self) -> None:
        if self._root is not None:
            return
        root = Folder('', client=self)
        for _ in self._client.list_folders():
            folder = _[2]
            root.add(folder)
        self._root = root

    @property
    def root(self) -> Folder:
        if self._root is None:
            self.build_folder_tree()
        return self._root  # ty:ignore[invalid-return-type]

    ##############################################

    def folder_size(self, folder: Folder | str) -> int:
        # ic = self._client
        # cmd = 'LIST'
        # directory = ic._normalise_folder('')
        # pattern = ic._normalise_folder('%')
        # typ, dat = ic._imap._simple_command(cmd, directory, pattern, 'RETURN (STATUS (MESSAGES SIZE))')
        # typ, dat = ic._imap._untagged_response(typ, dat, cmd)
        # print(dat)
        if self._has_status_size:
            # require: STATUS=SIZE
            _ = self._client.folder_status(str(folder), what=('SIZE'))
            return _[b'SIZE']
        else:
            self.select_folder(folder)
            size = 0
            for _, data in self._client.fetch('1:*', ['RFC822.SIZE']).items():
                size += data[b'RFC822.SIZE']
            return size

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
