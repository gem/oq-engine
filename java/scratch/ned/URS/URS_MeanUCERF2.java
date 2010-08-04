/**
 * 
 */
package scratch.ned.URS;
// Moved the *.java to scratch.christine.urs to keep all the trial versions together CG 2010-05-26

import java.util.ArrayList;

import org.opensha.commons.geo.Location;
import org.opensha.commons.param.BooleanParameter;
import org.opensha.commons.param.event.ParameterChangeEvent;
import org.opensha.refFaultParamDb.vo.FaultSectionPrefData;
import org.opensha.sha.earthquake.ProbEqkSource;
import org.opensha.sha.earthquake.rupForecastImpl.WGCEP_UCERF_2_Final.FaultSegmentData;
import org.opensha.sha.earthquake.rupForecastImpl.WGCEP_UCERF_2_Final.UCERF2;
import org.opensha.sha.earthquake.rupForecastImpl.WGCEP_UCERF_2_Final.UnsegmentedSource;
import org.opensha.sha.earthquake.rupForecastImpl.WGCEP_UCERF_2_Final.data.SegRateConstraint;
import org.opensha.sha.earthquake.rupForecastImpl.WGCEP_UCERF_2_Final.data.SegmentTimeDepData;
import org.opensha.sha.earthquake.rupForecastImpl.WGCEP_UCERF_2_Final.data.finalReferenceFaultParamDb.PrefFaultSectionDataFinal;
import org.opensha.sha.faultSurface.FaultTrace;
import org.opensha.sha.earthquake.rupForecastImpl.WGCEP_UCERF_2_Final.MeanUCERF2.MeanUCERF2;




/**
 * This class filters out some of the sources in MeanUCERF2 and adds others back in.  
 * 
 * 
 * @author 
 *
 */
public class URS_MeanUCERF2 extends MeanUCERF2 {
	//for Debug purposes
	private static String  C = new String("MeanUCERF2");
	private boolean D = true;

	// name of this ERF
	public final static String NAME = new String("URS Modified UCERF2");
	
	// for Cybershake Correction
	public final static String FILTER_PARAM_NAME ="URS Filter";
	public final static Boolean FILTER_PARAM_DEFAULT= new Boolean(false);
	protected final static String FILTER_PARAM_INFO = "Apply the URS Source Filter";
	protected BooleanParameter filterParam;
	
	FaultSectionPrefData sierraMadreData, sierraMadreSanFernData, santaSusanaData, verdugoData;
	



	/**
	 *
	 * No argument constructor
	 */
	public URS_MeanUCERF2() {
		super();
		
		// this parameter toggles whether to apply the URS modifications
		filterParam = new BooleanParameter(FILTER_PARAM_NAME);
		filterParam.setInfo(FILTER_PARAM_INFO);
		filterParam.setDefaultValue(FILTER_PARAM_DEFAULT);
		adjustableParams.addParameter(filterParam);
		filterParam.addParameterChangeListener(this);
		
		// turn this off for speed, and because it's no longer accurate (haven't modified with the changed sources)
		calcSummedMFDs  =false;
		
		// turn this off for speed
		setParameter(UCERF2.BACK_SEIS_NAME, UCERF2.BACK_SEIS_EXCLUDE);
		
		// I did the following once to get the original fault data
		// printOrigFaultSectionData();
		
		// make the new fault section data needed for URS modifications
		mkNewFaultSectionData();
		
	}
	
	/**
	 * update the forecast
	 **/

