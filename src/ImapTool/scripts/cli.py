####################################################################################################
#
# imap-tool -
# Copyright (C) 2026 Fabrice SALVAIRE
# SPDX-License-Identifier: GPL-3.0-or-later
#
####################################################################################################

__all__ = ['main']

####################################################################################################

import argparse

from ImapTool.Cli import Cli

# from ImapTool import config as Config
# from ImapTool import logging as Logging

####################################################################################################

def main():
    parser = argparse.ArgumentParser(
        prog='imap-tool',
        description='',
        epilog='',
    )
    parser.add_argument(
        '--config',
        default='config.yaml'
    )
    parser.add_argument(
        '--server',
    )
    # parser.add_argument('--debug', action='store_true')
    args = parser.parse_args()

    # if args.debug:
    #     Config.DEBUG = True
    # config = Config.load_config()
    # logger = Logging.setup_logging(
    #     config_file=config.LOGGING_CONFIG_FILE,
    #     level= 'DEBUG' if args.debug else 'INFO',
    # )
    # logger.info("Start...")

    cli = Cli(args)
    cli.cli(query='')
