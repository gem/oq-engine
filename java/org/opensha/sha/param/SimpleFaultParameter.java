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

package org.opensha.sha.param;


import java.util.ArrayList;

import org.dom4j.Element;
import org.opensha.commons.geo.Location;
import org.opensha.commons.param.DependentParameter;
import org.opensha.commons.param.DoubleParameter;
import org.opensha.commons.param.IntegerParameter;
import org.opensha.commons.param.ParameterAPI;
import org.opensha.commons.param.ParameterList;
import org.opensha.commons.param.ParameterListParameter;
import org.opensha.commons.param.StringParameter;
import org.opensha.commons.param.editor.ParameterEditor;
import org.opensha.commons.param.event.ParameterChangeEvent;
import org.opensha.commons.param.event.ParameterChangeListener;
import org.opensha.sha.faultSurface.EvenlyGriddedSurface;
import org.opensha.sha.faultSurface.FaultTrace;
import org.opensha.sha.faultSurface.FrankelGriddedSurface;
import org.opensha.sha.faultSurface.SimpleListricGriddedSurface;
import org.opensha.sha.faultSurface.StirlingGriddedSurface;
import org.opensha.sha.param.editor.SimpleFaultParameterEditor;


/**
 * <p>Title: SimpleFaultParameter</p>
 * <p>Description: This class acts as the intermediatory between SimpleFaultParameter
 * and its editor.It extends the Dependent Parameter class so as to save the list of
 * visible parameters. Most of the editor functionality has been embedded into this
 * class because we want to make all the functionality available to the user if
 * he does not want to use the GUI components.
 * This is a more general parameter than the simple fault.
 * Actually it creates an object for the EvenlyGriddedSurfaceEvenlyGriddedSurface</p>
 * @author : Ned Field, Nitin Gupta and Vipin Gupta
 * @version 1.0
 */

