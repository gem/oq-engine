MultiFaultSources
=============================

Starting from version 3.2, the OpenQuake Engine is able to manage
MultiFaultSources, which are special sources used for UCERF-like models.

Unlike regular sources, MultiFaultSources *are not self-consistent*:
they exist only in relation to a *geometryModel* which is a list of
surfaces (only *planarSurfaces* and *kiteSurfaces* are supported),
each one with an ID. MultiFaultSources are lists of nonparametric ruptures
with values mag, rake, probs_occur and IDs (called *sectionIndexes*)
taken from the geometryModel.

In order to understand MultiFaultSources, The example to study is in
the directory ``qa_tests_data/classical/case_65`` in the engine
repository. In this example the geometryModel (the file sections.xml)
contains two kiteSurfaces with IDs ``s1`` and ``s2`` respectively;
there is a single MultiFaultSource with the following content:

.. code-block:: xml

      <multiFaultSource id="1" name="Test1">
	<multiPlanesRupture probs_occur="0.8 0.2">
	  <magnitude>5.0</magnitude>
	  <sectionIndexes indexes="s1"/>
	  <rake>90</rake>
	</multiPlanesRupture>
	<multiPlanesRupture probs_occur="0.7 0.3">
	  <magnitude>6.0</magnitude>
	  <sectionIndexes indexes="s1,s2"/>
	  <rake>90</rake>
	</multiPlanesRupture>
	<multiPlanesRupture probs_occur="0.9 0.1">
	  <magnitude>5.2</magnitude>
	  <sectionIndexes indexes="s2"/>
	  <rake>90</rake>
	</multiPlanesRupture>
      </multiFaultSource>

The ``probs_occur`` must sum up to 1 and the number of probabilities must
be uniform across the MultiFaultSource; in this example there always two
``probs_occur`` for each rupture.

When the engine reads a multiFaultSource XML file, a ``MultiFaultSource``
object is instantiated. Such object cannot be used until the method
``.create_inverted_index(sections)`` is called. That is the essential
method associating the sectionIndices to the section objects. The reading
happens in three steps:

1. read and instantiate all MultiFaultSources
2. read the geometryFile and instantiate a dictionary of sections
   section_id -> surface
3. call ``src.set_sections(sections)`` for each MultiFaultSource: this
   will create an attribute .sections pointing to the sections dictionary

Only *after the .sections dictionary has been set*
it is possible to call ``.iter_ruptures`` and to instantiate the underlying
*NonParametricProbabilisticRupture* objects. Each rupture will have a
surface; if the rupture contains a single section index the
surface will be the surface in the geometryModel; if the ruptures contains
multiple section indexes the surface will be a MultiSurface built from
the corresponding surfaces in the geometryModel.

In our example the first rupture will be associated to the KiteSurface ``s1``,
the third rupture to the KiteSurface ``s2`` and the second rupture will
be associated to the MultiSurface obtained from the KiteSurfaces ``s1`` and
``s2``.
