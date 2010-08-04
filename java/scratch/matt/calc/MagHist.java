package scratch.matt.calc;

/**
 * <p>Title: MagHist</p>
 * <p>Description: counts the number of events within each bin as defined
*  by minMag, maxMag and deltaBin </p>\
 * @author Matt Gerstenberger 2004
 * @version 1.0
 */



public class MagHist {

  static int[] bins;
  static int numBins;
  private static double[] binEdges;
  private static double minMag,maxMag;
  private static double deltaBin;

  private static int overFlows=0,underFlows=0;

  /**
   * default constructor
   */
  public MagHist (){
  }

  /**
   *  get the number of events in each bin
   * @return int[] bins
   */
  public static int[] getNumInBins(){
    return bins;
  }

  public static double[] getBinEdges(){
    return binEdges;
  }

  /**
   * Define the magnitudes of interest and make the call to sort into mag bins
   * @param magList double[]
   */
  public static void setMags(double[] magList, double minMag, double maxMag,
                             double deltaBin){
    numBins = (int)java.lang.Math.round((maxMag-minMag)/deltaBin);
    bins = new int[numBins];
    binEdges = new double[numBins];
    for(int bLoop=0;bLoop<=numBins-1;++bLoop){
      binEdges[bLoop]=minMag+bLoop*deltaBin;
    }
    calcHist(magList);
  }

  /**
   * sort into magnitude bins
   * @param magList double[]
   */
  private static void calcHist(double[] magList){

    int size = magList.length;
                   //System.out.println(maxMag);
   for(int magLoop = 0;magLoop < size; ++magLoop){
     if( magList[magLoop] < minMag)
       underFlows++;
     else if ( magList[magLoop] >= maxMag)
       overFlows++;
     else{
       int bin = (int)((magList[magLoop]-minMag)/deltaBin);

       if(bin >=0 && bin < numBins) bins[bin]++;
     }
   }
  }

  /**
   * main method for testing
   * @param args String[]
   */
  public static void main(String[] args) {
    deltaBin = 0.1;
    minMag = 3.0;
    maxMag = 8.0;
    double[] magList = new double[10];
    double startMag = 3;
    for(int synMag = 0;synMag<10;++synMag){
      magList[synMag] = startMag;
      ++startMag;
    }
    MagHist.setMags(magList,minMag,maxMag,deltaBin);
    int[] numInBins = MagHist.getNumInBins();
    int length = numInBins.length;
    for(int lLoop = 1; lLoop<length; ++lLoop){
        System.out.println("Number in bins is: " + numInBins[lLoop-1] +
                           " Lower Bin Edge is: " + binEdges[lLoop-1]);
    }
  }

}

