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

package org.opensha.refFaultParamDb.gui;

import java.awt.BorderLayout;
import java.awt.GridBagConstraints;
import java.awt.GridBagLayout;
import java.awt.Insets;
import java.text.DecimalFormat;
import java.util.ArrayList;

import javax.swing.JFrame;
import javax.swing.JOptionPane;
import javax.swing.JPanel;
import javax.swing.JScrollPane;
import javax.swing.JSplitPane;
import javax.swing.JTabbedPane;
import javax.swing.JTextArea;
import javax.swing.UIManager;

import org.opensha.commons.data.estimate.DiscreteValueEstimate;
import org.opensha.commons.data.estimate.DiscretizedFuncEstimate;
import org.opensha.commons.data.estimate.Estimate;
import org.opensha.commons.data.estimate.IntegerEstimate;
import org.opensha.commons.data.estimate.LogNormalEstimate;
import org.opensha.commons.data.estimate.MinMaxPrefEstimate;
import org.opensha.commons.data.estimate.NormalEstimate;
import org.opensha.commons.data.function.ArbitrarilyDiscretizedFunc;
import org.opensha.commons.data.function.DiscretizedFunc;
import org.opensha.commons.exceptions.ConstraintException;
import org.opensha.commons.gui.LabeledBoxPanel;
import org.opensha.commons.param.StringParameter;
import org.opensha.commons.param.editor.ConstrainedStringParameterEditor;
import org.opensha.commons.param.event.ParameterChangeEvent;
import org.opensha.commons.param.event.ParameterChangeListener;
import org.opensha.refFaultParamDb.dao.db.CombinedEventsInfoDB_DAO;
import org.opensha.refFaultParamDb.dao.db.DB_AccessAPI;
import org.opensha.refFaultParamDb.dao.db.DB_ConnectionPool;
import org.opensha.refFaultParamDb.dao.db.ServerDB_Access;
import org.opensha.refFaultParamDb.data.ExactTime;
import org.opensha.refFaultParamDb.data.TimeAPI;
import org.opensha.refFaultParamDb.data.TimeEstimate;
import org.opensha.refFaultParamDb.gui.view.SiteSelectionAPI;
import org.opensha.refFaultParamDb.gui.view.ViewCumDisplacement;
import org.opensha.refFaultParamDb.gui.view.ViewIndividualEvent;
import org.opensha.refFaultParamDb.gui.view.ViewNumEvents;
import org.opensha.refFaultParamDb.gui.view.ViewSequences;
import org.opensha.refFaultParamDb.gui.view.ViewSiteCharacteristics;
import org.opensha.refFaultParamDb.gui.view.ViewSlipRate;
import org.opensha.refFaultParamDb.gui.view.ViewTimeSpan;
import org.opensha.refFaultParamDb.vo.CombinedDisplacementInfo;
import org.opensha.refFaultParamDb.vo.CombinedEventsInfo;
import org.opensha.refFaultParamDb.vo.CombinedNumEventsInfo;
import org.opensha.refFaultParamDb.vo.CombinedSlipRateInfo;
import org.opensha.refFaultParamDb.vo.EstimateInstances;
import org.opensha.refFaultParamDb.vo.EventSequence;
import org.opensha.refFaultParamDb.vo.PaleoEvent;
import org.opensha.refFaultParamDb.vo.PaleoSite;
import org.opensha.refFaultParamDb.vo.Reference;
import org.opensha.sha.gui.infoTools.CalcProgressBar;

/**
 * <p>Title: PaleoSiteApp2.java </p>
 * <p>Description:  Gets all the available paleo sites from the database and
 * displays information about a user selected site </p>
 * <p>Description:  This application allows user to add/view/edit information
 * for a paleo site </p>
 * <p>Copyright: Copyright (c) 2002</p>
 * <p>Company: </p>
 * @author not attributable
 * @version 1.0
 */

public class PaleoSiteApp2 extends JFrame implements SiteSelectionAPI, ParameterChangeListener {
	
	private final static DB_AccessAPI dbConnection = DB_ConnectionPool.getLatestReadWriteConn();

	private final static int WIDTH = 925;
	private final static int HEIGHT = 800;

