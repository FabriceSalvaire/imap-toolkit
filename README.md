This repository contains an IMAP toolkit written in Python.

I wrote this code to help me manage my mailboxes which were approaching the quota limit.

It was also the opportunity to discover that:
- Thunderbird is not well maintained
  - `mbox` can often be corrupted (got a size x 3 and lost several GB of space disk)
  - `.msf` mail index format is hell
- mail rely on quite old standards
- mbox format doesn't have an index
- mails use a lot of disk space due to encoding, headers, text and HTML parts...
- mail encoding is quite inefficient (e.g. for French)
- mails can have many custom headers
- mbox is not compressed
- IMAP servers behave differently

This toolkit is based on these packages (PSL means Python standard library):
- [imapclient](https://github.com/mjs/imapclient) to handle the IMAP protocol
  Notice that the [PSL imaplib](https://docs.python.org/3/library/imaplib.html) is too low level !
  imaplib lacks also a debugging log to trace the IMAP protocol.
- [PSL mailbox](https://docs.python.org/3/library/mailbox.html)
- [PSL email](https://docs.python.org/3/library/email.html)
- [prompt-toolkit](https://github.com/prompt-toolkit/python-prompt-toolkit) for the CLI

# Relevant RFC

- [RFC 2822 - Internet Message Format](https://datatracker.ietf.org/doc/html/rfc2822.html)
<br>

- [RFC 9051 - Internet Message Access Protocol (IMAP) - Version 4rev2](https://datatracker.ietf.org/doc/html/rfc9051)
- [Internet Message Access Protocol (IMAP) Capabilities Registry](https://www.iana.org/assignments/imap-capabilities/imap-capabilities.xhtml)
- [RFC 5256 - Internet Message Access Protocol - SORT and THREAD Extensions](https://datatracker.ietf.org/doc/html/rfc5256.html)
- [RFC 6154 - IMAP LIST Extension for Special-Use Mailboxes](https://datatracker.ietf.org/doc/html/rfc6154#section-5.2)

# Related projects

- [Thunderbird](https://www.thunderbird.net)
- [Betterbird](https://www.betterbird.eu)
  "Betterbird is a fine-tuned version of Mozilla Thunderbird"
- [thunderbird/import-export-tools-ng](https://github.com/thunderbird/import-export-tools-ng)
  Import Export Tools that supports Thunderbird v68-v128
<br>

- [lefcha/imapfilter](https://github.com/lefcha/imapfilter)
  IMAP mail filtering utility written in LUA
<br>

- [rcarmo/imapbackup](https://github.com/rcarmo/imapbackup)
  A Python script for incremental backups of IMAP mailboxes
