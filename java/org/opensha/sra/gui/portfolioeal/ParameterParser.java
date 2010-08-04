package org.opensha.sra.gui.portfolioeal;

/**
 * This class is used to parse the parameters from a csv portfolio file.  If you wish
 * to use different parameters than what are already supported, all you have to do is
 * add the string name of the parameter to the appropriate enum.  If you wish to add a
 * new parameter type, you need to create a new enum type, and follow the template of
 * the other array creations.  This should be changed in the future to allow for easier
 * code updating.  The enum values correspond to the type of parameter that should be
 * created.  This class is a singleton, so that the creation of the arrays only has to
 * occur once, which could end up being a lengthy process with many enum values.
 * 
 * @author Jeremy Leakakos
 *
 */
public class ParameterParser {
	
	// StringParameters
	private enum StringParam  { AssetGroupName, SiteName, Soil, AssetName,
								VulnModel, WindExp }

	// DoubleParameters; In the context of the portfolio, floats are counted as doubles
	private enum DoubleParam  { BaseHt, Ded, LimitLiab, Share, ValHi, ValLo,
								Value, Vs30, Lat, Lon, Elev }

	// IntegerParameters
	private enum IntegerParam { AssetID, ValYr }
	
	private String[] doubleStringArray;
	private String[] stringStringArray;
	private String[] integerStringArray;
	private static ParameterParser parameterParser = null;
	
	/**
	 * The constructor for the class.  It creates arrays from each of the enums, and
	 * then creates corresponding arrays of the same length.  It turns the values of the
	 * enums into strings, in the same order that they come in in the enums.  If you
	 * wish to add a new parameter type, you need to add a new enum to the class.  Then,
	 * you should add new two new arrays, one for the enum values, and one for the
	 * string representation of the given values, each with the same length.  Then you
	 * need to add a new for loop that adds the string representations of each of the
	 * enum's values into the string representation array. The constructor is private
	 * because it is part of the singleton definition.  You get  an instance of this
	 * class by calling <code>getParameterType( String paramName )</code>.
	 */
	private ParameterParser() {
		// Declare, initialize, and create arrays with the actual values of the enums
		DoubleParam[] doubleArray = DoubleParam.values();
		StringParam[] stringArray = StringParam.values();
		IntegerParam[] integerArray = IntegerParam.values();

		// Initialize the arrays that will store the string representations of the enums
		doubleStringArray = new String[DoubleParam.values().length];
		stringStringArray = new String[StringParam.values().length];
		integerStringArray = new String[IntegerParam.values().length];
		
		// Loop over the actual value arrays, and put their string representation into
		// the string arrays.
		// DoubleParam
		for( int i = 0; i < doubleArray.length; i++ ) {
			doubleStringArray[i] = doubleArray[i].toString();
		}
		// StringParam
		for( int i = 0; i < stringArray.length; i++ ) {
			stringStringArray[i] = stringArray[i].toString();
		}
		// IntegerParam
		for( int i = 0; i < integerArray.length; i++ ) {
			integerStringArray[i] = integerArray[i].toString();
		}
	}
	
	/**
	 * This method looks through the arrays created from the enum values, and tries to
	 * match the paramName to it.  If a match occurs, it returns the appropriate
	 * parameter type as a string.  It goes through each array created at initialization
	 * time, from the longest to the shortest.  If you add a new parameter type, you
	 * need to add a new for loop in the code.  It should iterate over the new string
	 * representation array created in the constructor, and return the proper string
	 * name of the new parameter.  It is recommended to put the parameter type that will
	 * be used the most first, as it is more likely to be used, and the method will
	 * return sooner.
	 * @param paramName The name of the parameter to find the type of.
	 * @return The parameter type.  This will be the string name of the parameter, or
	 * null.  The string name will be used to dynamically create a parameter object.
	 */
	public String getParameterType( String paramName ) {
		for( String type : doubleStringArray ) {
			if( paramName.equals(type)) return "DoubleParameter";
		}
		for( String type : stringStringArray ) {
			if( paramName.equals(type)) return "StringParameter";
		}
		for( String type : integerStringArray ) {
			if( paramName.equals(type)) return "IntegerParameter";
		}
		return null;
	}
	
	/**
	 * The singleton method.  This returns the single instance of ParameterParser, or
	 * if it is null, creates a new one.
	 * @return The singleton instance of ParameterParser
	 */
	public static ParameterParser getParameterParser() {
		if( parameterParser == null ) parameterParser = new ParameterParser();
		return parameterParser;
	}
}