	public void updateForecast() {
		if(this.parameterChangeFlag)  {

			super.updateForecast();

			String srcName;
			double wt;

			/*  This was added as a test (it keeps only the 5 sources changed below)
			System.out.println("updating forecast...");
			ArrayList<ProbEqkSource> tempSources = new ArrayList<ProbEqkSource>();
			for(int j=0;j<allSources.size();j++) {
				srcName = allSources.get(j).getName();
				if (srcName.equals("Sierra Madre") || srcName.equals("Sierra Madre (San Fernando)") ||
						srcName.equals("Sierra Madre Connected") || srcName.equals("Santa Susana, alt 1") ||
						srcName.equals("Verdugo")){
					tempSources.add(allSources.get(j));
				}
			}
			allSources = tempSources;
			System.out.println("numSrces="+allSources.size());
			*/



			// FILTER OUT SOURCES
			if(filterParam.getValue().booleanValue()) {
				ArrayList<ProbEqkSource> newAllSources = new ArrayList<ProbEqkSource>();
				ArrayList<UnsegmentedSource> newBFaultSources = new ArrayList<UnsegmentedSource>();
				
				// filter from allSources
				for(int i=0;i<allSources.size();i++) {
					srcName = allSources.get(i).getName();
					//				System.out.println(srcName);
					if (!srcName.equals("Sierra Madre") &&
							!srcName.equals("Sierra Madre (San Fernando)") &&
							!srcName.equals("Sierra Madre Connected") &&
							!srcName.equals("Santa Susana, alt 1") &&
							!srcName.equals("Verdugo")){

						newAllSources.add(allSources.get(i));
					}
					else {
						System.out.println(srcName+" was filetered from allSources");
					}	
				}
				
				//filter from bFaultSources
				for(int i=0;i<bFaultSources.size();i++) {
					srcName = bFaultSources.get(i).getName();
					//				System.out.println(srcName);
					if (!srcName.equals("Sierra Madre") &&
							!srcName.equals("Sierra Madre (San Fernando)") &&
							!srcName.equals("Sierra Madre Connected") &&
							!srcName.equals("Santa Susana, alt 1") &&
							!srcName.equals("Verdugo")){

						newBFaultSources.add(bFaultSources.get(i));
					}
					else {
						System.out.println(srcName+" was filetered from bFaultSources");
					}	
				}

				// ADD NEW SOURCES
				
				double fixMag = Double.NaN;
				ArrayList<UnsegmentedSource> newSources = new ArrayList<UnsegmentedSource>();
				// Santa Susana
				ArrayList<FaultSectionPrefData> ss_Sections = new ArrayList<FaultSectionPrefData>();
				ss_Sections.add(this.santaSusanaData);
				wt = 0.5;  // only in one fault model
				newSources.add(makeOrigSource(ss_Sections, wt, santaSusanaData.getSectionName(),fixMag));

				// Verdugo
				ArrayList<FaultSectionPrefData> v_Sections = new ArrayList<FaultSectionPrefData>();
				v_Sections.add(this.verdugoData);
				wt = 1.0;  // it's in both fault models and has no connections
				newSources.add(makeOrigSource(v_Sections, wt, verdugoData.getSectionName(),fixMag));

				// Sierra Madre
				ArrayList<FaultSectionPrefData> sm_Sections = new ArrayList<FaultSectionPrefData>();
				sm_Sections.add(this.sierraMadreData);
				wt = 0.5;
				newSources.add(makeOrigSource(sm_Sections, wt, sierraMadreData.getSectionName(),fixMag));

				// Sierra Madre (San Fernando)
				ArrayList<FaultSectionPrefData> smsf_Sections = new ArrayList<FaultSectionPrefData>();
				smsf_Sections.add(this.sierraMadreSanFernData);
				wt = 0.5;
				newSources.add(makeOrigSource(smsf_Sections, wt, sierraMadreSanFernData.getSectionName(),fixMag));

				// Sierra Madre Connected
				ArrayList<FaultSectionPrefData> sm_con_Sections = new ArrayList<FaultSectionPrefData>();
				sm_con_Sections.add(this.sierraMadreData);
				sm_con_Sections.add(this.sierraMadreSanFernData);
				wt = 0.5;
				String newName = sierraMadreData.getSectionName() + " Cannected";
				newSources.add(makeOrigSource(sm_con_Sections, wt, newName, fixMag));
				
				// ADD THESE SOURCES TO THE NEW LISTS
				newAllSources.addAll(newSources);
				newBFaultSources.addAll(newSources);

				// OVERIDE THE SOURCE LISTS WITH THE NEW ONE
				allSources = newAllSources;		
				bFaultSources = newBFaultSources;


			}
			/* this was just a check to make sure the sources were recreated correctly
			for(int k=0;k<allSources.size();k++)
				System.out.println(allSources.get(k).getName()+"\t"+allSources.get(k).computeTotalProb());
			*/
		}
	}
	
