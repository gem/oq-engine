/**
 * 
 */
package org.opensha.refFaultParamDb.gui.view;

import java.awt.GridBagConstraints;
import java.awt.GridBagLayout;
import java.awt.Insets;
import java.awt.event.ActionEvent;
import java.awt.event.ActionListener;
import java.io.File;
import java.io.FileWriter;
import java.io.IOException;
import java.util.ArrayList;

import javax.swing.JButton;
import javax.swing.JFileChooser;
import javax.swing.JOptionPane;
import javax.swing.JPanel;

import org.opensha.commons.data.estimate.Estimate;
import org.opensha.commons.geo.Location;
import org.opensha.commons.param.StringParameter;
import org.opensha.commons.param.editor.ConstrainedStringParameterEditor;
import org.opensha.commons.param.event.ParameterChangeEvent;
import org.opensha.commons.param.event.ParameterChangeListener;
import org.opensha.refFaultParamDb.dao.db.DB_AccessAPI;
import org.opensha.refFaultParamDb.dao.db.DB_ConnectionPool;
import org.opensha.refFaultParamDb.dao.db.FaultSectionVer2_DB_DAO;
import org.opensha.refFaultParamDb.dao.db.PrefFaultSectionDataDB_DAO;
import org.opensha.refFaultParamDb.gui.addEdit.faultSection.EditFaultSection;
import org.opensha.refFaultParamDb.gui.infotools.GUI_Utils;
import org.opensha.refFaultParamDb.gui.infotools.InfoLabel;
import org.opensha.refFaultParamDb.gui.infotools.SessionInfo;
import org.opensha.refFaultParamDb.vo.FaultSectionData;
import org.opensha.refFaultParamDb.vo.FaultSectionPrefData;
import org.opensha.refFaultParamDb.vo.FaultSectionSummary;
import org.opensha.sha.faultSurface.FaultTrace;


/**
 * this class allows the user to view fault sections from the database 
 * @author vipingupta
 *
 */
public class ViewFaultSection extends JPanel implements ParameterChangeListener, ActionListener {

	// paramter to provide a list of all fault sections in the database
	private final static String FAULT_SECTION_PARAM_NAME = "Fault Section";
	private StringParameter faultSectionParam;
	private final static String SHORT_NAME = "Short Name";
	private InfoLabel shortNameLabel = new InfoLabel();
	private final static String ENTRY_DATE = "Entry Date";
	private InfoLabel entryDateLabel = new InfoLabel();
	private final static String SOURCE = "Source";
	private InfoLabel sourceLabel = new InfoLabel();
	private final static String  AVE_LONG_TERM_SLIP_RATE= "Ave Long Term Slip Rate (mm/yr)";
	private InfoLabel slipRateLabel = new InfoLabel();
	private final static String  DIP= "Ave Dip (degrees)";
	private InfoLabel dipLabel = new InfoLabel();
	private final static String  DIP_DIRECTION= "Dip LocationVector";
	private InfoLabel dipDirectionLabel = new InfoLabel();
	private final static String  RAKE= "Ave Rake";
	private InfoLabel rakeLabel = new InfoLabel();
	private final static String  UPPER_DEPTH= "Upper Seis Depth (km)";
	private InfoLabel upperDepthLabel = new InfoLabel();
	private final static String  LOWER_DEPTH= "Lower Seis Depth (km)";
	private InfoLabel lowerDepthLabel = new InfoLabel();
	private final static String  ASEISMIC_SLIP= "Aseismic Slip Factor";
	private InfoLabel aseismicSlipLabel = new InfoLabel();
	private final static String  FAULT_TRACE= "Fault Section Trace";
	private InfoLabel faultTraceLabel = new InfoLabel();
	private final static String QFAULT_ID = "QFault_Id";
	private InfoLabel qfaultLabel = new InfoLabel();
	private final static String  COMMENTS= "COMMENTS";
	private final static String PROB = "Prob";
	private final static String INFO = "Info";
	private InfoLabel commentsLabel = new InfoLabel();
	private final static String DERIVED_VALS = "Derived Values";
	private final static String SECTION_LENGTH = "Fault Trace Length (km)";
	private InfoLabel sectionLengthLabel = new InfoLabel();
	private final static String SECTION_DOWN_DIP_WIDTH = "Down Dip Width (km)";
	private InfoLabel downDipWidthLabel = new InfoLabel();
	private final static String SECTION_AREA = "Area (sq km)";
	private InfoLabel sectionAreaLabel = new InfoLabel();
	private GridBagLayout gridBagLayout = new GridBagLayout();
	private FaultSectionVer2_DB_DAO faultSectionDAO; 
	private PrefFaultSectionDataDB_DAO prefFaultSectionDAO; 
	private JButton editButton = new JButton("Edit");
	private JButton removeButton = new JButton("Remove");
	private JButton saveButton = new JButton("Save All to File");
	private JButton saveSubSections = new JButton("Save Subsections");
	private final static String SAVE_BUTTON_TOOL_TIP = "Save All Fault Sections to a txt file";
	private final static String SAVE_SUBSECTIONS_BUTTON_TOOL_TIP = "Save All Sub Sections to a txt file";
	private JButton addButton = new JButton("Add");
	private final static String MSG_REMOVE_CONFIRM = "Do you want to delete this fault Section from the database?\n"+
	"All PaleoSites associated with this Fault Section will be removed.";
	private final static String MSG_REMOVE_SUCCESS = "Fault Section removed sucessfully from the database";
	private FaultSectionData selectedFaultSection;
	private ConstrainedStringParameterEditor faultSectionParamEditor;
	
