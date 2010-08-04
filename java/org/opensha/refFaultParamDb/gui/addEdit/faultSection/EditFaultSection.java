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

package org.opensha.refFaultParamDb.gui.addEdit.faultSection;

import java.awt.BorderLayout;
import java.awt.GridBagConstraints;
import java.awt.GridBagLayout;
import java.awt.Insets;
import java.awt.event.ActionEvent;
import java.awt.event.ActionListener;
import java.util.ArrayList;
import java.util.StringTokenizer;

import javax.swing.JButton;
import javax.swing.JFrame;
import javax.swing.JOptionPane;
import javax.swing.JPanel;
import javax.swing.JScrollPane;
import javax.swing.JSplitPane;
import javax.swing.JTextArea;

import org.opensha.commons.data.estimate.Estimate;
import org.opensha.commons.geo.Location;
import org.opensha.commons.param.DoubleParameter;
import org.opensha.commons.param.StringParameter;
import org.opensha.commons.param.editor.ConstrainedDoubleParameterEditor;
import org.opensha.commons.param.editor.ConstrainedStringParameterEditor;
import org.opensha.commons.param.editor.StringParameterEditor;
import org.opensha.commons.param.editor.estimate.ConstrainedEstimateParameterEditor;
import org.opensha.commons.param.estimate.EstimateConstraint;
import org.opensha.commons.param.estimate.EstimateParameter;
import org.opensha.commons.param.event.ParameterChangeEvent;
import org.opensha.commons.param.event.ParameterChangeListener;
import org.opensha.refFaultParamDb.dao.db.DB_AccessAPI;
import org.opensha.refFaultParamDb.dao.db.DB_ConnectionPool;
import org.opensha.refFaultParamDb.dao.db.FaultSectionVer2_DB_DAO;
import org.opensha.refFaultParamDb.dao.db.SectionSourceDB_DAO;
import org.opensha.refFaultParamDb.gui.CommentsParameterEditor;
import org.opensha.refFaultParamDb.gui.view.ViewFaultSection;
import org.opensha.refFaultParamDb.vo.EstimateInstances;
import org.opensha.refFaultParamDb.vo.FaultSectionData;
import org.opensha.refFaultParamDb.vo.SectionSource;
import org.opensha.sha.faultSurface.FaultTrace;

/**
 * <p>Title: EditFaultSection.java </p>
 *
 * <p>Description: This GUI allows the user to edit a fault section. </p>
 *
 * <p>Copyright: Copyright (c) 2002</p>
 *
 * <p>Company: </p>
 *
 * @author not attributable
 * @version 1.0
 */
public class EditFaultSection extends JFrame implements ActionListener, ParameterChangeListener {
	private JPanel mainPanel = new JPanel();
	private JSplitPane topSplitPane = new JSplitPane();
	private  JSplitPane innerSplitPane = new JSplitPane();
	private JButton cancelButton = new JButton();
	private JButton okButton = new JButton();
	private JPanel leftPanel = new JPanel();
	private JPanel rightPanel = new JPanel();
	private JPanel centerPanel = new JPanel();
	private GridBagLayout gridBagLayout1 = new GridBagLayout();
	private BorderLayout borderLayout1 = new BorderLayout();

	// units for various paramaters
	private final static String DIP_UNITS = "degrees";
	private final static String SLIP_RATE_UNITS = "mm/yr";
	private final static String DEPTH_UNITS = "km";
	private final static String RAKE_UNITS = "degrees";
	private final static String ASEISMIC_SLIP_FACTOR_UNITS = "";

	// fault section name
	private final static String FAULT_SECTION_PARAM_NAME = "Fault Section";
	private StringParameter faultSectionNameParam;
	// source
	private final static String SOURCE = "Source";
	private StringParameter sectionSourceParam;