	protected void printOrigFaultSectionData() {
		PrefFaultSectionDataFinal prefFaultSectionDataFinal = new PrefFaultSectionDataFinal();
		ArrayList<FaultSectionPrefData> allData = prefFaultSectionDataFinal.getAllFaultSectionPrefData();
		for(int i=0; i<allData.size();i++) {
			String name = allData.get(i).getSectionName();
			if(name.equals("Sierra Madre") || name.equals("Sierra Madre (San Fernando)") || 
					name.equals("Sierra Madre Connected") || name.equals("Santa Susana, alt 1") ||
					name.equals("Verdugo")) {
				System.out.println(allData.get(i).toString());
			}
					
		}
	}
	
	
	protected UnsegmentedSource makeOrigSource(ArrayList<FaultSectionPrefData> sectionsInSource, double wt, String name, double fixMag) {
		
		// Get the various adjustable parameter settings
		double rupOffset = ((Double)this.rupOffsetParam.getValue()).doubleValue();
		double empiricalModelWt=0.0;
		String probModel = (String)this.probModelParam.getValue();
		if(probModel.equals(UCERF2.PROB_MODEL_BPT) || probModel.equals(UCERF2.PROB_MODEL_POISSON) ) empiricalModelWt = 0;
		else if(probModel.equals(UCERF2.PROB_MODEL_EMPIRICAL)) empiricalModelWt = 1;
		else if(probModel.equals(PROB_MODEL_WGCEP_PREF_BLEND)) empiricalModelWt = 0.3;
		double duration = this.timeSpan.getDuration();
		boolean ddwCorr = (Boolean)cybershakeDDW_CorrParam.getValue();
		int floaterType = this.getFloaterType();
		
		ArrayList sectionToSegmentData = new ArrayList();
		sectionToSegmentData.add(sectionsInSource);
		// set the segment names and fault name (only one each; make is the same name)
		String[] segNames = new String[1];
		segNames[0] = name;
		String faultName = name;
		FaultSegmentData faultSegmentData = new  FaultSegmentData(sectionToSegmentData, segNames, true, faultName, null,null);
		
		return new UnsegmentedSource(faultSegmentData, empiricalModel,  rupOffset,  wt, 
				empiricalModelWt, duration, ddwCorr, floaterType, fixMag);
	}
	
	
	