	private DB_AccessAPI dbConnection;

	public ViewFaultSection(DB_AccessAPI dbConnection) {
		this(dbConnection, null);
	}

	public ViewFaultSection(DB_AccessAPI dbConnection, String selectedFaultSectionNameId) {
		this.dbConnection = dbConnection;
		faultSectionDAO = new FaultSectionVer2_DB_DAO(dbConnection);
		prefFaultSectionDAO = new PrefFaultSectionDataDB_DAO(dbConnection);
		
		initGUI(); // intialize the GUI
		if(selectedFaultSectionNameId!=null) this.faultSectionParam.setValue(selectedFaultSectionNameId);
		refreshFaultSectionValues(); // fill the fault section values according to selected Fault Section
		//		 do not allow edit for non authenticated users
		if(SessionInfo.getContributor()==null) {
			editButton.setEnabled(false);
			removeButton.setEnabled(false);
			addButton.setEnabled(false);
		}
	}

	/**
	 * Set the selected fault section
	 * 
	 * @param selectedFaultSectionNameId
	 */
	public void setSelectedFaultSectionNameId(String selectedFaultSectionNameId) {
		faultSectionParam.setValue(selectedFaultSectionNameId);
		faultSectionParamEditor.refreshParamEditor();
		refreshFaultSectionValues(); // fill the fault section values according to selected Fault Section

	}

