# Add OpenQuake Tools to the OpenQuake Engine server

_DRAFT_

## Prerequisites

A working installation of the OpenQuake Engine in a **Python 2.7** venv. Please refer to [Development installation](development.md).


## Clone repositories

```bash

git clone https://github.com/gem/oq-platform-standalone.git
git clone https://github.com/gem/oq-platform-ipt.git
git clone https://github.com/gem/oq-platform-taxtweb.git
git clone https://github.com/gem/oq-platform-taxonomy.git

pip install -e oq-platform-standalone
pip install -e oq-platform-ipt
pip install -e oq-platform-taxtweb
pip install -e oq-platform-taxonomy
```

## Start the server

```bash
oq webui start
```

***

## Getting help
If you need help or have questions/comments/feedback for us, you can:
  * Subscribe to the OpenQuake users mailing list: https://groups.google.com/forum/?fromgroups#!forum/openquake-users
  * Contact us on IRC: irc.freenode.net, channel #openquake
