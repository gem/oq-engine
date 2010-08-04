package scratch.matt.calc;

import org.opensha.commons.geo.GriddedRegion;
import org.opensha.sha.earthquake.griddedForecast.GenericAfterHypoMagFreqDistForecast;
import org.opensha.sha.earthquake.griddedForecast.GriddedHypoMagFreqDistForecast;
import org.opensha.sha.earthquake.griddedForecast.HypoMagFreqDistAtLoc;
import org.opensha.sha.earthquake.griddedForecast.STEP_CombineForecastModels;
import org.opensha.sha.earthquake.griddedForecast.SequenceAfterHypoMagFreqDistForecast;
import org.opensha.sha.earthquake.griddedForecast.SpatialAfterHypoMagFreqDistForecast;
import org.opensha.sha.earthquake.observedEarthquake.ObsEqkRupList;

/**
 * <p>Title: </p>
 *
 * <p>Description: </p>
 *
 * <p>Copyright: Copyright (c) 2002</p>
 *
 * <p>Company: </p>
 *
 * @author not attributable
 * @version 1.0
 */
public class UpdateSTEP_Forecast {
  private ObsEqkRupList aftershocks;
  private GenericAfterHypoMagFreqDistForecast forecastModelGen;
  private SequenceAfterHypoMagFreqDistForecast forecastModelSeq;
  private SpatialAfterHypoMagFreqDistForecast forecastModelSpa;
  private GriddedRegion backgroundRatesGrid;
  private STEP_CombineForecastModels sequenceModel;
  private boolean useSeqAndSpat, gridIsUpdated = false;
  private static int numGridNodes;
  private HypoMagFreqDistAtLoc genForecastAtLoc,seqForecastAtLoc,spaForecastAtLoc;
  private GriddedHypoMagFreqDistForecast genGriddedForecast;
 

  public UpdateSTEP_Forecast(STEP_CombineForecastModels sequenceModel) {
    this.sequenceModel = sequenceModel;
    initUpdate();
  }



  /**
   * initUpdate
   */
  private void initUpdate() {
	  forecastModelGen = this.sequenceModel.getGenElement();
	  aftershocks = sequenceModel.getAfterShocks();
	  
	  
	  /**
	   * check to see if the aftershock zone needs to be updated
	   * if it is, update the generic model
	   */
	  updateAftershockZone();
	  
	  //numGridNodes = forecastModelGen.getNumHypoLocs();
	  
	  if (gridIsUpdated) {
		  updateGenericModelParms();
	  }
	  
	  // check to see if there are enough aftershock above completeness
	  // to calculate all model elements
	  //
	  // There MUST be a better way to do this...
	  
	  sequenceModel.set_useSeqAndSpatial();
	  if ( sequenceModel.get_useSeqAndSpatial()){
		  // if the sequence specific element does not exist, create it
		  if (!sequenceModel.getExistSeqElement())
			  sequenceModel.createSequenceElement();
		  forecastModelSeq = sequenceModel.getSeqElement();
		  updateSequenceModelParms();
		  
		  // if the spatial element does not exist, create it.
		  if (!sequenceModel.getExistSpaElement())
			  sequenceModel.createSpatialElement();
		  forecastModelSpa = sequenceModel.getSpaElement();
		  updateSpatialModelParms();
	  }
	  
	  // now calculate the forecasts for each of the elements
	  this.updateGenericModelForecast();
	  if ( sequenceModel.get_useSeqAndSpatial()){
		  this.updateSequenceModelForecast();
		  this.updateSpatialModelForecast();
	  }
	  
	  // create the AIC combined model forecast
	  //this.updateAIC_CombinedModelForecast();
	  
  }
  
  /**
   * updateAftershockZone
   */
  public void updateAftershockZone() {
	  int numAftershocks = aftershocks.size();
	  
	  boolean hasExternalFault = sequenceModel.getHasExternalFaultModel();
	  
	  if ((numAftershocks >= 100) && (hasExternalFault = false)) {
		  sequenceModel.calcTypeII_AfterShockZone(aftershocks, backgroundRatesGrid);
		  gridIsUpdated = true;
	  } 
  }
  
