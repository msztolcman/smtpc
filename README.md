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

0.6.0

Features
--------

* Easily build email message as `text/plain`, `text/html` or full MIME
  message (`multipart/alternative`)
* Messages can be a templates with values replaced when sending
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

If you want to install Jinja2 modules together for using extended templating features,
install it like:

    python3 -m pip install smtpc[extended]

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
smtpc messages add plain --subject 'Some plain email' --body-plain 'Some plain message body' --from plain@smtpc.net --to receiver@smtpc.net
smtpc messages add html --subject 'Some html email' --body-html 'Some <b>HTML</b> message body' --from html@smtpc.net --to receiver@smtpc.net
smtpc messages add alternative --subject 'Some alternative email' --body-plain 'Some plain message body' --body-html 'Some <b>HTML</b> message body' --from alternative@smtpc.net --to receiver@smtpc.net
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
smtpc send --host 127.0.0.1 --port 1025 --body-type html --subject 'Some html email' --body-html 'Some <b>HTML</b> message body' --from not-funny@smtpc.net --to receiver@smtpc.net
```

But it's not so funny :)

Also you can use your predefined messages as templates:

```bash
smtpc messages add template-test --subject 'Some templated email: {{ date }}' --body-plain 'Some templated email body: {{ uuid }}' --from templated@smtpc.net --to receiver@smtpc.net
smtpc send --profile sendria --message template-test --template-field "date=$(date)" --template-field "uuid=$(uuidgen)"
```

And received email subject may looks like:

```
Some templated email: Thu Mar 18 19:05:53 CET 2021
```

And the body:

```
Some templated email body: C21B7FF0-C6BC-47C9-B3AC-5554865487E4
```

If there is also available [Jinja2](https://jinja.palletsprojects.com) module,
you can also use it as templating engine!

Templating
----------

Both, Subject and email body can also be used as a templates. By default, if
no `--template-field` or `--template-field-json` is specified, then no
templating engine is used.

If you will specify any template field, then SMTPc is looking for template engine.
By default, SMTPc try to use [Jinja2](https://jinja.palletsprojects.com)
templating system. If this module is not found, then simpler, builtin version is
used. This simplified engine can just find simple placeholder in format:

    {{ fieldName }}

and replace then with specified data.

Using this simplified engine, `fieldName` can contain only small and big ASCII letters,
digits and underscore sign. Placeholders are substituted by values, and this is all
this engine can do :)

However, if there is [Jinja2](https://jinja.palletsprojects.com) found, the possibilities
of templating are almost endless. For loop, blocks, conditions... Please read more at
[Jinja2 home](https://jinja.palletsprojects.com).

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

### v0.6.0

* added `--template-field` and `--template-field-json` params for `send` command,
  allows to replace some `{{ fields }}` in email body or subject with specified
  values. Or you can also use [Jinja2](https://jinja.palletsprojects.com) if
  module is installed

### v0.5.0

* safe writing config files: will show file content if writing will fail
* messages list is simplified by default (just message name like in profiles list)
* new commands: `smtpc profiles delete`, `smtpc messages delete` - self explanatory I guess :)
* few minor bugs squashed
* few internal changes and improvements

### v0.4.1

* fixed handling --ssl and --tls when sending message using profile
* added simple --dry-run option
* added --reply-to option
* minor fixes to error handling
* added User-Agent header to generated messages

### v0.4.0

* BC: renamed command: `profile` -> `profiles`
* added new command: `messages` for managing of saved email messages
* allow overwriting profile or message predefined options from CLI arguments
* cleaner and more elegant code

### v0.3.0

* using commands now instead of dozens of CLI arguments

### v0.2.0

* added profiles

### v0.1.1

* fixed --version

### v0.1.0

* very initial version
