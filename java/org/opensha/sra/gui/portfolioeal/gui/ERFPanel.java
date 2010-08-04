package org.opensha.sra.gui.portfolioeal.gui;
import java.util.ArrayList;

import org.opensha.sha.gui.beans.ERF_GuiBean;

/**
 * This class creates an instance of <code>ERF_GuiBean</code>, and implements it as a 
 * JPanel.
 * 
 * @author Jeremy Leakakos
 */
public class ERFPanel {
	// The object class names for all the supported Eqk Rup Forecasts 
	// The two that are commented out are not compatible with the current way of doing
	// calculations, and if no formal specifications of how to do those calculations
	// are provided, they will need to stay commented out.
	//public final static String NSHMP08_CEUS_ERF_CLASS_NAME = "org.opensha.sha.earthquake.rupForecastImpl.NSHMP_CEUS08.NSHMP08_CEUS_ERF";
	public final static String FRANKEL_ADJ_FORECAST_CLASS_NAME = "org.opensha.sha.earthquake.rupForecastImpl.Frankel96.Frankel96_AdjustableEqkRupForecast";
	public final static String FRANKEL_FORECAST_CLASS_NAME = "org.opensha.sha.earthquake.rupForecastImpl.Frankel96.Frankel96_EqkRupForecast";
	public final static String FRANKEL02_ADJ_FORECAST_CLASS_NAME = "org.opensha.sha.earthquake.rupForecastImpl.Frankel02.Frankel02_AdjustableEqkRupForecast";

	public final static String WG02_ERF_LIST_CLASS_NAME = "org.opensha.sha.earthquake.rupForecastImpl.WG02.WG02_ERF_Epistemic_List";
	public final static String WG02_ERF_CLASS_NAME = "org.opensha.sha.earthquake.rupForecastImpl.WG02.WG02_EqkRupForecast";
	public final static String WGCEP_UCERF1_CLASS_NAME = "org.opensha.sha.earthquake.rupForecastImpl.WGCEP_UCERF1.WGCEP_UCERF1_EqkRupForecast";
	public final static String WGCEP_UCERF_2_CLASS_NAME="org.opensha.sha.earthquake.rupForecastImpl.WGCEP_UCERF_2_Final.UCERF2";
	public final static String WGCEP_UCERF_2_EPISTEMIC_LIST_CLASS_NAME="org.opensha.sha.earthquake.rupForecastImpl.WGCEP_UCERF_2_Final.UCERF2_TimeIndependentEpistemicList";
	public final static String WGCEP_AVG_UCERF_2_CLASS_NAME="org.opensha.sha.earthquake.rupForecastImpl.WGCEP_UCERF_2_Final.MeanUCERF2.MeanUCERF2";

	public final static String PEER_AREA_FORECAST_CLASS_NAME = "org.opensha.sha.earthquake.rupForecastImpl.PEER_TestCases.PEER_AreaForecast";
	public final static String PEER_NON_PLANAR_FAULT_FORECAST_CLASS_NAME = "org.opensha.sha.earthquake.rupForecastImpl.PEER_TestCases.PEER_NonPlanarFaultForecast";
	public final static String PEER_MULTI_SOURCE_FORECAST_CLASS_NAME = "org.opensha.sha.earthquake.rupForecastImpl.PEER_TestCases.PEER_MultiSourceForecast";
	public final static String PEER_LOGIC_TREE_FORECAST_CLASS_NAME = "org.opensha.sha.earthquake.rupForecastImpl.PEER_TestCases.PEER_LogicTreeERF_List";
	//public final static String STEP_FORECAST_CLASS_NAME = "org.opensha.sha.earthquake.rupForecastImpl.step.STEP_EqkRupForecast";
	public final static String STEP_ALASKA_ERF_CLASS_NAME = "org.opensha.sha.earthquake.rupForecastImpl.step.STEP_AlaskanPipeForecast";
	public final static String POISSON_FAULT_ERF_CLASS_NAME = "org.opensha.sha.earthquake.rupForecastImpl.FloatingPoissonFaultERF";
	public final static String SIMPLE_FAULT_ERF_CLASS_NAME = "org.opensha.sha.earthquake.rupForecastImpl.PoissonFaultERF";
	public final static String POINT_SRC_FORECAST_CLASS_NAME="org.opensha.sha.earthquake.rupForecastImpl.PointSourceERF";
	public final static String POINT2MULT_VSS_FORECAST_CLASS_NAME="org.opensha.sha.earthquake.rupForecastImpl.Point2MultVertSS_Fault.Point2MultVertSS_FaultERF";
	public final static String POINT2MULT_VSS_ERF_LIST_CLASS_NAME="org.opensha.sha.earthquake.rupForecastImpl.Point2MultVertSS_Fault.Point2MultVertSS_FaultERF_List";
	public final static String YUCCA_MOUNTAIN_CLASS_NAME="org.opensha.sha.earthquake.rupForecastImpl.YuccaMountain.YuccaMountainERF";
	public final static String YUCCA_MOUNTAIN_ERF_LIST_CLASS_NAME="org.opensha.sha.earthquake.rupForecastImpl.YuccaMountain.YuccaMountainERF_List";
	//public final static String CYBERSHAKE_ERF_LIST_CLASS_NAME="org.opensha.sha.cybershake.openshaAPIs.CyberShakeERF";
	//public final static String CYBERSHAKE_ERF_WRAPPER_LIST_CLASS_NAME="org.opensha.sha.cybershake.openshaAPIs.CyberShakeUCERFWrapper_ERF";
	public final static String NZ_ERF0909_CLASS_NAME="org.opensha.sha.earthquake.rupForecastImpl.NewZealand.NewZealandERF0909";
//	public final static String GEM_TEST_ERF_CLASS_NAME="org.opensha.sha.earthquake.rupForecastImpl.GEM.TestGEM_ERF";
	
