package scratch.matt.calc;

//import org.opensha.sha.earthquake.griddedForecast.AfterShockHypoMagFreqDistForecast;
import org.opensha.sha.earthquake.observedEarthquake.ObsEqkRupList;
import org.opensha.sha.earthquake.observedEarthquake.ObsEqkRupListCalc;

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
public class OgataLogLike_Calc {
  private double k_value;
  private double c_value;
  private double p_value;
  private long[] intEventTimes;
  private double minIntTime;
  private double maxIntTime;
  private double logLikelihood;


  public OgataLogLike_Calc(double[] OmoriParms, ObsEqkRupList aftershockList) {
    set_OmoriParms(OmoriParms, aftershockList);
  }

  /**
   * set_OmoriParms
   */
  public void set_OmoriParms(double[] OmoriParms, ObsEqkRupList aftershockList) {
    k_value = OmoriParms[0];
    c_value = OmoriParms[1];
    p_value = OmoriParms[2];


    intEventTimes = ObsEqkRupListCalc.getInterEventTimes(aftershockList);
    minIntTime = ListSortingTools.getMinVal(intEventTimes);
    maxIntTime = ListSortingTools.getMaxVal(intEventTimes);
    calc_OgataLoglike();
  }

  /**
   * get_OgataLogLikelihood
   */
  public double get_OgataLogLikelihood() {
    return logLikelihood;
  }

  /**
   * calc_OgataLoglike
   */
  private void calc_OgataLoglike() {
    double sumInt = 0;
    double Acp;
    double pInv = 1-p_value;
    //double logLikelihood;

    int numInts = intEventTimes.length;

    for (int intLoop = 0; intLoop < numInts; ++intLoop){
      sumInt = sumInt + Math.log(intEventTimes[intLoop] + c_value);
    }
    if (p_value == 1)
      Acp = Math.log(maxIntTime+c_value)-Math.log(minIntTime+c_value);
    else
      Acp = (Math.pow(maxIntTime+c_value,pInv)-Math.pow(minIntTime+c_value,p_value))/pInv;

    if (numInts > 0)
      logLikelihood = numInts*Math.log(k_value)-p_value*sumInt-k_value*Acp;
    else
      logLikelihood = -p_value*sumInt-k_value*Acp;



  }

  public static void main(String[] args) {
  }
}
