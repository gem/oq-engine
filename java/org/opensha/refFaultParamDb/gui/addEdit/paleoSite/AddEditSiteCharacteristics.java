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

package org.opensha.refFaultParamDb.gui.addEdit.paleoSite;

import java.awt.Container;
import java.awt.GridBagConstraints;
import java.awt.Insets;
import java.awt.event.ActionEvent;
import java.awt.event.ActionListener;
import java.util.ArrayList;

import javax.swing.JButton;
import javax.swing.JOptionPane;
import javax.swing.JSplitPane;

import org.opensha.commons.data.estimate.Estimate;
import org.opensha.commons.exceptions.ConstraintException;
import org.opensha.commons.exceptions.InvalidRangeException;
import org.opensha.commons.exceptions.ParameterException;
import org.opensha.commons.geo.GeoTools;
import org.opensha.commons.geo.Location;
import org.opensha.commons.gui.LabeledBoxPanel;
import org.opensha.commons.param.DoubleParameter;
import org.opensha.commons.param.LocationParameter;
import org.opensha.commons.param.ParameterList;
import org.opensha.commons.param.ParameterListParameter;
import org.opensha.commons.param.StringListParameter;
import org.opensha.commons.param.StringParameter;
import org.opensha.commons.param.editor.ConstrainedStringListParameterEditor;
import org.opensha.commons.param.editor.ConstrainedStringParameterEditor;
import org.opensha.commons.param.editor.LocationParameterEditor;
import org.opensha.commons.param.editor.StringParameterEditor;
import org.opensha.commons.param.editor.estimate.ConstrainedEstimateParameterEditor;
import org.opensha.commons.param.estimate.EstimateConstraint;
import org.opensha.commons.param.estimate.EstimateParameter;
import org.opensha.commons.param.event.ParameterChangeEvent;
import org.opensha.commons.param.event.ParameterChangeListener;
import org.opensha.refFaultParamDb.dao.db.DB_AccessAPI;
import org.opensha.refFaultParamDb.dao.db.DB_ConnectionPool;
import org.opensha.refFaultParamDb.dao.db.FaultSectionVer2_DB_DAO;
import org.opensha.refFaultParamDb.dao.db.PaleoSiteDB_DAO;
import org.opensha.refFaultParamDb.dao.db.ReferenceDB_DAO;
import org.opensha.refFaultParamDb.dao.db.SiteRepresentationDB_DAO;
import org.opensha.refFaultParamDb.dao.db.SiteTypeDB_DAO;
import org.opensha.refFaultParamDb.dao.exception.InsertException;
import org.opensha.refFaultParamDb.gui.CommentsParameterEditor;
import org.opensha.refFaultParamDb.gui.event.DbAdditionFrame;
import org.opensha.refFaultParamDb.gui.event.DbAdditionListener;
import org.opensha.refFaultParamDb.gui.event.DbAdditionSuccessEvent;
import org.opensha.refFaultParamDb.gui.infotools.ConnectToEmailServlet;
import org.opensha.refFaultParamDb.gui.infotools.GUI_Utils;
import org.opensha.refFaultParamDb.gui.infotools.SessionInfo;
import org.opensha.refFaultParamDb.vo.EstimateInstances;
import org.opensha.refFaultParamDb.vo.FaultSectionSummary;
import org.opensha.refFaultParamDb.vo.PaleoSite;
import org.opensha.refFaultParamDb.vo.PaleoSitePublication;
import org.opensha.refFaultParamDb.vo.Reference;
import org.opensha.refFaultParamDb.vo.SiteRepresentation;
import org.opensha.refFaultParamDb.vo.SiteType;


/**
 * <p>Title: AddPaleoSite.java </p>
 * <p>Description:  GUI to allow the user to add a new paleo site or edit an exisitng
 * paleo site. </p>
 * <p>Copyright: Copyright (c) 2002</p>
 * <p>Company: </p>
 * @author not attributable
 * @version 1.0
 */

