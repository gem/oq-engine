/*******************************************************************************
 * Copyright 2009 OpenSHA.org in partnership with
 * the Southern California Earthquake Center (SCEC, http://www.scec.org)
 * at the University of Southern California and the UnitedStates Geological
 * Survey (USGS; http://www.usgs.gov)
 * 
 * Licensed under the Apache License, Version 2.0 (the "License");
 * you may not use this file except in compliance with the License.
 * You may obtain a copy of the License at
 * 
 *   http://www.apache.org/licenses/LICENSE-2.0
 * 
 * Unless required by applicable law or agreed to in writing, software
 * distributed under the License is distributed on an "AS IS" BASIS,
 * WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
 * See the License for the specific language governing permissions and
 * limitations under the License.
 ******************************************************************************/

package org.opensha.sha.earthquake.rupForecastImpl;

import java.util.ArrayList;

import org.opensha.commons.calc.magScalingRelations.MagAreaRelationship;
import org.opensha.commons.calc.magScalingRelations.MagScalingRelationship;
import org.opensha.commons.calc.magScalingRelations.magScalingRelImpl.PEER_testsMagAreaRelationship;
import org.opensha.commons.calc.magScalingRelations.magScalingRelImpl.WC1994_MagAreaRelationship;
import org.opensha.commons.calc.magScalingRelations.magScalingRelImpl.WC1994_MagLengthRelationship;
import org.opensha.commons.data.TimeSpan;
import org.opensha.commons.data.function.ArbitrarilyDiscretizedFunc;
import org.opensha.commons.geo.Location;
import org.opensha.commons.param.ArbitrarilyDiscretizedFuncParameter;
import org.opensha.commons.param.BooleanParameter;
import org.opensha.commons.param.DoubleParameter;
import org.opensha.commons.param.EvenlyDiscretizedFuncParameter;
import org.opensha.commons.param.IntegerParameter;
import org.opensha.commons.param.LocationParameter;
import org.opensha.commons.param.ParameterList;
import org.opensha.commons.param.StringParameter;
import org.opensha.commons.param.event.ParameterChangeEvent;
import org.opensha.sha.earthquake.EqkRupForecast;
import org.opensha.sha.earthquake.FocalMechanism;
import org.opensha.sha.earthquake.ProbEqkSource;
import org.opensha.sha.earthquake.griddedForecast.HypoMagFreqDistAtLoc;
import org.opensha.sha.earthquake.rupForecastImpl.Point2MultVertSS_FaultSource;
import org.opensha.sha.magdist.ArbIncrementalMagFreqDist;
import org.opensha.sha.magdist.GaussianMagFreqDist;
import org.opensha.sha.magdist.GutenbergRichterMagFreqDist;
import org.opensha.sha.magdist.IncrementalMagFreqDist;
import org.opensha.sha.magdist.SingleMagFreqDist;
import org.opensha.sha.magdist.SummedMagFreqDist;
import org.opensha.sha.magdist.YC_1985_CharMagFreqDist;
import org.opensha.sha.param.MagFreqDistParameter;
import org.opensha.sha.param.SimpleFaultParameter;


/**
 * <p>Title: PointToLineSourceERF
 * This is an ERF wrapper for PointToLineSource.  Only one mag-freq dist and focal mechanism is used 
 * (the latter being created from adjustable params for rake, strike, and dip).  A random strike is
 * applied if strike is null (or blank in the GUI).  See PointToLineSource for further description.
 * Tests: I confirmed that averaging a bunch of hazard curves for random strikes equals the curve
 * for a spoked source with numStrikes=45. 
 * @author Ned Field
 * Date : Feb , 2010
 * @version 1.0
 */

public class PointToLineSourceERF extends EqkRupForecast{

	//for Debug purposes
	private static String  C = new String("PointToLineSourceERF");
	private boolean D = false;

	//name for this classs
	public final static String  NAME = "Point To Line Source ERF";

	// this is the source (only 1 for this ERF)
	private PointToLineSource source;

