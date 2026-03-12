####################################################################################################
#
# imap-tool -
# Copyright (C) 2026 Fabrice SALVAIRE
# SPDX-License-Identifier: GPL-3.0-or-later
#
####################################################################################################

__all__ = ['ImapClientConfig']

####################################################################################################

from dataclasses import dataclass
from pathlib import Path
from typing import Self

import yaml

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
