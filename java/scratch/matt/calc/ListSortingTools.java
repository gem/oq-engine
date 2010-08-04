package scratch.matt.calc;

import java.util.Arrays;
import java.util.ListIterator;

import org.opensha.sha.earthquake.observedEarthquake.ObsEqkRupList;
import org.opensha.sha.earthquake.observedEarthquake.ObsEqkRupture;


/**
 * <p>Title: listSortingTools</p>
 * <p>Description: A suite of tools that will sort or operate on a
 * list of values </p>
 * @author Matt Gerstenberger 2004
 * @version 1.0
 */

public class ListSortingTools {


  /**
   * default constructor
   */
  public ListSortingTools() {
  }



  /**
   * Calculate the minimum value from a list
   * @param valList double[]
   * @return double minVal
   */


  public static double getMinVal(double[] valList) {
    // find the minimum magnitude of the given catalogue
    double minVal = valList[0];

    int size = valList.length;
    for (int valLoop = 1; valLoop < size; ++valLoop)
      if (valList[valLoop] < minVal) {
        minVal = valList[valLoop];
      }
    return minVal;
  }

  /**
   * Calculate the maximum value from a list
   * @param valList double[]
   * @return double
   */
  public static double getMaxVal(double[] valList) {
    // find the maximum magnitude of the given catalogue
    double maxVal = valList[0];

    int size = valList.length;
    for (int valLoop = 1; valLoop < size; ++valLoop)
      if (valList[valLoop] > maxVal) {
        maxVal = valList[valLoop];
      }
    return maxVal;
  }

  /**
     * Calculate the maximum value from a list
     * @param valList int[]
     * @return int
     */

  public static int getMaxVal(int[] valList) {

      // find the maximum magnitude of the given catalogue
      int maxVal = valList[0];
      int size = valList.length;
      for (int valLoop = 1; valLoop < size; ++valLoop)
        if (valList[valLoop] > maxVal) {
          maxVal = valList[valLoop];
        }
      return maxVal;
    }


    /**
     * Gets the Maximum value from long[].
     * @param valList long[] list of long values
     * @return long
     */
    public static long getMaxVal(long[] valList) {
      Arrays.sort(valList);
      return valList[valList.length - 1];
    }

    /**
     * Gets the Minimum value from long[].
     * @param valList long[] list of long values
     * @return long
     */
    public static long getMinVal(long[] valList) {
      Arrays.sort(valList);
      return valList[0];
    }



    /**
     * Calculate the mean value from a list
     * @param valList double[]
     * @return double
     */

  public static double getMeanVal(double[] valList) {
    // find the mean value
    double sum = 0;
    int size = valList.length;
    for (int valLoop = 0; valLoop < size; ++valLoop)
      sum += valList[valLoop];
    return (sum / size);
  }

  /**
   * find the array index for input value;
   * will return the first match only (assumes input is sorted)
   * @param val double
   * @param valList double[]
   * @return int
   */
  public static int findIndex(double val, double[] valList)
      throws NoValMatchFoundException {

    int size = valList.length;
    int indMatch = -1;
      for (int indLoop = 0; indLoop < size; ++indLoop) {
        if (val == valList[indLoop]){
          indMatch = indLoop;
          break;
        }
      }
      if (indMatch != -1)
        return indMatch;
      else
        throw new NoValMatchFoundException();
  }

  /**
     * find the array index for input value;
     * will return the first match only (assumes input is sorted)
     * @param val double
     * @param valList int[]
     * @return int
     */

  public static int findIndex(double val, int[] valList)
      throws NoValMatchFoundException {
    // find the index that corresponds to a certain value
    // will return the first match only (assumes input is sorted)
    int size = valList.length;
    int indMatch = -1;
      for (int indLoop = 0; indLoop < size; ++indLoop) {
        if (val == valList[indLoop]){
          indMatch = indLoop;
        }
      }
      if (indMatch != -1)
        return indMatch;
      else
        throw new NoValMatchFoundException();
  }

