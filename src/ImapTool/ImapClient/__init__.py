####################################################################################################
#
# imap-tool -
# Copyright (C) 2026 Fabrice SALVAIRE
# SPDX-License-Identifier: GPL-3.0-or-later
#
####################################################################################################

__all__ = [
    'add_logging_to_imaplib',
    'Email',
    'Folder',
    'ImapClient',
    'ImapClientConfig',
    'ImapExtensionError',
]

from .client import Folder, ImapClient, ImapExtensionError, add_logging_to_imaplib
from .config import ImapClientConfig
from .email import Email