	private final static String TITLE =
		"California Reference Geologic Fault Parameter (Paleo Site) GUI";
	private final static String TIMESPAN_PARAM_NAME = "TimeSpans";
	private final static String DATA_SPECIFIC_TO_TIME_INTERVALS =
		"Data currently in this database";
	private final static String SLIP_DISP_NUMEVENTS_SEQUENCES_TITLE = "Slip Rate, Displacement and Num Events";
	private final static String EVENTS_TITLE = "Events";
	private final static String SLIP_RATE_TITLE = "Slip Rate";
	private final static String DISPLACEMENT_TITLE = "Displacement";
	private final static String NUM_EVENTS_TITLE = "Num Events";
	private final static String SEQUENCE_TITLE = "Sequences";

	// various parameters
	private ViewSiteCharacteristics viewPaleoSites;
	private StringParameter timeSpanParam;
	private ConstrainedStringParameterEditor timeSpanParamEditor;

	// various parameter editors
	private BorderLayout borderLayout2 = new BorderLayout();
	private JSplitPane topSplitPane = new JSplitPane();
	private JPanel mainPanel = new JPanel();
	private JSplitPane mainSplitPane = new JSplitPane();
	private JSplitPane infoForTimeSpanSplitPane = new JSplitPane();
	private JSplitPane timespanSplitPane = new JSplitPane();
	private JSplitPane timeSpanSelectionSplitPane = new JSplitPane();
	private BorderLayout borderLayout1 = new BorderLayout();
	private JScrollPane statusScrollPane = new JScrollPane();
	private JTextArea statusTextArea = new JTextArea();
	private JTabbedPane eventSequenceTabbedPane = new JTabbedPane();
	private JTabbedPane slipDispNumEventsTabbedPane = new JTabbedPane();

	// panel to display the start time/end time and comments
	private ViewTimeSpan timeSpanPanel = new ViewTimeSpan();
	private LabeledBoxPanel availableTimeSpansPanel;
	private GridBagLayout gridBagLayout = new GridBagLayout();

	// panels for viewing slip rate, displacement and num events
	private ViewSlipRate slipRatePanel = new ViewSlipRate();
	private ViewCumDisplacement displacementPanel = new ViewCumDisplacement();
	private ViewNumEvents numEventsPanel= new ViewNumEvents() ;
	private ViewIndividualEvent individualEventPanel = new ViewIndividualEvent(dbConnection);
	private ViewSequences sequencesPanel = new ViewSequences();

	private ArrayList combinedEventsInfoList;
	private CombinedEventsInfo combinedEventsInfo ;
	private PaleoSite paleoSite;
	private CombinedEventsInfoDB_DAO combinedEventsInfoDAO;

	private final static String NOT_AVAILABLE = "Not Available";
	private CalcProgressBar progressBar = new CalcProgressBar("Retrieving data", "Retrieving data from database....");
	private final static String MSG_ERROR_RETRIEVING_DATA = "Error Retrieving data for the site";
	
	/**
	 * Constructor.
	 * Gets all the available paleo sites from the database and displays
	 * information about a user selected site
	 */
	public PaleoSiteApp2() {
		combinedEventsInfoDAO = new CombinedEventsInfoDB_DAO(dbConnection);
		try {
			setTitle(TITLE);
			jbInit();
			addTimeSpansPanel();
			addSitesPanel(); // add the available sites from database for viewing
			pack();
			setSize(WIDTH, HEIGHT);
			this.setLocationRelativeTo(null);
			this.setVisible(true);
		}
		catch (Exception e) {
			e.printStackTrace();
		}
	}

	/**
	 * Add the available time spans for this site
	 */
	private void addTimeSpansPanel() {
		availableTimeSpansPanel = new LabeledBoxPanel(this.gridBagLayout);
		availableTimeSpansPanel.setTitle(DATA_SPECIFIC_TO_TIME_INTERVALS);
		timeSpanSelectionSplitPane.add(availableTimeSpansPanel, JSplitPane.TOP);
	}

	private void makeTimeSpanParamAndEditor() throws ConstraintException {
		// remove the editor if it already exists
		if(timeSpanParamEditor!=null) availableTimeSpansPanel.remove(timeSpanParamEditor);
		// get all the start and end times associated with this site
		ArrayList timeSpans = getAllTimeSpans();
		timeSpanParam = new StringParameter(TIMESPAN_PARAM_NAME, timeSpans,
				(String) timeSpans.get(0));
		timeSpanParam.addParameterChangeListener(this);
		timeSpanParamEditor = new ConstrainedStringParameterEditor(timeSpanParam);
		availableTimeSpansPanel.add(timeSpanParamEditor,new GridBagConstraints( 0, 0, 1, 1, 1.0, 1.0
				,GridBagConstraints.CENTER, GridBagConstraints.BOTH, new Insets( 0, 0, 0, 0 ), 0, 0 ) );
		viewInfoBasedOnSelectedTimeSpan();
		availableTimeSpansPanel.updateUI();
	}

