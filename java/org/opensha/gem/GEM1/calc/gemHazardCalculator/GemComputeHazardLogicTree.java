package org.opensha.gem.GEM1.calc.gemHazardCalculator;

import java.util.ArrayList;
import java.util.HashMap;
import java.util.Iterator;
import java.util.Set;

import org.opensha.commons.data.Site;
import org.opensha.commons.data.TimeSpan;
import org.opensha.commons.data.function.ArbitrarilyDiscretizedFunc;
import org.opensha.commons.param.event.ParameterChangeEvent;
import org.opensha.commons.param.event.ParameterChangeWarningEvent;
import org.opensha.commons.param.event.ParameterChangeWarningListener;
import org.opensha.sha.earthquake.rupForecastImpl.GEM1.GEM1ERF;
import org.opensha.sha.earthquake.rupForecastImpl.GEM1.SourceData.GEMSourceData;
import org.opensha.gem.GEM1.calc.gemLogicTree.GemLogicTree;
import org.opensha.gem.GEM1.calc.gemOutput.GEMHazardCurveRepositoryList;
import org.opensha.gem.GEM1.commons.CalculationSettings;
import org.opensha.gem.GEM1.util.CpuParams;
import org.opensha.gem.GEM1.util.DistanceParams;
import org.opensha.gem.GEM1.util.IMLListParams;
import org.opensha.gem.GEM1.util.IntensityMeasureParams;
import org.opensha.gem.GEM1.util.SiteParams;
import org.opensha.gem.GEM1.util.SourceType;
import org.opensha.sha.imr.ScalarIntensityMeasureRelationshipAPI;
import org.opensha.sha.imr.param.OtherParams.ComponentParam;
import org.opensha.sha.imr.param.OtherParams.SigmaTruncLevelParam;
import org.opensha.sha.imr.param.OtherParams.SigmaTruncTypeParam;
import org.opensha.sha.imr.param.OtherParams.StdDevTypeParam;
import org.opensha.sha.imr.param.SiteParams.Vs30_Param;
import org.opensha.sha.util.TectonicRegionType;

public class GemComputeHazardLogicTree {

	private GemLogicTree<ArrayList<GEMSourceData>> ilt;
	private GemLogicTree<HashMap<TectonicRegionType,ScalarIntensityMeasureRelationshipAPI>> gmpeLT;
    private CalculationSettings calcSet;
	
	/**
	 * Constructor
	 * 
	 * @param gEMInputToERFLT
	 * @param nproc
	 * @param siteList
	 * @param AttenRel
	 */
	public GemComputeHazardLogicTree(GemLogicTree<ArrayList<GEMSourceData>> inputToERFLT,
			GemLogicTree<HashMap<TectonicRegionType,ScalarIntensityMeasureRelationshipAPI>> gmpeLT, CalculationSettings calcSet){
		this.ilt = inputToERFLT;
		this.gmpeLT = gmpeLT;
        this.calcSet = calcSet;
	}
	