	// adjustable parameter declarations
	LocationParameter locParam;
	MagFreqDistParameter magDistParam;
	DoubleParameter rakeParam;
	DoubleParameter strikeParam;
	DoubleParameter dipParam;
	StringParameter magScalingRelParam;
	ArbitrarilyDiscretizedFuncParameter rupTopDepthParam;
	DoubleParameter defaultHypoDepthParam;
	DoubleParameter lowerSeisDepthParam;
	DoubleParameter minMagParam;
	BooleanParameter spokedRupturesParam;
	IntegerParameter numStrikeParam;
	DoubleParameter firstStrikeParam;

	// loc Parameter stuff
	public final static String LOC_PARAM_NAME = "Location";
	private final static String LOC_PARAM_INFO = "Location of center of the source";

	//mag-freq dist parameter Name
	public final static String MAG_DIST_PARAM_NAME = "Mag Freq Dist";

	// rake parameter stuff
	public final static String RAKE_PARAM_NAME = "Rake";
	private final static String RAKE_PARAM_INFO = "The rake of the rupture (direction of slip)";
	private final static String RAKE_PARAM_UNITS = "degrees";
	private Double RAKE_PARAM_MIN = new Double(-180);
	private Double RAKE_PARAM_MAX = new Double(180);
	private Double RAKE_PARAM_DEFAULT = new Double(0.0);


	// strike parameter stuff
	public final static String STRIKE_PARAM_NAME = "Strike";
	private final static String STRIKE_PARAM_INFO = "The strike of the rupture (put blank for random)";
	private final static String STRIKE_PARAM_UNITS = "degrees";
	private Double STRIKE_PARAM_MIN = new Double(-180);
	private Double STRIKE_PARAM_MAX = new Double(180);
	private Double STRIKE_PARAM_DEFAULT = new Double(0.0);

	// dip parameter stuff
	public final static String DIP_PARAM_NAME = "Dip";
	private final static String DIP_PARAM_INFO = "The dip of the rupture";
	private final static String DIP_PARAM_UNITS = "degrees";
	private Double DIP_PARAM_MIN = new Double(0);
	private Double DIP_PARAM_MAX = new Double(90);
	private Double DIP_PARAM_DEFAULT = new Double(90);

	// Mag-scaling relationship parameter stuff
	public final static String MAG_SCALING_REL_PARAM_NAME = "Mag-Scaling Relationship";
	private final static String MAG_SCALING_REL_PARAM_INFO = "Relationship to use for Area(Mag) or Area(Length) calculations";
	private ArrayList<String> magScalingRelOptions;

	// magDepthParam stuff;
	public final static String RUP_TOP_DEPTH_FUNC_PARAM_NAME = "Rup-Top Depth vs Mag";
	private final static String RUP_TOP_DEPTH_FUNC_PARAM_INFO = "Used to set the depth of line sources";

	// defaultHypoDepthParam stuff
	public final static String DEFAULT_HYPO_DEPTH_PARAM_NAME = "Default Hypo Depth";
	private final static String DEFAULT_HYPO_DEPTH_PARAM_INFO = "This depth applied to small mags";
	private final static String DEFAULT_HYPO_DEPTH_PARAM_UNITS = "km";
	private Double DEFAULT_HYPO_DEPTH_PARAM_MIN = new Double(0);
	private Double DEFAULT_HYPO_DEPTH_PARAM_MAX = new Double(100);
	private Double DEFAULT_HYPO_DEPTH_PARAM_DEFAULT = new Double(5);

	// lowerSeisDepthParam stuff
	public final static String LOWER_SEIS_DEPTH_PARAM_NAME = "Lower Seis Depth";
	private final static String LOWER_SEIS_DEPTH_PARAM_INFO = "Lower Seismogenic Depth";
	private final static String LOWER_SEIS_DEPTH_PARAM_UNITS = "km";
	private Double LOWER_SEIS_DEPTH_PARAM_MIN = new Double(0);
	private Double LOWER_SEIS_DEPTH_PARAM_MAX = new Double(100);
	private Double LOWER_SEIS_DEPTH_PARAM_DEFAULT = new Double(14);

	// min mag parameter stuff
	public final static String MIN_MAG_PARAM_NAME = "Min Mag";
	private final static String MIN_MAG_PARAM_INFO = "The minimum mag to be considered from the mag freq dist";
	private Double MIN_MAG_PARAM_MIN = new Double(0);
	private Double MIN_MAG_PARAM_MAX = new Double(10);
	private Double MIN_MAG_PARAM_DEFAULT = new Double(5);

