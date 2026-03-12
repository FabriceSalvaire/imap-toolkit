####################################################################################################
#
# imap-tool -
# Copyright (C) 2026 Fabrice SALVAIRE
# SPDX-License-Identifier: GPL-3.0-or-later
#
####################################################################################################

###################################################################################################

__all__ = ['Cli']

####################################################################################################

import argparse
import inspect
import os
import traceback
from pathlib import Path

# See also [cmd — Support for line-oriented command interpreters — Python documentation](https://docs.python.org/3/library/cmd.html)
# Python Prompt Toolkit](https://python-prompt-toolkit.readthedocs.io/en/master/)
# from prompt_toolkit.completion import CompleteEvent, Completer, Completion, WordCompleter
# from prompt_toolkit.shortcuts import ProgressBar
from prompt_toolkit import PromptSession, shortcuts
from prompt_toolkit.completion import WordCompleter
from prompt_toolkit.history import FileHistory

from ImapTool.folder_helpers import CallbackData, folder_callback
from ImapTool.ImapClient import ImapClient, ImapClientConfig
from ImapTool.printer import byte_humanize, init_console

####################################################################################################

# _module_logger = logging.getLogger('')

LINESEP = os.linesep

type PathStr = Path | str
type CommandName = str

####################################################################################################

class Cli:

    ############################################################################

    def __init__(self, args: argparse.Namespace) -> None:
        self._args = args
        self._console = init_console()
        self.COMMANDS = [
            _
            for _ in dir(self)
            if not (_.startswith('_') or _[0].isupper() or _ in ('cli', 'run', 'print'))
        ]
        self.COMMANDS.sort()
        self._completer = WordCompleter(self.COMMANDS)
        # self._completer = CustomCompleter(self, self.COMMANDS)

        self._client: ImapClient | None = None
        if args.config and args.server:
            self.login(args.config, args.server)

    ##############################################

    def _run_line(self, query: str) -> bool:
        # try:
        command, *argument = query.split()
        # except ValueError:
        #     if query.strip() == 'quit':
        #         return False
        # print(f"|{command}|{argument}|")
        try:
            if command == 'quit':
                return False
            method = getattr(self, command)
            try:
                method(*argument)
            except KeyboardInterrupt:
                self.print(f"{LINESEP}[red]Interrupted")
            # except ApiError as e:
            #     self.print(f'API error: [red]{e}')
            # except CommandError as e:
            #     self.print(e)
            except Exception as e:
                print(traceback.format_exc())
                print(e)
        except AttributeError:
            self.print(f"[red]Invalid command[/] [blue]{query}[/]")
            self.usage()
        return True

    ##############################################

    def run(self, query: str) -> bool:
        commands = filter(bool, [_.strip() for _ in query.split(';')])
        return all(self._run_line(query) for query in commands)

    ##############################################

    def cli(self, query: str) -> None:
        if query and not self.run(query):
            return

        # history_path = config.CLI_HISTORY_PATH
        history_path = '.history'
        history = FileHistory(history_path)
        session = PromptSession(
            completer=self._completer,
            history=history,
        )
        self.usage()
        while True:
            try:
                message = [
                    ('class:prompt', '> '),
                ]
                query = session.prompt(
                    message,
                    # style=STYLE,
                )
            # except KeyboardInterrupt:
            #     continue
            except EOFError:
                break
            else:
                if query:
                    if not self.run(query):
                        break
                else:
                    self.usage()

    ##############################################

    def print(self, message: str = '') -> None:
        self._console.print(message)

    ############################################################################

    def clear(self) -> None:
        """Clear the console"""
        shortcuts.clear()

    ############################################################################
    #
    # Help
    #

    def usage(self) -> None:
        """Show usage"""
        for _ in (
            "[red]Enter[/]: [blue]command argument[/]",
            "    or [blue]command1 argument; command2 argument; ...[/]",
            "[red]Commands are[/]: " + ', '.join([f"[blue]{_}[/]" for _ in self.COMMANDS]),
            "use [blue]help[/] [green]command[/] to get help",
            "use [green]tab[/] key to complete",
            "use [green]up/down[/] key to navigate history",
            "[red]Exit[/] using command [blue]quit[/] or [blue]Ctrl+d[/]"
        ):
            self.print(_)

    ##############################################

    def _help(self, command: CommandName, show_parameters: bool = False) -> None:
        func = getattr(self, command)
        # help(func)
        self.print(f'[green]{command:16}[/] [blue]{func.__doc__ or ''}[/]')
        if show_parameters:
            signature = inspect.signature(func)
            for _ in signature.parameters.values():
                default = f' = [orange]{_.default}[/]' if _.default != inspect._empty else ''
                self.print(f'  [blue]{_.name}[/]: [green]{_.annotation.__name__}[/]{default}')

    def help(self, command: CommandName | None = None) -> None:
        """Show command help"""
        if command is None:
            for command in self.COMMANDS:
                self._help(command)
        else:
            self._help(command, show_parameters=True)

    ##############################################

    def _login(self, config_path: PathStr, server: str) -> None:
        config_path = Path(config_path)
        # config = yaml.load(config_path.read_text(), Loader=yaml.SafeLoader)
        # self.print(config)
        imap_config = ImapClientConfig.from_yaml(config_path, server)
        self._client = ImapClient(imap_config)
        self.print(f"Logged to [green]{imap_config.server}")

    def _check_logged(self) -> bool:
        if self._client is None:
            self.print("[red]Not logged")
            return False
        return True

    ##############################################

    def login(self, server: str) -> None:
        self._login(self._args.config, server)

    ##############################################

    def capabilities(self) -> None:
        if not self._check_logged():
            return
        self.print("Server Capabilities:")
        for _ in self._client.capabilities:
            self.print(f"  '{_}'")

    ##############################################

    def quota(self) -> None:
        if not self._check_logged():
            return
        self.print()
        self.print("[yellow]Quota:")
        for quota in self._client.quota:
            # self.print(quota)
            percent = round(100 * quota.usage / quota.limit)
            match quota.resource:
                case 'STORAGE':
                    usage = byte_humanize(quota.usage * 1024)
                    limit = byte_humanize(quota.limit * 1024)
                    title = 'Storage'
                    self.print(f"  {title:<20} {usage} / {limit} @{percent} %")
                case 'MESSAGE':
                    title = 'Number of Messages'
                    self.print(f"  {title:<20} {quota.usage:_} / {quota.limit:_} @{percent} %")

    ##############################################

    def folders(self, show_full_name: bool = False) -> None:
        if not self._check_logged():
            return
        self.print()
        self.print("[yellow]Folders:")
        size1 = self._client.size
        # print(f"Size {byte_humanize(size1)}")
        callback_data = CallbackData(console=self, size=size1, show_full_name=show_full_name)
        self._client.inbox.depth_first_search(folder_callback, callback_data)
        size = byte_humanize(callback_data.size2)
        self.print(f"  #folders {callback_data.number_of_folders}")
        self.print(f"{' ' * 40} {callback_data.number_of_mails:>8_} {size:>8}")