	public GEMHazardCurveRepositoryList calculateHaz(){
		
		// Instantiate the repository for the results
		GEMHazardCurveRepositoryList hcRepList = new GEMHazardCurveRepositoryList();
		
		// Set Gmpe(s) parameters
		setGmpeParams(gmpeLT, calcSet);
		
		// Iterator over input model end branches
		Set<String> modelLabels = ilt.getEBMap().keySet();
		Iterator<String> iterModelLabels = modelLabels.iterator();
		
		// Calculate the number of GMPE logic tree end branches. This corresponds to the 
		// number of Elements in the HashMap that associate the end branches of the logic 
		// tree to sets of GMPEs dependent on the tectonic region (in principle in each GMPE
		// set there should be one GMPE associated to each Tectonic region contained in the 
		// input model)
		int nEndBranchGmpe = gmpeLT.getEBMap().size();
		
		// Cycle through model end branches
		for (int i=0; i < ilt.getEBMap().size(); i++){

			// Label identifying the current end branch
			String currentModelLabel = iterModelLabels.next();
			System.out.println("ERF End-branch: "+currentModelLabel+" ,"+(i+1)+" of "+ilt.getEBMap().size());
			
			// Instantiate ERF
			GEM1ERF modelERF = new GEM1ERF(ilt.getEBMap().get(currentModelLabel),calcSet);// new GEM1ERF(ilt.getEBMap().get(currentModelLabel));
			// set ERF parameters
			//setErfParams(modelERF);
			// update forecast
			//ParameterChangeEvent event = new ParameterChangeEvent(modelERF,"ciccio","ciccio","ciccio");
			//modelERF.parameterChange(event);
			modelERF.updateForecast();
			
			// Iterator over GEMgmpe
			Set<String> gmpeLabels = gmpeLT.getEBMap().keySet();
			Iterator<String> iterGmpeLabel = gmpeLabels.iterator();
			
			// Cycle through the GMPE end branches
			for (int j=0; j < nEndBranchGmpe; j++){

				// Label identifying the current end branch of the GMPE logic tree
				String currentGmpeLabel = iterGmpeLabel.next();
				System.out.println("GMPE End-branch: "+currentGmpeLabel+" ,"+(j+1)+" of "+nEndBranchGmpe);
				
				// Calculate the hazard
				GemComputeHazard compHaz = new GemComputeHazard(
						(Integer)calcSet.getOut().get(CpuParams.CPU_NUMBER.toString()), 
						(ArrayList<Site>)calcSet.getOut().get(SiteParams.SITE_LIST.toString()), 
						modelERF, gmpeLT.getEBMap().get(currentGmpeLabel),
						(ArbitrarilyDiscretizedFunc)calcSet.getOut().get(IMLListParams.IML_LIST.toString()),
						(Double)calcSet.getOut().get(DistanceParams.MAX_DIST_SOURCE.toString()) );
				hcRepList.add(compHaz.getValues(),currentModelLabel+"_"+currentGmpeLabel);
			}
		}
		return hcRepList;
	}
	
//	public GEMHazardCurveRepositoryList calculateHaz2(){
//		
//		// Instantiate the repository for the results
//		GEMHazardCurveRepositoryList hcRepList = new GEMHazardCurveRepositoryList();
//		
//		// Set Gmpe(s) parameters
//		setGmpeParams();
//		
//		// Iterator over GEMinputToERF
//		Set<String> GEMInputToERFLabels = ilt.getEBMap().keySet();
//		Iterator<String> iterGEMInputToERFLabels = GEMInputToERFLabels.iterator();
//		
//		// Calculate the number of GMPE logic tree end branches. This corresponds to the 
//		// number of Elements in the HashMap that associate the end branches of the logic 
//		// tree to sets of GMPEs dependent on the tectonic region (in principle in each GMPE
//		// set there should be one GMPE associated to each Tectonic region contained in the 
//		// input model)
//		int nEndBranchGmpe = gmpeLT.getEBMap().size();
//		
//		// Cycle through the InputToERF
//		for (int i=0; i < ilt.getEBMap().size(); i++){
//
//			// Label identifying the current end branch
//			String currentGEMInputToERFLabel = iterGEMInputToERFLabels.next();
//			System.out.println("ERF End-branch: "+currentGEMInputToERFLabel+" ,"+(i+1)+" of "+ilt.getEBMap().size());
//			
//			// Instantiate ERF
//			//GEM1ERF modelERF = new GEM1ERF(ilt.getEBMap().get(currentGEMInputToERFLabel));
//			//modelERF.updateForecast();
//			// Iterator over GEMgmpe
//			Set<String> gmpeLabels = gmpeLT.getEBMap().keySet();
//			Iterator<String> iterGmpeLabel = gmpeLabels.iterator();
//			
//			// Cycle through the GMPE end branches
//			for (int j=0; j < nEndBranchGmpe; j++){
//
//				// Label identifying the current end branch of the GMPE logic tree
//				String currentGmpeLabel = iterGmpeLabel.next();
//				System.out.println("GMPE End-branch: "+currentGmpeLabel+" ,"+(j+1)+" of "+nEndBranchGmpe);
//				// Calculate the hazard
//				GemComputeHazard compHaz = new GemComputeHazard((Integer)calcSet.getOut().get(CpuParams.CPU_NUMBER.toString()), 
//						(ArrayList<Site>)calcSet.getOut().get(SiteParams.SITE_LIST.toString()), 
//						(ArrayList<GEMSourceData>)ilt.getEBMap().get(currentGEMInputToERFLabel), gmpeLT.getEBMap().get(currentGmpeLabel),
//						(ArbitrarilyDiscretizedFunc)calcSet.getOut().get(IMLListParams.IML_LIST.toString()),(Double)calcSet.getOut().get(DistanceParams.MAX_DIST_SOURCE.toString()));
//				hcRepList.add(compHaz.getValues(),currentGEMInputToERFLabel+"_"+currentGmpeLabel);
//			}
//		}
//		return hcRepList;
//	}
	
