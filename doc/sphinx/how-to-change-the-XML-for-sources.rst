Change the XML representation of a hazard source
================================================

Each hazardlib source has an XML representation and there are utilities
to convert from and to XML. Here is what you need to do if you want to
change the XML representation of a source, the typical use case being
adding new attributes.

1. decide the new format and update the file
   nrml_examples/source_model/mixed.xml
2. decide the new validations needed and update the modules valid.py, nrml.py
   and sourceconverter.py accordingly
3. run source_test.py and fight until all tests pass
4. update sourcewriter.py and make sure all the tests in
   sourcewriter_test.py pass, up to reformatting of the XML
5. if needed, add new tests, especially for tricky validations