	// long term slip rate estimate
	private final static String  AVE_LONG_TERM_SLIP_RATE= "Ave Long Term Slip Rate";
	private EstimateParameter avgLongTermSlipRateEstParam;
	private ConstrainedEstimateParameterEditor avgLongTermSlipRateEstParamEditor;
	private final static double SLIP_RATE_MIN = Double.NEGATIVE_INFINITY;
	private final static double SLIP_RATE_MAX = Double.POSITIVE_INFINITY;
	private final static String SLIP_RATE_TYPE_PARAM_NAME = "Slip Rate Type";
	private StringParameter slipRateTypeParam;
	private ConstrainedStringParameterEditor slipRateTypeParamEditor;

	// Ave dip estimate
	private final static String  DIP= "Ave Dip";
	private EstimateParameter aveDipEstParam;
	private ConstrainedEstimateParameterEditor aveDipEstParamEditor;
	private final static double DIP_MIN = Double.NEGATIVE_INFINITY;
	private final static double DIP_MAX = Double.POSITIVE_INFINITY;
	// dip direction
	private final static String  DIP_DIRECTION= "Dip LocationVector";
	private DoubleParameter dipDirectionParam;
	private final static double MIN_DIP_DIRECTION = 0;
	private final static double MAX_DIP_DIRECTION = 360;
	// ave rake estimate
	private final static String  RAKE= "Ave Rake";
	private EstimateParameter aveRakeEstParam;
	private ConstrainedEstimateParameterEditor aveRakeEstParamEditor;
	private final static double RAKE_MIN = Double.NEGATIVE_INFINITY;
	private final static double RAKE_MAX = Double.POSITIVE_INFINITY;
	private final static String RAKE_TYPE_PARAM_NAME = "Rake Type";
	private StringParameter rakeTypeParam;
	private ConstrainedStringParameterEditor rakeTypeParamEditor;

	// upper seis depth estimate
	private final static String  UPPER_DEPTH= "Upper Seis Depth";
	private EstimateParameter upperDepthEstParam;
	private ConstrainedEstimateParameterEditor upperDepthEstParamEditor;
	private final static double UPPER_DEPTH_MIN = Double.NEGATIVE_INFINITY;
	private final static double UPPER_DEPTH_MAX = Double.POSITIVE_INFINITY;
	// lower seis depth estimate
	private final static String  LOWER_DEPTH= "Lower Seis Depth";
	private EstimateParameter lowerDepthEstParam;
	private ConstrainedEstimateParameterEditor lowerDepthEstParamEditor;
	private final static double LOWER_DEPTH_MIN = Double.NEGATIVE_INFINITY;
	private final static double LOWER_DEPTH_MAX = Double.POSITIVE_INFINITY;
	// aseismic slip estimate
	private final static String  ASEISMIC_SLIP= "Aseismic Slip Factor";
	private EstimateParameter aseimsicSlipEstParam;
	private ConstrainedEstimateParameterEditor aseimsicSlipEstParamEditor;
	private final static double ASEISMIC_SLIP_FACTOR_MIN=0;
	private final static double ASEISMIC_SLIP_FACTOR_MAX=1;

	// Fault Trace
	private JTextArea faultTraceArea;

	// Qfault Id
	private final static String QFAULT_ID = "QFault_Id";
	private StringParameter qFaultIdParam;

	// short name
	private final static String SHORT_NAME = "Short_Name";
	private StringParameter shortNameParam;

	// comments
	private final static String  COMMENTS= "COMMENTS";
	private StringParameter commentsParam;
	private FaultSectionData selectedFaultSection;
	private final static String TITLE = "Edit Fault Section";
	private final static String MSG_FAULT_TRACE_FORMAT = "Fault Trace should be specified with a lon-lat pair\n"+
	"on each line separated by comma";
	private final static String MSG_UPDATE_SUCCESS = "Fault Section updated successfully in the database";
	private final static String MSG_ADD_SUCCESS = "Fault Section added succesfully to the database";
	private final static String KNOWN = "Known";
	private final static String UNKNOWN = "Unknown";
	private ViewFaultSection viewFaultSection;
	private boolean isEdit = false;

