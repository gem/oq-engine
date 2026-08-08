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
