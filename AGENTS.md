# code-style

Follow PEP8 with a hard-limit of 79 characters for line-length
and of 79 lines for function-length (not counting the docstring).
When refactoring, prefer middle-size functions (i.e. dozen of lines,
not too short). Do not strip comments away. Prefer the use of numpy
when possible.

# tips

The openquake/calculators tests are meant to be run with OQ_DISTRIBUTE=no and
pytest -n auto, having activated the ~/openquake venv if necessary.
After a refactoring run `ruff check` and make sure it does not fail.
Install ruff in the ~/openquake venv if necessary. It is also useful
to install pyqt5, qtawesome, PyOpenGL and silx to view HDF5 files.

The performance of a system can be assessed with the command
`oq engine --run https://downloads.openquake.org/jobs/performance.zip`.
On a laptop with an Intel Ultra/Ryzen 7 (or a modern Mac)
it should take less than 10 minutes.