	/**
	 * Get all the timespans from the database.
	 *
	 *
	 * @return
	 */
	private ArrayList getAllTimeSpans() {
		ArrayList timeSpansList = new ArrayList();;
		if (isTestSite()) {
			timeSpansList.add("TimeSpan 1");
			timeSpansList.add("TimeSpan 2");
		} else if(!isValidSiteAndInfoAvailable()) {
			// this is a valid site but info available for this
			timeSpansList.add(this.NOT_AVAILABLE);
		} else {
			for(int i=combinedEventsInfoList.size()-1; i>=0; --i) {
				// valid site and info available for the site
				CombinedEventsInfo combinedEventsInfo = (CombinedEventsInfo)combinedEventsInfoList.get(i);
				ArrayList referenceList  = combinedEventsInfo.getReferenceList();

				timeSpansList.add(getTimeString(combinedEventsInfo.getStartTime())+" to "+
						getTimeString(combinedEventsInfo.getEndTime()) +
						"     (Entry Date:"+combinedEventsInfo.getEntryDate()+")");
			}
		}
		return timeSpansList;
	}

	/**
	 * convert reference list to string of references
	 * @param references
	 * @return
	 */
	private String getReferencesAsString(ArrayList references) {
		String str = "";
		for(int i=0; i<references.size(); ++i)
			str+=((Reference)references.get(i)).getSummary()+";";
		return str;
	}


	/**
	 * whether the current site selected by user is a test site
	 * @return
	 */
	private boolean isTestSite() {
		return (combinedEventsInfoList == null &&  // if it is test site
				(paleoSite==null || paleoSite.getSiteName().equalsIgnoreCase(ViewSiteCharacteristics.TEST_SITE)));
	}

	private boolean isValidSiteAndInfoAvailable() {
		return (combinedEventsInfoList != null && combinedEventsInfoList.size()>0);
	}


	public void parameterChange(ParameterChangeEvent event) {
		String paramName = event.getParameterName();
		if(paramName.equalsIgnoreCase(TIMESPAN_PARAM_NAME)) viewInfoBasedOnSelectedTimeSpan();
	}

	/**
	 * View information or the selected time span
	 */
	private void viewInfoBasedOnSelectedTimeSpan() {
		ArrayList allowedStrings = timeSpanParam.getAllowedStrings();
		String timeSpan = (String)timeSpanParam.getValue();
		int index = allowedStrings.indexOf(timeSpan);
		if(this.isValidSiteAndInfoAvailable())
			combinedEventsInfo = (CombinedEventsInfo)this.combinedEventsInfoList.get(index);
		else combinedEventsInfo = null;
		viewSlipRateForTimePeriod(combinedEventsInfo);
		viewNumEventsForTimePeriod(combinedEventsInfo);
		viewDisplacementForTimePeriod(combinedEventsInfo);
		viewSequencesForTimePeriod(combinedEventsInfo);
		viewTimeSpanInfo(combinedEventsInfo);
	}

