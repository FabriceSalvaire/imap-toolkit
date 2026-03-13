# Mail format

- [RFC 2822 - Internet Message Format](https://datatracker.ietf.org/doc/html/rfc2822.html)
<br>

- At the most basic level, a message is a series of characters in range **US-ASCII** [1, 127].
- Messages are divided into **lines** of characters.
  A line is a series of characters that is **delimited with the two characters carriage-return and line-feed CRLF**;
  that is, the carriage return (CR) character (ASCII value 13)
  followed immediately by the line feed (LF) character (ASCII value 10).
-  A message consists of **header** fields followed, optionally, by a **body**.
   The **header is a sequence of lines** of characters with special syntax as defined in this standard.
   The **body is simply a sequence of characters** that follows the header and is **separated from the header by an empty line**.
- each line must be <= 1000
  Each line of characters MUST be no more than 998 characters,
  and SHOULD be no more than 78 characters,
  excluding the CRLF.
- Header fields are lines of the form `HEADER_NAME: HEADER_BODY\r\n`
  A field name MUST be composed of printable US-ASCII characters
  a header body can be folded or split into multi-lines by `\r\n `

# IMAP

- [RFC 9051 - Internet Message Access Protocol (IMAP) - Version 4rev2](https://datatracker.ietf.org/doc/html/rfc9051)
- [RFC 5256 - Internet Message Access Protocol - SORT and THREAD Extensions](https://datatracker.ietf.org/doc/html/rfc5256.html)
- [RFC 6154 - IMAP LIST Extension for Special-Use Mailboxes](https://datatracker.ietf.org/doc/html/rfc6154#section-5.2)
- [Internet Message Access Protocol (IMAP) Capabilities Registry](https://www.iana.org/assignments/imap-capabilities/imap-capabilities.xhtml)
<br>

- [Internet Message Access Protocol (IMAP) LIST EXTENDED Registry](https://www.iana.org/assignments/imap-list-extended/imap-list-extended.xhtml)
<br>

***Capabilities**
- 'ACL'
- 'BINARY'
- 'CATENATE'
- 'CHILDREN'
- 'CONDSTORE'
- 'CONTEXT=SEARCH'
- 'ENABLE'
- 'ESEARCH'
- 'ESORT'
- 'I18NLEVEL=1'
- 'ID'
- 'IDLE'
- 'IMAP4REV1'
- 'LIST-EXTENDED'
- 'LIST-STATUS'
- 'LITERAL+'
- 'LOGIN-REFERRALS'
- 'MOVE'
- 'MULTIAPPEND'
- 'NAMESPACE'
- 'NOTIFY'
- 'PREVIEW'
- 'PREVIEW=FUZZY'
- 'QRESYNC'
- 'QUOTA'
- 'RIGHTS=EKTX'
- 'SASL-IR'
- 'SAVEDATE'
- 'SEARCHRES'
- 'SEARCH=X-MIMEPART'
- 'SNIPPET=FUZZY'
- 'SORT'
- 'SORT=DISPLAY'
- 'SPECIAL-USE'
- 'STATUS=SIZE'
- 'THREAD=ORDEREDSUBJECT'
- 'THREAD=REFERENCES'
- 'THREAD=REFS'
- 'UIDPLUS'
- 'UNSELECT'
- 'URL-PARTIAL'
- 'WITHIN'
- 'XDOVECOT'
- 'XLIST'