	// spokedRupturesParam
	public final static String SPOKED_RUPTURES_PARAM_NAME = "Apply spoked source?";
	private final static String SPOKED_RUPTURES_PARAM_INFO = "This will apply a number of ruptures whose strikes are evenly spaced";

	// deltaStrike parameter stuff
	public final static String NUM_STRIKE_PARAM_NAME = "Num Strikes";
	private final static String NUM_STRIKE_PARAM_INFO = "Number of strikes for spoked source";
	private Integer NUM_STRIKE_PARAM_MIN = new Integer(1);
	private Integer NUM_STRIKE_PARAM_MAX = new Integer(180);
	private Integer NUM_STRIKE_PARAM_DEFAULT = new Integer(2);

	// min mag parameter stuff
	public final static String FIRST_STRIKE_PARAM_NAME = "First Strike";
	private final static String FIRST_STRIKE_PARAM_INFO = "The first strike for the spoked source";
	private final static String FIRST_STRIKE_PARAM_UNITS = "degrees";
	private Double FIRST_STRIKE_PARAM_MIN = new Double(0);
	private Double FIRST_STRIKE_PARAM_MAX = new Double(90);
	private Double FIRST_STRIKE_PARAM_DEFAULT = new Double(0);

	/**
	 * Constructor for this source (no arguments)
	 */
	public PointToLineSourceERF() {

		// create the timespan object with start time and duration in years
		timeSpan = new TimeSpan(TimeSpan.NONE,TimeSpan.YEARS);
		timeSpan.addParameterChangeListener(this);

		locParam = new LocationParameter(LOC_PARAM_NAME);
		locParam.setInfo(LOC_PARAM_INFO);

		// make the magFreqDistParameter
		ArrayList<String> supportedMagDists=new ArrayList<String>();
		supportedMagDists.add(GaussianMagFreqDist.NAME);
		supportedMagDists.add(SingleMagFreqDist.NAME);
		supportedMagDists.add(GutenbergRichterMagFreqDist.NAME);
		supportedMagDists.add(YC_1985_CharMagFreqDist.NAME);
		supportedMagDists.add(SummedMagFreqDist.NAME);
		supportedMagDists.add(ArbIncrementalMagFreqDist.NAME);
		magDistParam = new MagFreqDistParameter(MAG_DIST_PARAM_NAME, supportedMagDists);
		GaussianMagFreqDist mfd = new GaussianMagFreqDist(5.0,8.0,31,6.5,0.12,1e19);
		magDistParam.setValue(mfd);

		// create the rake param
		rakeParam = new DoubleParameter(RAKE_PARAM_NAME,RAKE_PARAM_MIN,
				RAKE_PARAM_MAX,RAKE_PARAM_UNITS,RAKE_PARAM_DEFAULT);
		rakeParam.setInfo(RAKE_PARAM_INFO);

		// create the strike param
		strikeParam = new DoubleParameter(STRIKE_PARAM_NAME,STRIKE_PARAM_MIN,
				STRIKE_PARAM_MAX,STRIKE_PARAM_UNITS,STRIKE_PARAM_DEFAULT);
		strikeParam.setInfo(STRIKE_PARAM_INFO);
		strikeParam.getConstraint().setNullAllowed(true);
	

		// create the dip param
		dipParam = new DoubleParameter(DIP_PARAM_NAME,DIP_PARAM_MIN,
				DIP_PARAM_MAX,DIP_PARAM_UNITS,DIP_PARAM_DEFAULT);
		dipParam.setInfo(DIP_PARAM_INFO);
		

	    // create the mag-scaling relationship param
	    magScalingRelOptions = new ArrayList();
	    magScalingRelOptions.add(WC1994_MagAreaRelationship.NAME);
	    magScalingRelOptions.add(WC1994_MagLengthRelationship.NAME);
	    magScalingRelOptions.add(PEER_testsMagAreaRelationship.NAME);
	    magScalingRelParam = new StringParameter(MAG_SCALING_REL_PARAM_NAME,magScalingRelOptions,
	                                             WC1994_MagAreaRelationship.NAME);
	    magScalingRelParam.setInfo(MAG_SCALING_REL_PARAM_INFO);

	    // create a default rup-top depth func and create the parameter
		ArbitrarilyDiscretizedFunc discretizedFunc = new ArbitrarilyDiscretizedFunc();  // these are about NSHMP values
		discretizedFunc.set(6.0, 5.0);
		discretizedFunc.set(6.5, 5.0);
		discretizedFunc.set(6.6, 1.0);
		discretizedFunc.set(9.0, 1.0);
		rupTopDepthParam = new ArbitrarilyDiscretizedFuncParameter(RUP_TOP_DEPTH_FUNC_PARAM_NAME, discretizedFunc);
		rupTopDepthParam.setInfo(RUP_TOP_DEPTH_FUNC_PARAM_INFO);

		// create defaultHypoDepthParam
		defaultHypoDepthParam = new DoubleParameter(DEFAULT_HYPO_DEPTH_PARAM_NAME,DEFAULT_HYPO_DEPTH_PARAM_MIN,
				DEFAULT_HYPO_DEPTH_PARAM_MAX,DEFAULT_HYPO_DEPTH_PARAM_UNITS,DEFAULT_HYPO_DEPTH_PARAM_DEFAULT);
		defaultHypoDepthParam.setInfo(DEFAULT_HYPO_DEPTH_PARAM_INFO);

		// create lowerSeisDepthParam
		lowerSeisDepthParam = new DoubleParameter(LOWER_SEIS_DEPTH_PARAM_NAME,LOWER_SEIS_DEPTH_PARAM_MIN,
				LOWER_SEIS_DEPTH_PARAM_MAX,LOWER_SEIS_DEPTH_PARAM_UNITS,LOWER_SEIS_DEPTH_PARAM_DEFAULT);
		lowerSeisDepthParam.setInfo(LOWER_SEIS_DEPTH_PARAM_INFO);

		// create the min mag param
		minMagParam = new DoubleParameter(MIN_MAG_PARAM_NAME,MIN_MAG_PARAM_MIN,
				MIN_MAG_PARAM_MAX,MIN_MAG_PARAM_DEFAULT);
		minMagParam.setInfo(MIN_MAG_PARAM_INFO);

		//
		spokedRupturesParam = new BooleanParameter(SPOKED_RUPTURES_PARAM_NAME,false);
		spokedRupturesParam.setInfo(SPOKED_RUPTURES_PARAM_INFO);

		// 
		numStrikeParam = new IntegerParameter(NUM_STRIKE_PARAM_NAME,NUM_STRIKE_PARAM_MIN,
				NUM_STRIKE_PARAM_MAX,NUM_STRIKE_PARAM_DEFAULT);
		numStrikeParam.setInfo(NUM_STRIKE_PARAM_INFO);

		// 
		firstStrikeParam = new DoubleParameter(FIRST_STRIKE_PARAM_NAME,FIRST_STRIKE_PARAM_MIN,
				FIRST_STRIKE_PARAM_MAX,FIRST_STRIKE_PARAM_UNITS,FIRST_STRIKE_PARAM_DEFAULT);
		firstStrikeParam.setInfo(FIRST_STRIKE_PARAM_INFO);


		// add params to adjustable parameter list
		createParamList();

		// register the parameters that need to be listened to
		spokedRupturesParam.addParameterChangeListener(this);
		magScalingRelParam.addParameterChangeListener(this);
	}
	
