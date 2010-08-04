package junk;


import org.opensha.commons.data.Site;
import org.opensha.commons.data.region.SitesInGriddedRegion;
import org.opensha.commons.util.FileUtils;
import org.opensha.commons.util.RunScript;
import org.opensha.sha.earthquake.EqkRupForecast;




/**
 *
 * <p>Title: ThreadHazardMapCalculator.java </p>
 * <p>Description: This class will accept 5
 *   THIS WILL BE USED TO RUN IN CONDOR POOL
       args array will have following order:
       // index 1 - GriddedRegion file name (region.dat)
      // index 2 - ERF File Name (stepForecast.dat)
      // index 0 - IMR File Name (shakemap_imr.dat)
      // index 3 - X-Values file name
       // index 4 - Max Source distance.</p>
 * @author Ned Field, Nitin Gupta, Vipin Gupta
 * @date Mar 16, 2004
 * @version 1.0
 */

public class ThreadHazardMapCalculator {
  private static boolean D = false;
  // make a array for saving the X values
 /* private static   double [] xValues = { .001, .01, .05, .1, .15, .2, .25, .3, .4, .5,
                             .6, .7, .8, .9, 1, 1.1, 1.2, 1.3, 1.4, 1.5 };*/
  //private static int MAX_DISTANCE = 200;
  //private DecimalFormat decimalFormat=new DecimalFormat("0.00##");
  //private boolean xLogFlag = true;

  //private static int numPoints = xValues.length;
  // now run the hazard map calculations
  //HazardCurveCalculator hazCurveCalc=new HazardCurveCalculator();

  public static void main(String[] args)
  {

    /** THIS WILL BE USED TO RUN IN CONDOR POOL
       args array will have following order:
       // index 1 - GriddedRegion file name (region.dat)
       // index 2 - ERF File Name (stepForecast.dat)
       // index 0 - IMR File Name (shakemap_imr.dat)
       // index 3 - X-Values file name
       // index 4 - Max Source distance.
       // index 5 - number of processors requested
       */
    try {
      // make a array for saving the X values
      ThreadHazardMapCalculator calc = new ThreadHazardMapCalculator();
      calc.getHazardMapCurves(args);
      } catch (Exception ex) {ex.printStackTrace(); }
  }


  /**
   * This method generates the threads that run HazardCurveCalculator for
   * each site on the multiprocessor machine at a time and each thread will
   * create the Hazard Curve for that site.
   * @param args :Command Line arguments for the ERF, IMR and Region
   */
  public void getHazardMapCurves(String[] args) {
    try{

    	SitesInGriddedRegion sites = (SitesInGriddedRegion)FileUtils.loadObject(args[1]);
      int numOfProcs = Integer.parseInt(args[5]);
      int numSites = sites.getRegion().getNodeCount();
      //dividing the number of sites on each processor based on the number of processor
      //requested from the server.
      int sitesPerProcessor = (int)(numSites/numOfProcs+1);
      for(int j=0;j<numSites;j+=sitesPerProcessor){
        int endIndex = j+sitesPerProcessor;
        if(endIndex >=numSites)
          endIndex = numSites;
        Thread t = new Thread(new HazardCurvesGenerator(args,j,endIndex));
        t.start();
      }
    }catch(Exception e){
      e.printStackTrace();
    }
  }




 /**
  * set x values in log space for Hazard Function to be passed to IMR
  * if the selected IMT are SA , PGA or PGV
  * It accepts 1 parameters
  *
  * @param originalFunc :  this is the function with X values set
  */
 //private void initX_Values(DiscretizedFuncAPI arb, double[] xValues) {
   // take log only if it is PGA, PGV or SA
   ///if (this.xLogFlag) {
    // for (int i = 0; i < xValues.length; ++i)
      // arb.set(Math.log(xValues[i]), 1);
   //}
   //else
    // throw new RuntimeException("Unsupported IMT");
 //}

 /**
  * set x values back from the log space to the original linear values
  * for Hazard Function after completion of the Hazard Calculations
  * if the selected IMT are SA , PGA or PGV
  * It accepts 1 parameters
  *
  * @param hazFunction :  this is the function with X values set
  */
 //private ArbitrarilyDiscretizedFunc toggleHazFuncLogValues(
  //   ArbitrarilyDiscretizedFunc hazFunc, double[] xValues) {
   //int numPoints = hazFunc.getNum();
   //DiscretizedFuncAPI tempFunc = hazFunc.deepClone();
   //hazFunc = new ArbitrarilyDiscretizedFunc();
   // take log only if it is PGA, PGV or SA
   //if (this.xLogFlag) {
    // for (int i = 0; i < numPoints; ++i)
      // hazFunc.set(xValues[i], tempFunc.getY(i));
     //return hazFunc;
  // }
   //else
    // throw new RuntimeException("Unsupported IMT");
// }

 private class HazardCurvesGenerator implements Runnable{

