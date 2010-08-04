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

package org.opensha.nshmp.util;

import java.util.ArrayList;
import java.util.Properties;

import javax.swing.ImageIcon;

import org.opensha.commons.util.FileUtils;

/**
 * <p>Title: GlobalConstants</p>
 *
 * <p>Description: This class provides the static declaration for some of the
 * variables that always remain constant.</p>
 *
 * @author  Ned Field, Nitin Gupta and E.V. Leyendecker
 * @version 1.0
 */
public final class GlobalConstants {
	public static final String VERSION = "Version: 5.0.9a - 10/21/2009";
	
	// Live application settings.  We use geohazards as a proxy to ghscweb. If that breaks we "can" connect directly.
	//public static final String SERVLET_PATH = "http://geohazards.usgs.gov/GroundMotionTool/servlet/HazardCalcServlet";
	//public static final String SERVLET_PATH = "http://gldplone.cr.usgs.gov/GroundMotionTool/servlet/HazardCalcServlet";
	//public static final String SERVLET_PATH = "http://137.227.224.99/GroundMotionTool/servlet/HazardCalcServlet";
	
	// Development application settings.       
	//public static final String SERVLET_PATH = "http://geohazards.usgs.gov/GroundMotionDevel/servlet/HazardCalcDevel";
	
	// Use this instead because the netcontinuum sucks terribly.
	public static final String SERVLET_PATH = "http://137.227.224.99/GroundMotionDevel/servlet/HazardCalcDevel";
	
	//public static final String SERVLET_PATH = "http://gldplone.cr.usgs.gov/GroundMotionDevel/servlet/HazardCalcDevel";
	
	
	//data files path
	public final static String DATA_FILE_PATH = "/usr/local/tomcat/webapps/dataFiles/"; // path at gldplone (geohazards)
  
	public final static String registrationName =
      "rmi://gravity.usc.edu:1099/USGS_HazardDataCalc_FactoryServer";

  private final static String USGS_LOGO = "logos/usgslogo.gif";
	private final static String USGS_LOGO_ONLY = "logos/usgs_logoonly.gif";
  public final static ImageIcon USGS_LOGO_ICON = new ImageIcon(FileUtils.loadImage(USGS_LOGO));
	public final static ImageIcon USGS_LOGO_ONLY_ICON = new
		ImageIcon(FileUtils.loadImage(USGS_LOGO_ONLY));

  //static declaration for the supported geographic regions
  public static final String CONTER_48_STATES = "Conterminous 48 States";
  public static final String ALASKA = "Alaska";
  public static final String HAWAII = "Hawaii";
  //public static final String INDONESIA = "Western Indonesia (Preliminary)";
  public static final String PUERTO_RICO = "Puerto Rico";
  public static final String CULEBRA = "Culebra";
  public static final String ST_CROIX = "St. Croix";
  public static final String ST_JOHN = "St. John";
  public static final String ST_THOMAS = "St. Thomas";
  public static final String VIEQUES = "Vieques";
  public static final String TUTUILA = "Tutuila";
  public static final String GUAM = "Guam";

