# Installing the OpenQuake Engine on a generic Linux distribution

If the distribution provides a recent Python version (>=3.6) we recommend to use the [universal installer](universal.md).
If the distribution provides an old Python version, google for instructions about how to install a more recent Python.
For instance if you have Ubuntu Xenial you can give the commands
```
$ sudo add-apt-repository ppa:deadsnakes/ppa
$ sudo apt install python3.8
```
After that, use the universal installer:
```
$ wget https://raw.githubusercontent.com/gem/oq-engine/master/install.py
$ sudo -H python3.8 install.py server  # NB: python3.8, not just python!
```
If you do not have root permissions, install on you $HOME with
```
$ python3.8 install.py user
```