	private DB_AccessAPI dbConnection;

	public EditFaultSection(DB_AccessAPI dbConnection, FaultSectionData faultSection, ViewFaultSection viewFaultSection) {
		this.dbConnection = dbConnection;
		try {
			if(faultSection!=null) { // edit the fault section
				this.selectedFaultSection = faultSection;
				this.isEdit = true;
			} else { // adda a new fault section
				selectedFaultSection = new FaultSectionData();
				this.isEdit = false;
			}
			this.viewFaultSection = viewFaultSection;
			// initialize GUI Components
			jbInit();
			// make parameter editors
			this.initParamsAndEditors();
			// set rake and slip rate visibility
			this.setRakeVisibility();
			this.setSlipRateVisibility();

			okButton.addActionListener(this);
			cancelButton.addActionListener(this);
			setTitle(TITLE);
			this.setSize(600, 800);
			this.show();
		}
		catch (Exception exception) {
			exception.printStackTrace();
		}
	}


	/**
	 * Make GUI components 
	 * 
	 * @throws Exception
	 */
	private void jbInit() throws Exception {
		getContentPane().setLayout(borderLayout1);
		mainPanel.setLayout(gridBagLayout1);
		cancelButton.setText("Cancel");
		okButton.setText("Update");
		leftPanel.setLayout(gridBagLayout1);
		centerPanel.setLayout(gridBagLayout1);
		rightPanel.setLayout(gridBagLayout1);
		topSplitPane.add(innerSplitPane, JSplitPane.LEFT);
		topSplitPane.add(new JScrollPane(rightPanel), JSplitPane.RIGHT);
		innerSplitPane.add(new JScrollPane(leftPanel), JSplitPane.LEFT);
		innerSplitPane.add(new JScrollPane(centerPanel), JSplitPane.RIGHT);
		mainPanel.add(topSplitPane, new GridBagConstraints(0, 0, 1, 1, 1.0, 1.0
				, GridBagConstraints.CENTER, GridBagConstraints.BOTH,
				new Insets(4, 4, 0, 3), 0, 0));
		mainPanel.add(getButtonPanel(), new GridBagConstraints(0, 1, 1, 1, 1.0, 0.0
				, GridBagConstraints.CENTER, GridBagConstraints.NONE,
				new Insets(0, 0, 0, 0), 0, 0));
		this.getContentPane().add(mainPanel, java.awt.BorderLayout.CENTER);
		topSplitPane.setDividerLocation(400);
		innerSplitPane.setDividerLocation(200);

	}


	private JPanel getButtonPanel() {
		JPanel panel = new JPanel(new GridBagLayout());
		panel.add(okButton, new GridBagConstraints(1, 0, 1, 1, 0.0, 0.0
				, GridBagConstraints.WEST, GridBagConstraints.NONE,
				new Insets(0, 0, 0, 0), 0, 0));
		panel.add(cancelButton, new GridBagConstraints(0, 0, 1, 1, 0.0, 0.0
				, GridBagConstraints.EAST, GridBagConstraints.NONE,
				new Insets(0, 0 , 0, 0), 0, 0));
		return panel;
	}