  //static declaration of the data editions suppported within this framework.
  //public static final String data_2007 = "2007 Data";
  public static final String data_1996 = "1996 Data";
  public static final String data_2002 = "2002 Data";
  public static final String data_1998 = "1998 Data";
  public static final String data_2003 = "2003 Data";
  public static final String NEHRP_1997 =
      "1997 NEHRP Seismic Design Provisions";
  public static final String NEHRP_2000 =
      "2000 NEHRP Seismic Design Provisions";
  public static final String NEHRP_2003 =
      "2003 NEHRP Seismic Design Provisions";
  public static final String NEHRP_2009 =
	  "2009 NEHRP Seismic Design Provisions";
  public static final String ASCE_1998 = "1998 ASCE 7 Standard";
  public static final String ASCE_2002 = "2002 ASCE 7 Standard";
  public static final String ASCE_2005 = "2005 ASCE 7 Standard";
  public static final String ASCE_2010 = "2010 ASCE 7 Standard";
  public static final String IBC_2000 = "2000 International Building Code";
  public static final String IBC_2003 = "2003 International Building Code";
  public static final String IBC_2004 = "2004 International Building Code - Supplement";
  public static final String IBC_2006 = "2006 International Building Code";
  public static final String IRC_2000 = "2000 International Residential Code";
  public static final String IRC_2003 = "2003 International Residential Code";
  public static final String IRC_2004 = "2004 International Residential Code";
  public static final String IRC_2006 = "2006 International Residential Code";
  public static final String FEMA_273_DATA =
      "FEMA 273, MCE Guidelines for the Seismic Rehab. of Bldgs";
  public static final String FEMA_310_DATA = "FEMA 310";
  public static final String FEMA_356_DATA =
      "FEMA 356, Prestandard for Siesmic Rehab of Bldgs";
  public static final String  SCI_ASCE = "SCI/ASCE 31-03, Seismic evaluation of existing buildings";
  public static final String ASCE_PRESTANDARD = "ASCE PreStandard";
  public static final String IEBC_2003 =
      "2003 International Existing Building Code";
  public static final String NFPA_2003 = "2003 NFPA 5000 - References the 2002 ASCE 7 Standard";
  public static final String NFPA_2006 = "2006 NFPA 5000 - References the 2005 ASCE 7 Standard";
  //static declaration for the analysis choices
  public static final String PROB_HAZ_CURVES = "Probabilistic hazard curves";
  public static final String PROB_UNIFORM_HAZ_RES =
      "Probabilistic Uniform Hazard Response Spectra";
  public static final String NEHRP = "NEHRP Recommended Provisions for Seismic Regulations for New Buildings and Other Structures";
  //public static final String FEMA_273 =
  //  "FEMA 273,MCE Guidelines for the Seismic Rehabilitation of Buildings";
  //public static final String FEMA_356 = "FEMA 356,Prestandard and Commentary for the Seismic Rehabilitation of Buildings";
  public static final String INTL_BUILDING_CODE = "International Building Code";
  public static final String INTL_RESIDENTIAL_CODE =
      "International Residential Code";
  public static final String NFPA_5000 = "NFPA 5000 Building Construction and Safety Code";
  //public static final String INTL_EXIST_CODE =
  //  "International Existing Building Code";
  //public static final String NFPA_5000 =
  //  "NFPA 5000 Building construction and safety code";
  //public static final String ASCE_7 =
  //  "ASCE 7 standard , Minimum Design Loads for Building and other structures";



  public static final String ASCE_7 =
      "ASCE 7 Standard, minimum design loads for buildings and other structures";

  public static final String NFPA =
      "NFPA 5000 Building Construction and Safety Code";


  public static final String PROB_HAZ_CURVES_INFO =
      "<b>USGS Probabilistic Hazard Curves  - </b>" +
      "This option allows the user to obtain " +
      "hazard curves for a number of acceleration " +
      "parameters, such as peak ground acceleration " +
      "or response spectral accleration.    " +
      "Data sets include the following: 48 conterminous states " +
      "- 1996 and 2002, Alaska - 1998, Hawaii - 1998, " +
      "Puerto Rico and the Virgin Islands - 2003.";

