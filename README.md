SMTPc
=====

[![smtpc version](https://img.shields.io/pypi/v/smtpc.svg)](https://pypi.python.org/pypi/smtpc)
[![smtpc license](https://img.shields.io/pypi/l/smtpc.svg)](https://pypi.python.org/pypi/smtpc)
[![smtpc python compatibility](https://img.shields.io/pypi/pyversions/smtpc.svg)](https://pypi.python.org/pypi/smtpc)
[![say thanks!](https://img.shields.io/badge/Say%20Thanks-!-1EAEDB.svg)](https://saythanks.io/to/marcin%40urzenia.net)

SMTPc is simple SMTP client for easy mail sending. It's purpose is to help
developers test and/or verify SMTP servers or configuration.

If you like this tool, just [say thanks](https://saythanks.io/to/marcin%40urzenia.net).

Current stable version
----------------------

0.3.0

Features
--------

* Easy build email message as `text/plain`, `text/html` or full MIME
  message (`multipart/alternative`)
* Handle SMTP authentication, SSL and TLS
* Profiles allows you to use predefined SMTP servers
* Allow use different from/to email addresses for SMTP session and
  email headers
* Allow specifying own headers
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

### v0.3.0

* using commands now instead of dozens of CLI arguments

### v0.2.0

* added profiles

### v0.1.1

* fixed --version

### v0.1.0

* very initial version