	/**
	 * Get the timespan as a string value which can be displayed in the StringParameter
	 * @param startTime
	 * @param endTime
	 * @return
	 */
	private String getTimeString(TimeAPI time) {
		String timeString="";
		DecimalFormat yearFormat = new DecimalFormat("0");
		DecimalFormat kaFormat = new DecimalFormat("0.##");
		DecimalFormat format;

		if(time instanceof ExactTime) { // if it is exact time
			ExactTime exactTime = (ExactTime)time;
			if(exactTime.getIsNow()) timeString+="Now";
			else timeString+=exactTime.getYear()+" "+exactTime.getEra();
		} else if(time instanceof TimeEstimate) { // if it is time estimate
			TimeEstimate timeEstimate = (TimeEstimate) time;
			if (timeEstimate.isKaSelected()) // if user entered ka values
				format = kaFormat;
			else format = yearFormat;

			Estimate estimate = timeEstimate.getEstimate();
			// for normal estimate, mean is displayed
			if (estimate instanceof NormalEstimate)
				timeString+=format.format(estimate.getMean());
			// if estimate is of log normal type, linear median is displayed
			else if(estimate instanceof LogNormalEstimate)
				timeString+=format.format(((LogNormalEstimate)estimate).getLinearMedian());
			// point of highest prob is displayed
			else if (estimate instanceof DiscretizedFuncEstimate) {
				DiscretizedFunc func = ( (DiscretizedFuncEstimate) estimate).getValues();
				timeString +=format.format(func.getFirstInterpolatedX(func.getMaxY()));
			}
			// try to display pref value, then maximum and then minimum
			else if (estimate instanceof MinMaxPrefEstimate) {
				MinMaxPrefEstimate minMaxPrefEst =  (MinMaxPrefEstimate) estimate;
				if(!Double.isNaN(minMaxPrefEst.getPreferred()))
					timeString +=  format.format(minMaxPrefEst.getPreferred());
				else if(!Double.isNaN(minMaxPrefEst.getMaximum()))
					timeString +=   format.format(minMaxPrefEst.getMaximum());
				else if(!Double.isNaN(minMaxPrefEst.getMinimum()))
					timeString +=   format.format(minMaxPrefEst.getMinimum());
			}
			if (timeEstimate.isKaSelected()) // if user entered ka values
				timeString += "ka";
			else  timeString += " "+timeEstimate.getEra();

		}
		return timeString;
	}


	/**
	 * Get the timespan as a string value which can be displayed in the StringParameter
	 * @param startTime
	 * @param endTime
	 * @return
	 */
	/*private String getTimeString(TimeAPI time) {
    String timeString="";
    if(time instanceof ExactTime) { // if it is exact time
      ExactTime exactTime = (ExactTime)time;
      timeString+="Exact Time:"+exactTime.getMonth()+"/"+exactTime.getDay()+"/"+
          exactTime.getYear()+exactTime.getEra()+" "+exactTime.getHour()+":"+exactTime.getMinute()+":"+
          exactTime.getSecond();
    } else if(time instanceof TimeEstimate) { // if it is time estimate
      TimeEstimate timeEstimate = (TimeEstimate) time;
      Estimate estimate = timeEstimate.getEstimate();
      if (timeEstimate.isKaSelected()) // if user entered ka values
        timeString += "Time Estimate:Units=ka,Zero Year=" +
            timeEstimate.getZeroYear()+":";
      else  timeString += "Time Estimate:Units=Calendar years"+":";
      if (estimate instanceof NormalEstimate) // for normal estimate
        timeString+=estimate.getName()+":Mean="+estimate.getMean()+","+
            "StdDev="+estimate.getStdDev();
      else if(estimate instanceof LogNormalEstimate)  // if estimate is of log normal type
        timeString+=estimate.getName()+":Linear Median="+
            ((LogNormalEstimate)estimate).getLinearMedian()+","+
            "StdDev="+estimate.getStdDev();
      else if (estimate instanceof DiscretizedFuncEstimate) {
        DiscretizedFunc func = ( (DiscretizedFuncEstimate) estimate).getValues();
        timeString += estimate.getName() + ":";
        for (int i = 0; i < func.getNum(); ++i)
          timeString += func.getX(i) + ",";
      }
      else if (estimate instanceof FractileListEstimate) {
        DiscretizedFunc func = ((FractileListEstimate)estimate).getValues();
        timeString +=  estimate.getName()+":";
        for(int i=0; i<func.getNum(); ++i)
          timeString+=  func.getX(i)+",";
      } else if (estimate instanceof MinMaxPrefEstimate) {
        MinMaxPrefEstimate minMaxPrefEst =  (MinMaxPrefEstimate) estimate;
        timeString += minMaxPrefEst.getName() + ":";
        if(!Double.isNaN(minMaxPrefEst.getMinimumX()))
          timeString +=   "Min="+minMaxPrefEst.getMinimumX()+",";
        if(!Double.isNaN(minMaxPrefEst.getMaximumX()))
          timeString +=   "Max="+minMaxPrefEst.getMaximumX()+",";
        if(!Double.isNaN(minMaxPrefEst.getPreferredX()))
          timeString +=  "Pref="+minMaxPrefEst.getPreferredX()+",";
      }
    }
    return timeString;
  }*/


	/**
	 * Add all the components to the GUI
	 * @throws java.lang.Exception
	 */