  public static final String PROB_UNIFORM_HAZ_RES_INFO =
      "<b>USGS Probabilistic Uniform Hazard Response Spectra - </b> " +
      "This option allows the user to obtain uniform hazard " +
      "response spectra for 2% probabililty of " +
      "exceedance in 50 years, 10% probability of " +
      "exceedance in 50 years, and in a few cases " +
      "for 5% probability of exceedance in 50 years.   " +
      "Data sets include the following: 48 conterminous " +
      "states - 1996 and 2002, Alaska - 1998, Hawaii - 1998, " +
      "Puerto Rico and the Virgin Islands - 2003. ";
  public static final String NEHRP_INFO =
      "<b>NEHRP Recommended Provisions for Seismic " +
      "Regulations for New Buildings and Other " +
      "Structures </b> - This option may be used for " +
      "the 1997, 2000, and 2003 editions of the  " +
      "NEHRP Recommended Provisions for Seismic " +
      "Regulations for New Buildings and Other Structures.  " +
      "The user may calculate seismic design parameters " +
      "and response spectra (both for period and displacement), " +
      "for Site Class A through E.";
  public static final String INTL_BUILDING_CODE_INFO =
      "<b>International Building Code </b> - This " +
      "option may be used for the 2000, 2003, 2004 (supplement), and 2006 " +
      "editions of the  International Building Code.  " +
      "The user may calculate seismic design parameters " +
      "and response spectra (both for period and displacement), " +
      "for Site Class A through E.";
  /*public static final String NFPA_INFO =
      "FEMA 273, MCE Guidelines for the Seismic " +
      "Rehabilitation of Buildings  - " +
      "This option may be used for FEMA 273,  " +
      "MCE Guidelines for the Seismic Rehabilitation of Buildings " +
      "(1997).  The user may calculate seismic " +
      "design parameters and response spectra " +
      "(both for period and displacement), for " +
      "Site Class A through E.\n" +
      "FEMA 356, Prestandard and Commentary for " +
      "the Seismic Rehabilitation of Buildings  - " +
      "This option may be used for FEMA 356,  " +
      "Prestandard and Commentary for the Seismic " +
      "Rehabilitation of Buildings (2000).  The " +
      "user may calculate seismic design parameters " +
      "and response spectra (both for period and " +
      "displacement), for Site Class A through E.\n" +
      "International Existing Building Code  - " +
      "This option may be used for the 1997, 2000, " +
      "and 2003 editions of the  International Existing " +
      "Building Code.  The user may calculate seismic " +
      "design parameters and response spectra " +
      "(both for period and displacement), " +
      "for Site Class A through E.";*/


  public static final String NFPA_INFO = "<b>NFPA 5000 Building Construction and Safety Code -</b> " +
          "This option may be used for the 2003 and 2006 editions " +
          "of the  NFPA 5000 Building Construction and " +
          "Safety Code.  The user may calculate seismic " +
          "design parameters and response spectra (both " +
          "for period and displacement), for Site Class A through E.\n" ;


  public static final String INTL_RESIDENTIAL_CODE_INFO =
      "<b>International Residential Code - </b>" +
      "This option may be used for the 2000, " +
      "2003, 2004 (supplement), and 2006 editions of the  " +
      "International Residential Code.  The " +
      "user may determine the Seismic Design " +
      "Categories for the default Site Class D.";
  public static final String ASCE_7_INFO =
          "<b>ASCE 7 Standard, Minimum Design Loads for " +
          "Buildings and Other Structures </b> - This option " +
          "may be used for the 1998, 2002, and 2005 editions " +
          "of the ASCE 7 Standard,  Minimum Design Loads " +
          "for Buildings and Other Structures.  " +
          "The user may calculate seismic design " +
          "parameters and response spectra (both for " +
          "period and displacement), for Site Class A through E.";


  public static final String analysis_choices_info =
      "The User may perform an " +
      "analysis for a site by selecting from the options listed. The type of analysis " +
      "depends on the option selected. In all cases the site location may be specified " +
      "by latitude-longiude (recommended) or zip code. The brief description of the " +
      "options are intended to provide information for the knowledgeable user. The " +
      "description are not a substitute for technical knowledge of seismic design " +
      "and/or analysis.";

  public static final String SITE_DISCUSSION =
      "There are two sets of site coefficients in use, \n" +
      "depending on the analysis option selected, differing only \n" +
      "for Site Class E when Ss or S1 equals or exceeds 1.25 or 0.50 \n" +
      "respectively.  The most recent set of site coefficients\n " +
      "has values of Fa = 0.9 and Fv = 2.4 for Site Class E for\n " +
      "these conditions.  The older tables \n" +
      "of site coefficients referred the user to footnote a.\n " +
      "The new tables were introduced in the 2000\n " +
      "Edition of the NEHRP Recommended Provisions for Seismic Regulations\n " +
      "for New Buildings and other Structures. Recent editions of other design\n " +
      "documents have adopted the new tables.\n\n" +
      "This program automatically selects the appropriate site \n" +
      "coefficient tables depending on the analysis option selected. The user may\n" +
      "see the difference by comparing the tables for the 1997 and 2000 editions\n " +
      "of the NEHRP Provisions.";

  public static final String SUMMARY_INFO ="<b>Summary- </b>"+
      "The user may perform an analysis for a site by selecting from the options listed "+
      "with the types of analysis dependent on the option selected. In most cases "+
      "the site location may be secified by latitude-longitude (recommended) or "+
      "zipcode. However, locations in Puerto Rico and Virgin islands may only be located "+
      "by latitude-longitude. The brief description of the options are intended to "+
      "provide information for the knowledgeable user. The description are not a substitute "+
      "for technical knowledge of seismic design and/or analysis.";