	// make parameter editors and estimate editors
	private void initParamsAndEditors() throws Exception {

		// fault section param editor
		faultSectionNameParam  = new StringParameter(FAULT_SECTION_PARAM_NAME, selectedFaultSection.getSectionName());
		StringParameterEditor faultSectionNameParamEditor = new StringParameterEditor(faultSectionNameParam);
		leftPanel.add(faultSectionNameParamEditor, new GridBagConstraints(0, 0, 1, 1, 1.0, 1.0
				, GridBagConstraints.CENTER, GridBagConstraints.HORIZONTAL,
				new Insets(0, 0, 0, 0), 0, 0));

		// short name
		String shortName = this.selectedFaultSection.getShortName();
		if(shortName==null) shortName="";
		shortNameParam = new StringParameter(SHORT_NAME, shortName);
		StringParameterEditor shortNameParamEditor = new StringParameterEditor(shortNameParam);
		leftPanel.add(shortNameParamEditor, new GridBagConstraints(0, 1, 1, 1, 1.0, 1.0
				, GridBagConstraints.CENTER, GridBagConstraints.HORIZONTAL,
				new Insets(0, 0, 0, 0), 0, 0));

		// fault section sources
		SectionSourceDB_DAO sectionSourceDB_DAO = new SectionSourceDB_DAO(dbConnection);
		ArrayList sectionSourcesList = sectionSourceDB_DAO.getAllSectionSource();
		ArrayList sectionSourceNamesList = new ArrayList();
		for(int i=0; i<sectionSourcesList.size(); ++i)
			sectionSourceNamesList.add(((SectionSource)sectionSourcesList.get(i)).getSectionSourceName());
		sectionSourceParam = new StringParameter(SOURCE, sectionSourceNamesList, (String)sectionSourceNamesList.get(0));
		ConstrainedStringParameterEditor sectionSourceParamEditor = new ConstrainedStringParameterEditor(sectionSourceParam);
		leftPanel.add(sectionSourceParamEditor, new GridBagConstraints(0, 2, 1, 1, 1.0, 1.0
				, GridBagConstraints.CENTER, GridBagConstraints.HORIZONTAL,
				new Insets(0, 0, 0, 0), 0, 0));

		// qfault param
		String qfaultId = this.selectedFaultSection.getQFaultId();
		if(qfaultId==null) qfaultId="";
		qFaultIdParam = new StringParameter(QFAULT_ID, qfaultId);
		StringParameterEditor qFaultIdParamEditor = new StringParameterEditor(qFaultIdParam);
		leftPanel.add(qFaultIdParamEditor, new GridBagConstraints(0, 3, 1, 1, 1.0, 1.0
				, GridBagConstraints.CENTER, GridBagConstraints.HORIZONTAL,
				new Insets(0, 0, 0, 0), 0, 0));

		// dip LocationVector
		float dipDirection = this.selectedFaultSection.getDipDirection();
		Double val;
		if(Double.isNaN(dipDirection)) val = null;
		else val = new Double(dipDirection);
		dipDirectionParam = new DoubleParameter(DIP_DIRECTION, MIN_DIP_DIRECTION, MAX_DIP_DIRECTION, val);
		dipDirectionParam.getConstraint().setNullAllowed(true);
		ConstrainedDoubleParameterEditor dipDirectionParamEditor = new ConstrainedDoubleParameterEditor(dipDirectionParam);
		this.leftPanel.add(dipDirectionParamEditor, new GridBagConstraints(0, 4, 1, 1, 1.0, 1.0
				, GridBagConstraints.CENTER, GridBagConstraints.HORIZONTAL,
				new Insets(0, 0, 0, 0), 0, 0));

		// comments param
		commentsParam = new StringParameter(COMMENTS, selectedFaultSection.getComments());
		CommentsParameterEditor commentsParamEditor = new CommentsParameterEditor(commentsParam);
		leftPanel.add(commentsParamEditor, new GridBagConstraints(0, 5, 1, 1, 1.0, 1.0
				, GridBagConstraints.CENTER, GridBagConstraints.HORIZONTAL,
				new Insets(0, 0, 0, 0), 0, 0));

		// make fault trace param
		makeFaultTraceParamAndEditor();
		leftPanel.add(new JScrollPane(this.faultTraceArea), new GridBagConstraints(0, 6, 1, 1, 1.0, 1.0
				, GridBagConstraints.CENTER, GridBagConstraints.BOTH,
				new Insets(0, 0, 0, 0), 0, 0));



		ArrayList allowedEstimates = EstimateConstraint.createConstraintForPositiveDoubleValues();

		//	 upper depth param
		makeUpperDepthParamAndEditor(allowedEstimates);
		this.centerPanel.add(this.upperDepthEstParamEditor, new GridBagConstraints(0, 0, 1, 1, 1.0, 1.0
				, GridBagConstraints.CENTER, GridBagConstraints.BOTH,
				new Insets(0, 0, 0, 0), 0, 0));

		// lower depth param
		makeLowerDepthParamAndEditor(allowedEstimates);
		this.centerPanel.add(this.lowerDepthEstParamEditor, new GridBagConstraints(0, 1, 1, 1, 1.0, 1.0
				, GridBagConstraints.CENTER, GridBagConstraints.BOTH,
				new Insets(0, 0, 0, 0), 0, 0));

		// dip estimate param
		makeAveDipParamAndEditor(allowedEstimates);
		this.centerPanel.add(this.aveDipEstParamEditor, new GridBagConstraints(0, 2, 1, 1, 1.0, 1.0
				, GridBagConstraints.CENTER, GridBagConstraints.BOTH,
				new Insets(0, 0, 0, 0), 0, 0));



		// long term slip rate param
		makeSlipRateParamAndEditor(allowedEstimates);
		rightPanel.add(this.slipRateTypeParamEditor, new GridBagConstraints(0, 0, 1, 1, 1.0, 1.0
				, GridBagConstraints.CENTER, GridBagConstraints.HORIZONTAL,
				new Insets(0, 0, 0, 0), 0, 0));
		this.rightPanel.add(this.avgLongTermSlipRateEstParamEditor, new GridBagConstraints(0, 1, 1, 1, 1.0, 1.0
				, GridBagConstraints.CENTER, GridBagConstraints.BOTH,
				new Insets(0, 0, 0, 0), 0, 0));

		// ave rake param
		makeAveRakeParamAndEditor(allowedEstimates);
		rightPanel.add(this.rakeTypeParamEditor, new GridBagConstraints(0, 2, 1, 1, 1.0, 1.0
				, GridBagConstraints.CENTER, GridBagConstraints.HORIZONTAL,
				new Insets(0, 0, 0, 0), 0, 0));
		this.rightPanel.add(this.aveRakeEstParamEditor, new GridBagConstraints(0, 3, 1, 1, 1.0, 1.0
				, GridBagConstraints.CENTER, GridBagConstraints.BOTH,
				new Insets(0, 0, 0, 0), 0, 0));

		// aseismic slip estimate
		makeAseismicSlipParamAndEditor(allowedEstimates);
		this.rightPanel.add(this.aseimsicSlipEstParamEditor, new GridBagConstraints(0, 4, 1, 1, 1.0, 1.0
				, GridBagConstraints.CENTER, GridBagConstraints.BOTH,
				new Insets(0, 0, 0, 0), 0, 0));

	}

