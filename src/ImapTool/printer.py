####################################################################################################
#
# imap-tool -
# Copyright (C) 2026 Fabrice SALVAIRE
# SPDX-License-Identifier: GPL-3.0-or-later
#
####################################################################################################

__all__ = [
    'byte_humanize',
    'ibyte_humanize',
    'init_console',
]

####################################################################################################

from rich.console import Console

####################################################################################################

def init_console() -> Console:
    console = Console()
    return console

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
    DOT_ZERO = '.' + '0' * number_of_digits
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