  public final static String SITE_ERROR =
      "Check the Site Class selection. A Site Class \n" +
      "resulting in the 'Note a' message requires a site \n" +
      "specific study.  To proceed, enter site factors in\n " +
      "the text boxes for Fa and Fv based on a site specific\n " +
      "study or select a different Site Class.";

  public static final int DIVIDING_FACTOR_HUNDRED = 100;

  //SITE CLASS VARIABLES
  public static final String SITE_CLASS_A = "Site Class A";
  public static final String SITE_CLASS_B = "Site Class B";
  public static final String SITE_CLASS_C = "Site Class C";
  public static final String SITE_CLASS_D = "Site Class D";
  public static final String SITE_CLASS_E = "Site Class E";
  public static final String SITE_CLASS_F = "Site Class F";

  // Fa table data for site coefficient window
  public final static String[] faColumnNames = {
      "Site Class", "Ss<=0.25", "Ss=0.50",
      "Ss=0.75", "Ss=1.00", "Ss>=1.25"};
  public final static Object[][] faData = {
      {
      "A", "0.8", "0.8", "0.8", "0.8", "0.8"}, {
      "B", "1.0", "1.0", "1.0", "1.0", "1.0"}, {
      "C", "1.2", "1.2", "1.1", "1.0", "1.0"}, {
      "D", "1.6", "1.4", "1.2", "1.1", "1.0"}, {
      "E", "2.5", "1.7", "1.2", "0.9", "0.9"}, {
      "F", "a", "a", "a", "a", "a"}
  };

  // Fv table data for site coefficient window
  public final static String[] fvColumnNames = {
      "Site Class", "S1<=0.10", "S1=0.20",
      "S1=0.30", "S1=0.40", "S1>=0.50"};
  public final static Object[][] fvData = {
      {
      "A", "0.8", "0.8", "0.8", "0.8", "0.8"}, {
      "B", "1.0", "1.0", "1.0", "1.0", "1.0"}, {
      "C", "1.7", "1.6", "1.5", "1.4", "1.3"}, {
      "D", "2.4", "2.0", "1.8", "1.6", "1.5"}, {
      "E", "3.5", "3.2", "2.8", "2.4", "2.4"}, {
      "F", "a", "a", "a", "a", "a"}
  };

  //Some constant declaration for data plotting and Metadata
  public final static String SA = "Sa (g)";
  public final static String SD = "Sd (in)";
  public final static String PERIOD_NAME = "T (sec)";
  public final static String MCE_SPECTRUM = "MCE Spectrum";
  public final static String SD_SPECTRUM = "Design Spectrum";
  public final static String SM_SPECTRUM = "Site Modified Spectrum";
  public final static String PERIOD_UNITS = "sec";
  public final static String SA_UNITS = "g";
  public final static String SD_UNITS = "inches";
  public final static String SA_Vs_SD_GRAPH_NAME = "Sa Vs Sd";
  public final static String SA_Vs_T_GRAPH_NAME = "Sa Vs T";
  public final static String MCE_SPECTRUM_SA_Vs_T_GRAPH =
      "MCE Spectrum Sa Vs T";
  public final static String MCE_SPECTRUM_SA_Vs_SD_GRAPH =
      "MCE Spectrum Sa Vs Sd";
  public final static String MCE_SPECTRUM_SD_Vs_T_GRAPH =
      "MCE Spectrum Sd Vs T";
  public final static String SITE_MODIFIED_SA_Vs_T_GRAPH =
      "Site Modified Sa Vs T";
  public final static String SITE_MODIFIED_SA_Vs_SD_GRAPH =
      "Site Modified Sa Vs Sd";
  public final static String SITE_MODIFIED_SD_Vs_T_GRAPH =
      "Site Modified Sd Vs T";
  public final static String DESIGN_SPECTRUM_SA_Vs_T_GRAPH =
      "Design Spectrum Sa Vs T";
  public final static String DESIGN_SPECTRUM_SA_Vs_SD_GRAPH =
      "Design Spectrum Sa Vs Sd";
  public final static String DESIGN_SPECTRUM_SD_Vs_T_GRAPH =
      "Design Spectrum Sd Vs T";

