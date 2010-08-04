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

package org.opensha.sha.gui.controls;

import java.awt.Component;
import java.awt.Dimension;
import java.awt.GridBagConstraints;
import java.awt.GridBagLayout;
import java.awt.Insets;
import java.awt.Window;
import java.util.ArrayList;
import java.util.StringTokenizer;

import javax.swing.JFrame;
import javax.swing.JOptionPane;

import org.opensha.commons.param.BooleanParameter;
import org.opensha.commons.param.DoubleParameter;
import org.opensha.commons.param.IntegerParameter;
import org.opensha.commons.param.ParameterAPI;
import org.opensha.commons.param.ParameterConstraintAPI;
import org.opensha.commons.param.ParameterList;
import org.opensha.commons.param.StringParameter;
import org.opensha.commons.param.editor.ParameterListEditor;
import org.opensha.commons.param.event.ParameterChangeEvent;
import org.opensha.commons.param.event.ParameterChangeFailEvent;
import org.opensha.commons.param.event.ParameterChangeFailListener;
import org.opensha.commons.param.event.ParameterChangeListener;
import org.opensha.sha.gui.HazardCurveServerModeApplication;


/**
 * <p>Title: DisaggregationControlPanel</p>
 * <p>Description: This is control panel in which user can choose whether
 * to choose disaggregation or not. In addition, prob. can be input by the user</p>
 * <p>Copyright: Copyright (c) 2002</p>
 * <p>Company: </p>
 * @author Nitin Gupta
 * @version 1.0
 */

