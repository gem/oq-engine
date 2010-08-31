from lxml import etree

def function_at(functions, index):
	"""Binds a single <VulnerabilityFunction/> tag into an instance of the VulnerabilityFunction class."""

	function_as_xml = functions[index]
	function = VulnerabilityFunction(function_as_xml.attrib['ID'], function_as_xml.attrib['IntensityMeasureType'], function_as_xml.attrib['ProbabilisticDistribution'])
	
	# parse and set intensity measure values
	intensity_measure_values = function_as_xml[0]
	function.intensity_measure_values = [float(value) for value in intensity_measure_values.text.strip().split(' ')]

    # parse and set loss ratio values
	loss_ratio_values = function_as_xml[1]
	function.loss_ratio_values = [float(value) for value in loss_ratio_values.text.strip().split(' ')]
	
	# parse and set coefficient of variation values
	coefficient_variation_values = function_as_xml[2]
	function.coefficient_variation_values = [float(value) for value in coefficient_variation_values.text.strip().split(' ')]

	return function

def asset_at(assets, index):
	"""Binds a single <AssetInstance/> tag into an instance of the AssetInstance class."""
	
	asset_as_xml = assets[index]
	return AssetInstance(asset_as_xml.attrib['AssetID'],asset_as_xml.attrib['AssetDescription'],asset_as_xml.attrib['AssetValue'],asset_as_xml.attrib['VulnerabilityFunction'],asset_as_xml.attrib['Latitude'], asset_as_xml.attrib['Longitude'])

class VulnerabilityFunction(object):
	"""Represents a vulnerability function."""

	def __init__(self, id, imt, distribution):
		self.id = id
		self.imt = imt
		self.distribution = distribution

		self.intensity_measure_values = []
		self.loss_ratio_values = []
		self.coefficient_variation_values = []
		
class AssetInstance(object):
	"""Represents a vulnerability function."""

	def __init__(self, AssetID, AssetDescription, AssetValue, VulnerabilityFunction, Latitude, Longitude,):
		self.Latitude = Latitude
		self.Longitude = Longitude
		self.VulnerabilityFunction = VulnerabilityFunction
		self.AssetValue = AssetValue
		self.AssetDescription = AssetDescription
		self.AssetID = AssetID

if __name__ == '__main__':
	assets = etree.parse('Portfolio_Assets.xml').getroot()
	functions = etree.parse('functions_Pager.xml').getroot()
	function = function_at(functions, 0)
	
	
	# function that loops and collects all the vulnerability functions...
	for function in functions:
	    print function.attrib['ID'], function.attrib['IntensityMeasureType'], function.attrib['ProbabilisticDistribution'],  function[0].text, function[1].text, function[2].text
	
	
	# ...and all the assets
	for asset in assets:
	    print asset.attrib['AssetID'], asset.attrib['AssetDescription'], asset.attrib['AssetValue'], asset.attrib['VulnerabilityFunction'], asset.attrib['Latitude'], asset.attrib['Longitude']