  public final static String UNIFORM_HAZARD_SPECTRUM_NAME =
      "Uniform Hazard Spectrum";
  public final static String APPROX_UNIFORM_HAZARD_SPECTRUM_NAME =
      "Approx. Uniform Hazard Spectrum";

  public final static String ANNUAL_FREQ_EXCEED_UNITS = "per year";
  public final static String BASIC_HAZARD_CURVE = "Basic Hazard Curve";
  public final static String HAZARD_CURVE_X_AXIS_NAME = "Acceleration";
  public final static String HAZARD_CURVE_Y_AXIS_NAME =
      "Annual Frequency of Exceedance";

  public static final String UHS_PGA_FUNC_NAME = "UHS PGA Values";

  //some SA constants
  public final static String SA_DAMPING = "5% Damping";

  //IMT Periods supported
  public final static String PGA = "Hazard Curve for PGA";
  public final static String IMT_POINT_ONE_SEC = "Hazard Curve for 0.1sec";
  public final static String IMT_POINT_TWO_SEC = "Hazard Curve for 0.2sec";
  public final static String IMT_POINT_THREE_SEC = "Hazard Curve for 0.3sec";
  public final static String IMT_POINT_FOUR_SEC = "Hazard Curve for 0.4sec";
  public final static String IMT_POINT_FIVE_SEC = "Hazard Curve for 0.5sec";
  public final static String IMT_ONE_SEC = "Hazard Curve for 1.0sec";
  public final static String IMT_TWO_SEC = "Hazard Curve for 2.0sec";

  //supported Return periods
  public final static String PERIOD_10_YEARS = "10";
  public final static String PERIOD_20_YEARS = "20";
  public final static String PERIOD_30_YEARS = "30";
  public final static String PERIOD_40_YEARS = "40";
  public final static String PERIOD_50_YEARS = "50";
  public final static String PERIOD_72_YEARS = "72";
  public final static String PERIOD_100_YEARS = "100";
  public final static String PERIOD_200_YEARS = "200";
  public final static String PERIOD_224_YEARS = "224";
  public final static String PERIOD_475_YEARS = "475";
  public final static String PERIOD_500_YEARS = "500";
  public final static String PERIOD_975_YEARS = "975";
  public final static String PERIOD_1000_YEARS = "1000";
  public final static String PERIOD_1500_YEARS = "1500";
  public final static String PERIOD_2475_YEARS = "2475";
  public final static String PERIOD_2500_YEARS = "2500";
  public final static String PERIOD_4975_YEARS = "4975";
  public final static String PERIOD_5000_YEARS = "5000";
  public final static String PERIOD_10000_YEARS = "10000";

  //supported exceed probabilities
  public final static String PROB_EXCEED_1 = "1";
  public final static String PROB_EXCEED_2 = "2";
  public final static String PROB_EXCEED_3 = "3";
  public final static String PROB_EXCEED_5 = "5";
  public final static String PROB_EXCEED_10 = "10";
  public final static String PROB_EXCEED_20 = "20";
  public final static String PROB_EXCEED_50 = "50";

  //supported exposure time
  public final static String EXP_TIME_10 = "10";
  public final static String EXP_TIME_30 = "30";
  public final static String EXP_TIME_50 = "50";
  public final static String EXP_TIME_75 = "75";
  public final static String EXP_TIME_100 = "100";
  public final static String EXP_TIME_250 = "250";

  //supported Spectra types
  public static final String MCE_GROUND_MOTION = "MCE Ground Motion";
  public static final String RTE_GROUND_MOTION = "MCE_R Ground Motion";
  public static final String PE_10 = "10 % PE in 50 years";
  public static final String PE_5 = "5 % PE in 50 years";
  public static final String PE_2 = "2 % PE in 50 years";