	/**
	 *  This acts on a parameter change event.
	 *
	 *  This sets the flag to indicate that the sources need to be updated
	 *
	 * @param  event
	 */
	public void parameterChange(ParameterChangeEvent event) {
		super.parameterChange(event);
		String paramName = event.getParameterName();

		// recreate the parameter list if any of the following were modified
		if(paramName.equals(SPOKED_RUPTURES_PARAM_NAME) || paramName.equals(MAG_SCALING_REL_PARAM_NAME)){
			createParamList();
		}
		parameterChangeFlag = true;

	}
	
	/**
	 * This put parameters in the ParameterList (depending on settings)
	 */
	private void createParamList() {

		adjustableParams = new ParameterList();
		adjustableParams.addParameter(locParam);
		adjustableParams.addParameter(magDistParam);
		if(!spokedRupturesParam.getValue())
			adjustableParams.addParameter(strikeParam);
		adjustableParams.addParameter(dipParam);
		adjustableParams.addParameter(rakeParam);
		adjustableParams.addParameter(magScalingRelParam);
		if(getmagScalingRelationship(magScalingRelParam.getValue()) instanceof MagAreaRelationship)
			adjustableParams.addParameter(lowerSeisDepthParam);
		adjustableParams.addParameter(rupTopDepthParam);
		adjustableParams.addParameter(defaultHypoDepthParam);
		adjustableParams.addParameter(minMagParam);
		adjustableParams.addParameter(spokedRupturesParam);
		if(spokedRupturesParam.getValue()) {
			adjustableParams.addParameter(numStrikeParam);
			adjustableParams.addParameter(firstStrikeParam);			
		}
	}


