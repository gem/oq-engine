/**
 * 
 */
package org.opensha.sha.earthquake.rupForecastImpl.WGCEP_UCERF_2_3.gui;

import java.awt.Container;
import java.awt.GridBagConstraints;
import java.awt.GridBagLayout;
import java.awt.Insets;
import java.awt.event.ActionEvent;
import java.awt.event.ActionListener;
import java.io.File;
import java.util.ArrayList;
import java.util.HashMap;
import java.util.Iterator;

import javax.swing.JButton;
import javax.swing.JFrame;

import org.opensha.commons.param.StringParameter;
import org.opensha.commons.param.editor.ConstrainedStringParameterEditor;
import org.opensha.commons.param.event.ParameterChangeEvent;
import org.opensha.commons.param.event.ParameterChangeListener;
import org.opensha.sha.earthquake.rupForecastImpl.WGCEP_UCERF_2_3.FaultSegmentData;
import org.opensha.sha.earthquake.rupForecastImpl.WGCEP_UCERF_2_3.A_Faults.A_FaultSegmentedSourceGenerator;

/**
 * This GUI can be used to select a fault and a segment to plot the 
 * ratio of recurrence intervals
 * 
 * @author vipingupta
 *
 */
public class FaultSegmentSelector extends JFrame implements ParameterChangeListener, ActionListener {
	private final static String FAULT_NAME_PARAM_NAME = "Fault Name";
	private final static String SEGMENT_NAME_PARAM_NAME = "Segment Name";
	private JButton okButton = new JButton("OK");
	private StringParameter faultNameParameter;
	private StringParameter segmentNameParameter;
	private HashMap<String, FaultSegmentData> faultSegmentDataList;
	private ConstrainedStringParameterEditor segmentNameParameterEditor;
	private String dirName, excelSheetName;
	private final static String TITLE = "Select Segment";
	private boolean isDeleteExcelSheet= false;
	private boolean isRecurIntvPlots = true;
	
	/**
	 * Get a List of A-Fault sources and get the fault name and segment name from this list
	 * 
	 * @param aFaultSourceList
	 */
	public FaultSegmentSelector(ArrayList aFaultSourceList, String dirName, String excelSheetName, boolean isRecurIntvPlots) {
		this.dirName = dirName;
		this.isRecurIntvPlots = isRecurIntvPlots;
		this.excelSheetName = excelSheetName;
		// get FaultSegmentData from A_FaultSourceList
		faultSegmentDataList = new HashMap<String, FaultSegmentData>();
		for(int i=0; i<aFaultSourceList.size(); ++i) {
			FaultSegmentData faultSegmentData = ((A_FaultSegmentedSourceGenerator)aFaultSourceList.get(i)).getFaultSegmentData();
			faultSegmentDataList.put(faultSegmentData.getFaultName(), faultSegmentData);
		}
		// Create GUI
		createGUI();
		// set title
		setTitle(TITLE);
		// show the window in the center of the screen
		this.setLocationRelativeTo(null);
		pack();
		show();
		
	}
	
	/**
	 * Whether to delete the excel sheet after making plots
	 * 
	 * @param isDelete
	 */
	public void deleteExcelSheet(boolean isDelete) {
		this.isDeleteExcelSheet = isDelete;
	}
	
	/**
	 * Create GUI
	 *
	 */
	private void createGUI() {
		// Fault Name parameter
		ArrayList<String> faultNames = new ArrayList<String>();
		Iterator it = faultSegmentDataList.keySet().iterator();
		while(it.hasNext()) faultNames.add((String)it.next());
		faultNameParameter = new StringParameter(FAULT_NAME_PARAM_NAME, faultNames, faultNames.get(0));
		faultNameParameter.addParameterChangeListener(this);
		ConstrainedStringParameterEditor faultNameParamEditor = new ConstrainedStringParameterEditor(faultNameParameter);
		
		Container container = this.getContentPane();
		container.setLayout(new GridBagLayout());
		container.add(faultNameParamEditor,new GridBagConstraints( 0, 0, 1, 1, 1.0, 1.0
      	      ,GridBagConstraints.CENTER, GridBagConstraints.BOTH, new Insets( 0, 0, 0, 0 ), 0, 0 ));		
		// create segment names based on selected fault
		setSegmentNames((String)faultNameParameter.getValue());
		
		// ok Button
		container.add(this.okButton,new GridBagConstraints( 0, 2, 1, 1, 1.0, 0.0
	      	      ,GridBagConstraints.CENTER, GridBagConstraints.NONE, new Insets( 0, 0, 0, 0 ), 0, 0 ));
		okButton.addActionListener(this);

	}
	
	/**
	 * Set the segment names based on selected fault name
	 * 
	 * @param faultName
	 */
	private void setSegmentNames(String faultName) {
		if(segmentNameParameterEditor!=null) {
			getContentPane().remove(segmentNameParameterEditor);
		}
		FaultSegmentData faultSegmentData = faultSegmentDataList.get(faultName);
		ArrayList<String> segNames = new ArrayList<String>();
		for(int i=0; i<faultSegmentData.getNumSegments(); ++i) segNames.add(faultSegmentData.getSegmentName(i));
		this.segmentNameParameter = new StringParameter(SEGMENT_NAME_PARAM_NAME, segNames, segNames.get(0));
		segmentNameParameterEditor = new ConstrainedStringParameterEditor(segmentNameParameter);
		getContentPane().add(segmentNameParameterEditor,new GridBagConstraints( 0, 1, 1, 1, 1.0, 1.0
	      	      ,GridBagConstraints.CENTER, GridBagConstraints.BOTH, new Insets( 0, 0, 0, 0 ), 0, 0 ));		

		this.validate();
		this.repaint();
	}
	
	/**
	 * Set the segment names based on selected fault name
	 */
	public void parameterChange(ParameterChangeEvent event) {
		setSegmentNames((String)faultNameParameter.getValue());
	}
	
	/**
	 * This function is called when OK button is clicked
	 */
	public void actionPerformed(ActionEvent event) {
		String faultName = (String)this.faultNameParameter.getValue();
		String segName = (String)this.segmentNameParameter.getValue();
		if(this.isRecurIntvPlots)
			CreateHistogramsFromSegRecurIntvFile.createHistogramPlots(dirName, excelSheetName, faultName, segName);
		else CreateHistogramsFromSegSlipRateFile.createHistogramPlots(dirName, excelSheetName, faultName, segName);
		if(isDeleteExcelSheet) new File(excelSheetName).delete();
		this.dispose();
	}

}