  /**
   * Supported Return Periods.
   * @return ArrayList
   */
  public static ArrayList getSupportedReturnPeriods() {
    ArrayList<String> supportedReturnPeriods = new ArrayList<String>();
    supportedReturnPeriods.add(PERIOD_10_YEARS);
    supportedReturnPeriods.add(PERIOD_20_YEARS);
    supportedReturnPeriods.add(PERIOD_30_YEARS);
    supportedReturnPeriods.add(PERIOD_40_YEARS);
    supportedReturnPeriods.add(PERIOD_50_YEARS);
    supportedReturnPeriods.add(PERIOD_72_YEARS);
    supportedReturnPeriods.add(PERIOD_100_YEARS);
    supportedReturnPeriods.add(PERIOD_200_YEARS);
    supportedReturnPeriods.add(PERIOD_224_YEARS);
    supportedReturnPeriods.add(PERIOD_475_YEARS);
    supportedReturnPeriods.add(PERIOD_500_YEARS);
    supportedReturnPeriods.add(PERIOD_975_YEARS);
    supportedReturnPeriods.add(PERIOD_1000_YEARS);
    supportedReturnPeriods.add(PERIOD_1500_YEARS);
    supportedReturnPeriods.add(PERIOD_2475_YEARS);
    supportedReturnPeriods.add(PERIOD_2500_YEARS);
    supportedReturnPeriods.add(PERIOD_4975_YEARS);
    supportedReturnPeriods.add(PERIOD_5000_YEARS);
    supportedReturnPeriods.add(PERIOD_10000_YEARS);
    return supportedReturnPeriods;
  }

  /**
   * Returns the list of the supported Exceedance Prob List
   * @return ArrayList
   */
  public static ArrayList getSupportedExceedanceProb() {
    ArrayList<String> supportedExceedProbList = new ArrayList<String>();
    supportedExceedProbList.add(PROB_EXCEED_1);
    supportedExceedProbList.add(PROB_EXCEED_2);
    supportedExceedProbList.add(PROB_EXCEED_3);
    supportedExceedProbList.add(PROB_EXCEED_5);
    supportedExceedProbList.add(PROB_EXCEED_10);
    supportedExceedProbList.add(PROB_EXCEED_20);
    supportedExceedProbList.add(PROB_EXCEED_50);
    return supportedExceedProbList;
  }

  /**
   * Returns the list of the supported Exposure time
   * @return ArrayList
   */
  public static ArrayList getSupportedExposureTime() {
    ArrayList<String> supportedExposureProbList = new ArrayList<String>();
    supportedExposureProbList.add(EXP_TIME_10);
    supportedExposureProbList.add(EXP_TIME_30);
    supportedExposureProbList.add(EXP_TIME_50);
    supportedExposureProbList.add(EXP_TIME_75);
    supportedExposureProbList.add(EXP_TIME_100);
    supportedExposureProbList.add(EXP_TIME_250);
    return supportedExposureProbList;
  }

  /**
   * Returns the supported Site Classes
   * @return ArrayList
   */
  public static ArrayList getSupportedSiteClasses() {
    ArrayList<String> supportedSiteClasses = new ArrayList<String>();
    supportedSiteClasses.add(SITE_CLASS_A);
    supportedSiteClasses.add(SITE_CLASS_B);
    supportedSiteClasses.add(SITE_CLASS_C);
    supportedSiteClasses.add(SITE_CLASS_D);
    supportedSiteClasses.add(SITE_CLASS_E);
    supportedSiteClasses.add(SITE_CLASS_F);
    return supportedSiteClasses;
  }

  /**
   * Returns the number of supported Analysis types
   * @return ArrayList
   */
  public static ArrayList getSupportedAnalysisOptions() {
    ArrayList<String> supportedAnalysisOption = new ArrayList<String>();
    supportedAnalysisOption.add(PROB_HAZ_CURVES);
    supportedAnalysisOption.add(PROB_UNIFORM_HAZ_RES);
    supportedAnalysisOption.add(NEHRP);
    supportedAnalysisOption.add(ASCE_7);
	supportedAnalysisOption.add(INTL_BUILDING_CODE);
    supportedAnalysisOption.add(INTL_RESIDENTIAL_CODE);
    //supportedAnalysisOption.add(INTL_EXIST_CODE);
    supportedAnalysisOption.add(NFPA);
    return supportedAnalysisOption;
  }