	public void actionPerformed(ActionEvent event) {
		Object source = event.getSource();
		if(source == this.okButton) { // update the fault section
			try {
				// set the parameters in the fault section object
				setParamsInSelectedFaultSection();
				// update in the database
				FaultSectionVer2_DB_DAO faultSectionDAO = new FaultSectionVer2_DB_DAO(dbConnection);
				if(this.isEdit) {  // edit fault section
					faultSectionDAO.update(this.selectedFaultSection);
					viewFaultSection.refreshFaultSectionValues();
					// show success message
					JOptionPane.showMessageDialog(this, MSG_UPDATE_SUCCESS);
				} else { // add a fault section
					faultSectionDAO.addFaultSection(selectedFaultSection);
					// show success message
					JOptionPane.showMessageDialog(this, MSG_ADD_SUCCESS);
					viewFaultSection.makeFaultSectionNamesEditor();
				}
				this.dispose();
			}catch(Exception e){
				JOptionPane.showMessageDialog(this, e.getMessage());
			}
		} else if(source==this.cancelButton) { // if cancel button is clicked, close this window
			this.dispose();

		}
	}

	private void setParamsInSelectedFaultSection() {
		// section name
		selectedFaultSection.setSectionName((String)this.faultSectionNameParam.getValue());
		// section source (2002, CFM, new)
		this.selectedFaultSection.setSource((String)sectionSourceParam.getValue());
		// slip rate
		if(((String)slipRateTypeParam.getValue()).equalsIgnoreCase(KNOWN)) {
			avgLongTermSlipRateEstParamEditor.setEstimateInParameter();
			selectedFaultSection.setAveLongTermSlipRateEst(new EstimateInstances((Estimate)avgLongTermSlipRateEstParam.getValue(), SLIP_RATE_UNITS));
		} else selectedFaultSection.setAveLongTermSlipRateEst(null);
		// rake
		if(((String)rakeTypeParam.getValue()).equalsIgnoreCase(KNOWN)) {
			aveRakeEstParamEditor.setEstimateInParameter();
			selectedFaultSection.setAveRakeEst(new EstimateInstances((Estimate)aveRakeEstParam.getValue(), RAKE_UNITS));
		}else selectedFaultSection.setAveRakeEst(null);
		// dip
		aveDipEstParamEditor.setEstimateInParameter();
		selectedFaultSection.setAveDipEst(new EstimateInstances((Estimate)this.aveDipEstParam.getValue(), DIP_UNITS));
		// upper seis depth
		this.upperDepthEstParamEditor.setEstimateInParameter();
		selectedFaultSection.setAveUpperDepthEst(new EstimateInstances((Estimate)this.upperDepthEstParam.getValue(), DEPTH_UNITS));
		// lower seis depth
		this.lowerDepthEstParamEditor.setEstimateInParameter();
		selectedFaultSection.setAveLowerDepthEst(new EstimateInstances((Estimate)this.lowerDepthEstParam.getValue(), DEPTH_UNITS));
		// aseismic slip 
		this.aseimsicSlipEstParamEditor.setEstimateInParameter();
		selectedFaultSection.setAseismicSlipFactorEst(new EstimateInstances((Estimate)this.aseimsicSlipEstParam.getValue(), ASEISMIC_SLIP_FACTOR_UNITS));
		// comments
		selectedFaultSection.setComments((String)this.commentsParam.getValue());
		// qfault Id
		String qFaultId = (String)this.qFaultIdParam.getValue();
		if(qFaultId.trim().equalsIgnoreCase("")) qFaultId=null;
		selectedFaultSection.setQFaultId(qFaultId);
		// short name
		String shortName = (String)this.shortNameParam.getValue();
		if(shortName.trim().equalsIgnoreCase("")) shortName = null;
		selectedFaultSection.setShortName(shortName);

		// dip direction
		Double dipDirectionVal = ((Double)dipDirectionParam.getValue());
		float dipDirection;
		if(dipDirectionVal==null) dipDirection=Float.NaN;
		else dipDirection = dipDirectionVal.floatValue();
		//System.out.println("Dip LocationVector="+dipDirection);
		selectedFaultSection.setDipDirection(dipDirection);
		//fault trace
		selectedFaultSection.setFaultTrace(getFaultTrace());
	}

