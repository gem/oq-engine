package scratch.matt.calc;

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
public class MaxLikeOmori_Calc {
  private static double cGuess = 0.05;
  private static double pGuess = 0.9;
  private static double kGuess;
  private static double maxErrorAllow = .001;
  private static double oldError2 = 1;
  private static double oldError1 = 1;
  private static double minStep = .0001;
  private static double pStep = 0.05;
  private static double cStep = 0.05;
  private static double error2 = 1;
  private static double error1 = 1;
  private static double minIntTime;
  private static double maxIntTime;
  private static double maxIterations = 500;

  public MaxLikeOmori_Calc() {
  }

  public void main(String[] args) {
    MaxLikeOmori_Calc maxlikeomori_calc = new MaxLikeOmori_Calc();
  }

  /**
   * set_Fixed_cValue
   * set the value c is fixed to.
   * Default is 0.05
   */
  public void set_Fixed_cValue(double cVal) {
    cGuess = cVal;
  }

  /**
   * set_pGuess
   * set the starting guess for p.  Default is 0.9
   */
  public void set_pGuess(double pVal) {
    pGuess = pVal;
  }

  /**
   * set_AfterShockListFixed_c
   * pass the afterhshock model and estimate p and k with a fixed c
   */
  public void set_AfterShockListFixed_c(ObsEqkRupList aftershockList) {

    long[] intEventTimes =  ObsEqkRupListCalc.getInterEventTimes(aftershockList);

    int iterCount = 1;

    while ((Math.abs(error2) > maxErrorAllow) && (pStep <= minStep)){
      calc_pErrFixed_c(intEventTimes);
      update_pFixed_c();

      /**
       * stop the iterations if it does not find an answer
       * in maxIterations attempts.  In this case p = 0.
       */

      if (iterCount++ >= maxIterations){
        pGuess = Double.NaN;
        break;
      }
    }

  }

  /**
   * set_AfterShockList
   */
  public void set_AfterShockList(ObsEqkRupList aftershockList) {
    double iterCount = 0;

    long[] intEventTimes =  ObsEqkRupListCalc.getInterEventTimes(aftershockList);

    while ((Math.abs(error1) > maxErrorAllow) && ((Math.abs(error2) > maxErrorAllow))) {

     if ( (cStep > minStep) && (pStep > minStep));{
       calc_pErr(intEventTimes);
       update_p_c();
     }
     /**
    * stop the iterations if it does not find an answer
    * in maxIterations attempts.  In this case p = 0.
    */

     if (iterCount++ >= maxIterations){
       pGuess = Double.NaN;
       break;
     }

    }
  }



  /**
  * get_p_value
  * return the estimate of the p_value
  */
 public double get_p_value() {
   return pGuess;
 }

 /**
 * get_k_value
 */
 public double get_k_value() {
   return kGuess;
}

/**
* get_c_value
  *  */
 public double get_c_value() {
  return cGuess;
}


  /**
   * calc_pErr
   * this estimates k, c and p.  It does not assume a fixed c value.
   * It calculates the misfit error, which is used in update_p_c
   */
  private void calc_pErr(long[] intEventTimes) {

    /**
     *  pGuess is guessed p-value.
     */
    minIntTime = ListSortingTools.getMinVal(intEventTimes);
    maxIntTime = ListSortingTools.getMaxVal(intEventTimes);
    double pInv=1-pGuess;
    int numInts = intEventTimes.length;

    double kGuess=(pInv*numInts)/(Math.pow(maxIntTime+cGuess,pInv)-Math.pow(minIntTime+cGuess,pInv));
    double pSum=0;
    double qSum=kGuess*(1.0/Math.pow(maxIntTime+cGuess,pGuess)-(1/Math.pow(minIntTime+cGuess,pGuess)));

    double sumln=0;
    for ( int intLoop = 0; intLoop <= numInts; intLoop++) {
      sumln = sumln + (Math.log(intEventTimes[intLoop] + cGuess));
      pSum = pSum + (1.0/(intEventTimes[intLoop] + cGuess));
    }

    double esum = qSum+pGuess*pSum;
    error1 = esum;

    double qsumln=kGuess/Math.pow(pInv,2);
    qsumln=qsumln*(Math.pow(maxIntTime+cGuess,pInv)*(1-pInv*Math.log(maxIntTime+cGuess))-(Math.pow(minIntTime+cGuess,pInv)*(1-pInv*Math.log(minIntTime+cGuess))));
    error2 = qsumln + sumln;
    double errCof=kGuess/pInv;
    double errCog=errCof*(Math.pow(minIntTime+cGuess,pInv));
    double likelihood =(numInts*Math.log(kGuess))-(pGuess*sumln)-numInts;
    double aic=-2*likelihood+4;

  }

