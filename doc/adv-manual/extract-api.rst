Extracting data from calculations
=================================

The engine has a relatively large set of predefined outputs, that you can
get in various formats, like CSV, XML or HDF5. They are all documented
in the manual and they are the recommended way of interacting with the
engine, if you are not tech-savvy.

However, sometimes you must be tech-savvy: for instance if you want to
post-process hundreds of GB of ground motion fields produced by an event
based calculation, you should NOT use the CSV output, if you care about
efficiency. There is instead an Extractor API which is meant to manage
this case (huge amounts of data) as well as the case of data lacking a
predefined exporter.

There are actually two different kind of extractors: the simple Extractor,
which is meant to manage large data (say > 100 MB) and the WebExtractor,
which is able to interact with the WebAPI and to extract data from a
remote machine. The WebExtractor is nice,
but cannot be used for large amount of data for various reasons; in
particular, unless your Internet connection is ultra-fast, downloading GBs
of data will probably send the web request in timeout, causing it to fail.
Even if there is no timeout, the WebAPI will block, everything will be slow,
the memory occupation and disk space will go up, and at certain moment
something will fail.

The WebExtractor is meant for small to medium
outputs, things like the mean hazard maps (for instance an hazard map
containing 100,000 points and 3 PoEs requires only 1.1 MB of data
at 4 bytes per point). Mean hazard curves or mean
average losses in risk calculation are still small enough for the
WebExtractor. But if you want to extract all the realizations you
must go with the simple Extractor and your postprocessing script must
be run in the remote machine, since it requires direct access to the
datastore.

Here is an example of usage of the `Extractor` to retrieve mean hazard curves:

>>> from openquake.calculators.extract import Extractor
>>> calc_id = 42  # for example
>>> extractor = Extractor(calc_id)
>>> obj = extractor.get('hcurves/mean/PGA')  # returns an ArrayWrapper object
>>> obj.array.shape  # an example with 10,000 sites and 20 levels per PGA
(10000, 20)
>>> extractor.close()

Here is an example of using the `WebExtractor`,
assuming you have a calculation with number 42
available in a remote machine where there is a WebAPI server running, a.k.a/
the Engine Server. The first thing to is to set up the credentials to
access the WebAPI. There are two cases:

1. you have a production installation of the engine in /opt
2. you have a development installation of the engine in a virtualenv

In both case you need to create a file called ``openquake.cfg`` with the
following format::
  
  [webapi]
  server = http(s)://the-url-of-the-server(:port)
  username = my-username
  password = my-password

``username`` and ``password`` can be left empty is the authentication is
not enabled in the server, which is the recommended way, if the
server is in your own secure LAN. Otherwise you must set them to the
right credentials. The difference between case 1 and case 2 is in
where to put the ``openquake.cfg`` file: if you have a production
installation put it in your $HOME, if you have a development
installation put it in your virtualenv directory.

The usage then is the same as the regular extractor; here is how to extract
the hazard maps:

>>> from openquake.calculators.extract import WebExtractor
>>> extractor = WebExtractor(calc_id)
>>> obj = extractor.get('hmaps/mean/PGA')  # returns an ArrayWrapper object
>>> obj.array.shape  # an example with 10,000 sites and 4 PoEs
(10000, 4)
>>> extractor.close()

If you do not want to put your credentials in the ``openquake.cfg`` file,
you can do so, but then you need to pass them explictly to the WebExtractor:

>>> extractor = WebExtractor(calc_id, server, username, password)
