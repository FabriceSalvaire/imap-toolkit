This repository contains an IMAP toolkit written in Python.

I wrote this code to help me manage my mailboxes which were approaching the quota limit.

It was also the opportunity to discover that:
- Thunderbird `mbox` can often be corrupted (got a size x 3)
- Thunderbird `.msf` mail index format is hell
- mail rely on quite old standards
- mbox format doesn't have an index
- mailboxes are not compressed
- mails use a lot of disk space due to encoding, headers, text and html parts...
- mail encoding is quite inefficient (e.g. for French)
- mails can have many custom headers
- IMAP servers behave differently

It is based on these packages (PSL means Python standard library):
- [imapclient](https://github.com/mjs/imapclient) to handle the IMAP protocol
  Notice that the [PSL imaplib](https://docs.python.org/3/library/imaplib.html) is too low level !
- [PSL mailbox](https://docs.python.org/3/library/mailbox.html)
- [PSL email](https://docs.python.org/3/library/email.html)
- [prompt-toolkit](https://github.com/prompt-toolkit/python-prompt-toolkit) for the CLI