   private EqkRupForecast erfObj;
   /*private AttenuationRelationshipAPI imrObj;
   private SitesInGriddedRectangularRegion regionObj;*/
   private Site site;
   private int startIndex;
   private int endIndex;
   private String[] args;
   HazardCurvesGenerator(String[] args,int startIndex, int endIndex){
     // load the objects from the file
     /*regionObj = (SitesInGriddedRectangularRegion)FileUtils.loadObject(args[1]);
     erfObj = (EqkRupForecast)FileUtils.loadObject(args[2]);
     imrObj = (AttenuationRelationshipAPI)FileUtils.loadObject(args[0]);*/
     this.args = args;
     this.startIndex = startIndex;
     this.endIndex = endIndex;
   }

   /*public void run(){
     Site site = null;
     Calendar calendar = Calendar.getInstance();
     String datetime = new String(calendar.get(Calendar.YEAR) + "-" +
                                 (calendar.get(Calendar.MONTH) + 1) + "-" +
                                 calendar.get(Calendar.DAY_OF_MONTH) + "  " +
                                 calendar.get(Calendar.HOUR_OF_DAY) + ":" +
                                 calendar.get(Calendar.MINUTE) + ":" +
                                 calendar.get(Calendar.SECOND));
     try{
       FileWriter fw = new FileWriter("ThreadTime.txt", true);
       fw.write("Thread for : "+startIndex+"-"+endIndex+" started at: "+datetime+"\n");
       for(int j=startIndex;j<endIndex;++j){
         site = regionObj.getSite(j);
         // make and initialize the haz function
         ArbitrarilyDiscretizedFunc hazFunction = new ArbitrarilyDiscretizedFunc();
         initX_Values(hazFunction,xValues);
         hazCurveCalc.getHazardCurve(hazFunction,site,imrObj,erfObj);
         String lat = decimalFormat.format(site.getLocation().getLatitude());
         String lon = decimalFormat.format(site.getLocation().getLongitude());
         hazFunction = toggleHazFuncLogValues(hazFunction, xValues);

         // write the result to the file
         FileWriter fr = new FileWriter(lat + "_" + lon + ".txt");
         for (int i = 0; i < numPoints; ++i)
           fr.write(hazFunction.getX(i) + " " + hazFunction.getY(i) + "\n");
         fr.close();
       }
       calendar = Calendar.getInstance();
       datetime = new String(calendar.get(Calendar.YEAR) + "-" +
                             (calendar.get(Calendar.MONTH) + 1) + "-" +
                             calendar.get(Calendar.DAY_OF_MONTH) + "  " +
                             calendar.get(Calendar.HOUR_OF_DAY) + ":" +
                             calendar.get(Calendar.MINUTE) + ":" +
                             calendar.get(Calendar.SECOND));
       fw.write("Thread for : "+startIndex+"-"+endIndex+" finished at: "+datetime+"\n");
       fw.close();
     }catch(Exception e){
       e.printStackTrace();
     }
   }*/

   public void run(){
     Site site =null;
     String[] command ={"sh","-c",""};
     //Calendar calendar = Calendar.getInstance();
     //String datetime = new String(calendar.get(Calendar.YEAR) + "-" +
      //                            (calendar.get(Calendar.MONTH) + 1) + "-" +
       //                           calendar.get(Calendar.DAY_OF_MONTH) + "  " +
        //                          calendar.get(Calendar.HOUR_OF_DAY) + ":" +
         //                         calendar.get(Calendar.MINUTE) + ":" +
          //                        calendar.get(Calendar.SECOND));
     try{
       //FileWriter fw = new FileWriter("ThreadTime.txt", true);
       //fw.write("Thread for : "+startIndex+"-"+endIndex+" started at: "+datetime+"\n");
       //fw.close();
       /**
        * calling a standalone java program that takes the following arguments in the order:
        * startSite index, endSite index ,regionfilename, erfFileName,imrFileName,
        * X-ValuesFileName and Max source distance.
         **/
       command[2] = "java -classpath opensha_hazardmapthread.jar:$CLASSPATH -Xmx500M "+
                    "org.opensha.sha.calc.GridHazardMapCalculator "+ startIndex +" "
                    + endIndex+" "+args[1]+" "+args[2]+
                    " "+args[0]+" "+args[3]+" "+args[4];
       RunScript.runScript(command);
       //calendar = Calendar.getInstance();
       //datetime = new String(calendar.get(Calendar.YEAR) + "-" +
         //                         (calendar.get(Calendar.MONTH) + 1) + "-" +
          //                        calendar.get(Calendar.DAY_OF_MONTH) + "  " +
           //                       calendar.get(Calendar.HOUR_OF_DAY) + ":" +
            //                      calendar.get(Calendar.MINUTE) + ":" +
             //                     calendar.get(Calendar.SECOND));
       //fw = new FileWriter("ThreadTime.txt", true);
       //fw.write("Thread for : "+startIndex+"-"+endIndex+" finished at: "+datetime+"\n");
       //fw.close();
      }catch(Exception e){
        e.printStackTrace();
      }


   }

 }

}