  /**
   * calc_pErrFixed_c
   * Given an estimate of p, this calculates the error estimate
   * a fixed c is used (default = .05)
   * update_p calculates a new p value based on the guess p and the misfit
   */
  private void calc_pErrFixed_c(long[] intEventTimes) {

    /**
     *  pGuess is guessed p-value.
     */
    minIntTime = ListSortingTools.getMinVal(intEventTimes);
    maxIntTime = ListSortingTools.getMaxVal(intEventTimes);
    double pInv=1-pGuess;
    int numInts = intEventTimes.length;

    double kGuess=(pInv*numInts)/(Math.pow(maxIntTime+cGuess,pInv)-Math.pow(minIntTime+cGuess,pInv));
    double sumln=0;
    for ( int intLoop = 0; intLoop <= numInts; intLoop++) {
      sumln = sumln + (Math.log(intEventTimes[0] + cGuess));
    }
    double qsumln=kGuess/Math.pow(pInv,2);
    qsumln=qsumln*(Math.pow(maxIntTime+cGuess,pInv)*(1-pInv*Math.log(maxIntTime+cGuess))-(Math.pow(minIntTime+cGuess,pInv)*(1-pInv*Math.log(minIntTime+cGuess))));
    error2 = qsumln + sumln;
    double errCof=kGuess/pInv;
    double errCog=errCof*(Math.pow(minIntTime+cGuess,pInv));
    double likelihood =(numInts*Math.log(kGuess))-(pGuess*sumln)-numInts;
    double aic=-2*likelihood+4;

    }

  /**
   * update_pFixed_c
   * given an estimate of p and the error, this
   * updates the estimate of p (pGuess).  A fixed c is assumed (default = .05)
   */
  private void update_pFixed_c() {

    if ((error2 * oldError2 <= 0.0) && (pStep >= minStep)) {
      pStep = pStep * 0.9;
    }
    if (error2 < 0) {
      pGuess = pGuess + pStep;
    }
    if (error2 > 0) {
      pGuess = pGuess - pStep;
    }

    oldError2 = error2;
  }

  /**
   * update_p
   */
  private void update_p_c() {
    if ((oldError1 * error1 < 0.0) && (cStep >= minStep));{
      cStep = cStep*0.9;
    }
    if ((oldError2 * error2 < 0.0) && (pStep >= minStep));{
      pStep = pStep * 0.9;
    }
    if (error1 < 0)
      cGuess = cGuess + cStep;
    else if (error1 > 0)
      cGuess = cGuess - cStep;

    if (cGuess < 0) {
      cGuess = 0;
      cStep = cStep * 0.9;
    }

    if (error2 < 0)
      pGuess = pGuess + pStep;
    else if (error2 > 0)
      pGuess = pGuess - pStep;

    oldError1 = error1;
    oldError2 = error2;

  }

  /**
   * calc_pFixedStdError
   */
  private void calc_pFixedStdError(double pGuess) {
         double[] s = new double[]{3};
         double f1=Math.pow(maxIntTime+cGuess,-pGuess+1)/(-pGuess+1);
         double h1=Math.pow(minIntTime+cGuess,-pGuess+1)/(-pGuess+1);
         s[0]=(1.0/kGuess)*(f1-h1);

         double f3=Math.pow(-(maxIntTime+cGuess),-pGuess+1)*(((Math.log(maxIntTime+cGuess))/(-pGuess+1))-(1/Math.pow(-pGuess+1,2)));
         double h3=Math.pow(-(minIntTime+cGuess),-pGuess+1)*(((Math.log(minIntTime+cGuess))/(-pGuess+1))-(1/Math.pow(-pGuess+1,2)));
         s[1]=f3-h3;
         s[2]=s[1];

         double f10=Math.pow(maxIntTime+cGuess,-pGuess+1)*Math.pow(Math.log(maxIntTime+cGuess),2)/(-pGuess+1);
         double f11=(2*(Math.pow(maxIntTime+cGuess,-pGuess+1)))/Math.pow(-pGuess+1,2);
         double f12=(Math.log(maxIntTime+cGuess))-(1/(-pGuess+1));
         double f9=f10-(f11*f12);

         double h10=Math.pow(minIntTime+cGuess,-pGuess+1)*Math.pow(Math.log(minIntTime+cGuess),2)/(-pGuess+1);
         double h11=(2*(Math.pow(minIntTime+cGuess,-pGuess+1)))/Math.pow(-pGuess+1,2);
         double h12=(Math.log(minIntTime+cGuess))-(1/(-pGuess+1));
         double h9=h10-(h11*h12);
         s[3]=(kGuess)*(f9-h9);

         /**
          * assign the values of s to the matrix a(i,j)
          * start inverting the matrix and calculate the standard deviation
          * for k and p
          */

         /**
         double ainv = Math.
   ainv=[s(1) s(2); s(3) s(4)];

   ainv=inv(ainv);

   sdk=sqrt(ainv(1,1));
   sdp=sqrt(ainv(2,2));
*/


  }



  }


