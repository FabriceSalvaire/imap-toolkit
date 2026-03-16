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
import re
import traceback
from collections.abc import Iterable
from pathlib import Path

# See also [cmd — Support for line-oriented command interpreters — Python documentation](https://docs.python.org/3/library/cmd.html)
# Python Prompt Toolkit](https://python-prompt-toolkit.readthedocs.io/en/master/)
# from prompt_toolkit.shortcuts import ProgressBar
from prompt_toolkit import PromptSession, shortcuts
from prompt_toolkit.completion import CompleteEvent, Completer, Completion
from prompt_toolkit.document import Document
from prompt_toolkit.history import FileHistory

from ImapTool.folder_helpers import CallbackData, folder_callback
from ImapTool.ImapClient import ImapClient, ImapClientConfig, add_logging_to_imaplib
from ImapTool.printer import byte_humanize, init_console

####################################################################################################

# _module_logger = logging.getLogger('')

LINESEP = os.linesep

type PathStr = Path | str
type CommandName = str
type FolderName = str

####################################################################################################

def percent_of(value: int, total: int) -> int:
    return round((100 * value) / total)

####################################################################################################

class CustomCompleter(Completer):

    """
    Simple autocompletion on a list of words.

    :param words: List of words or callable that returns a list of words.
    :param ignore_case: If True, case-insensitive completion.
    :param meta_dict: Optional dict mapping words to their meta-text. (This
        should map strings to strings or formatted text.)
    :param WORD: When True, use WORD characters.
    :param sentence: When True, don't complete by comparing the word before the
        cursor, but by comparing all the text before the cursor. In this case,
        the list of words is just a list of strings, where each string can
        contain spaces. (Can not be used together with the WORD option.)
    :param match_middle: When True, match not only the start, but also in the
                         middle of the word.
    :param pattern: Optional compiled regex for finding the word before
        the cursor to complete. When given, use this regex pattern instead of
        default one (see document._FIND_WORD_RE)
    """

    ##############################################

    def __init__(self, cli, commands: list[str]) -> None:
        self._cli = cli
        self._commands = commands

        self.ignore_case = True
        # self.display_dict = display_dict or {}
        # self.meta_dict = meta_dict or {}
        self.WORD = False
        self.sentence = False
        self.match_middle = False
        self.pattern = None

    ##############################################

    def _get_word_before_cursor1(self, document, separator: str) -> str:
        line = document.current_line
        index = line.rfind(separator)
        # "dump " -> ""
        # "dump /foo/b" -> "b"
        return line[index + 1:]

    def _get_word_before_cursor2(self, document, separator: str) -> str:
        return document.text_before_cursor

    # cf. prompt_toolkit/completion/word_completer.py
    def _get_completions(
            self,
            document: Document,
            complete_event: CompleteEvent,
            words: list[str],
            separator: str,
            get_word_before_cursor,
    ) -> Iterable[Completion]:
        word_before_cursor = get_word_before_cursor(document, separator)

        def word_matches(word: str) -> bool:
            return word.startswith(word_before_cursor)

        for _ in words:
            if word_matches(_):
                yield Completion(
                    text=_,
                    start_position=-len(word_before_cursor),
                )

    ##############################################

    def get_completions(
            self,
            document: Document,
            complete_event: CompleteEvent,
    ) -> Iterable[Completion]:
        # Get command info
        line = document.current_line.lstrip()
        # remove multiple spaces
        line = re.sub(' +', ' ', line)
        number_of_parameters = line.count(' ')
        command = None
        right_word = None
        parameter_type = None
        if number_of_parameters:
            # words = [_ for _ in line.split(' ') if _]
            # command = words[0]
            index = line.rfind(' ')
            right_word = line[index + 1:]
            index = line.find(' ')
            command = line[:index]
            try:
                func = getattr(Cli, command)
                signature = inspect.signature(func)
                parameters = list(signature.parameters.values())
                if len(parameters) > 1:
                    parameter = parameters[number_of_parameters]   # 0 is self
                    parameter_type = parameter.annotation.__name__   # Fixme: case type alias ???
            except AttributeError:
                pass
        # print(f'Debug: "{command}" | "{right_word}" | {number_of_parameters} | {parameter_type}')

        separator = ' '
        get_word_before_cursor = self._get_word_before_cursor1

        def handle_folder(right_word):
            if '/' in right_word:
                nonlocal separator
                separator = '/'
            # if right_word.startswith('/'):
            #     current_path = root_path
            # cwd = current_path.find(right_word)
            i = right_word.rfind('/')
            if i != -1:
                parent_path = right_word[:i]
                parent = self._cli._client.root.find(parent_path)
                childs = parent.childs
            else:
                childs = self._cli._client.root.childs
            # we have to enter a key to trigger the completion, tab doesn't work ???
            # return [_.name + ('/' if _.has_childs else '') for _ in childs]
            return [_.name for _ in childs]

        if command is None:
            # case "du" -> "dump"
            words = self._commands
        elif document.current_char == ' ' and document.cursor_position < (len(document.current_line) - 1):
            # case "du /foo" -> "dump /foo"
            words = self._commands
            get_word_before_cursor = self._get_word_before_cursor2
        else:
            # case "dump " -> "dump /foo"
            words = ()
            match parameter_type:
                # case 'bool':
                #     words = ('true', 'false')
                case 'CommandName':
                    words = self._commands
                # case 'FilePath':
                #     cwd = Path().cwd()
                #     filenames = sorted(cwd.glob('*.*'))
                #     words = [_.name for _ in filenames]
                case 'FolderName':
                    words = handle_folder(right_word)
        yield from self._get_completions(document, complete_event, words, separator, get_word_before_cursor)

