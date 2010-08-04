package org.opensha.sra.gui.portfolioeal;

import java.lang.reflect.Constructor;
import java.rmi.RemoteException;
import java.util.ArrayList;
import java.util.ListIterator;

import javax.swing.JOptionPane;

import org.opensha.commons.data.Site;
import org.opensha.commons.data.function.ArbitrarilyDiscretizedFunc;
import org.opensha.commons.data.function.DiscretizedFuncAPI;
import org.opensha.commons.exceptions.ParameterException;
import org.opensha.commons.geo.Location;
import org.opensha.commons.param.Parameter;
import org.opensha.commons.param.ParameterAPI;
import org.opensha.commons.param.ParameterList;
import org.opensha.sha.calc.HazardCurveCalculator;
import org.opensha.sha.calc.IM_EventSet.v03.IM_EventSetOutputWriter;
import org.opensha.sha.earthquake.EqkRupForecastAPI;
import org.opensha.sha.earthquake.EqkRupForecastBaseAPI;
import org.opensha.sha.imr.AttenuationRelationship;
import org.opensha.sha.imr.ScalarIntensityMeasureRelationshipAPI;
import org.opensha.sra.gui.portfolioeal.gui.PortfolioEALCalculatorView;
import org.opensha.sra.vulnerability.Vulnerability;

import org.opensha.sra.calc.EALCalculator;
import scratch.martinez.VulnerabilityModels.VulnerabilityModel;



/**
 * This class defines an asset.  Each asset has a ParameterList.  The parameters in the
 * list can be arbitrary, and will be defined based on the parameters name.  Each asset
 * is responsible for calculating its own EAL as well.
 * 
 * @author Jeremy Leakakos
 * @see PortfolioParser
 */
public class Asset implements Cloneable {

	private ParameterList paramList;
	private String errorMessage = "";
	private double EAL;
	private Site assetSite;
	private HazardCurveCalculator calc;
	private boolean calculationDone = false;
	private ArbitrarilyDiscretizedFunc hazFunction;
	
	/**
	 * This constructor takes a comma separated value String
	 * 
	 * @param asset The csv String from the portfolio file
	 */
	public Asset( String asset ) {
		String[] parameters = asset.split(",");
		paramList = new ParameterList();
		initParameterMap( parameters );
		EAL = 0.0;
	}

	/**
	 * This method sets the Parameter objects in the ParameterList from the parameters 
	 * in the string array.  It is only used on the first "asset", or first line of a'
	 * portfolio.  This line is a header, and used to define which parameters are in
	 * each asset.
	 * 
	 * @param parameters An string array to be turned into parameters.
	 */
	private void initParameterMap( String[] parameters ) {
		for( int i = 0; i < parameters.length; i ++ ) {
			paramList.addParameter( createParameter(parameters[i]) );
		}
	}
	
	/**
	 * This method will start a calculation progress bar is the progress bar
	 * CheckBox is checked.
	 */
	private void startCalcProgressBar() {
		if(PortfolioEALCalculatorView.getView().getProgressBarChecked()) {
			CalcProgressListener progressBar = new CalcProgressListener(this);
			progressBar.start();
		}
	}
	
	/**
	 * Set the parameters for the asset.  It takes an array of strings, which are the
	 * parameter values.
	 * 
	 * @param assetList The list of parameters
	 */
	public void setAssetParameters( String[] assetList ) {
		ParameterList list = getParameterList();
		ListIterator<ParameterAPI<?>> iter = list.getParametersIterator();
		Integer i = 0;
		Object val = null;
		while( iter.hasNext() ) {
			ParameterAPI param = iter.next();
			if ( param.getType().equals("IntegerParameter") ) {
				val = Integer.parseInt(assetList[i]);
			}
			else if ( param.getType().equals("StringParameter") ) {
				val = assetList[i];
			}
			else if ( param.getType().equals("DoubleParameter") ) {
				val = Double.parseDouble(assetList[i]);
			}
			param.setValue(val);
			i++;
		}
	}
	