	private void initGUI() {
		// set the Layout
		this.setLayout(gridBagLayout);
		int pos = 1;

		// fault section names parameter editor
		this.makeFaultSectionNamesEditor();

		// JPanel to view QfaultId, entry date, source and comments
		JPanel idPanel = getInfoPanel();	
		add(idPanel, new GridBagConstraints(0, pos++, 1, 1, 1.0, 1.0
				, GridBagConstraints.CENTER, GridBagConstraints.HORIZONTAL,
				new Insets(0, 0, 0, 0), 0, 0));	

		// fault trace label
		add(GUI_Utils.getPanel( this.faultTraceLabel, FAULT_TRACE), new GridBagConstraints(0, pos++, 1, 1, 1.0, 1.0
				, GridBagConstraints.CENTER, GridBagConstraints.HORIZONTAL,
				new Insets(0, 0, 0, 0), 0, 0));

		// upper depth
		add(GUI_Utils.getPanel(upperDepthLabel, UPPER_DEPTH), new GridBagConstraints(0, pos++, 1, 1, 1.0, 1.0
				, GridBagConstraints.CENTER, GridBagConstraints.HORIZONTAL,
				new Insets(0, 0, 0, 0), 0, 0));
		// lower depth
		add(GUI_Utils.getPanel(lowerDepthLabel, LOWER_DEPTH), new GridBagConstraints(0, pos++, 1, 1, 1.0, 1.0
				, GridBagConstraints.CENTER, GridBagConstraints.HORIZONTAL,
				new Insets(0, 0, 0, 0), 0, 0));

		pos = 0;

		//		 button to allow editing of Fault Section 
		add(this.makeButtonPanel(), new GridBagConstraints(1, pos++, 1, 1, 1.0, 1.0
				, GridBagConstraints.CENTER, GridBagConstraints.BOTH,
				new Insets(0, 0, 0, 0), 0, 0));

		// slip rate
		add(GUI_Utils.getPanel(slipRateLabel, AVE_LONG_TERM_SLIP_RATE), new GridBagConstraints(1, pos++, 1, 1, 1.0, 1.0
				, GridBagConstraints.CENTER, GridBagConstraints.HORIZONTAL,
				new Insets(0, 0, 0, 0), 0, 0));
		// dip Panel
		JPanel dipPanel = getDipPanel();
		add(dipPanel, new GridBagConstraints(1, pos++, 1, 1, 1.0, 1.0
				, GridBagConstraints.CENTER, GridBagConstraints.HORIZONTAL,
				new Insets(0, 0, 0, 0), 0, 0));

		// rake
		add(GUI_Utils.getPanel(rakeLabel, RAKE), new GridBagConstraints(1, pos++, 1, 1, 1.0, 1.0
				, GridBagConstraints.CENTER, GridBagConstraints.HORIZONTAL,
				new Insets(0, 0, 0, 0), 0, 0));


		// aseismic slip factor
		add(GUI_Utils.getPanel(aseismicSlipLabel, ASEISMIC_SLIP), new GridBagConstraints(1, pos++, 1, 1, 1.0, 1.0
				, GridBagConstraints.CENTER, GridBagConstraints.HORIZONTAL,
				new Insets(0, 0, 0, 0), 0, 0));

		// derived values
		add(getDerivedValsPanel(), new GridBagConstraints(1, pos++, 1, 1, 1.0, 1.0
				, GridBagConstraints.CENTER, GridBagConstraints.HORIZONTAL,
				new Insets(0, 0, 0, 0), 0, 0));
	}

	private JPanel makeButtonPanel() {
		JPanel panel = new JPanel(new GridBagLayout());
		// edit fault section button
		panel.add(this.editButton, new GridBagConstraints(0, 0, 1, 1, 1.0, 1.0
				, GridBagConstraints.CENTER, GridBagConstraints.NONE,
				new Insets(0, 0, 0, 0), 0, 0));
		editButton.addActionListener(this);
		// remove fault section button
		panel.add(this.removeButton, new GridBagConstraints(1, 0, 1, 1, 1.0, 1.0
				, GridBagConstraints.CENTER, GridBagConstraints.NONE,
				new Insets(0, 0, 0, 0), 0, 0));
		removeButton.addActionListener(this);
		// add fault section button
		panel.add(this.addButton, new GridBagConstraints(2, 0, 1, 1, 1.0, 1.0
				, GridBagConstraints.CENTER, GridBagConstraints.NONE,
				new Insets(0, 0, 0, 0), 0, 0));
		addButton.addActionListener(this);
		// save all fault sections to a file button
		panel.add(this.saveButton, new GridBagConstraints(3, 0, 1, 1, 1.0, 1.0
				, GridBagConstraints.CENTER, GridBagConstraints.NONE,
				new Insets(0, 0, 0, 0), 0, 0));
		saveButton.addActionListener(this);
		saveButton.setToolTipText(SAVE_BUTTON_TOOL_TIP);
		// save subsections to a file
		panel.add(this.saveSubSections, new GridBagConstraints(4, 0, 1, 1, 1.0, 1.0
				, GridBagConstraints.CENTER, GridBagConstraints.NONE,
				new Insets(0, 0, 0, 0), 0, 0));
		saveSubSections.addActionListener(this);
		saveSubSections.setToolTipText(SAVE_SUBSECTIONS_BUTTON_TOOL_TIP);
		return panel;
	}