public class AddEditSiteCharacteristics extends DbAdditionFrame implements ActionListener,
ParameterChangeListener, DbAdditionListener {

	// various input parameter names
	private final static String SITE_NAME_PARAM_NAME="Site Name";
	private final static String OLD_SITE_ID_PARAM_NAME="QFault Site Id";
	private final static String SITE_LOCATION_PARAM_NAME="Site Location";
	private final static String COMMENTS_PARAM_NAME = "Comments";
	private final static String CHOOSE_REFERENCE_PARAM_NAME = "Choose Reference";
	private final static String ASSOCIATED_WITH_FAULT_PARAM_NAME="Associated With Fault";
	private final static String SITE_TYPE_PARAM_NAME="Site Type";
	private final static String DIP_PARAM_NAME = "Dip Estimate";
	private final static String DIP_NAME = "Dip";
	private final static String DIP_UNITS = "Degrees";
	private final static String SITE_REPRESENTATION_PARAM_NAME="How Representative is this Site";

	// params for entering a site
	private final static String LAT_PARAM_NAME="Site Latitude";
	private final static String LON_PARAM_NAME="Site Longitude";
	private final static String ELEVATION_PARAM_NAME="Site Elevation";
	private final static double DEFAULT_LAT_VAL=34.00;
	private final static double DEFAULT_LON_VAL=-118.0;

	private final static String TITLE = "Add/Edit Paleo Site";
	private final static String BETWEEN_LOCATIONS_SITE_TYPE = "Between Locations";
	private final static String LAT_LON_UNITS = "Decimal Degrees";
	private final static String ELEVATION_UNITS = "meters";
	private final static int WIDTH = 600;
	private final static int HEIGHT = 700;
	private final static double DIP_MIN =Double.NEGATIVE_INFINITY;
	private final static double DIP_MAX =Double.POSITIVE_INFINITY;

	// various messages
	private final static String MSG_COMMENTS_MISSING = "Please Enter Comments";
	private final static String MSG_REFERENCES_MISSING = "Please choose atleast 1 reference";
	private final static String MSG_INSERT_SUCCESS = "Site added sucessfully to the database";
	private final static String MSG_UPDATE_SUCCESS = "Site updated sucessfully in the database";
	private final static String MSG_DIP_INCORRECT = "Dip Value is incorrect/missing.\n"+
	" Due to put the site into database anyway?";


	// input parameters declaration
	private StringParameter siteNameParam;
	private LocationParameter siteLocationParam;
	private LocationParameter siteLocationParam2;
	private StringParameter assocWithFaultParam;
	private StringListParameter siteTypeParam;
	private StringParameter siteRepresentationParam;
	private StringListParameter siteReferenceParam;
	private StringParameter commentsParam;
	private StringParameter oldSiteIdParam;
	private EstimateParameter dipEstParam;

	// input parameter editors
	private StringParameterEditor siteNameParamEditor;
	private LocationParameterEditor siteLocationParamEditor;
	private LocationParameterEditor siteLocationParamEditor2;
	private ConstrainedStringParameterEditor assocWithFaultParamEditor;
	private ConstrainedStringListParameterEditor siteTypeParamEditor;
	private ConstrainedStringParameterEditor siteRepresentationParamEditor;
	private ConstrainedStringListParameterEditor siteReferenceParamEditor;
	private CommentsParameterEditor commentsParamEditor;
	private StringParameterEditor oldSiteIdParamEditor;
	private ConstrainedEstimateParameterEditor dipEstParamEditor;


	// various buttons in thos window
	private JButton addNewSiteButton = new JButton("Add New Site Type");
	private JButton okButton = new JButton("Submit");
	private JButton cancelButton = new JButton("Cancel");
	private JButton addNewReferenceButton = new JButton("Add New Reference");
	private final static String ADD_NEW_REF_TOOL_TIP= "Add Reference not currently in database";

	// site type DAO
	private SiteTypeDB_DAO siteTypeDAO;
	// references DAO
	private ReferenceDB_DAO referenceDAO;
	// site representations DAO
	private SiteRepresentationDB_DAO siteRepresentationDAO;
	// paleo site DAO
	private PaleoSiteDB_DAO paleoSiteDAO;
	// fault DAO
	private FaultSectionVer2_DB_DAO faultSectionDAO;
	private AddNewSiteType addNewSiteType;
	private AddNewReference addNewReference;
	private LabeledBoxPanel labeledBoxPanel;
	private LabeledBoxPanel labeledBoxPanel2;
	private ArrayList referenceList;
	private ArrayList referenceSummaryList;
	
	private DB_AccessAPI dbConnection;

	/**
	 * This constructor allows the editing of an existing site
	 *
	 * @param isEdit
	 * @param paleoSite
	 */
	public AddEditSiteCharacteristics(DB_AccessAPI dbConnection) {
		this.dbConnection = dbConnection;
		siteTypeDAO = new SiteTypeDB_DAO(dbConnection);
		referenceDAO = new ReferenceDB_DAO(dbConnection);
		siteRepresentationDAO = new SiteRepresentationDB_DAO(dbConnection);
		paleoSiteDAO = new PaleoSiteDB_DAO(dbConnection);
		faultSectionDAO = new FaultSectionVer2_DB_DAO(dbConnection);
		try {
			// initialize the parameters and editors
			initParametersAndEditors();
			// add the editors and buttons to the window
			jbInit();
			// make parameter and editor for site type
			makeSiteTypeParamAndEditor();
			// show/not show second site location
			setSecondLocationVisible();
			// make parameter and editor for reference
			makeReferenceParamAndEditor();
			this.setTitle(TITLE);
			// add listeners for the buttons in this window
			addActionListeners();
		}catch(Exception e) {
			e.printStackTrace();
		}
		this.pack();
		setSize(WIDTH, HEIGHT);
		this.setLocationRelativeTo(null);
		this.setVisible(true);
	}

	// add action listeners on the buttons in this window
	private void addActionListeners() {
		this.addNewSiteButton.addActionListener(this);
		addNewReferenceButton.addActionListener(this);
		addNewReferenceButton.setToolTipText(ADD_NEW_REF_TOOL_TIP);
		okButton.addActionListener(this);
		cancelButton.addActionListener(this);
	}

	/**
	 * Whenever user presses a button on this window, this function is called
	 * @param event
	 */
	public void actionPerformed(ActionEvent event) {
		Object source  = event.getSource();
		// if it is "Add New Site" request, pop up another window to fill the new site type
		if(source==this.addNewSiteButton) {
			addNewSiteType = new AddNewSiteType(dbConnection);
			addNewSiteType.addDbAdditionSuccessListener(this);
		}
		else if(source == addNewReferenceButton)  { // add new reference to the database
			addNewReference = new AddNewReference(dbConnection);
			addNewReference.addDbAdditionSuccessListener(this);
		}
		else if(source == okButton) {
			putSiteInDatabase();
		}
		else if (source==cancelButton) {
			this.dispose();
		}
	}

	/**
	 * Put the site into the database
	 */
	private void putSiteInDatabase() {
		PaleoSite paleoSite = new PaleoSite();
		// set the site Id to update a existing site
		/**
		 * There is always insertion operation in database. Even in case of update,
		 * a new row is entered into database but site id is retained. This insertion allows
		 * us to hold the multiple versions.
		 */

		paleoSite.setSiteName((String)this.siteNameParam.getValue());
		String comments = (String)this.commentsParam.getValue();
		// user must provide comments
		if(comments==null || comments.trim().equalsIgnoreCase("")) {
			JOptionPane.showMessageDialog(this, MSG_COMMENTS_MISSING);
			return;
		}
		paleoSite.setGeneralComments(comments);
		paleoSite.setOldSiteId((String)this.oldSiteIdParam.getValue());
		FaultSectionSummary faultSectionSummary = FaultSectionSummary.getFaultSectionSummary((String)this.assocWithFaultParam.getValue());
		paleoSite.setFaultSectionNameId(faultSectionSummary.getSectionName(), faultSectionSummary.getSectionId());
		// see that user chooses at least 1 site reference
		ArrayList siteReferences = (ArrayList)this.siteReferenceParam.getValue();
		if(siteReferences==null || siteReferences.size()==0) {
			JOptionPane.showMessageDialog(this, MSG_REFERENCES_MISSING);
			return;
		}
		ArrayList paleoSitePubList = new ArrayList();
		String siteRep = (String)this.siteRepresentationParam.getValue();
		ArrayList siteTypes = (ArrayList)this.siteTypeParam.getValue();

		for(int i=0; i<siteReferences.size(); ++i) {
			int index = this.referenceSummaryList.indexOf(siteReferences.get(i));
			PaleoSitePublication paleoSitePub = new PaleoSitePublication();
			paleoSitePub.setReference((Reference)this.referenceList.get(index));
			paleoSitePub.setRepresentativeStrandName(siteRep);
			paleoSitePub.setSiteTypeNames(siteTypes);
			paleoSitePubList.add(paleoSitePub);
		}
		paleoSite.setPaleoSitePubList(paleoSitePubList);
		try {
			this.dipEstParamEditor.setEstimateInParameter();
			paleoSite.setDipEstimate(new EstimateInstances((Estimate)this.dipEstParam.getValue(), DIP_UNITS));
		}catch(Exception e){
			int option = JOptionPane.showConfirmDialog(this, MSG_DIP_INCORRECT, TITLE, JOptionPane.YES_NO_OPTION);
			if(option == JOptionPane.NO_OPTION) return;
		}

		// location 1
		ParameterList location1ParamList = ((ParameterListParameter)siteLocationParam.getLocationParameter()).getParameter();
		Double lat1 = (Double)location1ParamList.getValue(LAT_PARAM_NAME);
		Double lon1 = (Double)location1ParamList.getValue(LON_PARAM_NAME);
		Double elev1 = (Double)location1ParamList.getValue(ELEVATION_PARAM_NAME);
		paleoSite.setSiteLat1((float)lat1.doubleValue());
		paleoSite.setSiteLon1((float)lon1.doubleValue());
		if(elev1!=null) paleoSite.setSiteElevation1((float)elev1.doubleValue());
		else   paleoSite.setSiteElevation1(Float.NaN);

		//location 2
		ParameterList location2ParamList = ((ParameterListParameter)siteLocationParam2.getLocationParameter()).getParameter();
		float lat2 =  Float.NaN, lon2 = Float.NaN, elev2 = Float.NaN;
		ArrayList selectedSiteType =  (ArrayList)this.siteTypeParam.getValue();
		if(selectedSiteType.contains(BETWEEN_LOCATIONS_SITE_TYPE)) {
			lat2 = (float)((Double)location2ParamList.getValue(LAT_PARAM_NAME)).doubleValue();
			lon2 = (float)((Double)location2ParamList.getValue(LON_PARAM_NAME)).doubleValue();
			Double elev2Double = (Double)location2ParamList.getValue(ELEVATION_PARAM_NAME);
			if(elev2Double!=null) elev2 =(float) elev2Double.doubleValue();
		}
		paleoSite.setSiteLat2(lat2);
		paleoSite.setSiteLon2(lon2);
		paleoSite.setSiteElevation2(elev2);

		try {
			// add the paleo site to the database
			ConnectToEmailServlet.sendEmail(SessionInfo.getUserName()+" trying to add new Site Characteristics to database\n"+ paleoSite.toString());
			paleoSiteDAO.addPaleoSite(paleoSite);
			// show the success message to the user
			JOptionPane.showMessageDialog(this,MSG_INSERT_SUCCESS);
			ConnectToEmailServlet.sendEmail("Site Characteristics added successfully for a new site by "+SessionInfo.getUserName());
			this.sendEventToListeners(paleoSite);
			this.dispose();
		}catch(InsertException e) {
			JOptionPane.showMessageDialog(this, e.getMessage());
		}
	}

	// make site type param and editor
	private void makeSiteTypeParamAndEditor() {
		if(siteTypeParamEditor!=null) labeledBoxPanel.remove(siteTypeParamEditor);
		ArrayList siteTypes = getSiteTypes();
		ArrayList defaultSiteType;

		defaultSiteType = new ArrayList() ;
		defaultSiteType.add(siteTypes.get(0));
		// available study types
		siteTypeParam = new StringListParameter(SITE_TYPE_PARAM_NAME, siteTypes,
				defaultSiteType);
		siteTypeParamEditor = new ConstrainedStringListParameterEditor(siteTypeParam);
		siteTypeParam.addParameterChangeListener(this);
		// site types
		labeledBoxPanel.add(siteTypeParamEditor,  new GridBagConstraints(0, 4, 1, 1, 1.0, 1.0
				,GridBagConstraints.CENTER, GridBagConstraints.BOTH, new Insets(5, 5, 5, 5), 0, 0));
	}

	// make reference param and editor
	private void makeReferenceParamAndEditor() {

		if(this.siteReferenceParamEditor!=null) this.labeledBoxPanel.remove(siteReferenceParamEditor);
		ArrayList referencesList = this.getAvailableReferences();
		ArrayList dafaultReference;
		dafaultReference = new ArrayList();

		// references for this site
		this.siteReferenceParam = new StringListParameter(CHOOSE_REFERENCE_PARAM_NAME,
				referencesList, dafaultReference);
		this.siteReferenceParamEditor = new ConstrainedStringListParameterEditor(siteReferenceParam);

		// references
		labeledBoxPanel2.add(this.siteReferenceParamEditor,  new GridBagConstraints(0, 3, 2, 1, 1.0, 1.0
				,GridBagConstraints.CENTER, GridBagConstraints.BOTH, new Insets(5, 5, 5, 5), 0, 0));
	}

	/**
	 * Add the editors and buttons to the window
	 */
	private void jbInit() {
		labeledBoxPanel = new LabeledBoxPanel(GUI_Utils.gridBagLayout);
		labeledBoxPanel.setTitle(TITLE);
		labeledBoxPanel2 = new LabeledBoxPanel(GUI_Utils.gridBagLayout);
		labeledBoxPanel2.setTitle(TITLE);
		int yPos = 0;
		// site name editor
		labeledBoxPanel.add(siteNameParamEditor,  new GridBagConstraints(0, yPos++, 2, 1, 1.0, 1.0
				,GridBagConstraints.CENTER, GridBagConstraints.BOTH, new Insets(5, 5, 5, 5), 0, 0));
		// old site id
		labeledBoxPanel.add(this.oldSiteIdParamEditor,  new GridBagConstraints(0, yPos++, 2, 1, 1.0, 1.0
				,GridBagConstraints.CENTER, GridBagConstraints.BOTH, new Insets(5, 5, 5, 5), 0, 0));
		// site location
		labeledBoxPanel.add(siteLocationParamEditor,  new GridBagConstraints(0, yPos++, 2, 1, 1.0, 1.0
				,GridBagConstraints.CENTER, GridBagConstraints.BOTH, new Insets(5, 5, 5, 5), 0, 0));
		// associated with fault
		labeledBoxPanel.add(assocWithFaultParamEditor,  new GridBagConstraints(0, yPos++, 2, 1, 1.0, 1.0
				,GridBagConstraints.CENTER, GridBagConstraints.BOTH, new Insets(5, 5, 5, 5), 0, 0));
		// add new site type
		labeledBoxPanel.add(addNewSiteButton,  new GridBagConstraints(1, yPos++, 1, 1, 1.0, 1.0
				,GridBagConstraints.CENTER, GridBagConstraints.HORIZONTAL, new Insets(5, 5, 5, 5), 0, 0));
		// site location 2
		labeledBoxPanel.add(siteLocationParamEditor2,  new GridBagConstraints(0, yPos++, 2, 1, 1.0, 1.0
				,GridBagConstraints.CENTER, GridBagConstraints.BOTH, new Insets(5, 5, 5, 5), 0, 0));

		yPos = 0;
		// sdip estimate
		labeledBoxPanel2.add(this.dipEstParamEditor,  new GridBagConstraints(0, yPos++, 2, 1, 1.0, 1.0
				,GridBagConstraints.CENTER, GridBagConstraints.BOTH, new Insets(5, 5, 5, 5), 0, 0));
		// how representative is this site
		labeledBoxPanel2.add(siteRepresentationParamEditor,  new GridBagConstraints(0, yPos++, 2, 1, 1.0, 1.0
				,GridBagConstraints.CENTER, GridBagConstraints.BOTH, new Insets(5, 5, 5, 5), 0, 0));
		// comments
		labeledBoxPanel2.add(this.commentsParamEditor,  new GridBagConstraints(0, yPos++, 2, 1, 1.0, 1.0
				,GridBagConstraints.CENTER, GridBagConstraints.BOTH, new Insets(5, 5, 5, 5), 0, 0));
		++yPos; // this postion taken by references param editor
		// references
		labeledBoxPanel2.add(this.addNewReferenceButton,  new GridBagConstraints(0, yPos++, 1, 1, 1.0, 1.0
				,GridBagConstraints.CENTER, GridBagConstraints.NONE, new Insets(5, 5, 5, 5), 0, 0));
		// ok button
		labeledBoxPanel2.add(okButton,  new GridBagConstraints(0, yPos, 1, 1, 1.0, 1.0
				,GridBagConstraints.CENTER, GridBagConstraints.HORIZONTAL, new Insets(5, 5, 5, 5), 0, 0));
		// cancel button
		labeledBoxPanel2.add(cancelButton,  new GridBagConstraints(1, yPos++, 1, 1, 1.0, 1.0
				,GridBagConstraints.CENTER, GridBagConstraints.HORIZONTAL, new Insets(5, 5, 5, 5), 0, 0));

		Container contentPane = this.getContentPane();
		contentPane.setLayout(GUI_Utils.gridBagLayout);
		JSplitPane splitPane = new JSplitPane();
		splitPane.setOrientation(JSplitPane.HORIZONTAL_SPLIT);
		splitPane.add(labeledBoxPanel, JSplitPane.LEFT);
		splitPane.add(labeledBoxPanel2, JSplitPane.RIGHT);
		splitPane.setDividerLocation(WIDTH/2);
		contentPane.add(splitPane,  new GridBagConstraints(0, 0, 1, 1, 1.0, 1.0
				,GridBagConstraints.CENTER, GridBagConstraints.BOTH, new Insets(5, 5, 5, 5), 0, 0));
	}



	/**
	 * Initialize all the parameters and the editors
	 */
	private void initParametersAndEditors() throws Exception {

		String defaultSiteName, defaultOldSiteId, defaultFaultSectionName;
		String defaultSiteRepresentation, defaultComments;
		Location defaultLocation1, defaultLocation2;

		// get various lists from the database
		ArrayList faultSectionNamesList = getFaultSectionNames();
		ArrayList siteRepresentations = getSiteRepresentations();
		Estimate dipEstVal=null;

		// if a new site has to be added, set some default values
		defaultSiteName =" ";
		defaultOldSiteId = " ";
		defaultFaultSectionName = (String)faultSectionNamesList.get(0);
		defaultSiteRepresentation = (String)siteRepresentations.get(0);
		defaultComments = " ";
		defaultLocation1 = new Location(DEFAULT_LAT_VAL, DEFAULT_LON_VAL);
		defaultLocation2 = new Location(DEFAULT_LAT_VAL, DEFAULT_LON_VAL);
		dipEstVal=null;


		// parameter so that user can enter the site name
		siteNameParam = new StringParameter(SITE_NAME_PARAM_NAME, defaultSiteName);
		siteNameParamEditor = new StringParameterEditor(siteNameParam);

		// parameter so that user can enter a site Id
		oldSiteIdParam = new StringParameter(OLD_SITE_ID_PARAM_NAME,defaultOldSiteId);
		oldSiteIdParamEditor = new StringParameterEditor(oldSiteIdParam);

		// site location parameter
		siteLocationParam = createLocationParam(defaultLocation1);
		siteLocationParamEditor = new LocationParameterEditor(siteLocationParam,true);

		// second site location, in "Between Locations" is selected as the Site type
		siteLocationParam2 = createLocationParam(defaultLocation2);
		siteLocationParamEditor2 = new LocationParameterEditor(siteLocationParam2,true);

		// choose the fault with which this site is associated
		assocWithFaultParam = new StringParameter(ASSOCIATED_WITH_FAULT_PARAM_NAME, faultSectionNamesList,
				defaultFaultSectionName);
		assocWithFaultParamEditor = new ConstrainedStringParameterEditor(assocWithFaultParam);

		// how representative is this site?
		siteRepresentationParam = new StringParameter(SITE_REPRESENTATION_PARAM_NAME, siteRepresentations,
				defaultSiteRepresentation);
		siteRepresentationParamEditor = new ConstrainedStringParameterEditor(siteRepresentationParam);
		// dip estimate
		ArrayList allowedEstimates = EstimateConstraint.createConstraintForPositiveDoubleValues();
		EstimateConstraint estConstraint = new EstimateConstraint(DIP_MIN, DIP_MAX, allowedEstimates);
		this.dipEstParam = new EstimateParameter(DIP_PARAM_NAME,
				estConstraint,
				DIP_UNITS,
				dipEstVal);
		dipEstParamEditor  = new ConstrainedEstimateParameterEditor(dipEstParam, true);
		// user comments
		this.commentsParam = new StringParameter(COMMENTS_PARAM_NAME,defaultComments);
		this.commentsParamEditor = new CommentsParameterEditor(commentsParam);
	}

	/**
	 * create location parameter
	 *
	 * @throws InvalidRangeException
	 * @throws ParameterException
	 * @throws ConstraintException
	 */
	private LocationParameter createLocationParam(Location loc) throws InvalidRangeException,
	ParameterException, ConstraintException {
		//creating the Location parameterlist for the Site
		DoubleParameter siteLocLatParam = new DoubleParameter(LAT_PARAM_NAME,
				GeoTools.LAT_MIN, GeoTools.LAT_MAX,LAT_LON_UNITS,new Double(loc.getLatitude()));
		DoubleParameter siteLocLonParam = new DoubleParameter(LON_PARAM_NAME,
				GeoTools.LON_MIN,GeoTools.LON_MAX,LAT_LON_UNITS, new Double(loc.getLongitude()));
		DoubleParameter siteLocElevationParam = new DoubleParameter(ELEVATION_PARAM_NAME,
				GeoTools.DEPTH_MIN, GeoTools.DEPTH_MAX, ELEVATION_UNITS);
		// allow null value in elevation
		siteLocElevationParam.getConstraint().setNullAllowed(true);
		ParameterList siteLocParamList = new ParameterList();
		siteLocParamList.addParameter(siteLocLatParam);
		siteLocParamList.addParameter(siteLocLonParam);
		siteLocParamList.addParameter(siteLocElevationParam);
		Location siteLoc = new Location(loc.getLatitude(),
				loc.getLongitude());

		// Site Location(Lat/lon/)
		return (new LocationParameter(SITE_LOCATION_PARAM_NAME,siteLocParamList,
				siteLoc));
	}


	/**
	 * If site type added is "BETWEEN LOCATIONS", then  allow the user to enter
	 * the second location
	 *
	 * @param event
	 */
	public void parameterChange(ParameterChangeEvent event) {
		if(event.getParameterName().equalsIgnoreCase(SITE_TYPE_PARAM_NAME))
			setSecondLocationVisible();
	}

	/**
	 * If site type added is "BETWEEN LOCATIONS", then  allow the user to enter
	 * the second location
	 *
	 */
	private void setSecondLocationVisible() {
		ArrayList selectedSiteType =  (ArrayList)this.siteTypeParam.getValue();
		if(selectedSiteType.contains(BETWEEN_LOCATIONS_SITE_TYPE))
			this.siteLocationParamEditor2.setVisible(true);
		else this.siteLocationParamEditor2.setVisible(false);
	}


	/**
	 * Get the site representations.
	 * It gets the SITE REPRSENTATIONS from the database
	 *
	 * @return
	 */
	private ArrayList getSiteRepresentations() {
		ArrayList siteRepresentationVOs = siteRepresentationDAO.getAllSiteRepresentations();
		ArrayList siteRepresentations = new ArrayList();
		for(int i=0; i<siteRepresentationVOs.size(); ++i) {
			siteRepresentations.add(((SiteRepresentation)siteRepresentationVOs.get(i)).getSiteRepresentationName());
		}
		return siteRepresentations;
	}

	/**
	 * Get a list of available references.
	 * @return
	 */
	private ArrayList getAvailableReferences() {
		this.referenceList  = referenceDAO.getAllReferencesSummary();
		this.referenceSummaryList = new ArrayList();
		for(int i=0; referenceList!=null && i<referenceList.size(); ++i)
			referenceSummaryList.add(((Reference)referenceList.get(i)).getSummary());
		return referenceSummaryList;
	}


	/**
	 * It gets all the Fault Section Names from the database
	 * @return
	 */
	private ArrayList getFaultSectionNames() {
		ArrayList faultSectionSummaryList = faultSectionDAO.getAllFaultSectionsSummary();
		ArrayList faultSectionNamesList = new ArrayList();
		for(int i=0; i<faultSectionSummaryList.size(); ++i) {
			faultSectionNamesList.add(((FaultSectionSummary)faultSectionSummaryList.get(i)).getAsString());
		}
		return faultSectionNamesList;
	}

	/**
	 * Get the study types.
	 * It gets all the SITE TYPES from the database
	 *
	 * @return
	 */
	private ArrayList getSiteTypes() {
		ArrayList siteTypeVOs = siteTypeDAO.getAllSiteTypes();
		ArrayList siteTypesList = new ArrayList();
		for(int i=0; i<siteTypeVOs.size(); ++i)
			siteTypesList.add(((SiteType)siteTypeVOs.get(i)).getSiteType());
		return siteTypesList;
	}

	/**
	 * This function is called whenever a new site type/ new Reference is added
	 * to the database
	 *
	 * @param event
	 */
	public void dbAdditionSuccessful(DbAdditionSuccessEvent event) {
		Object source  = event.getSource();
		if(source==this.addNewSiteType) makeSiteTypeParamAndEditor();
		else if(source == this.addNewReference) makeReferenceParamAndEditor();
		this.labeledBoxPanel.updateUI();
	}
}
