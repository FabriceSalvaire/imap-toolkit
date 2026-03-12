####################################################################################################
#
# imap-tool -
# Copyright (C) 2026 Fabrice SALVAIRE
# SPDX-License-Identifier: GPL-3.0-or-later
#
####################################################################################################

__all__ = ['CallbackData', 'folder_callback']

####################################################################################################

from dataclasses import dataclass

from rich.console import Console

from ImapTool.ImapClient import Folder
from ImapTool.printer import byte_humanize

####################################################################################################

@dataclass
class CallbackData:
    console: Console
    show_full_name: bool = False
    number_of_mails: int = 0
    number_of_folders: int = 0
    size: int = 0
    size2: int = 0

def folder_callback(folder: Folder, callback_data, level: int) -> None:
    console = callback_data.console
    indent = ' ' * level * 4
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