	/**
	 * This makes the new fault-section data needed for the URS modifications
	 */
	protected void mkNewFaultSectionData() {
		
		/* Original values obtained from running the printOrigFaultSectionData() method here
		sectionId = 227
		sectionName = Santa Susana, alt 1
		shortName = 
		aveLongTermSlipRate = 5.0
		slipRateStdDev = 0.0
		aveDip = 55.0
		aveRake = 90.0
		aveUpperDepth = 0.0
		aveLowerDepth = 16.299999237060547
		aseismicSlipFactor = 0.0
		dipDirection = 8.9989805
		faultTrace:
			34.32418, -118.49553, 0.0
			34.30532, -118.52319, 0.0
			34.30029, -118.54583, 0.0
			34.32041, -118.58105, 0.0
			34.32292, -118.61626, 0.0
			34.33298, -118.63386, 0.0
			34.35059, -118.70806, 0.0
			34.35939, -118.76715, 0.0
		*/
		santaSusanaData = new FaultSectionPrefData();
		santaSusanaData.setSectionId(227);
		santaSusanaData.setSectionName("Santa Susana, alt 1");
		santaSusanaData.setAveLongTermSlipRate(5.0);
		santaSusanaData.setSlipRateStdDev(0.0);
		santaSusanaData.setAveDip(55.0);
		santaSusanaData.setAveRake(90.0);
		santaSusanaData.setAveUpperDepth(0.0);
		santaSusanaData.setAveLowerDepth(16.3);
		santaSusanaData.setAseismicSlipFactor(0.0);
		santaSusanaData.setDipDirection((float)8.9989805);
		FaultTrace trace = new FaultTrace(null);
		trace.add(new Location(34.32418, -118.49553, 0.0));
		trace.add(new Location(34.30532, -118.52319, 0.0));
		trace.add(new Location(34.30029, -118.54583, 0.0));
		trace.add(new Location(34.32041, -118.58105, 0.0));
		trace.add(new Location(34.32292, -118.61626, 0.0));
		trace.add(new Location(34.33298, -118.63386, 0.0));
		trace.add(new Location(34.35059, -118.70806, 0.0));
		trace.add(new Location(34.35939, -118.76715, 0.0));
		santaSusanaData.setFaultTrace(trace);
		

  		/* Original values obtained from running the printOrigFaultSectionData() method here
		sectionId = 114
		sectionName = Sierra Madre
		shortName = 
		aveLongTermSlipRate = 2.0
		slipRateStdDev = 0.0
		aveDip = 53.0
		aveRake = 90.0
		aveUpperDepth = 0.0
		aveLowerDepth = 14.199999809265137
		aseismicSlipFactor = 0.0
		dipDirection = 18.630968
		faultTrace:
			34.1231, -117.74, 0.0
			34.1219, -117.755, 0.0
			34.1317, -117.769, 0.0
			34.1305, -117.807, 0.0
			34.1323, -117.818, 0.0
			34.1587, -117.86, 0.0
			34.147, -117.881, 0.0
			34.1501, -117.94, 0.0
			34.1611, -117.985, 0.0
			34.1752, -118.003, 0.0
			34.1758, -118.068, 0.0
			34.201, -118.112, 0.0
			34.2028, -118.149, 0.0
			34.21074, -118.18902, 0.0
			34.23489, -118.22268, 0.0
			34.24946, -118.26234, 0.0
			34.25849, -118.27932, 0.0
			34.2751, -118.29, 0.0
		*/
		sierraMadreData = new FaultSectionPrefData();
		sierraMadreData.setSectionId(114);
		sierraMadreData.setSectionName("Sierra Madre");
		sierraMadreData.setAveLongTermSlipRate(2.0);
		sierraMadreData.setSlipRateStdDev(0.0);
		sierraMadreData.setAveDip(53.0);
		sierraMadreData.setAveRake(90.0);
		sierraMadreData.setAveUpperDepth(0.0);
		sierraMadreData.setAveLowerDepth(14.2);
		sierraMadreData.setAseismicSlipFactor(0.0);
		sierraMadreData.setDipDirection((float)18.630968);
		FaultTrace trace2 = new FaultTrace(null);
		trace2.add(new Location(34.1231, -117.74, 0.0));
		trace2.add(new Location(34.1219, -117.755, 0.0));
		trace2.add(new Location(34.1317, -117.769, 0.0));
		trace2.add(new Location(34.1305, -117.807, 0.0));
		trace2.add(new Location(34.1323, -117.818, 0.0));
		trace2.add(new Location(34.1587, -117.86, 0.0));
		trace2.add(new Location(34.147, -117.881, 0.0));
		trace2.add(new Location(34.1501, -117.94, 0.0));
		trace2.add(new Location(34.1611, -117.985, 0.0));
		trace2.add(new Location(34.1752, -118.003, 0.0));
		trace2.add(new Location(34.1758, -118.068, 0.0));
		trace2.add(new Location(34.201, -118.112, 0.0));
		trace2.add(new Location(34.2028, -118.149, 0.0));
		trace2.add(new Location(34.21074, -118.18902, 0.0));
		trace2.add(new Location(34.23489, -118.22268, 0.0));
		trace2.add(new Location(34.24946, -118.26234, 0.0));
		trace2.add(new Location(34.25849, -118.27932, 0.0));
		trace2.add(new Location(34.2751, -118.29, 0.0));
		sierraMadreData.setFaultTrace(trace2);
		

		/* Original values obtained from running the printOrigFaultSectionData() method here
		sectionId = 113
		sectionName = Sierra Madre (San Fernando)
		shortName = 
		aveLongTermSlipRate = 2.0
		slipRateStdDev = 0.0
		aveDip = 45.0
		aveRake = 90.0
		aveUpperDepth = 0.0
		aveLowerDepth = 13.0
		aseismicSlipFactor = 0.0
		dipDirection = 9.279146
		faultTrace:
			34.2782, -118.2951, 0.0
			34.27452, -118.31963, 0.0
			34.29046, -118.39563, 0.0
			34.30394, -118.41894, 0.0
			34.30272, -118.43365, 0.0
			34.29291, -118.46185, 0.0
			34.30272, -118.47778, 0.0
		*/
		sierraMadreSanFernData = new FaultSectionPrefData();
		sierraMadreSanFernData.setSectionId(113);
		sierraMadreSanFernData.setSectionName("Sierra Madre (San Fernando)");
		sierraMadreSanFernData.setAveLongTermSlipRate(2.0);
		sierraMadreSanFernData.setSlipRateStdDev(0.0);
		sierraMadreSanFernData.setAveDip(45.0);
		sierraMadreSanFernData.setAveRake(90.0);
		sierraMadreSanFernData.setAveUpperDepth(0.0);
		sierraMadreSanFernData.setAveLowerDepth(13.0);
		sierraMadreSanFernData.setAseismicSlipFactor(0.0);
		sierraMadreSanFernData.setDipDirection((float)9.279146);
		FaultTrace trace3 = new FaultTrace(null);
		trace3.add(new Location(34.2782, -118.2951, 0.0));
		trace3.add(new Location(34.27452, -118.31963, 0.0));
		trace3.add(new Location(34.29046, -118.39563, 0.0));
		trace3.add(new Location(34.30394, -118.41894, 0.0));
		trace3.add(new Location(34.30272, -118.43365, 0.0));
		trace3.add(new Location(34.29291, -118.46185, 0.0));
		trace3.add(new Location(34.30272, -118.47778, 0.0));
		sierraMadreSanFernData.setFaultTrace(trace3);

		
		/* Original values obtained from running the printOrigFaultSectionData() method here
		sectionId = 112
		sectionName = Verdugo
		shortName = 
		aveLongTermSlipRate = 0.5
		slipRateStdDev = 0.0
		aveDip = 55.0
		aveRake = 90.0
		aveUpperDepth = 0.0
		aveLowerDepth = 14.5
		aseismicSlipFactor = 0.0
		dipDirection = 30.52965
		faultTrace:
			34.13131, -118.15357, 0.0
			34.1496, -118.18648, 0.0
			34.15508, -118.22854, 0.0
			34.19714, -118.29071, 0.0
			34.22274, -118.36569, 0.0
			34.25383, -118.40775, 0.0
			34.26115, -118.42055, 0.0
		*/
		verdugoData = new FaultSectionPrefData();
		verdugoData.setSectionId(112);
		verdugoData.setSectionName("Verdugo");
		verdugoData.setAveLongTermSlipRate(0.5);
		verdugoData.setSlipRateStdDev(0.0);
		verdugoData.setAveDip(55.0);
		verdugoData.setAveRake(90.0);
		verdugoData.setAveUpperDepth(0.0);
		verdugoData.setAveLowerDepth(14.5);
		verdugoData.setAseismicSlipFactor(0.0);
		verdugoData.setDipDirection((float)30.52965);
		FaultTrace trace4 = new FaultTrace(null);
		trace4.add(new Location(34.13131, -118.15357, 0.0));
		trace4.add(new Location(34.1496, -118.18648, 0.0));
		trace4.add(new Location(34.15508, -118.22854, 0.0));
		trace4.add(new Location(34.19714, -118.29071, 0.0));
		trace4.add(new Location(34.22274, -118.36569, 0.0));
		trace4.add(new Location(34.25383, -118.40775, 0.0));
		trace4.add(new Location(34.26115, -118.42055, 0.0));
		verdugoData.setFaultTrace(trace4);

	}
	
	public void parameterChange(ParameterChangeEvent event) {
		// System.out.println("parameter changed");
		super.parameterChange(event);
		if(!adjustableParams.containsParameter(filterParam.getName()))
			adjustableParams.addParameter(filterParam);
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
		
		URS_MeanUCERF2 meanUCERF2 = new URS_MeanUCERF2();
		meanUCERF2.updateForecast();
	}
}