public class DisaggregationControlPanel extends ControlPanel
implements ParameterChangeFailListener, ParameterChangeListener{

	public static final String NAME = "Disaggregation";

	private final static String DISAGGREGATION_PROB_PARAM_NAME = "Disaggregation Prob";
	private final static String DISAGGREGATION_IML_PARAM_NAME = "Disaggregation IML";


	//Disaggregation Parameter
	private DoubleParameter disaggregationProbParam =
		new DoubleParameter(DISAGGREGATION_PROB_PARAM_NAME, 0, 1, new Double(.01));

	private DoubleParameter disaggregationIMLParam =
		new DoubleParameter(DISAGGREGATION_IML_PARAM_NAME, 0, 11, new Double(.1));

	private StringParameter disaggregationParameter ;

	private final static String DISAGGREGATION_PARAM_NAME = "Diasaggregate";

	public final static String NO_DISAGGREGATION = "No Disaggregation";
	public final static String DISAGGREGATE_USING_PROB = "Probability";
	public final static String DISAGGREGATE_USING_IML = "IML";

	//Shows the source disaggregation only if this parameter is selected
	private final static String SOURCE_DISAGGR_PARAM_NAME = "Show Source Disaggregation List";
	private BooleanParameter sourceDisaggregationParam = new BooleanParameter
	(SOURCE_DISAGGR_PARAM_NAME,new Boolean(false));

	private final static String NUM_SOURCE_PARAM_NAME = "Num Sources in List";
	private IntegerParameter numSourcesToShow = new IntegerParameter(NUM_SOURCE_PARAM_NAME,new Integer(100));

	private final static String SHOW_DISTANCES_PARAM_NAME = "Include Source Distances";
	private BooleanParameter showDistancesParam = new BooleanParameter(SHOW_DISTANCES_PARAM_NAME, false);

	//show the bin data only if this parameter is selected
	private final static String SHOW_DISAGGR_BIN_RATE_PARAM_NAME = "Show Disaggregation Bin Rate Data";
	private BooleanParameter binRateDisaggregationParam = new BooleanParameter
	(SHOW_DISAGGR_BIN_RATE_PARAM_NAME,new Boolean(false));



	//sets the Mag Range for Disaggregation calculation
	private static final String MIN_MAG_PARAM_NAME = "Min Mag (bin center)";
	private static final String NUM_MAG_PARAM_NAME = "Num Mag";
	private static final String DELTA_MAG_PARAM_NAME = "Delta Mag";
	private DoubleParameter minMagParam = new DoubleParameter(MIN_MAG_PARAM_NAME,0,10,new Double(5));
	private IntegerParameter numMagParam = new IntegerParameter(NUM_MAG_PARAM_NAME,new Integer(10));
	private DoubleParameter deltaMagParam = new DoubleParameter(DELTA_MAG_PARAM_NAME,new Double(0.5));

	//sets the Dist range for Disaggregation calculation
	private static final String DIST_TYPE_PARAM_NAME = "Distance Binning Type";
	private static final String CUSTOM_DIST_PARAM_NAME = "Comma Separated Custom Bin Edges";
	private static final String CUSTOM_DIST_DEFAULT = "0,1,2,5,10,20,50,100,200";
	private StringParameter distBinTypeSelector = null;
	private StringParameter customDistBinParam = null;
	private static final String DIST_TYPE_EVEN = "Even";
	private static final String DIST_TYPE_CUSTOM = "Custom";
	private static final String MIN_DIST_PARAM_NAME = "Min Dist (bin center)";
	private static final String NUM_DIST_PARAM_NAME = "Num Dist";
	private static final String DELTA_DIST_PARAM_NAME = "Delta Dist";
	private DoubleParameter minDistParam = new DoubleParameter(MIN_DIST_PARAM_NAME,new Double(5));
	private IntegerParameter numDistParam = new IntegerParameter(NUM_DIST_PARAM_NAME,new Integer(11));
	private DoubleParameter deltaDistParam = new DoubleParameter(DELTA_DIST_PARAM_NAME,new Double(10));

	//If the manual range for the Z-Axis Max is selected, then user can set the value in this parameter 
	private static final String Z_AXIS_MAX_NAME = "Z-Axis Max";
	private static final String Z_AXIS_MAX_INFO ="Set the max value for the Z -Axis in percentage";
	private DoubleParameter zMaxParam = new DoubleParameter(Z_AXIS_MAX_NAME,0,100,new Double(50));

	//Parameter to allow to select if the Z-Axis max to be set manually or from data
	private StringParameter zMaxChoiceParam;
	private static final String Z_AXIS_MAX_CHOICE_NAME = "Set Z-Axis Max. from";
	private static final String Z_AXIS_MAX_CHOICE_INFO ="Allows to set the Z-Axis max either from data or manually";
	private static final String Z_AXIS_MAX_CHOICE_MANUALLY = "Manually";
	private static final String Z_AXIS_MAX_CHOICE_FROM_DATA = "From Data";



	private ParameterListEditor paramListEditor;

	private boolean isDisaggregationSelected;


	// applet which called this control panel
	HazardCurveServerModeApplication parent;
	private GridBagLayout gridBagLayout1 = new GridBagLayout();

	private JFrame frame;

	private Component parentComponent;

	public DisaggregationControlPanel(HazardCurveServerModeApplication parent,
			Component parentComponent) {
		super(NAME);
		this.parent = parent;
		this.parentComponent = parentComponent;
	}

	public void doinit() {
		frame = new JFrame();

		// set info strings for parameters
		minMagParam.setInfo("The center of the first magnitude bin (for histogram & mode calcs)");
		minDistParam.setInfo("The center of the first distance bin (for histogram & mode calcs)");

		numMagParam.setInfo("The number of magnitude bins (for histogram & mode calcs)");
		numDistParam.setInfo("The number of distance bins (for histogram & mode calcs)");

		deltaMagParam.setInfo("The width of magnitude bins (for histogram & mode calcs)");
		deltaDistParam.setInfo("The width of distance bins (for histogram & mode calcs)");

		sourceDisaggregationParam.setInfo("To show a list of sources in descending order"+
		" of their contribution to the hazard");

		numSourcesToShow.setInfo("The number of sources to show in the list");
		showDistancesParam.setInfo("Compute and display source distance metrics");

		zMaxParam.setInfo(Z_AXIS_MAX_INFO);


		try {

			this.parent= parent;

			ArrayList disaggregateList = new ArrayList();
			disaggregateList.add(NO_DISAGGREGATION);
			disaggregateList.add(DISAGGREGATE_USING_PROB);
			disaggregateList.add(DISAGGREGATE_USING_IML);

			disaggregationParameter = new StringParameter(DISAGGREGATION_PARAM_NAME,disaggregateList,
					(String)disaggregateList.get(0));


			disaggregationParameter.addParameterChangeListener(this);
			disaggregationProbParam.addParameterChangeFailListener(this);
			disaggregationIMLParam.addParameterChangeFailListener(this);
			sourceDisaggregationParam.addParameterChangeListener(this);

			ArrayList<String> distBinTypes = new ArrayList<String>();
			distBinTypes.add(DIST_TYPE_EVEN);
			distBinTypes.add(DIST_TYPE_CUSTOM);

			distBinTypeSelector = new StringParameter(DIST_TYPE_PARAM_NAME, distBinTypes);
			distBinTypeSelector.setValue(DIST_TYPE_EVEN);
			distBinTypeSelector.addParameterChangeListener(this);

			customDistBinParam = new StringParameter(CUSTOM_DIST_PARAM_NAME);
			customDistBinParam.setValue(CUSTOM_DIST_DEFAULT);

			ArrayList zAxisChoiceList = new ArrayList();
			zAxisChoiceList.add(Z_AXIS_MAX_CHOICE_FROM_DATA);
			zAxisChoiceList.add(Z_AXIS_MAX_CHOICE_MANUALLY);


			zMaxChoiceParam = new StringParameter(Z_AXIS_MAX_CHOICE_NAME,zAxisChoiceList,
					(String)zAxisChoiceList.get(0));
			zMaxChoiceParam.setInfo(Z_AXIS_MAX_CHOICE_INFO);
			zMaxChoiceParam.addParameterChangeListener(this);

			ParameterList paramList = new ParameterList();
			paramList.addParameter(disaggregationParameter);
			paramList.addParameter(disaggregationProbParam);
			paramList.addParameter(disaggregationIMLParam);
			paramList.addParameter(sourceDisaggregationParam);
			paramList.addParameter(numSourcesToShow);
			paramList.addParameter(showDistancesParam);
			paramList.addParameter(binRateDisaggregationParam);
			paramList.addParameter(minMagParam);
			paramList.addParameter(numMagParam);
			paramList.addParameter(deltaMagParam);
			paramList.addParameter(distBinTypeSelector);
			//      String distType = (String)distBinTypeSelector.getValue(); 
			//      if (distType.equals(DIST_TYPE_EVEN)) {
			paramList.addParameter(minDistParam);
			paramList.addParameter(numDistParam);
			paramList.addParameter(deltaDistParam);
			//      } else if (distType.equals(DIST_TYPE_CUSTOM)) {
			paramList.addParameter(customDistBinParam);
			//      }

			paramList.addParameter(zMaxChoiceParam);
			paramList.addParameter(zMaxParam);


			paramListEditor = new ParameterListEditor(paramList);
			setParamsVisible((String)disaggregationParameter.getValue());

			jbInit();
			// show the window at center of the parent component
			frame.setLocation(parentComponent.getX()+parentComponent.getWidth()/2,0);
			parent.setDisaggregationSelected(isDisaggregationSelected);


		}
		catch(Exception e) {
			e.printStackTrace();
		}
	}

	// initialize the gui components
	private void jbInit() throws Exception {

		frame.getContentPane().setLayout(gridBagLayout1);
		frame.getContentPane().add(paramListEditor,
				new GridBagConstraints(0, 0, 1, 1, 1.0, 1.0
						, GridBagConstraints.NORTH, GridBagConstraints.BOTH,
						new Insets(2, 2, 2, 2), 0, 0));
		frame.setTitle("Disaggregation Control Panel");
		paramListEditor.setTitle("Set Disaggregation Params");
		frame.setSize(300,200);
	}


	/**
	 *  Shown when a Constraint error is thrown on Disaggregation ParameterEditor
	 * @param  e  Description of the Parameter
	 */
	public void parameterChangeFailed( ParameterChangeFailEvent e ) {

		StringBuffer b = new StringBuffer();
		ParameterAPI param = ( ParameterAPI ) e.getSource();

		ParameterConstraintAPI constraint = param.getConstraint();
		String oldValueStr = e.getOldValue().toString();
		String badValueStr = e.getBadValue().toString();
		String name = param.getName();


		b.append( "The value ");
		b.append( badValueStr );
		b.append( " is not permitted for '");
		b.append( name );
		b.append( "'.\n" );
		b.append( "Resetting to ");
		b.append( oldValueStr );
		b.append( ". The constraints are: \n");
		b.append( constraint.toString() );

		JOptionPane.showMessageDialog(
				frame, b.toString(),
				"Cannot Change Value", JOptionPane.INFORMATION_MESSAGE
		);

	}

	/**
	 * shows the num sources to be shown for the disaggregation passed in
	 * argument is true.
	 * @param paramToShow boolean
	 */
	private void showNumSourcesParam(boolean paramToShow){
		paramListEditor.getParameterEditor(NUM_SOURCE_PARAM_NAME).setVisible(paramToShow);
		paramListEditor.getParameterEditor(SHOW_DISTANCES_PARAM_NAME).setVisible(paramToShow);
	}

	/**
	 * Makes ZAxisMax Parameter to be visible if Z-Max is specified manually
	 */
	private void showZMaxAxisParam(){
		String zAxisChoiceVal =  (String)this.zMaxChoiceParam.getValue();
		if(zAxisChoiceVal.equals(this.Z_AXIS_MAX_CHOICE_FROM_DATA))
			paramListEditor.getParameterEditor(this.Z_AXIS_MAX_NAME).setVisible(false);
		else
			paramListEditor.getParameterEditor(this.Z_AXIS_MAX_NAME).setVisible(true);
	}

	/**
	 * Makes ZAxisMax Parameter to be visible if Z-Max is specified manually
	 */
	private void setCustomBinning(boolean custom){
		paramListEditor.getParameterEditor(this.MIN_DIST_PARAM_NAME).setVisible(!custom);
		paramListEditor.getParameterEditor(this.NUM_DIST_PARAM_NAME).setVisible(!custom);
		paramListEditor.getParameterEditor(this.DELTA_DIST_PARAM_NAME).setVisible(!custom);
		paramListEditor.getParameterEditor(this.CUSTOM_DIST_PARAM_NAME).setVisible(custom);

	}

	/**
	 *
	 * @param e ParameterChangeEvent
	 */
	public void parameterChange (ParameterChangeEvent e){
		String paramName = e.getParameterName();
		if(paramName.equals(DISAGGREGATION_PARAM_NAME))
			setParamsVisible((String)disaggregationParameter.getValue());
		else if(paramName.equals(SOURCE_DISAGGR_PARAM_NAME))
			showNumSourcesParam(((Boolean)sourceDisaggregationParam.getValue()).booleanValue());
		else if(paramName.equals(this.Z_AXIS_MAX_CHOICE_NAME)){
			showZMaxAxisParam();
		} else if(paramName.equals(this.DIST_TYPE_PARAM_NAME)){
			String distType = (String)distBinTypeSelector.getValue(); 
			if (distType.equals(DIST_TYPE_EVEN)) {
				setCustomBinning(false);
			} else if (distType.equals(DIST_TYPE_CUSTOM)) {
				setCustomBinning(true);
			}
		} 

	}


	/**
	 * Returns the mininum Magnitude
	 * @return double
	 */
	public double getMinMag(){
		return ((Double)minMagParam.getValue()).doubleValue();
	}

	/**
	 * Returns the number of magnitude intervals
	 * @return double
	 */
	public int getNumMag(){
		return ((Integer)numMagParam.getValue()).intValue();
	}

	/**
	 * Returns the Mag range Discritization. It is evenly discretized.
	 * @return double
	 */
	public double getdeltaMag(){
		return ((Double)deltaMagParam.getValue()).doubleValue();
	}

	/**
	 * Returns the minimum Distance
	 * @return double
	 */
	public double getMinDist(){
		return ((Double)minDistParam.getValue()).doubleValue();
	}

	/**
	 * Returns the number of Distance intervals
	 * @return double
	 */
	public int getNumDist(){
		return ((Integer)numDistParam.getValue()).intValue();
	}

	/**
	 * Returns the Distance range Discritization. It is evenly discretized.
	 * @return double
	 */
	public double getdeltaDist(){
		return ((Double)deltaDistParam.getValue()).doubleValue();
	}


	/**
	 * Returns the Z Axis max if parameter visible
	 * @return
	 */
	public double getZAxisMax(){
		boolean isVisible = paramListEditor.getParameterEditor(this.Z_AXIS_MAX_NAME).isVisible();
		if(isVisible)
			return ((Double)this.zMaxParam.getValue()).doubleValue();
		return Double.NaN;  
	}

	/**
	 * Makes the parameters visible based on the choice of the user for Disaggregation
	 */
	private void setParamsVisible(String paramValue){
		if(paramValue.equals(NO_DISAGGREGATION)){
			paramListEditor.getParameterEditor(DISAGGREGATION_PROB_PARAM_NAME).
			setVisible(false);
			paramListEditor.getParameterEditor(DISAGGREGATION_IML_PARAM_NAME).
			setVisible(false);
			isDisaggregationSelected = false;
			paramListEditor.getParameterEditor(MIN_MAG_PARAM_NAME).setVisible(false);
			paramListEditor.getParameterEditor(NUM_MAG_PARAM_NAME).setVisible(false);
			paramListEditor.getParameterEditor(DELTA_MAG_PARAM_NAME).setVisible(false);
			paramListEditor.getParameterEditor(MIN_DIST_PARAM_NAME).setVisible(false);
			paramListEditor.getParameterEditor(NUM_DIST_PARAM_NAME).setVisible(false);
			paramListEditor.getParameterEditor(DELTA_DIST_PARAM_NAME).setVisible(false);
			paramListEditor.getParameterEditor(SOURCE_DISAGGR_PARAM_NAME).setVisible(false);
			paramListEditor.getParameterEditor(SHOW_DISAGGR_BIN_RATE_PARAM_NAME).setVisible(false);
			paramListEditor.getParameterEditor(DIST_TYPE_PARAM_NAME).setVisible(false);
			paramListEditor.getParameterEditor(CUSTOM_DIST_PARAM_NAME).setVisible(false);
			paramListEditor.getParameterEditor(Z_AXIS_MAX_CHOICE_NAME).setVisible(false);
			showNumSourcesParam(false);
			paramListEditor.getParameterEditor(this.Z_AXIS_MAX_NAME).setVisible(false);

			frame.setSize(300,200);
		}
		else{
			if (paramValue.equals(DISAGGREGATE_USING_PROB)) {
				paramListEditor.getParameterEditor(DISAGGREGATION_PROB_PARAM_NAME).
				setVisible(true);
				paramListEditor.getParameterEditor(DISAGGREGATION_IML_PARAM_NAME).
				setVisible(false);
				isDisaggregationSelected = true;
			}
			else if (paramValue.equals(DISAGGREGATE_USING_IML)) {
				paramListEditor.getParameterEditor(DISAGGREGATION_PROB_PARAM_NAME).
				setVisible(false);
				paramListEditor.getParameterEditor(DISAGGREGATION_IML_PARAM_NAME).
				setVisible(true);
				isDisaggregationSelected = true;
			}
			paramListEditor.getParameterEditor(MIN_MAG_PARAM_NAME).setVisible(true);
			paramListEditor.getParameterEditor(NUM_MAG_PARAM_NAME).setVisible(true);
			paramListEditor.getParameterEditor(DELTA_MAG_PARAM_NAME).setVisible(true);
			paramListEditor.getParameterEditor(MIN_DIST_PARAM_NAME).setVisible(true);
			paramListEditor.getParameterEditor(NUM_DIST_PARAM_NAME).setVisible(true);
			paramListEditor.getParameterEditor(DELTA_DIST_PARAM_NAME).setVisible(true);
			paramListEditor.getParameterEditor(SOURCE_DISAGGR_PARAM_NAME).setVisible(true);
			paramListEditor.getParameterEditor(SHOW_DISAGGR_BIN_RATE_PARAM_NAME).setVisible(true);
			paramListEditor.getParameterEditor(DIST_TYPE_PARAM_NAME).setVisible(true);
			String distType = (String)distBinTypeSelector.getValue(); 
			setCustomBinning(distType.equals(DIST_TYPE_CUSTOM));
			paramListEditor.getParameterEditor(Z_AXIS_MAX_CHOICE_NAME).setVisible(true);
			this.showZMaxAxisParam();
			showNumSourcesParam(((Boolean)sourceDisaggregationParam.getValue()).booleanValue());
			Dimension curDims = frame.getSize();
			int width = 300;
			int height = 500;
			if (curDims.width > width)
				width = curDims.width;
			if (curDims.height > height)
				height = curDims.height;
			frame.setSize(width,height);
		}
		frame.repaint();
		frame.validate();
		parent.setDisaggregationSelected(isDisaggregationSelected);
	}


	/**
	 *
	 * @return String : Returns on wht basis Diaggregation is being done either
	 * using Probability or IML.
	 */
	public String getDisaggregationParamValue(){
		return (String)disaggregationParameter.getValue();
	}


	/**
	 * This function returns disaggregation prob value if disaggregation to be done
	 * based on Probability else it returns IML value if disaggregation to be done
	 * based on IML. If not disaggregation to be done , return -1.
	 */
	public double getDisaggregationVal() {

		if(isDisaggregationSelected){
			String paramValue = getDisaggregationParamValue();
			if(paramValue.equals(DISAGGREGATE_USING_PROB))
				return ( (Double) disaggregationProbParam.getValue()).doubleValue();
			else if(paramValue.equals(DISAGGREGATE_USING_IML))
				return ( (Double) disaggregationIMLParam.getValue()).doubleValue();
		}
		return -1;
	}

	/**
	 * Checks if Source Disaggregation needs to be calculated and shown in the window.
	 * @return boolean
	 */
	public boolean isSourceDisaggregationSelected(){
		if(isDisaggregationSelected)
			return ((Boolean)sourceDisaggregationParam.getValue()).booleanValue();
		return false;
	}

	/**
	 * Returns the number of sources to show in Disaggregation.
	 * @return int
	 */
	public int getNumSourcesForDisagg(){
		if(isDisaggregationSelected && isSourceDisaggregationSelected())
			return ((Integer)numSourcesToShow.getValue()).intValue();
		return 0;
	}
	
	public boolean isShowSourceDistances() {
		return showDistancesParam.getValue();
	}

	/**
	 * Returns if Disaggregation Bin Rate Data is to be selected
	 * @return boolean
	 */
	public boolean isShowDisaggrBinDataSelected(){
		return ((Boolean)binRateDisaggregationParam.getValue()).booleanValue();
	}

	/**
	 * Returns true if custom distance binning is selected
	 * @return
	 */
	public boolean isCustomDistBinning() {
		String distType = (String)distBinTypeSelector.getValue(); 
		return distType.equals(DIST_TYPE_CUSTOM);
	}

	public double[] getCustomBinEdges() {
		String edgesStr = (String)customDistBinParam.getValue();

		StringTokenizer tok = new StringTokenizer(edgesStr, ", ;");

		ArrayList<Double> edgesList = new ArrayList<Double>();

		while (tok.hasMoreTokens()) {
			String tokStr = tok.nextToken();
			try {
				double val = Double.parseDouble(tokStr);
				edgesList.add(val);
			} catch (NumberFormatException e) {
				System.err.println("Bin Edge '" + tokStr + "' is not a number!");
			}
		}

		double edges[] = new double[edgesList.size()];

		for (int i=0; i<edgesList.size(); i++) {
			edges[i] = edgesList.get(i);
		}

		return edges;
	}

	@Override
	public Window getComponent() {
		return frame;
	}
}