	/**
	 * Obtain fault trace from text area
	 * @return
	 */
	private  FaultTrace getFaultTrace() {
		FaultTrace faultTrace = new FaultTrace(this.selectedFaultSection.getSectionName());
		String traceString = this.faultTraceArea.getText();
		try {	
			StringTokenizer tokenizer = new StringTokenizer(traceString,"\n");
			double lon, lat;
			while(tokenizer.hasMoreTokens()) {
				String line = tokenizer.nextToken();
				if(line.trim().equalsIgnoreCase("")) continue;
				StringTokenizer lineTokenizer = new StringTokenizer(line,",");
				lon = Double.parseDouble(lineTokenizer.nextToken().trim());
				lat = Double.parseDouble(lineTokenizer.nextToken().trim());
				faultTrace.add(new Location(lat,lon));
			}
		}catch(Exception e) {
			throw new RuntimeException(MSG_FAULT_TRACE_FORMAT);
		}
		return faultTrace;
	}

	/**
	 * Long term slip rate param and editor
	 * @param allowedEstimates
	 */
	private void makeSlipRateParamAndEditor(ArrayList allowedEstimates) {
		EstimateConstraint slipEstConstraint = new EstimateConstraint(SLIP_RATE_MIN, SLIP_RATE_MAX, allowedEstimates);
		Estimate slipRateEst = null; 
		if(this.selectedFaultSection.getAveLongTermSlipRateEst()!=null)
			slipRateEst = selectedFaultSection.getAveLongTermSlipRateEst().getEstimate();
		avgLongTermSlipRateEstParam = new EstimateParameter(AVE_LONG_TERM_SLIP_RATE, slipEstConstraint,
				SLIP_RATE_UNITS, slipRateEst);
		avgLongTermSlipRateEstParamEditor= new ConstrainedEstimateParameterEditor(avgLongTermSlipRateEstParam, true);
		// whether slip rate is known/unknown
		ArrayList slipRateTypes = new ArrayList();
		slipRateTypes.add(UNKNOWN);
		slipRateTypes.add(KNOWN);
		String defaultVal = KNOWN;
		if(slipRateEst==null) defaultVal = UNKNOWN;
		slipRateTypeParam = new StringParameter(SLIP_RATE_TYPE_PARAM_NAME, slipRateTypes, defaultVal);
		slipRateTypeParam.addParameterChangeListener(this);
		this.slipRateTypeParamEditor = new ConstrainedStringParameterEditor(slipRateTypeParam);
	}