	public static ArrayList<String> getLocalERFClasses() {
		ArrayList<String> erf_Classes = new ArrayList<String>();

		//adding the client based ERF's to the application
		erf_Classes.add(FRANKEL_ADJ_FORECAST_CLASS_NAME);
		erf_Classes.add(FRANKEL_FORECAST_CLASS_NAME);
		erf_Classes.add(FRANKEL02_ADJ_FORECAST_CLASS_NAME);
		//      erf_Classes.add(NSHMP08_CEUS_ERF_CLASS_NAME);
		erf_Classes.add(WG02_ERF_LIST_CLASS_NAME);
		erf_Classes.add(WGCEP_UCERF1_CLASS_NAME);
		erf_Classes.add(PEER_AREA_FORECAST_CLASS_NAME);
		erf_Classes.add(PEER_NON_PLANAR_FAULT_FORECAST_CLASS_NAME);
		erf_Classes.add(PEER_MULTI_SOURCE_FORECAST_CLASS_NAME);
		erf_Classes.add(PEER_LOGIC_TREE_FORECAST_CLASS_NAME);
		//erf_Classes.add(STEP_FORECAST_CLASS_NAME);
		erf_Classes.add(STEP_ALASKA_ERF_CLASS_NAME);
		erf_Classes.add(POISSON_FAULT_ERF_CLASS_NAME);
		erf_Classes.add(SIMPLE_FAULT_ERF_CLASS_NAME);
		erf_Classes.add(POINT_SRC_FORECAST_CLASS_NAME);
		erf_Classes.add(POINT2MULT_VSS_FORECAST_CLASS_NAME);
		erf_Classes.add(POINT2MULT_VSS_ERF_LIST_CLASS_NAME);
		
		erf_Classes.add(WGCEP_UCERF_2_CLASS_NAME);
		erf_Classes.add(WGCEP_UCERF_2_EPISTEMIC_LIST_CLASS_NAME);
		erf_Classes.add(WGCEP_AVG_UCERF_2_CLASS_NAME);
		
		erf_Classes.add(YUCCA_MOUNTAIN_CLASS_NAME);
		erf_Classes.add(YUCCA_MOUNTAIN_ERF_LIST_CLASS_NAME);
		
//		erf_Classes.add(GEM_TEST_ERF_CLASS_NAME);
		//      erf_Classes.add(CYBERSHAKE_ERF_LIST_CLASS_NAME);
		//      erf_Classes.add(CYBERSHAKE_ERF_WRAPPER_LIST_CLASS_NAME);
		erf_Classes.add(NZ_ERF0909_CLASS_NAME);
		
		return erf_Classes;
	}
	
	private ERF_GuiBean erfPanel;
	
	/**
	 * The default constructor.  An ERF_GuiBean is created, which is called by the main view.  Since
	 * the class ERF_GuiBean is already a JPanel, there is no UI formatting done in this class.
	 */
	public ERFPanel() {
		
		try {
			erfPanel = new ERF_GuiBean(getLocalERFClasses());
		}
		catch ( Exception e ) {
			e.printStackTrace();
		}
		
		erfPanel.getParameter("Eqk Rup Forecast").addParameterChangeListener(BCR_ApplicationFacade.getBCR());
	}
	
	/**
	 * @return This is the instance of ERF_GuiBean that is to be used in the main program
	 */
	public ERF_GuiBean getPanel() {
		return erfPanel;
	}

}