####################################################################################################

class Cli:

    ##############################################

    @staticmethod
    def _to_bool(value: str) -> bool:
        if isinstance(value, bool):
            return value
        match str(value).lower():
            case 'true' | 't':
                return True
            case _:
                return False

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
        # self._completer = WordCompleter(self.COMMANDS)
        self._completer = CustomCompleter(self, self.COMMANDS)

        if args.debug:
            self.debug(True)
        self._client: ImapClient | None = None
        if args.server:
            self.login(args.server)

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
        self._client = ImapClient(imap_config, debug=False)
        self.print(f"Logged to [green]{imap_config.server}")
        self.print(f"  {self._client.welcome}")

    def _check_logged(self) -> bool:
        if self._client is None:
            self.print("[red]Not logged")
            return False
        return True

    ##############################################

    def debug(self, value: bool) -> None:
        value = self._to_bool(value)
        if value:
            self.print("[warning]Enable debugging")
            add_logging_to_imaplib(self._console)

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
            percent = percent_of(quota.usage, quota.limit)
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
        self._client.root.depth_first_search(folder_callback, callback_data)
        size = byte_humanize(callback_data.size2)
        self.print(f"  #folders {callback_data.number_of_folders}")
        self.print(f"{' ' * 40} {callback_data.number_of_mails:>8_} {size:>8}")

    ##############################################

    def list_folder(self, folder_name: FolderName, limit: str = '25') -> None:
        limit = int(limit)
        folder = self._client.root.find(folder_name)
        for email_id in folder.ids('recent')[:limit]:
            email = folder.fetch(email_id)
            size = byte_humanize(email.size)
            self.print(f"{email_id:6} {size:>8}")
            # headers |= set(email_message.keys())
            indent = ' ' * 10
            self.print(f"{indent}{email.date}")
            self.print(f"{indent}{email.from_}")
            self.print(f"{indent}{email.subject}")
            # email.structure()
        # self.print(sorted(headers))

    ##############################################

    def header_stat(self, folder_name: FolderName) -> None:
        folder = self._client.root.find(folder_name)
        headers = {}
        email_count = 0
        for email_id in folder.ids():
            email_count += 1
            email = folder.fetch(email_id)
            for _ in email.headers:
                headers.setdefault(_, 0)
                headers[_] += 1
        for name in sorted(headers):
            count = headers[name]
            percent = percent_of(count, email_count)
            self.print(f"  {name:50}  {percent:5.1f}%  {count:6}")

    ##############################################

    def save(self, folder_name: FolderName, mbox_file: str, limit: str = '25') -> None:
        # Fixme: sorting ?
        limit = int(limit)
        folder = self._client.root.find(folder_name)
        folder.save(mbox_file, 'recent', limit)
