package scratch.matt.calc;

/**
 * <p>Title: </p>
 *
 * <p>Description: Calculates the forecasted rate of events based on the modified
 * Omori law and the given time span
 * Input is, in the following order:
 * double k value
 * double c value
 * double p value
 * timeParms[0] = forecastStartTime
 * timeParms[1] = forecastEndTime
 *  </p>
 *
 * <p>Copyright: Copyright (c) 2002</p>
 *
 * <p>Company: </p>
 *
 * @author Matt Gerstenberger
 * @version 1.0
 */
public class OmoriRate_Calc {
  private double k_value;
  private double c_value;
  private double p_value;
  private double time_start;
  private double time_end;
  private double eventRate;

  public OmoriRate_Calc(){
  }

  public OmoriRate_Calc(double[] rjParms, double[] timeParms) {
    setTimeParms(timeParms);
    set_OmoriParms(rjParms);
  }

  /**
   * set_OmoriParms
   * set the k,c and p values
   * set the begin time and end time for the calculations
   * do the calculation
   */
  public void set_OmoriParms(double[] rjParms) {
    k_value = rjParms[0];
    c_value = rjParms[1];
    p_value = rjParms[2];

    calc_OmoriRate();
  }

  /**
   * setTimeParms
   */
  public void setTimeParms(double[] timeParms) {
    time_start = timeParms[0];
    time_end = timeParms[1];
  }

  /**
   * get_OmoriRate
   * return the calculated rate
   */
  public double get_OmoriRate() {
    return eventRate;
  }

  /**
   * calc_OmoriRate
   * calculate the Omori rate based on the set parameters
   * k,c,p, start time and end time
   */
  private void calc_OmoriRate() {

    double pInv = 1 - p_value;

    if (p_value == 1)
        eventRate = k_value*Math.log((time_end+c_value)/(time_start+c_value));
    else
        eventRate = k_value/(pInv)*(Math.pow(time_end+c_value,pInv)-Math.pow(time_start+c_value,pInv));
  }


}
