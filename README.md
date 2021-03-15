SMTPc
=====

[![smtpc version](https://img.shields.io/pypi/v/smtpc.svg)](https://pypi.python.org/pypi/smtpc)
[![smtpc license](https://img.shields.io/pypi/l/smtpc.svg)](https://pypi.python.org/pypi/smtpc)
[![smtpc python compatibility](https://img.shields.io/pypi/pyversions/smtpc.svg)](https://pypi.python.org/pypi/smtpc)
[![say thanks!](https://img.shields.io/badge/Say%20Thanks-!-1EAEDB.svg)](https://saythanks.io/to/marcin%40urzenia.net)

SMTPc is simple SMTP client for easy mail sending. It's purpose is to help
developers test and/or verify SMTP servers or configuration. It's also useful if you
are sending email of constant content from daemons or other crons.

If you like this tool, just [say thanks](https://saythanks.io/to/marcin%40urzenia.net).

Current stable version
----------------------

0.4.0

Features
--------

* Easily build email message as `text/plain`, `text/html` or full MIME
  message (`multipart/alternative`)
* Handles SMTP authentication, SSL and TLS
* Profiles allows you to use predefined SMTP servers
* Predefine messages set and use them for sending
* Allow for using different from/to email addresses for SMTP session and
  email headers
* Allow specifying own email headers
* Allow using particular IP address in case when your host has more then one
* It's all Python!

Installation
------------

`SMTPc` should work on any POSIX platform where [Python](http://python.org)
is available, it means Linux, MacOS/OSX etc.

Simplest way is to use Python's built-in package system:

    python3 -m pip install smtpc

You can also use [pipx](https://pipxproject.github.io/pipx/) if you don't want to
mess with system packages and install `SMTPc` in virtual environment:

    pipx install smtpc

Voila!

Python version
--------------

`SMTPc` is tested against Python 3.7+. Older Python versions may work, or may not.

How to use
----------

First, add some account you want to use for sending. In this example we are using
[Sendria](https://github.com/msztolcman/sendria) run on local environment:

```bash
smtpc profiles add sendria --host 127.0.0.1 --port 1025
```

You can verify:
```bash
smtpc profiles list
```

Now, add few messages for future use:

```bash
smtpc messages add plain --subject 'Some plain email' --body-plain 'Some plain message body' --from smtpc@example.com --to receiver@example.net
smtpc messages add html --subject 'Some html email' --body-html 'Some <b>HTML</b> message body' --from smtpc@example.com --to receiver@example.net
smtpc messages add alternative --subject 'Some alternative email' --body-plain 'Some plain message body' --body-html 'Some <b>HTML</b> message body' --from smtpc@example.com --to receiver@example.net
```

You can verify:
```bash
smtpc messages list
```

Now, send something:

```bash
smtpc send --profile sendria --message alternative
smtpc send --profile sendria --message plain --subject 'Changed subject for plain'
```
In second example above, we are using predefined message `plain`, but with changed subject.

Of course, if you don't want, you don't need to use predefined profiles and/or messages, you can pass them directly when sending:

```bash
smtpc send --host 127.0.0.1 --port 1025 --body-type html --subject 'Some html email' --body-html 'Some <b>HTML</b> message body' --from smtpc@example.com --to receiver@example.net
```

But it's not so funny :)

Authors
-------

* Marcin Sztolcman ([marcin@urzenia.net](mailto:marcin@urzenia.net))

Contact
-------

If you like or dislike this software, please do not hesitate to tell me about
this me via email ([marcin@urzenia.net](mailto:marcin@urzenia.net)).

If you find bug or have an idea to enhance this tool, please use GitHub's
[issues](https://github.com/msztolcman/smtpc/issues).

ChangeLog
---------

### v0.4.0

* BC: renamed command: `profile` -> `profiles`
* added new command: `messages` for managing of saved email messages
* allow to overwrite profile or message predefined options from CLI arguments
* cleaner and more elegant code

### v0.3.0

* using commands now instead of dozens of CLI arguments

### v0.2.0

* added profiles

### v0.1.1

* fixed --version

### v0.1.0

* very initial version
