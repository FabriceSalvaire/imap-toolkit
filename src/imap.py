####################################################################################################

import argparse
import mailbox
from pathlib import Path

from ImapTool.folder_helpers import CallbackData, folder_callback
from ImapTool.ImapClient import ImapClient, ImapClientConfig
from ImapTool.printer import byte_humanize, init_console

####################################################################################################

# logging.basicConfig(
#     format='%(asctime)s - %(levelname)s: %(message)s',
#     level=logging.DEBUG
# )

####################################################################################################

parser = argparse.ArgumentParser(
    prog='',
    description='',
    epilog='',
)
parser.add_argument(
    '--config',
    default='config.yaml'
)
parser.add_argument(
    '--imap',
    required=True,
)
parser.add_argument(
    '--capabilities',
    action='store_true',
)
parser.add_argument(
    '--quota',
    action='store_true',
)
parser.add_argument(
    '--folders',
    action='store_true',
)
parser.add_argument(
    '--folders-full-name',
    action='store_true',
)
args = parser.parse_args()

console = init_console()

config_path = Path(args.config)
# config = yaml.load(config_path.read_text(), Loader=yaml.SafeLoader)
# console.print(config)
imap_config = ImapClientConfig.from_yaml(config_path, args.imap)
client = ImapClient(imap_config)
console.print(f"Logged to [green]{imap_config.server}")

if args.capabilities:
    console.print("Server Capabilities:")
    for _ in client.capabilities:
        console.print(f"  '{_}'")

if args.quota:
    console.print()
    console.print("[yellow]Quota:")
    for quota in client.quota:
        # console.print(quota)
        percent = round(100 * quota.usage / quota.limit)
        match quota.resource:
            case 'STORAGE':
                usage = byte_humanize(quota.usage * 1024)
                limit = byte_humanize(quota.limit * 1024)
                title = 'Storage'
                console.print(f"  {title:<20} {usage} / {limit} @{percent} %")
            case 'MESSAGE':
                title = 'Number of Messages'
                console.print(f"  {title:<20} {quota.usage:_} / {quota.limit:_} @{percent} %")

if args.folders:
    console.print()
    console.print("[yellow]Folders:")
    size1 = client.size
    # print(f"Size {byte_humanize(size1)}")
    callback_data = CallbackData(console=console, size=size1, show_full_name=args.folders_full_name)
    client.inbox.depth_first_search(folder_callback, callback_data)
    size = byte_humanize(callback_data.size2)
    console.print(f"  #folders {callback_data.number_of_folders}")
    console.print(f"{' ' * 40} {callback_data.number_of_mails:>8_} {size:>8}")

folder_name = 'INBOX/Compte Site Web'
# client.select_folder(folder_name)
# email_ids = client.folder_ids()
# email_id = email_ids[0]
# _ = client.fetch(email_id)

folder = client.inbox.find(folder_name)
# email_ids = folder.ids
# email_id = email_ids[0]
# _ = folder.fetch(email_id)
# console.print(_.data)
# headers = set()
mbox = mailbox.mbox('csw.mbox')
for email_id in folder.ids('size')[:100]:
    email = folder.fetch(email_id)
    size = byte_humanize(email.size)
    console.print(f"{email_id:6} {size:>8}")
    # headers |= set(email_message.keys())
    indent = ' ' * 10
    console.print(f"{indent}{email.date}")
    console.print(f"{indent}{email.from_}")
    console.print(f"{indent}{email.subject}")
    email.structure()
    mbox.add(email.data)
# console.print(sorted(headers))

# # _ = server.fetch(email_id, '(BODY.PEEK[HEADER.FIELDS (MESSAGE-ID)])')
# console.print(_)
