[pytest]
markers =
  slow: a slow test
addopts = --tb short
consider_namespace_packages = true
DJANGO_SETTINGS_MODULE = openquake.server.settings
