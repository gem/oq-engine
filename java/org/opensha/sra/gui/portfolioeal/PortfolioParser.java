package org.opensha.sra.gui.portfolioeal;

import java.io.File;
import java.io.FileNotFoundException;
import java.util.ArrayList;
import java.util.Scanner;
import java.util.StringTokenizer;

/**
 * This class parses a well-formatted portfolio file and turns it in to Asset objects.
 * These Assets in turn are used by the PortfolioEALCalculatorController to make EAL
 * calculations.  A standard portfolio file should be a csv file.  Each value may also
 * have one set of quotations, to allow for slightly different formats.
 * 
 * @author Jeremy Leakakos
 * @see Asset
 * @see Portfolio
 */
public class PortfolioParser {
	
	/**
	 * The default constructor for the class.
	 */
	public PortfolioParser() { }

	
	/**
	 * This method scans and parses the file in the portfolio.  It breaks the file up
	 * by line, with each line being a separate <code>Asset</code>.  The first line 
	 * defines the parameters that will be stored in each asset.  The 
	 * <code>Clone()</code> method defined in <code>Asset</code> is used to allow for
	 * easy creation of assets with arbitrary parameters.
	 */
	public ArrayList<Asset> scanFile( File portfolioFile ) throws NumberFormatException {
		Scanner fileScanner = null;
		try {
			fileScanner = new Scanner( portfolioFile );
		} catch( FileNotFoundException exception) {
			exception.printStackTrace();
			System.err.println( exception.getMessage() );
		}
		boolean firstLine = true;
		ArrayList<Asset> assetList = new ArrayList<Asset>();
		Asset baseAsset = null;
		while( fileScanner.hasNextLine() ) {
			String assetLine = fileScanner.nextLine();
			Asset asset = null;
			if( !firstLine ) {
				// Clone the default asset, then set the parameters to what is
				// in the current line
				try {
					asset = (Asset) baseAsset.clone();
				} catch (CloneNotSupportedException e) {
					e.printStackTrace();
				}

				// Parse the current line and set the parameters in the asset to it
				ArrayList<String> assetArrayList = parseLine( assetLine );
				String[] assetValueList = new String[assetArrayList.size()];
				assetValueList = assetArrayList.toArray( assetValueList );
				if( assetValueList.length > 0 ) {
					asset.setAssetParameters( assetValueList );
					assetList.add( asset );
				}
			}
			else {
				// Create the default asset with all parameters set to null
				baseAsset = new Asset( assetLine );
				firstLine = false;
			}
		}
		return assetList;
	}
	
	/**
	 * Parse an asset line from a portfolio file.  Using a StringTokenizer, parse the
	 * line using commas as delimiters, until a double quote is found.  After a double
	 * quote, ignore commas until another double quote has been found.  After the second
	 * double quote, continute using commas as delimiters.
	 * 
	 * @param assetLine A string representing all of the values of the parameters in an
	 * asset.
	 * @return An ArrayList 
	 */
	private ArrayList<String> parseLine( String assetLine ) {
		StringTokenizer tokenizer = new StringTokenizer(assetLine);
		ArrayList<String> assetArrayList = new ArrayList<String>();
		while( tokenizer.hasMoreTokens() ) {
			String token = tokenizer.nextToken(",");
			if( token.startsWith("\"") && !token.endsWith("\"")) {
				while( !token.endsWith("\"")) token += tokenizer.nextToken(); 
				token.substring(1, token.length() - 1);
			}
			assetArrayList.add(token);
		}
		return assetArrayList;
	}
}
