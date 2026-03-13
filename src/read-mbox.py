from pathlib import Path

path = '/home/fabrice/.thunderbird/5j9ynvbk.default/ImapMail/ssl0.ovh.net/'
path = Path(path)

# path = path / 'Nvidia-1'
# path = path / 'Salons'

path = path / 'Electrolab.sbd/Core'
# number of lines: 85_061_291
# number of mails: 16_656
# mail size max: 33.0 MB
# mbox size: 6131.3 MB

line_count = 0
mail_count = 0
mbox_size = 0
mail_size = 0
mail_size_max = 0
was_part = False
with open(path, 'rb') as fh:
    for line in fh:
        line_count += 1
        _ = len(line)
        mbox_size += _
        mail_size += _
        # if line == b'From \r\n':
        # if len(line) > 2 and line[:2] == b'--':
        #     print(line)
        # if was_part:
        #     print(line)
        if len(line) > 5 and line[:5] == b'From ':
            # print(line)
            if line_count == 1 or was_part:
                mail_count += 1
                print(f"{mail_count} {line}")
                mail_size_max = max(mail_size, mail_size_max)
                mail_size = 0
                was_part = False
        else:
            if len(line) > 4 and line[:2] == b'--' and line[-4:] == b'--\r\n':
                was_part = True
            elif len(line) > 2:
                was_part = False
            if len(line) > 6 and line[:6] == b'Date: ':
                print(f"    {line}")
            if len(line) > 9 and line[:9] == b'Subject: ':
                print(f"    {line}")
        # if was_part:
        #     print(f"    {line}")
mail_size_max = max(mail_size, mail_size_max)

mail_size_max /= 1024**2
mbox_size /= 1024**2

print(f"number of lines: {line_count:_}")
print(f"number of mails: {mail_count:_}")
print(f"mail size max: {mail_size_max:.1f} MB")
print(f"mbox size: {mbox_size:.1f} MB")
