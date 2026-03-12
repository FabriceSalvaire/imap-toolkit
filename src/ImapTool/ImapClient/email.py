####################################################################################################
#
# imap-tool -
# Copyright (C) 2026 Fabrice SALVAIRE
# SPDX-License-Identifier: GPL-3.0-or-later
#
####################################################################################################

__all__ = ['Email']

####################################################################################################

import email as py_email
import email.iterators as py_email_iterators
import email.policy as py_email_policy
import email.utils as py_email_utils
from datetime import datetime
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from .client import Folder

####################################################################################################

class Email:

    ##############################################

    def __init__(
        self,
        folder: Folder,
        id: int,
        data: bytes,
    ):

        # Fixme: slot ?
        self._folder = folder
        self._id = id
        self._data = data
        self._email = None   # : py_email. Message | None

    ##############################################

    @property
    def folder(self) -> Folder:
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
    def date(self) -> datetime:
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
        py_email_iterators._structure(self._email, level=4)  # ty:ignore[invalid-argument-type]
