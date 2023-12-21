(tools)=

# Add OpenQuake Tools to the OpenQuake Engine server

## Prerequisites

A working installation of the OpenQuake Engine in a Python venv. Please refer to {ref}`Development installation <development>`.


## Clone repositories

```bash

git clone https://github.com/gem/oq-platform-standalone.git
git clone https://github.com/gem/oq-platform-ipt.git
git clone https://github.com/gem/oq-platform-taxtweb.git
git clone https://github.com/gem/oq-platform-taxonomy.git

pip install -e oq-platform-standalone
pip install -e oq-platform-ipt
pip install -e oq-platform-taxtweb
PYBUILD_NAME=oq-taxonomy pip install -e oq-platform-taxonomy
```

## Start the server

```bash
oq webui start
```

***

## Getting help
If you need help or have questions/comments/feedback for us, you can subscribe to the OpenQuake users mailing list: https://groups.google.com/g/openquake-users