public class SimpleFaultParameter extends DependentParameter implements ParameterChangeListener,
java.io.Serializable{

	/** Class name for debugging. */
	protected final static String C = "SimpleFaultParameter";
	/** If true print out debug statements. */
	protected final static boolean D = false;

	/** For serialization. */
	private static final long serialVersionUID = 123456789099999999L;


	//Final static declaration for the Parameters in the EvenlyGriddedSurface
	public static final String FAULT_NAME = "Fault Name";
	public static final String GRID_SPACING = "Grid Spacing";
	public static final String GRID_SPACING_UNITS = "km";
	public static final String NUMBER_OF_FAULT_TRACE = "Num. of Fault Trace Points";
	public static final String NUM_DIPS = "Num. of Dips";
	public static final String DEPTH_PARAM_NAME = "Depth-";
	public static final String DIP_PARAM_NAME = "Dip-";
	public static final String LON_PARAM_NAME = "Lon-";
	public static final String LAT_PARAM_NAME = "Lat-";

	//Default Values for the param
	public static final int DEFAULT_NUM_FAULT_TRACE =3;
	public static final int DEFAULT_DIPS =1;
	public static final int latlonCols = 2;
	public static final double DEFAULT_GRID_SPACING = 1.0;


	//static string declaration for the Lat, Lon , Dip and Depth Paramater (ParameterListParameter) names title
	public static final String LAT_TITLE = "Fault Latitudes";
	public static final String LON_TITLE = "Fault Longitudes";
	public static final String DIP_TITLE = "Dips";
	public static final String DEPTH_TITLE = "Depths";

	//Fault Type Param Name
	public static final String FAULT_TYPE_TITLE = "Finite Fault Type";

	//static string for the Fault type supported
	public static final String FRANKEL ="Frankel's";
	public static final String STIRLING ="Stirling's";

	//checks when the parameter has changed only then update the fault param else not.
	private boolean faultParameterChange = true;

	/**
	 * Some variable declarations
	 */
	private double avgDip;
	private FaultTrace fltTrace;
	private double upperSies;
	private double lowerSies;


	/**
	 * Paramter List for holding all parameters
	 */
	private ParameterList parameterList ;

	/**
	 * List to store the Lats
	 */
	private ParameterListParameter parameterListParameterForLats ;

	/**
	 * List to store the Lons
	 */
	private ParameterListParameter parameterListParameterForLons ;
	/**
	 * ParameterList for the Dips
	 */
	private ParameterListParameter parameterListParameterForDips ;

	/**
	 * ParameterList for the Depths
	 */
	private ParameterListParameter parameterListParameterForDepths ;

	/**
	 * DoubleParameter for Ave. Dip LocationVector, if the person has selected
	 * Stirling Fault Model
	 */
	public static final String DIP_DIRECTION_PARAM_NAME = "Ave. Dip LocationVector";
	//used only when stirling fault model is selected
	private static final Double DEFAULT_DIP_DIRECTION = null;
	private static final String DIP_DIRECTION_PARAM_UNITS = "degrees";
	private static final String DIP_DIRECTION_INFO = "Leave blank to make this perpendicular to fault-Strike";
	private DoubleParameter dipDirectionParam = new DoubleParameter(DIP_DIRECTION_PARAM_NAME,
			new Double(0),new Double(360),DIP_DIRECTION_PARAM_UNITS,DEFAULT_DIP_DIRECTION);

	//creating the Double parameter for the Dips
	private IntegerParameter numDipParam = new IntegerParameter(NUM_DIPS,new Integer(this.DEFAULT_DIPS));

	//Fault Name param
	StringParameter faultName= new StringParameter(this.FAULT_NAME);
	//Grid Spacing Param
	DoubleParameter gridSpacing = new DoubleParameter(this.GRID_SPACING,0.01,5,GRID_SPACING_UNITS,new Double(this.DEFAULT_GRID_SPACING));
	//FaultTrace Param
	IntegerParameter numFltTrace = new IntegerParameter(this.NUMBER_OF_FAULT_TRACE,2,100,new Integer(this.DEFAULT_NUM_FAULT_TRACE));

	//creating the StringParameter for the FaultType
	StringParameter faultTypeParam;

	//vectors to store the previous values for the lats, lons,dips and depths
	private ArrayList prevLats;
	private ArrayList prevLons;
	private ArrayList prevDepths;
	private ArrayList prevDips;

	private transient ParameterEditor paramEdit= null;

	/**
	 *  No constraints specified for this parameter. Sets the name of this
	 *  parameter.
	 *
	 * @param  name  Name of the parameter
	 */
	public SimpleFaultParameter(String name) {
		super(name,null,null,null);
		//initializing the simple fault parameter
		initParamList();
	}

	/**
	 * No constraints specified, all values allowed. Sets the name and value.
	 *
	 * @param  name   Name of the parameter
	 * @param  surface  EvenlyGriddedSurface  object
	 */
	public SimpleFaultParameter(String name, EvenlyGriddedSurface surface){
		super(name,null,null,surface);
		//initializing the simple fault parameter
		initParamList();
	}


	/**
	 *  Compares the values to if this is less than, equal to, or greater than
	 *  the comparing objects.
	 *
	 * @param  obj                     The object to compare this to
	 * @return                         -1 if this value < obj value, 0 if equal,
	 *      +1 if this value > obj value
	 * @exception  ClassCastException  Is thrown if the comparing object is not
	 *      a DoubleParameter, or DoubleDiscreteParameter.
	 */
	public int compareTo( Object obj ) throws UnsupportedOperationException {
		throw new java.lang.UnsupportedOperationException("This method not implemented yet");
	}


	/**
	 *  Set's the parameter's value.
	 *
	 * @param  value                 The new value for this Parameter
	 * @throws  ParameterException   Thrown if the object is currenlty not
	 *      editable
	 * @throws  ConstraintException  Thrown if the object value is not allowed
	 */
	/*public void setValue( EvenlyGriddedSurface value ) throws ParameterException {
    setValue( (Object) value);
  }*/

	/**
	 *  Compares value to see if equal.
	 *
	 * @param  obj                     The object to compare this to
	 * @return                         True if the values are identical
	 * @exception  ClassCastException  Is thrown if the comparing object is not
	 *      a DoubleParameter, or DoubleDiscreteParameter.
	 */
	public boolean equals( Object obj ) throws UnsupportedOperationException {
		throw new java.lang.UnsupportedOperationException("This method not implemented yet");

	}


	/**
	 *  Returns a copy so you can't edit or damage the origial.
	 *
	 * @return    Exact copy of this object's state
	 */
	public Object clone() throws UnsupportedOperationException {
		throw new java.lang.UnsupportedOperationException("This method not implemented yet");
	}


	/**
	 * Adds the Independent Params to the selected Params
	 */
	private void addDependenParamList(){
		//faultType param is dependent on the numDip param
		numDipParam.addIndependentParameter(faultTypeParam);
		//dipdirection param is dependent on the numDipParam
		numDipParam.addIndependentParameter(dipDirectionParam);

		//dipDirection param is also dependent on the value of the faultTypeParam
		faultTypeParam.addIndependentParameter(dipDirectionParam);
		dipDirectionParam.addParameterChangeListener(this);
		faultTypeParam.addParameterChangeListener(this);

	}

	/**
	 *
	 * creating the parameters for the parameterList that includes:
	 * 1)name of the fault
	 * 2)Grid Spacing
	 * 3)Num of the Flt Trace
	 * All the above parameters are added to one param List and to one ParamList Editor
	 * This is only few parameters that compose the SimpleFaultParameter, which is a complex
	 * parameter comprising of other parameters too.
	 */
	private void initParamList(){

		parameterList = new ParameterList();
		parameterList.addParameter(faultName);
		parameterList.addParameter(gridSpacing);
		parameterList.addParameter(numFltTrace);
		dipDirectionParam.setInfo(DIP_DIRECTION_INFO);
		dipDirectionParam.getConstraint().setNullAllowed(true);
		//create the String parameter if the dip is one
		ArrayList fltType = new ArrayList();
		fltType.add(this.FRANKEL);
		fltType.add(this.STIRLING);
		faultTypeParam = new StringParameter(this.FAULT_TYPE_TITLE,fltType,(String)fltType.get(0));

		//adding the parameter change listener to each parameter in the list
		faultName.addParameterChangeListener(this);
		gridSpacing.addParameterChangeListener(this);
		numFltTrace.addParameterChangeListener(this);
		numDipParam.addParameterChangeListener(this);
		//creates the dependent ParamList
		addDependenParamList();
	}


	/**
	 *
	 * @returns the ParameterList comprising of following parameters:
	 * 1)name of the fault
	 * 2)Grid Spacing
	 * 3)Num of the Flt Trace
	 */
	public ParameterList getFaultTraceParamList(){
		return parameterList;
	}


	/**
	 * returns ParameterListParameter
	 * @returns the Parameter comprising of all the latitudes
	 */
	public ParameterAPI getLatParam(){
		return parameterListParameterForLats;
	}

	/**
	 * returns ParameterListParameter
	 * @returns the Parameter comprising of all the longitudes
	 */
	public ParameterAPI getLonParam(){
		return parameterListParameterForLons;
	}

	/**
	 * returns ParameterListParameter
	 * @returns the Parameter comprising of all the depths
	 */
	public ParameterAPI getDepthParam(){
		return parameterListParameterForDepths;
	}

	/**
	 * returns ParameterListParameter
	 * @returns the Parameter comprising of all the dips
	 */
	public ParameterAPI getDipParam(){
		return parameterListParameterForDips;
	}

	/**
	 *
	 * @returns the parameter for the number of Dips
	 */
	public ParameterAPI getNumDipParam(){
		return numDipParam;
	}

	/**
	 *
	 * @returns the parameter for selected fault type
	 */
	public ParameterAPI getFaultTypeParam(){
		return faultTypeParam;
	}

	/**
	 *
	 * @returns the parameter for Dip direction
	 */
	public ParameterAPI getDipDirectionParam(){
		return dipDirectionParam;
	}


	/**
	 *  This is the main function of this interface. Any time a control
	 *  paramater or independent paramater is changed by the user this
	 *  function is called, and a paramater change event is passed in.
	 *
	 * @param  event
	 */
	public void parameterChange( ParameterChangeEvent event ) {
		faultParameterChange = true;
	}

	/**
	 * Returns the grid spacing of the Fault Surface.
	 * @return
	 */
	public double getGridSpacing(){
		return ((Double)gridSpacing.getValue()).doubleValue();
	}

	/**
	 * Creates Latitude and Longitude parameters based on the number of the faultTrace.
	 * If the user has already specified the values for these parameters once ,it saves
	 * those values for future reference. So that when the number of fault-trace changes
	 * user does not always have to fill in all the values.
	 */
	public void initLatLonParamList(){

		int numFltTracePoints = ((Integer)parameterList.getParameter(this.NUMBER_OF_FAULT_TRACE).getValue()).intValue();
		DoubleParameter[] lat = new DoubleParameter[numFltTracePoints];
		DoubleParameter[] lon = new DoubleParameter[numFltTracePoints];

		//making the parameterList for the Lat and Lons
		ParameterList parameterListForLats = new ParameterList();
		ParameterList parameterListForLons = new ParameterList();

		//getting the size  of the list which stores the actual double value of the parameter.
		int size = 0;
		if(prevLats != null)
			size = prevLats.size();
		else
			prevLats = new ArrayList();
		//creating the editor for the lons
		for(int i=0;i<numFltTracePoints;++i){
			//checks if any value exists in the vector for that lats parameter else just fill it up with a blank.
			if(size<(i+1) && size>0)
				lat[i] = new DoubleParameter(LAT_PARAM_NAME+(i+1),-90.0,90.0,"Degrees");
			else if(size ==0)
				lat[i] = new DoubleParameter(LAT_PARAM_NAME+(i+1),-90.0,90.0,"Degrees",
						new Double(38.2248 - i/2.0));
			else
				lat[i] = new DoubleParameter(LAT_PARAM_NAME+(i+1),-90.0,90.0,"Degrees", (Double)prevLats.get(i));
			lat[i].addParameterChangeListener(this);
			parameterListForLats.addParameter(lat[i]);

		}
		parameterListParameterForLats = new ParameterListParameter(LAT_TITLE,parameterListForLats);
		if(prevLons !=null)
			size = prevLons.size();
		else
			prevLons = new ArrayList();
		//creating the editor for the Lons
		for(int i=0;i<numFltTracePoints;++i){
			//checks if any value exists in the vector for that lons parameter else just fill it up with a blank.
			if(size < (i+1) && size >0)
				lon[i] = new DoubleParameter(LON_PARAM_NAME+(i+1),-360.0,360.0,"Degrees");
			else if(size ==0)
				lon[i] = new DoubleParameter(LON_PARAM_NAME+(i+1),-360.0,360.0,"Degrees",
						new Double(-122.0 - i/2.0));
			else
				lon[i] = new DoubleParameter(this.LON_PARAM_NAME+(i+1),-360.0,360.0,"Degrees",(Double)prevLons.get(i));
			lon[i].addParameterChangeListener(this);
			parameterListForLons.addParameter(lon[i]);
		}
		parameterListParameterForLons = new ParameterListParameter(LON_TITLE,parameterListForLons);

		//Lats and Lon params are dependent on the number of fault trace
		//if they already exists in the dependentParam List remove the earlier one and add new
		//Lat and Lon param.
		if(numFltTrace.containsIndependentParameter(LAT_TITLE))
			numFltTrace.removeIndependentParameter(LAT_TITLE);
		if(numFltTrace.containsIndependentParameter(LON_TITLE))
			numFltTrace.removeIndependentParameter(LON_TITLE);
		numFltTrace.addIndependentParameter(parameterListParameterForLats);
		numFltTrace.addIndependentParameter(parameterListParameterForLons);
	}


	/**
	 * Creates Dips parameters based on the number of the Dips.
	 * If the user has already specified the values for these parameters once ,it saves
	 * those values for future reference. So that when the number of dips changes
	 * user does not always have to fill in all the values.
	 */
	public void initDipParamList(){
		int numDips = ((Integer)numDipParam.getValue()).intValue();

		DoubleParameter[] dip = new DoubleParameter[numDips];

		//making the parameterList for the Dips
		ParameterList parameterListForDips = new ParameterList();
		int size = 0;
		if(prevDips !=null)
			size= prevDips.size();
		else
			prevDips = new ArrayList();

		for(int i=0;i<numDips;++i){
			//checks if any value exists in the vector for that dips parameter else just fill it up with a blank.
			if(size < (i+1) && size >0)
				dip[i] = new DoubleParameter(DIP_PARAM_NAME+(i+1),0.0,90.0,"Degrees");
			else if(size ==0)
				dip[i] = new DoubleParameter(DIP_PARAM_NAME+(i+1),0.0,90.0,"Degrees",
						new Double(90-(i+30)));
			else
				dip[i] = new DoubleParameter(DIP_PARAM_NAME+(i+1),0.0,90.0,"Degrees",(Double)prevDips.get(i));
			dip[i].addParameterChangeListener(this);
			parameterListForDips.addParameter(dip[i]);
		}
		parameterListParameterForDips = new ParameterListParameter(DIP_TITLE,parameterListForDips);

		//Dips are dependent on the number of dips
		//if they already exists in the dependentParam List remove the earlier one and add new
		//dip param.
		if(numDipParam.containsIndependentParameter(DIP_TITLE))
			numDipParam.removeIndependentParameter(DIP_TITLE);
		numDipParam.addIndependentParameter(parameterListParameterForDips);
	}


	/**
	 * Creates Latitude and Longitude parameters based on the number of the Dips.
	 * If the user has already specified the values for these parameters once ,it saves
	 * those values for future reference. So that when the number of dips changes
	 * user does not always have to fill in all the values.
	 * Number of Depths are always one more than the number of dips
	 */
	public void initDepthParamList(){
		int numDepths = ((Integer)numDipParam.getValue()).intValue()+1;
		DoubleParameter[] depth = new DoubleParameter[numDepths];

		//making the parameterList for the Dips
		ParameterList parameterListForDepths = new ParameterList();

		int size = 0;
		if(prevDepths!=null)
			size = prevDepths.size();
		else
			prevDepths = new ArrayList();
		for(int i=0;i<numDepths;++i){
			//checks if any value exists in the vector for that Depth parameter else just fill it up with a blank.
			if(size < (i+1) && size >0)
				depth[i] = new DoubleParameter(DEPTH_PARAM_NAME+(i+1),0.0,99999.0,"km");
			else if( size ==0)
				depth[i] = new DoubleParameter(DEPTH_PARAM_NAME+(i+1),0.0,99999.0,"km",
						new Double(0+(i+6)));
			else
				depth[i] = new DoubleParameter(DEPTH_PARAM_NAME+(i+1),0.0,99999.0,"km",(Double)prevDepths.get(i));
			parameterListForDepths.addParameter(depth[i]);
			depth[i].addParameterChangeListener(this);
		}
		parameterListParameterForDepths = new ParameterListParameter(DEPTH_TITLE,parameterListForDepths);

		//Depths are dependent on the number of dips
		//if they already exists in the dependentParam List remove the earlier one and add new
		//depth param.
		if(numDipParam.containsIndependentParameter(DEPTH_TITLE))
			numDipParam.removeIndependentParameter(DEPTH_TITLE);
		numDipParam.addIndependentParameter(parameterListParameterForDepths);
	}


	/**
	 * creates the evenly gridded surface from the fault parameter.
	 * This function has to be called explicitly in order to Create/Update
	 * the  gridded surface , if user is not using the GUI.
	 * @throws RuntimeException
	 */
	public void setEvenlyGriddedSurfaceFromParams()throws RuntimeException{
		//only update the parameter if any parameter in the parameer list has been changed
		if(faultParameterChange){
			faultParameterChange = false;
			ParameterList independentParamList  = new ParameterList();
			// EvenlyGriddedSurface
			EvenlyGriddedSurface surface = null;
			//gets the faultName
			String fltName = (String)parameterList.getParameter(this.FAULT_NAME).getValue();
			//creates the fault trace data
			fltTrace = new FaultTrace(fltName);

			//Adding the fault Name to the independent Param List
			if(fltName !=null) //add only if the flt NAme is not equal to null
				independentParamList.addParameter(parameterList.getParameter(this.FAULT_NAME));

			//initializing the vectors for the lats, lons, depths and dips
			ArrayList lats = new ArrayList();
			ArrayList lons = new ArrayList();
			ArrayList depths = new ArrayList();
			ArrayList dips = new ArrayList();
			//getting the number of  fault trace
			int fltTracePoints = ((Integer)parameterList.getParameter(this.NUMBER_OF_FAULT_TRACE).getValue()).intValue();
			//getting the number of dips
			int numDips = ((Integer)numDipParam.getValue()).intValue();

			//adding the fault trace and num dip param to the independent param list
			independentParamList.addParameter(parameterList.getParameter(this.NUMBER_OF_FAULT_TRACE));
			independentParamList.addParameter(numDipParam);

			//adding the latitudes to the ArrayList
			for(int i=0;i<fltTracePoints;++i){
				Double latLocation =(Double)parameterListParameterForLats.getParameter().getParameter(this.LAT_PARAM_NAME+(i+1)).getValue();
				lats.add(latLocation);
			}

			//adding the longitudes to the ArrayList
			for(int i=0;i<fltTracePoints;++i){
				Double lonLocation =(Double)parameterListParameterForLons.getParameter().getParameter(this.LON_PARAM_NAME+(i+1)).getValue();
				lons.add(lonLocation);
			}

			//variable added to store the previous Depth (to make sure they're in ascending order)
			double prevDepth=((Double)parameterListParameterForDepths.getParameter().getParameter(this.DEPTH_PARAM_NAME+("1")).getValue()).doubleValue();

			//adding the depths(equal to numDips +1) to the ArrayList
			for(int i=0;i<=numDips;++i){
				Double depthLocation = (Double)parameterListParameterForDepths.getParameter().getParameter(this.DEPTH_PARAM_NAME+(i+1)).getValue();
				depths.add(depthLocation);
				//compares the depths, becuase depths should be entered in the increasing order
				if(depthLocation.doubleValue() < prevDepth)
					throw new RuntimeException("Depths should be entered in increasing order");
				prevDepth = depthLocation.doubleValue();
			}

			//adding the dips to the vector
			for(int i=0;i<numDips;++i){
				Double dipLocation = (Double)parameterListParameterForDips.getParameter().getParameter(this.DIP_PARAM_NAME+(i+1)).getValue();
				dips.add(dipLocation);
			}

			//adding the Lat,Lon,Depths and Dip param to the independent Param List
			independentParamList.addParameter(parameterListParameterForLats);
			independentParamList.addParameter(parameterListParameterForLons);
			independentParamList.addParameter(parameterListParameterForDepths);
			independentParamList.addParameter(parameterListParameterForDips);

			//adding the locations to the FaultTrace
			for(int i=0;i<fltTracePoints;++i){
				double lat = ((Double)lats.get(i)).doubleValue();
				double lon = ((Double)lons.get(i)).doubleValue();
				double depth = ((Double)depths.get(0)).doubleValue();
				Location loc = new Location(lat,lon,depth);
				fltTrace.add(loc);
			}
			//this.fltTrace = fltTrace;

			if(D)
				System.out.println("Fault-trace length (km) = "+fltTrace.getTraceLength());

			//getting the gridSpacing
			double gridSpacing = ((Double)this.parameterList.getParameter(this.GRID_SPACING).getValue()).doubleValue();

			//adding the gridSpacing param to the indendent Param List
			independentParamList.addParameter(parameterList.getParameter(this.GRID_SPACING));

			/**
			 * Checking for the number of Dips.
			 * If the number of dip is equal to 1 then give the option to the user
			 * to make the FaultType (Frankel or Stirling) parameter visible to the
			 * user. Else no choice is given to the user and make the object of the
			 * SimpleListricGriddedFaultFactory.
			 */
			if(numDips ==1){
				//gets the dip as the only value in the vector of dips
				double dip = ((Double)dips.get(0)).doubleValue();
				this.avgDip =dip;
				//gets the fault type
				String fltType = (String)this.faultTypeParam.getValue();
				//System.out.println("Fault-type: "+fltType);
				//gets the upperSiesDepth and LowerSiesDepth
				double upperSiesDepth =((Double)depths.get(0)).doubleValue();
				double lowerSiesDepth =((Double)depths.get(1)).doubleValue();
				upperSies = upperSiesDepth;
				lowerSies = lowerSiesDepth;
				//make the object of the FrankelGriddedSurface
				if(fltType.equalsIgnoreCase(this.FRANKEL)){
					surface = new FrankelGriddedSurface(fltTrace,dip,upperSiesDepth,lowerSiesDepth,gridSpacing);
				}
				//make the object for the Stirling gridded fault
				if(fltType.equalsIgnoreCase(this.STIRLING)){
					//checking to see if the Dip LocationVector Param value is null then assign default Double.NaN
					//else assign the dip direction value.
					Double aveDipDir = (Double)dipDirectionParam.getValue();
					if(aveDipDir == null)
						surface = new StirlingGriddedSurface(fltTrace,dip,upperSiesDepth,lowerSiesDepth,gridSpacing,Double.NaN);
					else
						surface = new StirlingGriddedSurface(fltTrace,dip,upperSiesDepth,lowerSiesDepth,gridSpacing,aveDipDir.doubleValue());
				}

				//adding the Fault type param to the independent param list
				independentParamList.addParameter(faultTypeParam);
			}
			else{
				//make the object for the simple Listric fault
				surface = new SimpleListricGriddedSurface(fltTrace,dips,depths,gridSpacing);
			}
			//gets the griddedsurface from the faultFactory and sets the Value for the
			//SimpleFaultParameter
			setValue(surface);

			if(D) {
				EvenlyGriddedSurface surf = surface;
				for(int i=0;i<surf.getNumCols();i++)
					for(int k=0;k<surf.getNumRows();k++)
						System.out.println(surf.getLocation(k,i).toString());
			}

			//saving the independent Param List inside SimpleFault parameter
			setIndependentParameters(independentParamList);
		}
	}

	/**
	 *
	 * @returns the fault trace
	 */
	public FaultTrace getFaultTrace(){
		return fltTrace;
	}

	/**
	 *
	 * @returns the Upper Siesmogenic depth
	 */
	public double getUpperSiesmogenicDepth(){
		return upperSies;
	}

	/**
	 *
	 * @returns the Lower Siesmogenic depth
	 */
	public double getLowerSiesmogenicDepth(){
		return lowerSies;
	}

	/**
	 * Sets the Num Fault Trace Points
	 * @param numPoints number of locations on the fault trace
	 */
	public void setNumFaultTracePoints(int numPoints){
		this.numFltTrace.setValue(new Integer(numPoints));
		this.initLatLonParamList();
	}

	/**
	 * Sets the Num Dips
	 * @param numDips
	 */
	public void setNumDips(int numDips){
		this.numDipParam.setValue(new Integer(numDips));
		this.initDipParamList();
		this.initDepthParamList();
	}

	/**
	 *
	 * @returns the name of the fault
	 */
	public String getFaultName(){
		return (String)parameterList.getParameter(this.FAULT_NAME).getValue();
	}

	/**
	 * Sets the Average Dip LocationVector for the evenly discritized fault.
	 * By Default its value is NaN and its value can only be set if one has
	 * selected the Fault type to be Stirling
	 */
	public void setDipDirection(double value){
		if(((String)faultTypeParam.getValue()).equals(STIRLING))
			dipDirectionParam.setValue(new Double(value));
	}



	/**
	 * This sets all the fault data needed to make a evenly discretized fault
	 * @param name : Name of the fault
	 * @param gridSpacing
	 * @param lats : ArrayList of Latitudes for the discretized fault
	 * @param lons : ArrayList of Longitudes for the discretized fault
	 * @param dips : ArrayList of Dips
	 * @param depths : ArrayList of Depths, which are one more then the number of dips
	 * @param faultType : STIRLING or FRANKEL fault
	 */
	public void setAll(String name, double gridSpacing, ArrayList lats, ArrayList lons,
			ArrayList dips, ArrayList depths, String faultType) {
		parameterList.getParameter(SimpleFaultParameter.FAULT_NAME).setValue(name);
		setAll(gridSpacing, lats, lons, dips, depths, faultType);
	}


	/**
	 * This sets all the fault data needed to make a evenly discretized fault
	 * @param gridSpacing
	 * @param lats : ArrayList of Latitudes for the discretized fault
	 * @param lons : ArrayList of Longitudes for the discretized fault
	 * @param dips : ArrayList of Dips
	 * @param depths : ArrayList of Depths, which are one more then the number of dips
	 * @param faultType : STIRLING or FRANKEL fault
	 */
	public void setAll(double gridSpacing, ArrayList lats, ArrayList lons,
			ArrayList dips, ArrayList depths, String faultType) {
		int numFltPts = lats.size();
		int numDips = dips.size();

		if (lats.size() != lons.size())
			throw new RuntimeException(C+".setAll(): lats and lons Vectors must be the same size");

		if (dips.size() != depths.size()-1)
			throw new RuntimeException(C+".setAll(): size of dips ArrayList must one less than the depths ArrayList");

		if (dips.size()>1 && faultType.equals(SimpleFaultParameter.FRANKEL))
			throw new RuntimeException(C+".setAll(): "+SimpleFaultParameter.FRANKEL+" fault type can't be used if dips.size() > 1");

		prevLats = lats;
		prevLons = lons;
		prevDepths = depths;
		prevDips = dips;
		parameterList.getParameter(SimpleFaultParameter.GRID_SPACING).setValue(new Double(gridSpacing));
		parameterList.getParameter(SimpleFaultParameter.NUMBER_OF_FAULT_TRACE).setValue(new Integer(numFltPts));
		numDipParam.setValue(new Integer(numDips));
		initLatLonParamList();
		
		// NOTE added during Peer Test build
		// parameterListParameterForDips/Depths were returning npe's. Why???
		// It seems that when inited from a gui, calls to the init functions
		// correctly made (at some point).
		initDipParamList();
		initDepthParamList();
		
		for(int i=0;i<numFltPts;++i) {
			parameterListParameterForLats.getParameter().getParameter(SimpleFaultParameter.LAT_PARAM_NAME+(i+1)).setValue(lats.get(i));
			parameterListParameterForLons.getParameter().getParameter(SimpleFaultParameter.LON_PARAM_NAME+(i+1)).setValue(lons.get(i));
		}

		for(int i=0;i<numDips;++i) 
			parameterListParameterForDips.getParameter().getParameter(SimpleFaultParameter.DIP_PARAM_NAME+(i+1)).setValue(dips.get(i));
		
		for(int i=0;i<numDips+1;++i)
			parameterListParameterForDepths.getParameter().getParameter(SimpleFaultParameter.DEPTH_PARAM_NAME+(i+1)).setValue(depths.get(i));

		faultTypeParam.setValue(faultType);
	}

	/**
	 *
	 * @returns the ArrayList containing the values for all the specified Latitudes
	 */
	public ArrayList getLatParamVals(){
		return prevLats;
	}

	/**
	 *
	 * @returns the ArrayList containing the values for all the specified Longitudes
	 */
	public ArrayList getLonParamVals(){
		return prevLons;
	}

	/**
	 *
	 * @returns the ArrayList containing the values for all the specified Dips
	 */
	public ArrayList getDipParamVals(){
		return prevDips;
	}

	/**
	 *
	 * @returns the ArrayList containing the values for all the specified Depths
	 */
	public ArrayList getDepthParamVals(){
		return prevDepths;
	}

	/**
	 * This overrides the getmetadataString() method because the value here
	 * does not have an ASCII representation (and we need to know the values
	 * of the independent parameter instead).
	 * @returns Sstring
	 */
	public String getMetadataString() {
		return getDependentParamMetadataString();
	}

	/**
	 * Returns the name of the parameter class
	 */
	public String getType() {
		String type = C;
		return type;
	}

	public boolean setIndividualParamValueFromXML(Element el) {
		// TODO Auto-generated method stub
		return false;
	}

	public ParameterEditor getEditor() {
		if (paramEdit == null)
			paramEdit = new SimpleFaultParameterEditor(this);
		return paramEdit;
	}
}