	public void actionPerformed(ActionEvent event) {
		Object source = event.getSource();
		if(source == this.editButton) { // edit fault section
			EditFaultSection editFaultSection = new EditFaultSection(dbConnection, this.selectedFaultSection, this);
		}
		else if(source == this.removeButton) { // remove fault section
			removeFaultSection();
			refreshFaultSectionValues(); // fill the fault section values according to selected Fault Section
		} else if(source == this.addButton) { // add a new fault section
			EditFaultSection editFaultSection = new EditFaultSection(dbConnection, null, this);
		} else if(source == this.saveButton) { // save all fault sections to a file
			File file = getOutFile();
			if(file!=null) writeSectionsToFile(file);
		} else if(source==this.saveSubSections) { // svae subsections ot a file
			String str = JOptionPane.showInputDialog(this, 
					"Enter Maximum Length (in km) of a subsection", "10");
			try {
				double subSecLen = Double.parseDouble(str);
				File file = getOutFile();
				if(file!=null) writeSubSectionsToFile(file,subSecLen);
			}catch(NumberFormatException ex) {
				JOptionPane.showMessageDialog(this, "Invalid subsection length");
			}

		}
	}

	/**
	 * Get output filename
	 * @return
	 */
	private File getOutFile() {
		JFileChooser fileChooser = new JFileChooser();
		fileChooser.showSaveDialog(this);
		File file = fileChooser.getSelectedFile();
		return file;
	}

	/**
	 * Write fault sub sections to a file
	 * @param file
	 */
	private void writeSubSectionsToFile(File file, double subSecLen) {
		ArrayList faultSectionPrefDataList = prefFaultSectionDAO.getAllFaultSectionPrefData();
		SectionInfoFileWriter sectionWriter = new SectionInfoFileWriter(dbConnection);
		FileWriter fw;
		try {
			fw = new FileWriter(file);

			fw.write(sectionWriter.getFormatStringForFaultModel());
			//for(int i=0; i<1; ++i) {
			int totalSubSections =0;
			for(int i=0; i<faultSectionPrefDataList.size(); ++i) {
				FaultSectionPrefData faultSecPrefData = (FaultSectionPrefData)faultSectionPrefDataList.get(i);
				ArrayList<FaultSectionPrefData> subSecList = faultSecPrefData.getSubSectionsList(subSecLen);
				totalSubSections+=subSecList.size();
				for(int j=0; j<subSecList.size(); ++j) {
					sectionWriter.writeForFaultModel(subSecList.get(j), fw);
				}
			}
			System.out.println("Total Subsections="+totalSubSections);
			fw.close();
		} catch (IOException e) {
			// TODO Auto-generated catch block
			e.printStackTrace();
		}
	}


	/**
	 * Write fault sections to a file
	 * @param file
	 */
	private void writeSectionsToFile(File file) {
		ArrayList faultSectionsSummaryList = faultSectionDAO.getAllFaultSectionsSummary();
		int[] faultSectionIds = new int[faultSectionsSummaryList.size()];
		for(int i=0; i<faultSectionsSummaryList.size(); ++i) {
			faultSectionIds[i] = ((FaultSectionSummary)faultSectionsSummaryList.get(i)).getSectionId();
		}
		SectionInfoFileWriter fileWriter = new SectionInfoFileWriter(dbConnection);
		fileWriter.writeForFaultModel(faultSectionIds, file);
	}

	/**
	 * Remove the fault section from the database.
	 * Ask the user to confirm the removal of fault section first
	 *
	 */
	private void removeFaultSection() {
		int option = JOptionPane.showConfirmDialog(this, MSG_REMOVE_CONFIRM);
		// if user chooses to remove the fault section
		if(option == JOptionPane.OK_OPTION) {
			String faultSectionName = (String)faultSectionParam.getValue();
			// get id of the selected fault section
			FaultSectionSummary faultSectionSummary = FaultSectionSummary.getFaultSectionSummary(faultSectionName);
			faultSectionDAO.removeFaultSection(faultSectionSummary.getSectionId());
			JOptionPane.showMessageDialog(this, MSG_REMOVE_SUCCESS);
			makeFaultSectionNamesEditor();	
		}
	}


	private JPanel getDipPanel() {
		JPanel dipPanel = GUI_Utils.getPanel(DIP);

		// dip
		dipPanel.add(dipLabel, new GridBagConstraints(0, 0, 1, 1, 1.0, 1.0
				, GridBagConstraints.CENTER, GridBagConstraints.BOTH,
				new Insets(0, 0, 0, 0), 0, 0));

		// dip direction
		dipPanel.add(dipDirectionLabel, new GridBagConstraints(0, 1, 1, 1, 1.0, 1.0
				, GridBagConstraints.CENTER, GridBagConstraints.NONE,
				new Insets(0, 0, 0, 0), 0, 0));
		return dipPanel;
	}