	/**
	 * Ave dip estimate parama and editor
	 * @param allowedEstimates
	 */
	private void makeAveDipParamAndEditor(ArrayList allowedEstimates) {
		EstimateConstraint dipEstConstraint = new EstimateConstraint(DIP_MIN, DIP_MAX, allowedEstimates);
		Estimate dipEst = null; 
		if(this.selectedFaultSection.getAveDipEst()!=null)
			dipEst = selectedFaultSection.getAveDipEst().getEstimate();
		aveDipEstParam = new EstimateParameter(DIP, dipEstConstraint, DIP_UNITS, dipEst);
		aveDipEstParamEditor= new ConstrainedEstimateParameterEditor(aveDipEstParam, true);
	}

	/**
	 * Ave rake estimate param and editor
	 * @param allowedEstimates
	 */
	private void makeAveRakeParamAndEditor(ArrayList allowedEstimates) {
		EstimateConstraint rakeEstConstraint = new EstimateConstraint(RAKE_MIN, RAKE_MAX, allowedEstimates);
		Estimate rakeEst = null; 
		if(this.selectedFaultSection.getAveRakeEst()!=null)
			rakeEst = selectedFaultSection.getAveRakeEst().getEstimate();
		aveRakeEstParam = new EstimateParameter(RAKE, rakeEstConstraint, RAKE_UNITS, rakeEst);
		aveRakeEstParamEditor= new ConstrainedEstimateParameterEditor(aveRakeEstParam, true);
		//	 whether rake is known/unknown
		ArrayList rakeTypes = new ArrayList();
		rakeTypes.add(UNKNOWN);
		rakeTypes.add(KNOWN);
		String defaultVal = KNOWN;
		if(rakeEst==null) defaultVal = UNKNOWN;
		rakeTypeParam = new StringParameter(RAKE_TYPE_PARAM_NAME, rakeTypes, defaultVal);
		rakeTypeParam.addParameterChangeListener(this);
		rakeTypeParamEditor = new ConstrainedStringParameterEditor(rakeTypeParam);
	}