	/**
	 * This method creates a parameter based on the name of the parameter from the
	 * portfolio file, using reflection. This method is only used when the first "asset"
	 * needs to be created.  It is called from <code>initParameterMap</code>, once for
	 * each parameter to be created.  It initializes the base asset that the other
	 * assets with be cloned from.
	 * 
	 * @param paramName The name of the parameter to be created
	 * @return The created parameter, based on the name
	 * @see ParameterParser
	 */
	private Parameter createParameter( String paramName ) {
		Parameter param = null;
		ParameterParser parameterParser = ParameterParser.getParameterParser();
		Class<?> c = null;
		try {
			String className = "org.opensha.commons.param." + parameterParser.getParameterType(paramName);
			c = Class.forName( className );
			Class<?>[] paramTypes = {String.class};
			Constructor<?> cons = c.getConstructor(paramTypes);
			param = (Parameter) cons.newInstance(paramName);
		} catch( Exception e ) {
			e.printStackTrace();
			JOptionPane.showMessageDialog(null, "Parameter type" + paramName + " in file not reckognized!", "Error", JOptionPane.ERROR_MESSAGE );
			PortfolioEALCalculatorView.getView().setButtonsOnCancel();
		}
		return param;
	}
	
	/**
	 * Sets up the site with the name and location from the asset
	 * 
	 * @param site The site to have its values changed
	 * @return The updated site
	 */
	private void siteSetup( Site site ) {
		site.setName((String) getParameterList().getParameter("SiteName").getValue());
		site.setLocation(new Location((Double) getParameterList().getParameter("Lat").getValue(), (Double) paramList.getParameter("Lon").getValue()));
		assetSite = (Site)site.clone();
	}
	
	/**
	 * Sets up the vulnerability model based on the name from the asset.  It uses
	 * reflection to create the class at runtime.
	 * @return The vulnerability model
	 * @throws ClassNotFoundException
	 * @throws InstantiationException
	 * @throws IllegalAccessException
	 */
	private Vulnerability getVulnModel() throws ClassNotFoundException,
													 InstantiationException,
													 IllegalAccessException {
		String vulnName = (String) paramList.getParameter("VulnModel").getValue();
		
		System.out.println("looking for vuln: '" + vulnName + "'");
		
		return PortfolioEALCalculatorController.vulnerabilities.get(vulnName);
	}
	