	private void jbInit() throws Exception {
		this.getContentPane().setLayout(borderLayout2);
		mainPanel.setLayout(borderLayout1);
		mainSplitPane.setOrientation(JSplitPane.HORIZONTAL_SPLIT);
		timespanSplitPane.setOrientation(JSplitPane.HORIZONTAL_SPLIT);
		topSplitPane.setOrientation(JSplitPane.VERTICAL_SPLIT);
		timeSpanSelectionSplitPane.setOrientation(JSplitPane.VERTICAL_SPLIT);
		statusTextArea.setEnabled(false);
		statusTextArea.setEditable(false);
		statusTextArea.setText("");
		this.setDefaultCloseOperation(EXIT_ON_CLOSE);
		this.getContentPane().add(topSplitPane, BorderLayout.CENTER);
		topSplitPane.add(mainPanel, JSplitPane.TOP);
		mainPanel.add(mainSplitPane, BorderLayout.CENTER);
		//mainSplitPane.add(timespanSplitPane, JSplitPane.LEFT);
		eventSequenceTabbedPane.add(SLIP_DISP_NUMEVENTS_SEQUENCES_TITLE, timeSpanSelectionSplitPane);
		eventSequenceTabbedPane.add(EVENTS_TITLE, this.individualEventPanel);
		mainSplitPane.add(eventSequenceTabbedPane, JSplitPane.RIGHT);
		timeSpanSelectionSplitPane.add(timespanSplitPane, JSplitPane.BOTTOM);
		timespanSplitPane.add(slipDispNumEventsTabbedPane, JSplitPane.RIGHT);
		//mainSplitPane.add(infoForTimeSpanSplitPane, JSplitPane.RIGHT);
		topSplitPane.add(statusScrollPane, JSplitPane.BOTTOM);
		statusScrollPane.getViewport().add(statusTextArea, null);
		timespanSplitPane.add(timeSpanPanel, JSplitPane.LEFT);
		topSplitPane.setDividerLocation(625);
		mainSplitPane.setDividerLocation(200);
		timeSpanSelectionSplitPane.setDividerLocation(75);
		timespanSplitPane.setDividerLocation(300);
		slipDispNumEventsTabbedPane.add(SLIP_RATE_TITLE, slipRatePanel);
		slipDispNumEventsTabbedPane.add(DISPLACEMENT_TITLE, displacementPanel);
		slipDispNumEventsTabbedPane.add(NUM_EVENTS_TITLE, numEventsPanel);
		slipDispNumEventsTabbedPane.add(SEQUENCE_TITLE, sequencesPanel);
	}

	/**
	 * Add the panel to display the available paleo sites in the database
	 */
	private void addSitesPanel() {
		viewPaleoSites = new ViewSiteCharacteristics(dbConnection, this);
		mainSplitPane.add(viewPaleoSites, JSplitPane.LEFT);
	}

	//static initializer for setting look & feel
	static {
		String osName = System.getProperty("os.name");
		try {
			UIManager.setLookAndFeel(UIManager.getSystemLookAndFeelClassName());
		}
		catch(Exception e) {
		}
	}

	/**
	 * Get the currently displayed data in the window
	 * @return
	 */
	public CombinedEventsInfo getSelectedCombinedInfo() {
		return combinedEventsInfo;
	}

	/**
	 * display the slip Rate info for the selected time period
	 */
	private void viewSlipRateForTimePeriod(CombinedEventsInfo combinedEventsInfo) {
		if(this.isTestSite()) {
			CombinedSlipRateInfo combinedSlipRateInfo = new CombinedSlipRateInfo();
			// FAKE DATA FOR TEST SITE
			// Slip Rate Estimate
			LogNormalEstimate slipRateEstimate = new LogNormalEstimate(1.5, 0.25);
			combinedSlipRateInfo.setSlipRateEstimate(new EstimateInstances(slipRateEstimate,"units"));
			// Aseismic slip rate estimate
			NormalEstimate aSiemsicSlipEstimate = new NormalEstimate(0.7, 0.5);
			combinedSlipRateInfo.setASeismicSlipFactorEstimateForSlip(new EstimateInstances(aSiemsicSlipEstimate,"units"));
			// comments
			String comments = "Pertinent comments will be displayed here";
			combinedSlipRateInfo.setSlipRateComments(comments);
			slipRatePanel.setInfo(combinedSlipRateInfo);
		} else if(this.isValidSiteAndInfoAvailable() &&
				combinedEventsInfo.getCombinedSlipRateInfo()!=null)  { // information available FOR THIS SITE
			CombinedSlipRateInfo combinedSlipRateInfo = combinedEventsInfo.getCombinedSlipRateInfo();
			this.slipRatePanel.setInfo(combinedSlipRateInfo);
		} else { // valid site but no info available
			slipRatePanel.setInfo(null);
		}

	}