	private JPanel getDerivedValsPanel() {
		JPanel derivedValsPanel = GUI_Utils.getPanel(DERIVED_VALS);	
		// Fault Trace Length
		derivedValsPanel.add(this.sectionLengthLabel, new GridBagConstraints(0, 0, 1, 1, 1.0, 1.0
				, GridBagConstraints.CENTER, GridBagConstraints.BOTH,
				new Insets(0, 0, 0, 0), 0, 0));
		// Down Dip width
		derivedValsPanel.add(this.downDipWidthLabel, new GridBagConstraints(0, 1, 1, 1, 1.0, 1.0
				, GridBagConstraints.CENTER, GridBagConstraints.BOTH,
				new Insets(0, 0, 0, 0), 0, 0));
		// Section Area
		derivedValsPanel.add(this.sectionAreaLabel, new GridBagConstraints(0, 2, 1, 1, 1.0, 1.0
				, GridBagConstraints.CENTER, GridBagConstraints.BOTH,
				new Insets(0, 0, 0, 0), 0, 0));
		return derivedValsPanel;
	}

	/**
	 * JPanel to view QfaultId, entry date, source and comments
	 * @return
	 */
	private JPanel getInfoPanel() {
		// JPanel to view QfaultId, entry date, source and comments
		JPanel idPanel = GUI_Utils.getPanel(INFO);

		// short name
		idPanel.add(shortNameLabel, new GridBagConstraints(0, 0, 1, 1, 1.0, 1.0
				, GridBagConstraints.CENTER, GridBagConstraints.BOTH,
				new Insets(0, 0, 0, 0), 0, 0));

		// entry date
		idPanel.add(entryDateLabel, new GridBagConstraints(0, 1, 1, 1, 1.0, 1.0
				, GridBagConstraints.CENTER, GridBagConstraints.BOTH,
				new Insets(0, 0, 0, 0), 0, 0));

		// qfault Id
		idPanel.add(qfaultLabel, new GridBagConstraints(0, 2, 1, 1, 1.0, 1.0
				, GridBagConstraints.CENTER, GridBagConstraints.BOTH,
				new Insets(0, 0, 0, 0), 0, 0));

		// source 
		idPanel.add(sourceLabel, new GridBagConstraints(0, 3, 1, 1, 1.0, 1.0
				, GridBagConstraints.CENTER, GridBagConstraints.BOTH,
				new Insets(0, 0, 0, 0), 0, 0));

		//		 comments
		idPanel.add(commentsLabel, new GridBagConstraints(0, 4, 1, 1, 1.0, 1.0
				, GridBagConstraints.CENTER, GridBagConstraints.BOTH,
				new Insets(0, 0, 0, 0), 0, 0));
		return idPanel;
	}

	/**
	 * Make parameter editor to list all availble Fault Section names
	 * @return
	 */
	public void makeFaultSectionNamesEditor() {
		if(faultSectionParamEditor!=null) this.remove(faultSectionParamEditor);
		ArrayList faultSectionsSummaryList = faultSectionDAO.getAllFaultSectionsSummary();
		ArrayList faultSectionsList = new ArrayList();
		for(int i=0; i<faultSectionsSummaryList.size(); ++i)
			faultSectionsList.add(((FaultSectionSummary)faultSectionsSummaryList.get(i)).getAsString());
		faultSectionParam = new StringParameter(FAULT_SECTION_PARAM_NAME, faultSectionsList, (String)faultSectionsList.get(0));
		faultSectionParam.addParameterChangeListener(this);
		faultSectionParamEditor = new ConstrainedStringParameterEditor(faultSectionParam);
		// fault section name editor 
		add(faultSectionParamEditor, new GridBagConstraints(0, 0, 1, 1, 1.0, 1.0
				, GridBagConstraints.CENTER, GridBagConstraints.HORIZONTAL,
				new Insets(0, 0, 0, 0), 0, 0));
		this.updateUI();
	}

	/**
	 * This function is called whenever chooses a different fault section
	 */
	public void parameterChange(ParameterChangeEvent event) {
		refreshFaultSectionValues();
	}