	public void parameterChange(ParameterChangeEvent event) {
		String name = event.getParameterName();

		if(name.equalsIgnoreCase(RAKE_TYPE_PARAM_NAME)) { // rake type param/ whether rake is known/unknown
			setRakeVisibility();
		} else if(name.equalsIgnoreCase(SLIP_RATE_TYPE_PARAM_NAME)) { // whether slip rate is known/unknown
			setSlipRateVisibility();
		}
	}

	private void setRakeVisibility() {
		String rakeType = (String)this.rakeTypeParam.getValue();
		if(rakeType.equalsIgnoreCase(UNKNOWN)) this.aveRakeEstParamEditor.setVisible(false);
		else aveRakeEstParamEditor.setVisible(true);
	}

	private void setSlipRateVisibility() {
		String slipRateType = (String)this.slipRateTypeParam.getValue();
		if(slipRateType.equalsIgnoreCase(UNKNOWN)) this.avgLongTermSlipRateEstParamEditor.setVisible(false);
		else avgLongTermSlipRateEstParamEditor.setVisible(true);
	}

	private void makeUpperDepthParamAndEditor(ArrayList allowedEstimates) {
		EstimateConstraint upperDepthConstraint = new EstimateConstraint(UPPER_DEPTH_MIN, UPPER_DEPTH_MAX, allowedEstimates);
		Estimate upperDepthEst = null; 
		if(this.selectedFaultSection.getAveUpperDepthEst()!=null)
			upperDepthEst = selectedFaultSection.getAveUpperDepthEst().getEstimate();
		upperDepthEstParam = new EstimateParameter(UPPER_DEPTH, upperDepthConstraint, DEPTH_UNITS, upperDepthEst);
		upperDepthEstParamEditor= new ConstrainedEstimateParameterEditor(upperDepthEstParam, true);
	}

	private void makeLowerDepthParamAndEditor(ArrayList allowedEstimates) {
		EstimateConstraint lowerDepthConstraint = new EstimateConstraint(LOWER_DEPTH_MIN, LOWER_DEPTH_MAX, allowedEstimates);
		Estimate lowerDepthEst = null; 
		if(this.selectedFaultSection.getAveLowerDepthEst()!=null)
			lowerDepthEst = selectedFaultSection.getAveLowerDepthEst().getEstimate();
		lowerDepthEstParam = new EstimateParameter(LOWER_DEPTH, lowerDepthConstraint, DEPTH_UNITS, lowerDepthEst);
		lowerDepthEstParamEditor= new ConstrainedEstimateParameterEditor(lowerDepthEstParam, true);
	}

	private void makeAseismicSlipParamAndEditor(ArrayList allowedEstimates) {
		EstimateConstraint aseismicSlipConstraint = new EstimateConstraint(ASEISMIC_SLIP_FACTOR_MIN, ASEISMIC_SLIP_FACTOR_MAX, allowedEstimates);
		Estimate aseimsicSlipEst = null; 
		if(this.selectedFaultSection.getAseismicSlipFactorEst()!=null)
			aseimsicSlipEst = selectedFaultSection.getAseismicSlipFactorEst().getEstimate();
		aseimsicSlipEstParam = new EstimateParameter(ASEISMIC_SLIP, aseismicSlipConstraint, ASEISMIC_SLIP_FACTOR_UNITS, aseimsicSlipEst);
		aseimsicSlipEstParamEditor= new ConstrainedEstimateParameterEditor(aseimsicSlipEstParam, true);
	}

	private void makeFaultTraceParamAndEditor() {
		faultTraceArea = new JTextArea();
		FaultTrace faultTrace = this.selectedFaultSection.getFaultTrace();
		for(int i=0; faultTrace!=null && i<faultTrace.getNumLocations(); ++i) {
			Location loc = faultTrace.get(i);
			faultTraceArea.append(loc.getLongitude()+","+loc.getLatitude()+"\n");
		}
	}

}
