Dropping support for Python 2.7
===============================

Python 3 came out nearly 10 years ago, Python 2.7 is not really supported
anymore - no bug fixes are accepted except security bugs - and it will reach
the end of line in 2020. For these reasons [several projects have
already dropped support for it](http://www.python3statement.org/).
In particular, the following projects that we rely upon have already dropped
support for Python 2.7 or they will do it shortly:

- ipython
- jupyter
- pandas
- matplotlib
- QGIS
- Django

In such a situation we are forced to drop support for Python 2 too,
unless we want to keep using old/deprecated versions of our
dependencies.  The OpenQuake Engine already supports Python 3 and has
done so for more than one year. We develop with Python 3.5 and we use it
in production since the beginning of this year.

We could drop support for Python 2 even in the next release, but in
consideration for our users we will keep supporting it until the end
of 2017 (see [our roadmap](https://github.com/gem/oq-engine/issues/2803)).
In the course of 2018, however, we will start using Python 3
features. This means that users of hazardlib and the engine will have
to upgrade to Python 3 to stay updated. This requirement only applies to
users *importing* directly Python modules. If you are using the Web
API of the engine, you will be able to keep your client in Python 2,
even if the server will require Python 3. Still, it is a good idea to
migrate. Python 2.7 is dying.
