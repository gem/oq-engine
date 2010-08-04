package org.opensha.sra.gui.portfolioeal;

import java.io.BufferedWriter;
import java.io.File;
import java.io.FileWriter;
import java.io.IOException;
import java.util.ArrayList;

import org.opensha.commons.data.Site;
import org.opensha.sha.earthquake.EqkRupForecastBaseAPI;
import org.opensha.sha.imr.ScalarIntensityMeasureRelationshipAPI;


/**
 * The representation of a site portfolio, which holds assets and represents
 * the model of the PortfolioEALCalculator.
 * @author Jeremy Leakakos
 * @see PortfolioParser
 * @see Asset
 *
 */
public class Portfolio {

	private ArrayList<Asset> assetList;
	private File portfolioFile;
	private double EAL;
	
	/**
	 * The constructor for Portfolio.  It is a private constructor, and can only be
	 * accessed through the <code>createPortfolio</code> method.
	 * 
	 * @param portfolioFile The csv file that holds the portfolio information
	 */
	private Portfolio( File portfolioFile ) {
		assetList = new ArrayList<Asset>();
		this.portfolioFile = portfolioFile;
		EAL = 0.0;
	}
	
	/**
	 * This method acts as a factory of sorts.  It is used to access the private
	 * portfolio constructor.  It calls the constructor to create a portfolio object,
	 * and then calls a method to create/set the assets based on the file set in the
	 * constructor.
	 * 
	 * @param portfolioFile The file the portfolio is based on.
	 * @return The created portfolio
	 * @throws IOException
	 */
	public static Portfolio createPortfolio( File portfolioFile ) throws IOException {
		Portfolio portfolio = new Portfolio( portfolioFile );
		portfolio.createAssets();
		return portfolio;
	}
	
	/**
	 * This method creates/sets the assets based on the portfolio file.
	 * 
	 * @throws IOException
	 */
	private void createAssets() throws IOException {
		PortfolioParser parser = new PortfolioParser();
		assetList = parser.scanFile( portfolioFile );
	}
	
	/**
	 * This computes the EAL for a portfolio.
	 * 
	 * @param imr The imr gotten from the view
	 * @param value The asset's value
	 * @param site The site that the asset is at
	 * @param erf The erf gotten from the view
	 * @param controller The controller
	 */
	public double calculatePortfolioEAL( ScalarIntensityMeasureRelationshipAPI imr, double value,
										 Site site, EqkRupForecastBaseAPI erf,
										 PortfolioEALCalculatorController controller ) {
		String toWrite = "";
		try {
			BufferedWriter out = null;
			for( Asset asset : assetList ) {
				EAL += asset.calculateEAL( imr, value, site, erf, controller );
				toWrite += asset.getParameterList().getParameter("Lat").getValue();
				toWrite += ", ";
				toWrite += asset.getParameterList().getParameter("Lon").getValue();
				toWrite += ", ";
				toWrite += asset.getAssetEAL();
				toWrite += "\n";
				out = new BufferedWriter( new FileWriter( new File("EAL.csv") ) );
			}
			out.write(toWrite, 0, toWrite.length());
			out.close();
		} catch (IOException e ) {
			e.printStackTrace();
		}
		return EAL;
	}
	
	/**
	 * Set the portofolio file for the given portfolio
	 * @param portfolioFile The portfolio file
	 */
	public void setPortfolioFile( File portfolioFile ) {
		assetList.clear();
		this.portfolioFile = portfolioFile;
		EAL = 0.0;
	}
	
	/**
	 * @return The list of assets stored in the portfolio
	 */
	public ArrayList<Asset> getAssetList() {
		return assetList;	
	}
	
	/**
	 * @return The list of sites associated with this portfolio
	 */
	public ArrayList<Site> getSiteList() {
		ArrayList<Site> siteList = new ArrayList<Site>();
		for( Asset asset : assetList ) {
			siteList.add(asset.getSite());
		}
		return siteList;
	}

	public File getPortfolioFile() {
		return portfolioFile;
	}
}