	/**
	 * display the sequences for the selected time period
	 */
	private void viewSequencesForTimePeriod(CombinedEventsInfo combinedEventsInfo) {
		if(this.isTestSite()) {
			// FAKE DATA FOR TEST SITE
			ArrayList fakeSeqList = new ArrayList();

			EventSequence seq1 = new EventSequence();
			EventSequence seq2 = new EventSequence();
			fakeSeqList.add(seq1);
			fakeSeqList.add(seq2);

			seq1.setSequenceName("Test Sequence 1");
			seq2.setSequenceName("Test Sequence 2");
			// comments
			String comments = "Comments about this sequence";
			seq1.setComments(comments);
			seq2.setComments(comments);
			// events in this sequence
			PaleoEvent event1 = new PaleoEvent();
			event1.setEventName("Event 5");
			PaleoEvent event2 = new PaleoEvent();
			event2.setEventName("Event 6");
			ArrayList eventsList = new ArrayList();
			eventsList.add(event1);
			eventsList.add(event2);
			seq1.setEventsParam(eventsList);
			seq2.setEventsParam(eventsList);
			// sequence prob
			double sequenceProb=0.5;
			seq1.setSequenceProb(sequenceProb);
			seq2.setSequenceProb(sequenceProb);
			// missed events prob
			double[] missedEventProb = {0.1,0.5, 0.4};
			seq1.setMissedEventsProbList(missedEventProb);
			seq2.setMissedEventsProbList(missedEventProb);
			sequencesPanel.setSequenceList(fakeSeqList);
		} else if(this.isValidSiteAndInfoAvailable() &&
				combinedEventsInfo.getEventSequence()!=null)  { // information available FOR THIS SITE
			this.sequencesPanel.setSequenceList(combinedEventsInfo.getEventSequence());
		} else { // valid site but no info available
			sequencesPanel.setSequenceList(null);
		}

	}



	/**
	 * Display the displacement info for the selected time period
	 */
	private void viewDisplacementForTimePeriod(CombinedEventsInfo combinedEventsInfo) {
		if(this.isTestSite()) {
			CombinedDisplacementInfo combinedDisplacementInfo = new CombinedDisplacementInfo();
			combinedDisplacementInfo.setMeasuredComponentQual("Total");
			// FAKE DATA FOR TEST SITE
			// Slip Rate Estimate
			MinMaxPrefEstimate diplacementEstimate = new MinMaxPrefEstimate(60, 150, 95, 0.2, 0.8, 0.7);
			combinedDisplacementInfo.setDisplacementEstimate(new EstimateInstances(diplacementEstimate,"units"));
			// Aseismic slip rate estimate
			ArbitrarilyDiscretizedFunc func = new ArbitrarilyDiscretizedFunc();
			func.set(0.0, 0.1);
			func.set(0.5, 0.4);
			func.set(0.6, 0.4);
			func.set(1.0, 0.1);
			DiscreteValueEstimate aSiemsicSlipEstimate = new DiscreteValueEstimate(func, true);
			combinedDisplacementInfo.setASeismicSlipFactorEstimateForDisp(new EstimateInstances(aSiemsicSlipEstimate,"units"));
			// comments
			String comments = "Pertinent comments will be displayed here";
			combinedDisplacementInfo.setDisplacementComments(comments);
			combinedDisplacementInfo.setSenseOfMotionQual("RL-R");
			MinMaxPrefEstimate rakeEst = new MinMaxPrefEstimate(165, 180, 170, 0.4, 0.7, 0.5);
			combinedDisplacementInfo.setSenseOfMotionRake(new EstimateInstances(rakeEst,""));
			displacementPanel.setInfo(combinedDisplacementInfo);
		} else if(this.isValidSiteAndInfoAvailable() &&
				combinedEventsInfo.getCombinedDisplacementInfo()!=null)  { // information available FOR THIS SITE
			CombinedDisplacementInfo combinedDisplacementInfo = combinedEventsInfo.getCombinedDisplacementInfo();
			displacementPanel.setInfo(combinedDisplacementInfo);
		} else { // valid site but no info available
			displacementPanel.setInfo(null);
		}

	}