	/**
	 * This resets the X values of the hazard function.
	 * @param hazFunction The hazard function to be reset
	 * @param vulnModel The vulnerability model where the X values come fro
	 * @return The reset hazard function
	 */
	private DiscretizedFuncAPI resetHazardXValues( DiscretizedFuncAPI hazFunction, Vulnerability vulnModel ) {
	    DiscretizedFuncAPI tempFunc = hazFunction.deepClone();
	    hazFunction = new ArbitrarilyDiscretizedFunc();
	    double imlvals[] = vulnModel.getIMLValues();
	    for( int i = 0; i < tempFunc.getNum(); ++i ) {
	    	hazFunction.set(imlvals[i],tempFunc.getY(i));
	    }
	    return hazFunction;
	}
	/**
	 * This calculates the EAL for a given asset
	 * 
	 * @return The EAL for the asset.  This will be summed up with all of the EAL's
	 * for the other assets in the list.
	 */
	public double calculateEAL( ScalarIntensityMeasureRelationshipAPI imr, double distance, Site site, EqkRupForecastBaseAPI erf, PortfolioEALCalculatorController controller ) {
		// Edit the site with the asset values
		siteSetup(site);
		Site newSite = getSite();
		boolean error = false;
		
		errorMessage = "";
		
		// Create a new hazard function, which will will be used to make calculation
		hazFunction = new ArbitrarilyDiscretizedFunc();
		
		// Setup for the HazardCurveCalculator
		try {
			calc = new HazardCurveCalculator();
			wait(5000);
		} catch (RemoteException e) {
			e.printStackTrace();
			error = true;
			errorMessage += e.getMessage();
		} catch( Exception e ) {
		}
		
		startCalcProgressBar();
		
		// Setup for the forcast gotten from the ERF
		EqkRupForecastBaseAPI forecast = null;
		
		// Setup for the annualized rates gotten from the hazard function with the HazardCurveCalculator
		ArbitrarilyDiscretizedFunc annualizedRates = null;
		
		// The vulnerability model, which is hard coded for now
		Vulnerability vulnModel = null;
		
		try {
			vulnModel = getVulnModel();
		} catch( Exception e ) {
			e.printStackTrace();
			errorMessage += e.getMessage();
			error = true;
		}
		
		String imt = vulnModel.getIMT();
		double imls[] = vulnModel.getIMLValues();
		
		// Sets the intensity measure for the imr instance
		try {				
//			((AttenuationRelationship)imr).setIntensityMeasure(imt, period);
			System.out.println("IMT: " + imt);
			IM_EventSetOutputWriter.setIMTFromString(imt, imr);
//			((AttenuationRelationship)imr).setIntensityMeasure(imt);
		} catch( ParameterException e ) {
			e.printStackTrace();
			controller.calculationException( e.getMessage() );
		}
		
		// Take the log of the x values of the hazard function
		// Used to make calculations
	    for( int i = 0; i < imls.length; ++i ) {
	    	hazFunction.set( Math.log( imls[i] ), 1 );
	    }
	    
	    // Create a HazardCurveCalculator with a site, imr, and erf
	    try {
	    	calc.setMaxSourceDistance( distance );
	    	forecast = erf;
		    hazFunction = (ArbitrarilyDiscretizedFunc)calc.getHazardCurve(hazFunction, newSite, imr, (EqkRupForecastAPI) forecast);
	    } catch( Exception e ) {
			e.printStackTrace();
			errorMessage += e.getMessage();
			error = true;
		}
	    
	    // Reset the x values of the hazard function
	    hazFunction = (ArbitrarilyDiscretizedFunc) resetHazardXValues( hazFunction, vulnModel );
	    
	    // Create the annualized rates function to be used in the EAL calculator
	    try {
	    	annualizedRates = (ArbitrarilyDiscretizedFunc)calc.getAnnualizedRates(hazFunction, forecast.getTimeSpan().getDuration());
	    } catch( Exception e ) {
			e.printStackTrace();
			errorMessage += e.getMessage();
			error = true;
		}
	    
	    if ( error ) controller.calculationException( errorMessage );
	    
	    EALCalculator currentCalc = new EALCalculator( annualizedRates, vulnModel.getVulnerabilityFunc(), (Double)paramList.getParameter("Value").getValue() );
	    EAL = currentCalc.computeEAL();
	    calculationDone();
	    calc = null;
	    return EAL;
	}
	
	/**
	 * Set the calculationDone boolean to true when the calculation finishes.
	 */
	private void calculationDone() {
		calculationDone = true;
	}
	
	/**
	 * @return The boolean representing whether the calculation is done or not.
	 */
	public boolean isCalculationDone() {
		return calculationDone;
	}
	
	/**
	 * @return The total amount of ruptures in a hazard calculation.
	 * @throws RemoteException
	 */
	public int getTotalRuptures() throws RemoteException {
		return calc.getTotRuptures();
	}
	
	/**
	 * @return The current amount of ruptures in a hazard calculation.
	 * @throws RemoteException
	 */
	public int getCurrentRuptures() throws RemoteException {
		return calc.getCurrRuptures();
	}
	
	/**
	 * @return The ParameterList storing the parameters for a given Asset.
	 */
	public ParameterList getParameterList() {
		return paramList;
	}
	
	/**
	 * @return The EAL for the asset
	 */
	public double getAssetEAL() {
		return EAL;
	}
	
	/**
	 * This method sets the parameter list for an asset
	 * @param paramList The ParameterList to be set to
	 */
	private void setParamList( ParameterList paramList ) {
		this.paramList = paramList;
	}
	
	/**
	 * Get the site associated with an asset.
	 * @return The site for the asset
	 */
	public Site getSite() {
		return assetSite;
	}
	
	/**
	 * @return The hazard function associated with an asset
	 */
	public ArbitrarilyDiscretizedFunc getHazardFunction() {
		return hazFunction;
	}
	
	/**
	 * The clone method for Asset.  It overrides the default clone operation in Object.
	 * It creates an a shallow clone of the base asset, and then it creates a clone of
	 * the base asset's ParameterList.  The new asset then has its ParameterList set
	 * to the cloned one.
	 */
	@Override
	public Asset clone() throws CloneNotSupportedException {
		Asset asset = (Asset) super.clone();
		asset.setParamList((ParameterList)this.getParameterList().clone());
		return asset;
	}
}