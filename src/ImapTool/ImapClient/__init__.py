####################################################################################################
#
# imap-tool -
# Copyright (C) 2026 Fabrice SALVAIRE
# SPDX-License-Identifier: GPL-3.0-or-later
#
####################################################################################################

__all__ = [
    'Email',
    'Folder',
    'ImapClient',
    'ImapClientConfig',
]

from .client import Folder, ImapClient
from .config import ImapClientConfig
from .email import Email