  /**
   * Returns the selected Analysis option
   * @param selectedAnalysisOption String : Selected Analysis Option
   * @return String
   */
  public static String getExplainationForSelectedAnalysisOption(String
      selectedAnalysisOption) {
    if (selectedAnalysisOption.equals(PROB_HAZ_CURVES)) {
      return PROB_HAZ_CURVES_INFO;
    }
    else if (selectedAnalysisOption.equals(PROB_UNIFORM_HAZ_RES)) {
      return PROB_UNIFORM_HAZ_RES_INFO;
    }
    else if (selectedAnalysisOption.equals(NEHRP)) {
      return NEHRP_INFO;
    }
    else if (selectedAnalysisOption.equals(NFPA)) {
      return NFPA_INFO;
    }
    /*else if (selectedAnalysisOption.equals(GlobalConstants.FEMA_356)) {
     this.explainationText.setText("FEMA 356, Prestandard and Commentary for " +
     "the Seismic Rehabilitation of Buildings  - " +
                                    "This option may be used for FEMA 356,  " +
     "Prestandard and Commentary for the Seismic " +
     "Rehabilitation of Buildings (2000).  The " +
     "user may calculate seismic design parameters " +
     "and response spectra (both for period and " +
     "displacement), for Site Class A through E.");
         }*/
    else if (selectedAnalysisOption.equals(INTL_BUILDING_CODE)) {
      return INTL_BUILDING_CODE_INFO;
    }
    else if (selectedAnalysisOption.equals(INTL_RESIDENTIAL_CODE)) {
      return INTL_RESIDENTIAL_CODE_INFO;
    }
    /*else if (selectedAnalysisOption.equals(GlobalConstants.INTL_EXIST_CODE)) {
     this.explainationText.setText("International Existing Building Code  - " +
     "This option may be used for the 1997, 2000, " +
     "and 2003 editions of the  International Existing " +
     "Building Code.  The user may calculate seismic " +
                                    "design parameters and response spectra " +
                                    "(both for period and displacement), " +
                                    "for Site Class A through E.");
         }*/
    else if (selectedAnalysisOption.equals(ASCE_7)) {
      return ASCE_7_INFO;
    }
    /*else if (selectedAnalysisOption.equals(GlobalConstants.ASCE_7)) {
      this.explainationText.setText(
          "ASCE 7 Standard, Minimum Design Loads for " +
          "Buildings and Other Structures  - This option " +
          "may be used for the 1998 and 2002 editions " +
          "of the ASCE 7 Standard,  Minimum Design Loads " +
          "for Buildings and Other Structures.  " +
          "The user may calculate seismic design " +
          "parameters and response spectra (both for " +
          "period and displacement), for Site Class A through E.");
         }*/
    return null;
  }

  /**
   * Returns the Explaination for all Anaysis option supported in our framework.
   * @return String
   */
  public static String getAllExplainationsForAnalysisOption(){
    return  "<html>"+SUMMARY_INFO +"<p>"+"<b>List of options based on "+
       "Probabilistic Calculations.</b><ul>"+"<li>"+PROB_HAZ_CURVES_INFO+
       "<li>"+PROB_UNIFORM_HAZ_RES_INFO+"</ul><b>List of options based on design "+
       "documents for new buildings.</b>"+"<p>"+"<ul>"+
       "<li>"+NEHRP_INFO+"<li>"+ASCE_7_INFO+"<li>"+INTL_BUILDING_CODE_INFO+"<li>"+
       INTL_RESIDENTIAL_CODE_INFO+"<li>"+NFPA_INFO+"</ul></html>";
  }
  
  //#####################################################################
  //                        Versions
  //#####################################################################

	public static String getCurrentVersion() {
		return VERSION;
	}

	public static String getAbout() {
		String about = "Earthquake Ground Motion Parameters\n" + VERSION;
		return about;
	}

	public static String getServletPath() {
		try {
			String OS = System.getProperty("os.name").toLowerCase();

			if (OS.equals("mac os x")) {
				Runtime r = Runtime.getRuntime();
				Process p = r.exec("env");
				Properties envVars = new Properties();
				envVars.load(p.getInputStream());
				if ( envVars.getProperty("GMTSERVER") != null ) {
					return envVars.getProperty("GMTSERVER");
				} else {
					return SERVLET_PATH;
				}
			} else {
				return SERVLET_PATH;
			}
		} catch (Throwable ex) {
			ex.printStackTrace();
			return "";
		}

	} // End of getServletPath()
	
}