	public static void setGmpeParams(GemLogicTree<HashMap<TectonicRegionType,ScalarIntensityMeasureRelationshipAPI>> gmpeLT, CalculationSettings calcSet){
		
	    // loop over Gmpes logic tree end-branches
		for(int ig=0;ig<gmpeLT.getEBMap().size();ig++){
			
			// number of tectonic regions
			int numTecRegType = TectonicRegionType.values().length;
			// loop over tectonic regions
			for(int itec=0;itec<numTecRegType;itec++){
				
				// current tectonic region
				TectonicRegionType trt = TectonicRegionType.values()[itec];
			
				// if a gmpe for the current tectonic region type is considered in the logic tree than set the params
				if(gmpeLT.getEBMap().get(Integer.toString(ig+1)).get(trt)!=null){
					
					// current attenuation relationship short name
					String arShortName = gmpeLT.getEBMap().get(Integer.toString(ig+1)).get(trt).getShortName();
					
					// if the calculation settings for the corresponding gmpe exists than set the parameters
					if(calcSet.getGmpe().get(arShortName)!=null){
						
						// intensity measure type
						String imt = calcSet.getOut().get(IntensityMeasureParams.INTENSITY_MEAS_TYPE.toString()).toString();
						gmpeLT.getEBMap().get(Integer.toString(ig+1)).get(trt).setIntensityMeasure(imt);
						
						// truncation type
						String sttp = calcSet.getOut().get(SigmaTruncTypeParam.NAME).toString();
						gmpeLT.getEBMap().get(Integer.toString(ig+1)).get(trt).getParameter(SigmaTruncTypeParam.NAME).setValue(sttp);
						
						// truncation level
						double stlp = (Double)calcSet.getOut().get(SigmaTruncLevelParam.NAME);
						gmpeLT.getEBMap().get(Integer.toString(ig+1)).get(trt).getParameter(SigmaTruncLevelParam.NAME).setValue(stlp);
						
						// standard deviation type
						String sdtp = calcSet.getOut().get(StdDevTypeParam.NAME).toString();
						gmpeLT.getEBMap().get(Integer.toString(ig+1)).get(trt).getParameter(StdDevTypeParam.NAME).setValue(sdtp);
						
						// component
						String cp = calcSet.getGmpe().get(arShortName).get(ComponentParam.NAME).toString();
						gmpeLT.getEBMap().get(Integer.toString(ig+1)).get(trt).getParameter(ComponentParam.NAME).setValue(cp);
						
						// vs 30 (This is optional)
						if((Double)calcSet.getGmpe().get(arShortName).get(Vs30_Param.NAME)!=null){
							double vs30 = (Double)calcSet.getGmpe().get(arShortName).get(Vs30_Param.NAME);
							gmpeLT.getEBMap().get(Integer.toString(ig+1)).get(trt).getParameter(Vs30_Param.NAME).setValue(vs30);
						}

					}
				    // else throw exception 
					else{
						System.out.println("Calculation settings for "+arShortName+" does not exist!");
						System.exit(0);
					}
			}
			}
		}
	}
	
