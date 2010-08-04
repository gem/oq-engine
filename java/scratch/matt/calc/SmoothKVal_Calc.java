package scratch.matt.calc;

import java.util.Iterator;
import java.util.ListIterator;

import org.opensha.commons.geo.GriddedRegion;
import org.opensha.commons.geo.Location;
import org.opensha.commons.geo.LocationUtils;
import org.opensha.sha.earthquake.griddedForecast.GenericAfterHypoMagFreqDistForecast;
import org.opensha.sha.earthquake.griddedForecast.STEP_AftershockForecast;
import org.opensha.sha.earthquake.griddedForecast.SequenceAfterHypoMagFreqDistForecast;
import org.opensha.sha.earthquake.observedEarthquake.ObsEqkRupture;
import org.opensha.sha.faultSurface.FaultTrace;
import org.opensha.sha.faultSurface.SimpleFaultData;

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
public class SmoothKVal_Calc {
  private  STEP_AftershockForecast aftershockModel;
  private  GriddedRegion aftershockZone;
  private double global_aVal, global_bVal, global_Mc, mainshockMag, numInd;
  private double seq_kVal;
  private ObsEqkRupture mainshock;
  private FaultTrace faultTrace;
  private double[] nodeTaperGen_k, nodeTaperSeq_k, nodePerc;
  private int numLocs;


  public SmoothKVal_Calc() {
  }

  /**
  * setAftershockModel
  */
 public void setAftershockModel(GenericAfterHypoMagFreqDistForecast aftershockModel) {
   aftershockZone = aftershockModel.getAfterShockZone();

     double global_aVal = aftershockModel.get_a_valueGeneric();
     double global_bVal = aftershockModel.get_b_valueGeneric();
     double global_Mc = aftershockModel.get_genNodeCompletenessMag();

   SimpleFaultData mainshockFault = aftershockModel.get_FaultModel();
   mainshock = aftershockModel.getMainShock();
   faultTrace = mainshockFault.getFaultTrace();
   mainshockMag = mainshock.getMag();

   //now do the calculations
   setNodePerc();
 }

 /**
   * setAftershockModel
   *
   */
  public void setAftershockModel(SequenceAfterHypoMagFreqDistForecast aftershockModel) {
    aftershockZone = aftershockModel.getAfterShockZone();

      double global_aVal = aftershockModel.get_aValSequence();
      double global_bVal = aftershockModel.get_bValSequence();
      double global_Mc = aftershockModel.getSeqNodeCompletenessMag();

    SimpleFaultData mainshockFault = aftershockModel.get_FaultModel();
    mainshock = aftershockModel.getMainShock();
    faultTrace = mainshockFault.getFaultTrace();

    //now do the calculations
    //set_k_value();

 }


      /**
     * setNodePerc
     * This will taper assign a percentage of the k value that should
     * be assigned to each grid node.
     */
    private void setNodePerc() {
      double sumInvDist = 0;

      numLocs = aftershockZone.getNodeCount();
      double[] nodeDistFromFault = new double[numLocs];
      double[] invDist = new double[numLocs];
      nodePerc = new double[numLocs];

      //get the iterator of all the locations within that region
      Iterator<Location> it = aftershockZone.getNodeList().iterator();
      int ind = 0;
      int numFaultPoints = faultTrace.size();
      double totDistFromFault = 0;
      while (it.hasNext()) {
        nodeDistFromFault[ind++] = LocationUtils.distanceToLineFast(
        		faultTrace.get(0),
        		faultTrace.get(numFaultPoints),
        		it.next());
        totDistFromFault = totDistFromFault +
            Math.pow(nodeDistFromFault[ind - 1], 2.0);
      }

      for (int indLoop = 0; indLoop < numLocs; ++indLoop) {
        invDist[indLoop] = totDistFromFault /
            Math.pow(nodeDistFromFault[indLoop], 2.0);
        sumInvDist = sumInvDist + invDist[indLoop];
      }

      for (int indLoop = 0; indLoop < ind - 1; ++indLoop) {
        nodePerc[indLoop] = invDist[indLoop] / sumInvDist;
      }

      numInd = ind;

    }

  /**
   * setSeq_kVal
   */
  public void setSeq_kVal(double seq_kVal) {
    this.seq_kVal = seq_kVal;
    calcSeqGrid_kVal();
  }

  /**
   * calcGenGrid_kVal
   */
  private void calcGenGrid_kVal() {
    double rightSide = global_aVal + global_bVal * (mainshockMag - global_Mc);
      double generic_k = Math.pow(10,rightSide);
      nodeTaperGen_k =  new double[numLocs];

      for (int indLoop = 0; indLoop < numInd -1; ++indLoop) {
           nodeTaperGen_k[indLoop] = generic_k * nodePerc[indLoop];
      }

  }

  /**
   * calcSeqGrid_kVal
   */
  private void calcSeqGrid_kVal() {
    nodeTaperSeq_k =  new double[numLocs];
    for (int indLoop = 0; indLoop < numInd -1; ++indLoop) {
           nodeTaperSeq_k[indLoop] = seq_kVal * nodePerc[indLoop];
      }
  }

  /**
   * get_SmoothGen_kVal
   */
  public double[] get_SmoothGen_kVal() {
    calcGenGrid_kVal();
    return nodeTaperGen_k;
  }

  /**
   * get_SmoothSeq_kVal
   */
  public double[] get_SmoothSeq_kVal() {
    return nodeTaperSeq_k;
  }



}