  /**
   * calculate a list of evenly discretised values between a min and
   * max value
   * @param minVal double
   * @param maxVal double
   * @param deltaBin double - step size for increments
   * @return double[]
   */
  public static double[] getEvenlyDiscrVals(double minVal, double maxVal,
                                            double deltaBin){
    int vblSize = (int)((maxVal-minVal)/deltaBin)+1;
    double[] valBinList = new double[vblSize];
    int ct = 0;
    for (double vLoop = minVal; vLoop <= maxVal; vLoop += deltaBin) {
      valBinList[ct] = vLoop;
      ++ct;
    }
    return valBinList;
  }

  /**
   * finds all values in a list above, and including a given value
   * @param valList double[]
   * @param minVal double - the min value that should be returned
   * @return double[]
   */
  public static double[] getValsAbove(double[] valList, double minVal)
   throws NoValsFoundException {
    int size = valList.length;
    int ct = 0;
    //Whats the best way to define the size of the following?!?!
    double[] valsAbove =  new double[valList.length];
    for(int vLoop = 0; vLoop < size; ++vLoop){
      if(valList[vLoop] >= minVal){
        valsAbove[ct] = valList[vLoop];
        ++ct;
      }
    }
    if(ct > 0)
      return valsAbove;
    else
      throw new NoValsFoundException();
  }

  /**
   * getValsAbove
   */
  public void getValsAboveMag(ObsEqkRupList obs_eqkList, double minMag) {
    ListIterator eventIt = obs_eqkList.listIterator();
    ObsEqkRupture event;
    int numEvents = obs_eqkList.size();
    int ind = 0;
    double[] valList = new double[numEvents];
    while (eventIt.hasNext())  {
      event = (ObsEqkRupture)eventIt.next();
      valList[ind++] = event.getMag();
    }
    getValsAbove(valList, minMag);
  }


  /**
   * calculate the sum of a list
   * @param valList double[]
   * @return double
   */
  public static double getListSum(double[] valList){
    int size = valList.length;
    double sum = 0;
    for(int vLoop = 0; vLoop < size; ++vLoop)
      sum = sum + valList[vLoop];
    return sum;
  }

  /**
     * calculate the sum of a list
     * @param valList int[]
     * @return int
  */
  public static int getListSum(int[] valList){
      int size = valList.length;
      int sum = 0;
      for(int vLoop = 0; vLoop < size; ++vLoop)
        sum = sum + valList[vLoop];
      return sum;
    }


  /**
   * Calculates the cumulative sum of a list of numbers
   * @param valList double[]
   * @param flip boolean - True means to calculate starting
   * from the last number in the list
   * @return double[]
   */
  public static double[] calcCumSum(double[] valList, boolean flip){
    int vlLength = valList.length;
    double cumSumValList[] = new double[vlLength];
    if(flip){
      cumSumValList[vlLength-1] = valList[vlLength-1];
      for (int csLoop = vlLength-2; csLoop >= 0; csLoop--){
        cumSumValList[csLoop] = cumSumValList[csLoop+1] + valList[csLoop];
      }
    }
    else{
      cumSumValList[0] = valList[0];
        for (int csLoop = 1; csLoop < vlLength; csLoop++) {
            cumSumValList[csLoop] = cumSumValList[csLoop - 1] + valList[csLoop];
          }
    }
    return cumSumValList;
  }

  /**
     * Calculates the cumulative sum of a list of numbers
     * @param valList int[]
     * @param flip boolean - True means to calculate starting
     * from the last number in the list
     * @return int[]
     */

  public static double[] calcCumSum(int[] valList, boolean flip){
      int vlLength = valList.length;
      double cumSumValList[] = new double[vlLength];
      if(flip){
        cumSumValList[vlLength-1] = valList[vlLength-1];
        for (int csLoop = vlLength-2; csLoop >= 0; csLoop--){
          cumSumValList[csLoop] = cumSumValList[csLoop+1] + valList[csLoop];
        }
      }
      else{
        cumSumValList[0] = valList[0];
          for (int csLoop = 1; csLoop < vlLength; csLoop++) {
              cumSumValList[csLoop] = cumSumValList[csLoop - 1] + valList[csLoop];
            }
      }
      return cumSumValList;
    }


  public static void main(String[] args) {
      double[] magList = new double[10];
      boolean flip = true;
      double startMag = 12;
      for(int synMag = 0;synMag<10;++synMag){
        magList[synMag] = startMag;
        System.out.print(" "+magList[synMag]);
        --startMag;
      }

    }


}