	private void setErfParams(GEM1ERF modelERF){
		
		// set area source parameters
	    // source modeling type
	    modelERF.setParameter(GEM1ERF.AREA_SRC_RUP_TYPE_NAME, (String) calcSet.getErf().get(SourceType.AREA_SOURCE).get(GEM1ERF.AREA_SRC_RUP_TYPE_NAME));
	    // lower seismogenic depth
	    modelERF.setParameter(GEM1ERF.AREA_SRC_LOWER_SEIS_DEPTH_PARAM_NAME, (Double) calcSet.getErf().get(SourceType.AREA_SOURCE).get(GEM1ERF.AREA_SRC_LOWER_SEIS_DEPTH_PARAM_NAME));
	    // source discretization
	    modelERF.setParameter(GEM1ERF.AREA_SRC_DISCR_PARAM_NAME, (Double) calcSet.getErf().get(SourceType.AREA_SOURCE).get(GEM1ERF.AREA_SRC_DISCR_PARAM_NAME));
	    // magnitude scaling relationship
		modelERF.setParameter(GEM1ERF.AREA_SRC_MAG_SCALING_REL_PARAM_NAME, (String) calcSet.getErf().get(SourceType.AREA_SOURCE).get(GEM1ERF.AREA_SRC_MAG_SCALING_REL_PARAM_NAME));
		
		// set point source parameters
	    // source modeling type
	    modelERF.setParameter(GEM1ERF.GRIDDED_SEIS_RUP_TYPE_NAME, (String) calcSet.getErf().get(SourceType.GRID_SOURCE).get(GEM1ERF.GRIDDED_SEIS_RUP_TYPE_NAME));
	    // lower seismogenic depth
	    modelERF.setParameter(GEM1ERF.GRIDDED_SEIS_LOWER_SEIS_DEPTH_PARAM_NAME, (Double) calcSet.getErf().get(SourceType.GRID_SOURCE).get(GEM1ERF.GRIDDED_SEIS_LOWER_SEIS_DEPTH_PARAM_NAME));
	    // mag scaling relationship
	    modelERF.setParameter(GEM1ERF.GRIDDED_SEIS_MAG_SCALING_REL_PARAM_NAME, (String) calcSet.getErf().get(SourceType.GRID_SOURCE).get(GEM1ERF.GRIDDED_SEIS_MAG_SCALING_REL_PARAM_NAME));
	    
	    // set fault source parameters
	    // rupture offset
	    modelERF.setParameter(GEM1ERF.FAULT_RUP_OFFSET_PARAM_NAME, (Double) calcSet.getErf().get(SourceType.FAULT_SOURCE).get(GEM1ERF.FAULT_RUP_OFFSET_PARAM_NAME));
	    // fault discretization
	    modelERF.setParameter(GEM1ERF.FAULT_DISCR_PARAM_NAME, (Double) calcSet.getErf().get(SourceType.FAULT_SOURCE).get(GEM1ERF.FAULT_DISCR_PARAM_NAME));
	    // mag scaling relationship
	    modelERF.setParameter(GEM1ERF.FAULT_MAG_SCALING_REL_PARAM_NAME, (String) calcSet.getErf().get(SourceType.FAULT_SOURCE).get(GEM1ERF.FAULT_MAG_SCALING_REL_PARAM_NAME));
	    // standard deviation
	    modelERF.setParameter(GEM1ERF.FAULT_SCALING_SIGMA_PARAM_NAME, (Double) calcSet.getErf().get(SourceType.FAULT_SOURCE).get(GEM1ERF.FAULT_SCALING_SIGMA_PARAM_NAME));
	    // rupture aspect ratio
	    modelERF.setParameter(GEM1ERF.FAULT_RUP_ASPECT_RATIO_PARAM_NAME, (Double) calcSet.getErf().get(SourceType.FAULT_SOURCE).get(GEM1ERF.FAULT_RUP_ASPECT_RATIO_PARAM_NAME));
	    // rupture floating type
	    modelERF.setParameter(GEM1ERF.FAULT_FLOATER_TYPE_PARAM_NAME, (String) calcSet.getErf().get(SourceType.FAULT_SOURCE).get(GEM1ERF.FAULT_FLOATER_TYPE_PARAM_NAME));
	    
	    // set subduction fault parameters
	    modelERF.setParameter(GEM1ERF.SUB_RUP_OFFSET_PARAM_NAME, (Double) calcSet.getErf().get(SourceType.SUBDUCTION_FAULT_SOURCE).get(GEM1ERF.SUB_RUP_OFFSET_PARAM_NAME));
	    // fault discretization
	    modelERF.setParameter(GEM1ERF.SUB_DISCR_PARAM_NAME, (Double) calcSet.getErf().get(SourceType.SUBDUCTION_FAULT_SOURCE).get(GEM1ERF.SUB_DISCR_PARAM_NAME));
	    // mag scaling relationship
	    modelERF.setParameter(GEM1ERF.SUB_MAG_SCALING_REL_PARAM_NAME, (String) calcSet.getErf().get(SourceType.SUBDUCTION_FAULT_SOURCE).get(GEM1ERF.SUB_MAG_SCALING_REL_PARAM_NAME));
	    // standard deviation
	    modelERF.setParameter(GEM1ERF.SUB_SCALING_SIGMA_PARAM_NAME, (Double) calcSet.getErf().get(SourceType.SUBDUCTION_FAULT_SOURCE).get(GEM1ERF.SUB_SCALING_SIGMA_PARAM_NAME));
	    // rupture aspect ratio
	    modelERF.setParameter(GEM1ERF.SUB_RUP_ASPECT_RATIO_PARAM_NAME, (Double) calcSet.getErf().get(SourceType.SUBDUCTION_FAULT_SOURCE).get(GEM1ERF.SUB_RUP_ASPECT_RATIO_PARAM_NAME));
	    // rupture floating type
	    modelERF.setParameter(GEM1ERF.SUB_FLOATER_TYPE_PARAM_NAME, (String) calcSet.getErf().get(SourceType.SUBDUCTION_FAULT_SOURCE).get(GEM1ERF.SUB_FLOATER_TYPE_PARAM_NAME));
	    
		// set time span
		TimeSpan timeSpan = new TimeSpan(TimeSpan.NONE,TimeSpan.YEARS);
		timeSpan.setDuration((Double) calcSet.getOut().get(TimeSpan.DURATION));
		modelERF.setTimeSpan(timeSpan);
	    
		
	}

	
}