	/**
	 * display the Num events info for the selected time period
	 */
	private void viewNumEventsForTimePeriod(CombinedEventsInfo combinedEventsInfo) {
		if(isTestSite()) {
			// Num Events Estimate
			// FAKE DATA FOR TEST SITE
			ArbitrarilyDiscretizedFunc func = new ArbitrarilyDiscretizedFunc();
			func.set(4.0, 0.2);
			func.set(5.0, 0.3);
			func.set(6.0, 0.1);
			func.set(7.0, 0.4);
			func.setXAxisName("# Events");
			func.setYAxisName("Prob this is correct #");
			IntegerEstimate numEventsEstimate = new IntegerEstimate(func, false);
			String comments = "Pertinent comments will be displayed here";
			this.numEventsPanel.setInfo(numEventsEstimate, comments);
		}else if(this.isValidSiteAndInfoAvailable() && combinedEventsInfo.getCombinedNumEventsInfo()!=null) {
			CombinedNumEventsInfo combinedNumEventsInfo =combinedEventsInfo.getCombinedNumEventsInfo();
			numEventsPanel.setInfo(combinedNumEventsInfo.getNumEventsEstimate().getEstimate(),
					combinedNumEventsInfo.getNumEventsComments());
		}
		else { // information not available yet
			this.numEventsPanel.setInfo(null, null);
		}
	}

	/**
	 * Whenever a user selects a site, this function is called in the listener class
	 * @param siteName
	 */
	public void siteSelected(PaleoSite paleoSite, int referenceId) {
		this.paleoSite = paleoSite;
		String siteName;
		progressBar.setVisible(true);
		try {
			if (paleoSite == null) { // for test site
				siteName = ViewSiteCharacteristics.TEST_SITE;
				combinedEventsInfoList = null;
			}
			else { // for actual sites from database
				siteName = paleoSite.getSiteName();
				this.combinedEventsInfoList = combinedEventsInfoDAO.
				getCombinedEventsInfoList(paleoSite.getSiteId(), referenceId);
			}
			makeTimeSpanParamAndEditor(); // get a list of all the timespans for which data is available for this site
			this.individualEventPanel.setSite(paleoSite); // view the events for this site
		}catch(Exception e) {
			e.printStackTrace();
			JOptionPane.showMessageDialog(this, MSG_ERROR_RETRIEVING_DATA);
		}
		progressBar.setVisible(false);
	}


	/**
	 * Add the start and end time estimate parameters
	 */
	private void viewTimeSpanInfo(CombinedEventsInfo combinedEventsInfo) {
		if (isTestSite()) {
			// FAKE DATA FOR TEST SITE
			ExactTime endTime = new ExactTime(1857, 1, 15, 10, 56, 21, TimeAPI.AD, false);
			TimeEstimate startTime = new TimeEstimate();
			startTime.setForKaUnits(new NormalEstimate(1000, 50), 1950);
			String comments = "Summary of Dating techniques and dated features ";
			ArrayList references = new ArrayList();
			references.add("Ref 4");
			references.add("Ref 1");
			// timeSpan panel which will contain start time and end time
			this.timeSpanPanel.setTimeSpan(startTime, endTime, comments, references,null, null, null);
		} else if(this.isValidSiteAndInfoAvailable()){
			ArrayList refList =  combinedEventsInfo.getReferenceList();
			ArrayList summaryList = new ArrayList();
			for(int i=0 ; i<refList.size(); ++i)
				summaryList.add(((Reference)refList.get(i)).getSummary());

			timeSpanPanel.setTimeSpan(combinedEventsInfo.getStartTime(),
					combinedEventsInfo.getEndTime(),
					combinedEventsInfo.getDatedFeatureComments(),
					summaryList,
					combinedEventsInfo.getEntryDate(),
					combinedEventsInfo.getContributorName(),
					combinedEventsInfo.getDataSource());
		}
		else {
			this.timeSpanPanel.setTimeSpan(null, null, null, null,null,null, null);
		}
	}

	public static void main(String args[]) {
		new LoginWindow(dbConnection, PaleoSiteApp2.class.getName());
	}
}