	/**
	 * Refresh the fault section values based on fault section chosen by the user
	 * @param faultSectionName
	 */
	public void refreshFaultSectionValues() {
		String faultSectionName = (String)faultSectionParam.getValue();
		// get id of the selected fault section
		FaultSectionSummary faultSectionSummary = FaultSectionSummary.getFaultSectionSummary(faultSectionName);
		selectedFaultSection = faultSectionDAO.getFaultSection(faultSectionSummary.getSectionId());
		// Entry Date
		entryDateLabel.setTextAsHTML(ENTRY_DATE, selectedFaultSection.getEntryDate());
		// Source
		sourceLabel.setTextAsHTML(SOURCE, selectedFaultSection.getSource());
		// Slip Rate Est
		Estimate slipRateEst = null;
		if(selectedFaultSection.getAveLongTermSlipRateEst()!=null)
			slipRateEst = selectedFaultSection.getAveLongTermSlipRateEst().getEstimate();
		slipRateLabel.setTextAsHTML(slipRateEst, AVE_LONG_TERM_SLIP_RATE, PROB);

		// Dip Est
		Estimate dipEst = null;
		if(selectedFaultSection.getAveDipEst()!=null)
			dipEst = selectedFaultSection.getAveDipEst().getEstimate();
		dipLabel.setTextAsHTML(dipEst, DIP, PROB);

		// Dip LocationVector Label
		dipDirectionLabel.setTextAsHTML(DIP_DIRECTION, ""+selectedFaultSection.getDipDirection());

		// rake
		Estimate rakeEst = null;
		if(selectedFaultSection.getAveRakeEst()!=null) rakeEst = selectedFaultSection.getAveRakeEst().getEstimate();
		rakeLabel.setTextAsHTML(rakeEst, RAKE, PROB);

		// upper depth
		Estimate upperDepthEst = null;
		if(selectedFaultSection.getAveUpperDepthEst()!=null) upperDepthEst = selectedFaultSection.getAveUpperDepthEst().getEstimate();
		upperDepthLabel.setTextAsHTML(upperDepthEst, UPPER_DEPTH, PROB);

		// lower Depth
		Estimate lowerDepthEst = null;
		if(selectedFaultSection.getAveLowerDepthEst()!=null) lowerDepthEst = selectedFaultSection.getAveLowerDepthEst().getEstimate();
		lowerDepthLabel.setTextAsHTML(lowerDepthEst, LOWER_DEPTH, PROB);

		// aseismic slip factor
		Estimate aseismicSlipEst = null;
		if(selectedFaultSection.getAseismicSlipFactorEst()!=null) aseismicSlipEst = selectedFaultSection.getAseismicSlipFactorEst().getEstimate();
		aseismicSlipLabel.setTextAsHTML(aseismicSlipEst, ASEISMIC_SLIP, PROB);

		// fault trace
		FaultTrace faultTrace = selectedFaultSection.getFaultTrace();
		ArrayList locsAsString = new ArrayList();
		int numLocs = faultTrace.getNumLocations();
		for(int i=0; i<numLocs; ++i) {
			Location loc = faultTrace.get(i);
			locsAsString.add(loc.getLongitude()+","+loc.getLatitude());
		}

		faultTraceLabel.setTextAsHTML(locsAsString);
		FaultSectionPrefData faultsectionPrefData = selectedFaultSection.getFaultSectionPrefData();
		// fault trace length
		double length = faultsectionPrefData.getLength();
		this.sectionLengthLabel.setTextAsHTML(SECTION_LENGTH, ""+(float)length);
		// down dip width
		double ddw = faultsectionPrefData.getDownDipWidth();
		this.downDipWidthLabel.setTextAsHTML(SECTION_DOWN_DIP_WIDTH, ""+(float)ddw);
		// area
		this.sectionAreaLabel.setTextAsHTML(SECTION_AREA, ""+(float)(length*ddw));
		// comments
		commentsLabel.setTextAsHTML(COMMENTS, selectedFaultSection.getComments());

		// qfault Id
		qfaultLabel.setTextAsHTML(QFAULT_ID, selectedFaultSection.getQFaultId());
		this.shortNameLabel.setTextAsHTML(SHORT_NAME, selectedFaultSection.getShortName());

	}


}
