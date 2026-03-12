####################################################################################################
#
# imap-tool -
# Copyright (C) 2026 Fabrice SALVAIRE
# SPDX-License-Identifier: GPL-3.0-or-later
#
####################################################################################################

__all__ = ['Folder', 'ImapClient']

####################################################################################################

from typing import Self, Callable

import imapclient

from .config import ImapClientConfig
from .email import Email
from ImapTool.unicode import collator

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
        for quota in self.quota:
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
