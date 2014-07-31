Information for developers
===================================


Conventions
-----------------------

The PEP8 conventions for Python variables are used.
The abbreviation `lt` usually refers to logic trees.
As a prefix it is used for Django objects, for instance
`lt_rlz` is an instance of the class `LtRealization`
and `lt_model` is an instance of the class `LtSourceModel`.
A suffix is used for non-Django objects: for instance `gsim_lt`
is an instance of the class `GsimLogicTree`; the suffix is
also used in the logic tree files, for instance in the QA
tests we have files named `haz_map_gsim_lt.xml`.