  /**
   * updateGenericModelParms
   * 
   * Redistribute the generic values on the aftershock zone grid
   * (which has probably been updated)
   */
  public void updateGenericModelParms() {
	  forecastModelGen.setNumGridLocs();
	  double[] kScaler = DistDecayFromRupCalc.getDensity(sequenceModel.getMainShock(),sequenceModel.getAfterShockZone());
	  forecastModelGen.set_kScaler(kScaler);
	  forecastModelGen.set_Gridded_Gen_bValue();
	  forecastModelGen.set_Gridded_Gen_cValue();
	  forecastModelGen.set_Gridded_Gen_kValue();
	  forecastModelGen.set_Gridded_Gen_pValue();
  }
  
  /**
   * updateSequenceModelParms
   */
  public void updateSequenceModelParms() {
	  double[] kScaler = DistDecayFromRupCalc.getDensity(sequenceModel.getMainShock(),sequenceModel.getAfterShockZone());
	  forecastModelSeq.set_kScaler(kScaler);
	  forecastModelSeq.calc_SeqNodeCompletenessMag();
	  forecastModelSeq.set_SequenceRJParms();
	  forecastModelSeq.set_SequenceOmoriParms();
	  forecastModelSeq.fillGridWithSeqParms();
  }
  
  /**
   * updateSpatialModelParms
   */
  public void updateSpatialModelParms() {
	  // this will calc a, b, c, p, k and completeness on the grid
	  forecastModelSpa.calc_GriddedRJParms();
	  forecastModelSpa.setAllGridedRJ_Parms();
  }
  
  /**
 *  updateGenericModelForecast
 */
public void updateGenericModelForecast() {
	//first initialise the array that will contain the forecast
	forecastModelGen.initNumGridInForecast();
	int numGridLocs = sequenceModel.getAfterShockZone().getNodeCount();
	int gLoop = 0;
	while ( gLoop < numGridLocs) {
		 genForecastAtLoc = forecastModelGen.calcHypoMagFreqDist(gLoop);
		 forecastModelGen.setGriddedMagFreqDistAtLoc(genForecastAtLoc, gLoop++);
	}
	  
  }

/**
 *  updateSequenceModelForecast
 */
public void updateSequenceModelForecast() {
	//first initialise the array that will contain the forecast
	forecastModelSeq.initNumGridInForecast();
	int numGridLocs = sequenceModel.getAfterShockZone().getNodeCount();
	int gLoop = 0;
	while ( gLoop < numGridLocs) {
		 seqForecastAtLoc = forecastModelSeq.calcHypoMagFreqDistAtLoc(gLoop);
		 forecastModelSeq.setGriddedMagFreqDistAtLoc(seqForecastAtLoc, gLoop++);
	}
	  
  }
  

/**
 *  updateSpatialModelForecast
 */
public void updateSpatialModelForecast() {
	//first initialise the array that will contain the forecast
	forecastModelSpa.initNumGridInForecast();
	int numGridLocs = sequenceModel.getAfterShockZone().getNodeCount();
	int gLoop = 0;
	while ( gLoop < numGridLocs) {
		 spaForecastAtLoc = forecastModelSpa.calcHypoMagFreqDistAtLoc(gLoop);
		 forecastModelSpa.setGriddedMagFreqDistAtLoc(spaForecastAtLoc, gLoop++);
	}
	  
  }

public void updateAIC_CombinedModelForecast(){
	sequenceModel.createCombinedForecast();
}
  /**
   * setBackGroundGrid
   * if the background needs to be changed - this also recalculates the
   * aftershock zone if necessary.
   */
  public void setBackGroundGrid(GriddedRegion backgroundRatesGrid) {
	  this.backgroundRatesGrid = backgroundRatesGrid;
	  // forecastModelGen.calcTypeI_AftershockZone(backgroundRatesGrid);
	  updateAftershockZone();
  }
  
  /**
   * getBackGroundGrid
   */
  public GriddedRegion getBackGroundGrid() {
	  return this.backgroundRatesGrid;
  }
  
  
  
}