	/**
	 * update the source based on the parameters
	 */
	public void updateForecast(){
		if (D) System.out.println(this.adjustableParams.toString());
		Double strikeValue = strikeParam.getValue();
		double strike;
		// convert null strikes to NaN
		if(strikeValue == null)
			strike = Double.NaN;
		else
			strike = strikeValue;
		FocalMechanism focalMech = new FocalMechanism(strike, dipParam.getValue(), rakeParam.getValue());
		HypoMagFreqDistAtLoc hypoMagFreqDistAtLoc = new HypoMagFreqDistAtLoc((IncrementalMagFreqDist)magDistParam.getValue(), 
				locParam.getValue(), focalMech);
		
		if(spokedRupturesParam.getValue()) {
			source = new PointToLineSource(hypoMagFreqDistAtLoc,
					rupTopDepthParam.getValue(), 
					defaultHypoDepthParam.getValue(),
					getmagScalingRelationship(magScalingRelParam.getValue()),
					lowerSeisDepthParam.getValue(), 
					timeSpan.getDuration(), 
					minMagParam.getValue(), 
					numStrikeParam.getValue(), 
					firstStrikeParam.getValue());
		}
		else {
			source = new PointToLineSource(hypoMagFreqDistAtLoc,
					rupTopDepthParam.getValue(), 
					defaultHypoDepthParam.getValue(),
					getmagScalingRelationship(magScalingRelParam.getValue()),
					lowerSeisDepthParam.getValue(), 
					timeSpan.getDuration(), 
					minMagParam.getValue());
		}
	}


	private MagScalingRelationship getmagScalingRelationship(String magScName) {
		if (magScName.equals(WC1994_MagAreaRelationship.NAME))
			return new WC1994_MagAreaRelationship();
		else if (magScName.equals(WC1994_MagLengthRelationship.NAME))
			return new WC1994_MagLengthRelationship();
		else
			return new PEER_testsMagAreaRelationship();
	}

	
	/**
	 * Return the earthquake source at index i.   Note that this returns a
	 * pointer to the source held internally, so that if any parameters
	 * are changed, and this method is called again, the source obtained
	 * by any previous call to this method will no longer be valid.
	 *
	 * @param iSource : index of the desired source (only "0" allowed here).
	 *
	 * @return Returns the ProbEqkSource at index i
	 *
	 */
	public ProbEqkSource getSource(int iSource) {

		// we have only one source
		if(iSource!=0)
			throw new RuntimeException("Only 1 source available, iSource should be equal to 0");

		return source;
	}


	/**
	 * Returns the number of earthquake sources (always "1" here)
	 *
	 * @return integer value specifying the number of earthquake sources
	 */
	public int getNumSources(){
		return 1;
	}


	/**
	 *  This returns a list of sources (contains only one here)
	 *
	 * @return ArrayList of Prob Earthquake sources
	 */
	public ArrayList  getSourceList(){
		ArrayList v =new ArrayList();
		v.add(source);
		return v;
	}


	/**
	 * Return the name for this class
	 *
	 * @return : return the name for this class
	 */
	public String getName(){
		return NAME;
	}
	
	// this is temporary for testing purposes
	public static void main(String[] args) {
		PointToLineSourceERF src = new PointToLineSourceERF();
		src.updateForecast();
	}


}
