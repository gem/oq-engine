package scratch.matt.calc;

import java.util.ListIterator;

import org.opensha.sha.earthquake.observedEarthquake.ObsEqkRupList;
import org.opensha.sha.earthquake.observedEarthquake.ObsEqkRupture;
import org.opensha.sha.magdist.GutenbergRichterMagFreqDist;



/**
 * <p>Title: CompletenessMagCalc</p>
 * <p>Description: </p>
 * <p>Copyright: Copyright (c) 2002</p>
 * <p>Company: </p>
 * @author not attributable
 * @version 1.0
 */

public class CompletenessMagCalc {
  public static double mcBest;
  public static double mcSynth;
  public static double mcMaxCurv;
  public static int numInBin;
  private static double deltaBin = 0.1;
  private static double GR_MMax = 10.0; // max mag to use in GR calc

  public CompletenessMagCalc() {

  }

  /**
   * set_McBest
   * Calculate the best Mc estimate based on the synthetic and max curvature
   * methods
   */
  public static void setMcBest(ObsEqkRupList eventList) {
    ListIterator eventIt = eventList.listIterator();
    ObsEqkRupture event;
    int numEvents = eventList.size();
    int ind = 0;
    double[] magList = new double[numEvents];
    while (eventIt.hasNext())  {
      event = (ObsEqkRupture)eventIt.next();
      magList[ind++] = event.getMag();
    }
    calcMcSynth(magList);
  }

  /**
   * setMcMaxCurv
   */
  public void setMcMaxCurv(ObsEqkRupList eventList) {
    ListIterator eventIt = eventList.listIterator();
    ObsEqkRupture event;
    int numEvents = eventList.size();
    int ind = 0;
    double[] magList = new double[numEvents];
    while (eventIt.hasNext())  {
      event = (ObsEqkRupture)eventIt.next();
      magList[ind++] = event.getMag();
    }
    calcMcMaxCurv(magList);
  }

  /**
   *
   * @return mcBest double
   */
  public static double getMcBest(){
    if (mcSynth != -99)
        mcBest = mcSynth;
      else
        mcBest = mcMaxCurv;
    return mcBest;
    }

    /**
     * Calculate Mc based on the max curvature method
     * @return mcMaxCurv double
     */
    public static double getMcMaxCurv(){
      return mcMaxCurv;
    }

    /**
     * Calculate Mc based on synthetic GR distributions.  Return the value
     * estimated at 95% probability, if not return the 90%.  If this is not
     * possible to estimate, return a -99
     * @return double
     */
    public static double getMcSynth(){

      //HOW TO BETTER HANDLE THE -99?!?!?!?!?!
      return mcSynth;
    }

    private static void calcMcMaxCurv(double[] magList){

      double minMag = ListSortingTools.getMinVal(magList);
      double maxMag = ListSortingTools.getMaxVal(magList);
      if(minMag>0){
        minMag=0;
      }

      //number of mag bins
      int numMags = (int)(maxMag*10)+1;

      //create the histogram of the mag bins
      MagHist.setMags(magList,minMag,maxMag,deltaBin);
      int[] numInBin = MagHist.getNumInBins();
      // find the value of max curvature and the bin it corresponds to
      double maxCurv = ListSortingTools.getMaxVal(numInBin);
      double[] magRange = ListSortingTools.getEvenlyDiscrVals(minMag,maxMag,deltaBin);
      int maxCurvInd = ListSortingTools.findIndex((int)maxCurv,numInBin);
      //set mc to the M value at the maximum curvature
      mcMaxCurv = magRange[maxCurvInd];
    }

    private static void calcMcSynth(double[] magList){
      // make a first guess at Mc using max curvature
      mcMaxCurv = getMcMaxCurv();
      int numEvents = magList.length;
      int aSize = (int)((((mcMaxCurv+1.5)-(mcMaxCurv-0.9))/deltaBin)+1.0);
      double[] fitProb = new double[aSize];
      int ct = 0;

      // loop over a range of completeness guesses
      for(double mcLoop = mcMaxCurv-0.9; mcLoop < mcMaxCurv + 1.5;
          mcLoop += deltaBin){
        double[] magBins = new double[numEvents];

      // get all events above the completeness guess (mcLoop)
        double[] cutCat = ListSortingTools.getValsAbove(magList,mcLoop);
        int sizeCutCat = cutCat.length;

        // if > 25 events calculate the b value and estimate Mc
        if(sizeCutCat >= 25){
          MaxLikeGR_Calc.setMags(cutCat);
          double bvalMaxLike = MaxLikeGR_Calc.get_bValueMaxLike();
          int numBins = (int)Math.round((GR_MMax-mcLoop)/deltaBin)+1;

          // create the GR distribution of synthetic events
          GutenbergRichterMagFreqDist GR_FMD =
              new GutenbergRichterMagFreqDist(mcLoop,GR_MMax,numBins);
          GR_FMD.setAllButTotMoRate(mcLoop,GR_MMax,sizeCutCat,bvalMaxLike);
          // loop over all bins and get the # of synthetic  events in each bin
          int mIndex = 0;
          double[] mbinRates = new double[numBins];
          for(double mbinLoop = mcLoop; mbinLoop <= GR_MMax; mbinLoop += deltaBin){
            mbinRates[mIndex] = GR_FMD.getIncrRate(mIndex++);
          }

          //create the histogram of the observed events (in mag bins)
          boolean flip = true;
          MagHist.setMags(magList,mcLoop,GR_MMax,deltaBin);
          int[] numObsInBin = MagHist.getNumInBins();
          double[] obsCumSum = ListSortingTools.calcCumSum(numObsInBin,flip);
          double sumObs = ListSortingTools.getListSum(obsCumSum);
          double numer = 0;

          // calculate the fit of the synthetic to the real
          for(int sLoop = 0; sLoop < obsCumSum.length; ++ sLoop){
            numer = numer + Math.abs(obsCumSum[sLoop]-mbinRates[sLoop]);
          }
          fitProb[ct] = (numer/sumObs)*100.0;
        }
       ++ct;  // increment the mcLoop counter
      }
      try{
        double[] mc95List = ListSortingTools.getValsAbove(fitProb,95.0);
        double mcSynth = ListSortingTools.getMinVal(mc95List);
      }
      catch (NoValsFoundException err1){
        try {
          double[] mc90List = ListSortingTools.getValsAbove(fitProb, 90.0);
          double mcSynth = ListSortingTools.getMinVal(mc90List);
        }
        catch (NoValsFoundException err2){
          double mcSynth = Double.NaN;
        }

      }


      // double[] mc95List = ListSortingTools.getValsAbove(fitProb,95.0);
      //double mc95 = ListSortingTools.getMinVal(mc95List);

    }


}
