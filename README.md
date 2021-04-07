SMTPc
=====

[![smtpc version](https://img.shields.io/pypi/v/smtpc.svg)](https://pypi.python.org/pypi/smtpc)
[![smtpc license](https://img.shields.io/pypi/l/smtpc.svg)](https://pypi.python.org/pypi/smtpc)
[![smtpc python compatibility](https://img.shields.io/pypi/pyversions/smtpc.svg)](https://pypi.python.org/pypi/smtpc)
[![Downloads](https://static.pepy.tech/personalized-badge/smtpc?period=total&units=international_system&left_color=grey&right_color=yellow&left_text=Downloads)](https://pepy.tech/project/smtpc)
[![say thanks!](https://img.shields.io/badge/Say%20Thanks-!-1EAEDB.svg)](https://saythanks.io/to/marcin%40urzenia.net)

`SMTPc` is a simple SMTP client for easy mail sending using CLI. It's dedicated
for developers, however it's easy to use and every CLI user will be satisfied
using this.

The main purpose of `SMTPc` is to help developers test and/or verify SMTP servers or
their SMTP configuration. Of course, it can be used in every place you want
to automate any system, and use predefined messages (with templates) for
notifications, like daemons or crons.

If you like this tool, just [say thanks](https://saythanks.io/to/marcin%40urzenia.net).

Current stable version
----------------------

0.9.1

Features
--------

* Predefined profiles for use with many SMTP servers
* Predefined messages for sending messages just by referencing the message name
* Automatically build message from given parameters, do not glue headers manually
* Store passwords in an encrypted form (optionally)
* Ability to edit raw message body just before sending
* Templating system customizing messages (with Jinja2)
* Clean and readable SMTP session logs (if enabled). Especially with
  [colorama](https://pypi.org/project/colorama/) module (available by default in
  `smtpc[extended]` version)!
* SSL and TLS connections, of course
* You can easily spoof your own messages, by specifying other sender/recipient in
  message headers, and other one for SMTP session
* Easily add custom email headers
* If you have multiple IP addresses available, choose which one you want to use
* It's all Python!

Installation
------------

`SMTPc` should work on any POSIX platform where [Python](http://python.org)
is available. This includes Linux, macOS/OSX etc.

The simplest way is to use Python's built-in package system:

    python3 -m pip install 'smtpc[extended]'

It will install `SMTPc` and related packages for the best user experience. If you want
to install the basic version without additions (colors, extended Jinja2 templates),
then start with:

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

First, add the account that you want to use for sending. In this example we are using
[Sendria](https://github.com/msztolcman/sendria), which runs on our local environment:

```bash
smtpc profiles add sendria --host 127.0.0.1 --port 1025
```

You can verify that the profile is stored:

```bash
smtpc profiles list
```

Now, add a few messages for future use:

```bash
smtpc messages add plain --subject 'Some plain email' --body 'Some plain message body' --from plain@smtpc.net --to receiver@smtpc.net
smtpc messages add html --subject 'Some html email' --body 'Some <b>HTML</b> message body' --body-type=html --from html@smtpc.net --to receiver@smtpc.net
smtpc messages add alternative --subject 'Some alternative email' --body 'Some plain message body' --body-html 'Some <b>HTML</b> message body' --from alternative@smtpc.net --to receiver@smtpc.net
```

You can verify that your messages are stored:

```bash
smtpc messages list
```

Now, lets send some emails:

```bash
smtpc send --profile sendria --message alternative
smtpc send --profile sendria --message plain --subject 'Changed subject for plain'
```
In the second example above, we are using a predefined message named `plain`, but with a changed subject.

You don't need to use any predefined profiles or messages. You can just pass them directly when sending:

```bash
smtpc send --host 127.0.0.1 --port 1025 --body-type html --subject 'Some html email' --body-html 'Some <b>HTML</b> message body' --from not-funny@smtpc.net --to receiver@smtpc.net
```

But it's not where the fun is :)

You can also use your predefined messages as templates:

```bash
smtpc messages add template-test --subject 'Some templated email: {{ date }}' --body 'Some templated email body: {{ uuid }}' --from templated@smtpc.net --to receiver@smtpc.net
smtpc send --profile sendria --message template-test --template-field "date=$(date)" --template-field "uuid=$(uuidgen)"
```

So when the email is received, the subject will look like this:

```
Some templated email: Thu Mar 18 19:05:53 CET 2021
```

and the body will look like this:

```
Some templated email body: C21B7FF0-C6BC-47C9-B3AC-5554865487E4
```

If [Jinja2](https://jinja.palletsprojects.com) module is available,
you can use it as a templating engine!
See more in [Templating chapter](#Templating).

Templating
----------

Templating can be done in both simple and extended forms. In the simplest case, when
[Jinja2](https://jinja.palletsprojects.com) module is not found, `SMTPc` can only
substitute simple placeholders with data.

For example, if you specify the subject as:

```
--subject "Now we have {{ date }}"
```

and when sending you provide a value:

```
--template-field "date=$(date +"%Y-%m-%dT%H:%M:%S%Z")"
```

then in the final email it will look like:

```
Now we have 2021-03-19T10:56:31CET
```

But if you want to add conditions, loops or any other more complex syntax, you will need
to install [Jinja2](https://jinja.palletsprojects.com) module (more: [Installation](#Installation)).

You willl then have the full power of one of best templating engines Python has. Here's an example:

```bash
smtpc messages add template-test --subject 'Some of my projects, state on {{ date }}' --from templated@smtpc.net --to receiver@smtpc.net --body-html '<p>Here I am!</p>
{% if projects %}
<p>Some of my projects:</p>
<ul>
{% for project in projects %}
    <li><a href="https://github.com/msztolcman/{{ project }}">{{ project }}</a></li>
{% endfor %}
</ul>
{% else %}
<p>I have no projects to show :(</p>
{% endif %}
<p>That&#39;s all folks!</p>'
smtpc send --profile sendria --message template-test --template-field "date=$(date -u +'%Y-%m-%dT%H:%M:%S%Z')" --template-field-json='projects=["sendria", "smtpc", "versionner", "ff"]'
```

So when the email is received, the subject will look like this:

```
Some of my projects, state on 2021-03-19T10:03:56UTC
```

and the body (slightly reformatted here):

```html
<p>Here I am!</p>
<p>Some of my projects:</p>
<ul>
    <li><a href="https://github.com/msztolcman/sendria">sendria</a></li>
    <li><a href="https://github.com/msztolcman/smtpc">smtpc</a></li>
    <li><a href="https://github.com/msztolcman/versionner">versionner</a></li>
    <li><a href="https://github.com/msztolcman/ff">ff</a></li>
</ul>
<p>That&#39;s all folks!</p>
```

There are also available fields from message configuration (like `subject` or `address_to`).
These fields (full list below) are the final values (calculated from `CLI` params to `SMTPc` and
predefined message configuration). All of them are prefixed with `smtpc_`. This allows for
much better customization of emails.

Available predefined fields:
- `smtpc_subject` - analogous to `--subject`
- `smtpc_envelope_from` - analogous to `--envelope-from`
- `smtpc_from` - analogous to `--from`
- `smtpc_envelope_to` - analogous to `--envelope-to`
- `smtpc_to` - analogous to `--to`
- `smtpc_cc` - analogous to `--cc`
- `smtpc_bcc` - analogous to `--bcc`
- `smtpc_reply_to` - analogous to `--reply-to`
- `smtpc_body_type` - analogous to `--body-type`, but it's the final content-type of message
- `smtpc_raw_body` - True if `--raw-body` was used, and False if not
- `smtpc_predefined_profile` - almost all informations from profile, if specified (see: `--profile`)
- `smtpc_predefined_message` - almost all informations from message, if specified (see: `--message`)

You can read more about Jinja2 capabilities on [Jinja2 homepage](https://jinja.palletsprojects.com).

Authors
-------

* Marcin Sztolcman ([marcin@urzenia.net](mailto:marcin@urzenia.net))

Contact
-------

If you like or dislike this software, please do not hesitate to tell me about
it via email ([marcin@urzenia.net](mailto:marcin@urzenia.net)).

If you find a bug or have an idea to enhance this tool, please use GitHub's
[issues](https://github.com/msztolcman/smtpc/issues).

ChangeLog
---------

### v0.9.1

* minor bugfixes

### v.0.9.0

* changed way of building message body
* added template fields from message configuration to templates, with prefix `smtpc_`
* default subcommand for commands `profiles` and `messages` is `list` now (calling without
  subcommand will display list of profiles/messages instead of help)
* allow reading message body from STDIN if no `--body` or `--body=-` is used
* improved handling rejects from SMTP server
* added short aliases for main commands: `p` - for `profiles`, `s` for `send`, `m` for `messages`
* huge improvements for debug messages
* allow for missing from/envelope_from, to/cc/bcc/envelope_to when
  adding new predefined message
* new e2e tests: sending messages


### v0.8.1

* fix error related to Content-Type (fixes #2 - thanks for [tuxfamily](https://github.com/tuxfamily) for reporting)
* fixed grammar and informations in README (thanks to [slawekp](https://github.com/slawekp) for PR)
* many minor changes reported by linters

### v0.8.0

* `send` and `profiles` commands: ask for password if `--password` param
  was used with no argument
* when adding a new profile, you can choose to encrypt your password. In this
  case you will be asked for encryption key. The same key must be used to
  decrypt password when sending.
* added many e2e tests

### v0.7.0

* added `--message-interactive` param for `send` command. Allows editing of
  raw message body just before sending
* changed url in `User-Agent` header and when `--version` is called to `smtpc.net`
* many internal fixes and rewrites, added few new tests

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

* fixed handling `--ssl` and `--tls` when sending message using profile
* added simple `--dry-run` option
* added `--reply-to` option
* minor fixes to error handling
* added `User-Agent` header to generated messages

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

* fixed `--version`

### v0.1.0

* very initial version
