package junk;


import java.io.FileWriter;
import java.lang.reflect.Constructor;
import java.text.DecimalFormat;
import java.util.ArrayList;
import java.util.ListIterator;

import org.opensha.commons.data.Site;
import org.opensha.commons.data.function.ArbitrarilyDiscretizedFunc;
import org.opensha.commons.data.function.DiscretizedFuncAPI;
import org.opensha.commons.data.region.SitesInGriddedRegion;
import org.opensha.commons.param.ParameterAPI;
import org.opensha.commons.param.event.ParameterChangeWarningEvent;
import org.opensha.commons.param.event.ParameterChangeWarningListener;
import org.opensha.commons.util.FileUtils;
import org.opensha.sha.calc.HazardCurveCalculator;
import org.opensha.sha.earthquake.EqkRupForecast;
import org.opensha.sha.imr.ScalarIntensityMeasureRelationshipAPI;



/**
 *
 * <p>Title: CondorHazardMapCalculator.java </p>
 * <p>Description: This class will accept 5
 *   THIS WILL BE USED TO RUN IN CONDOR POOL
       args array will have following order:
       // index 0 - start index for sites
       // index 1 - end index for sites
       // index 2 - GriddedRegion file name (region.dat)
      // index 3 - ERF File Name (stepForecast.dat)
      // index 4 - IMR File Name (shakemap_imr.dat)
      // index 5 - X values File Name (xValues.dat)
      // index 6 - Max Source Distance value
 </p>
 * <p>Copyright: Copyright (c) 2002</p>
 * <p>Company: </p>
 * @author Ned Field, Nitin Gupta, Vipin Gupta
 * @date Mar 16, 2004
 * @version 1.0
 */

public class GridHazardMapCalculator implements ParameterChangeWarningListener
{
  private static boolean D = false;
  // make a array for saving the X values
  private double[] xValues ;
  private static double MAX_DISTANCE = 200;
  private DecimalFormat decimalFormat=new DecimalFormat("0.00##");
  private boolean xLogFlag = true;



  public static void main(String[] args)
  {

  /** THIS WILL BE USED TO RUN IN CONDOR POOL
       args array will have following order:
       // index 0 - start index for sites
       // index 1 - end index for sites
       // index 2 - GriddedRegion file name (region.dat)
      // index 3 - ERF File Name (stepForecast.dat)
      // index 4 - IMR File Name (shakemap_imr.dat)
  */
  try {
    // make a array for saving the X values
    GridHazardMapCalculator calc = new GridHazardMapCalculator();
    calc.getHazardMapCurves(args, Integer.parseInt(args[0]), Integer.parseInt(args[1]));
  } catch (Exception ex) {ex.printStackTrace(); }


}


public void parameterChangeWarning(ParameterChangeWarningEvent e) {

   e.getWarningParameter().setValueIgnoreWarning(e.getNewValue());
 }


/**
 * this function generates a set of curves for a region
 *
 * @param urls  addresses to IMR/ Forecast/griddedregion metadata files
 * @param mapParametersInfo Parameters need to regenerate the map
 */
public void getHazardMapCurves(String[] args, int startSiteIndex,
                                int endSiteIndex) {
   try{
     // load the objects from the file
	   SitesInGriddedRegion sites = (SitesInGriddedRegion)FileUtils.loadObject(args[2]);
     EqkRupForecast eqkRupForecast = (EqkRupForecast)FileUtils.loadObject(args[3]);
     ScalarIntensityMeasureRelationshipAPI imr = (ScalarIntensityMeasureRelationshipAPI)FileUtils.loadObject(args[4]);

     /**
      * LOAD THE IMR FROM THE FILE
      */
     ScalarIntensityMeasureRelationshipAPI imr_temp =
         (ScalarIntensityMeasureRelationshipAPI)createIMRClassInstance(imr.getClass().getName(), this);

     // set other params
     ListIterator lt = imr.getOtherParamsIterator();
     while(lt.hasNext()){
       ParameterAPI tempParam=(ParameterAPI)lt.next();
       imr_temp.getParameter(tempParam.getName()).setValue(tempParam.getValue());
     }
   // set IM
   //imr_temp.setIntensityMeasure(imr.getIntensityMeasure().getName());
   //imr_temp.setIntensityMeasureLevel(imr.getIntensityMeasureLevel());
     imr_temp.setIntensityMeasure(imr.getIntensityMeasure());
     imr  = imr_temp;


     ArrayList xValuesList = FileUtils.loadFile(args[5]);
     MAX_DISTANCE = Double.parseDouble(args[6]);

     xValues = new double[xValuesList.size()];
     for(int i=0; i<xValuesList.size(); ++i)
       xValues[i] = Double.parseDouble((String)xValuesList.get(i));

     // now run the hazard map calculations
     HazardCurveCalculator hazCurveCalc=new HazardCurveCalculator();
     hazCurveCalc.setMaxSourceDistance(this.MAX_DISTANCE);
     int numSites = sites.getRegion().getNodeCount();
     int numPoints = xValues.length;
     Site site;
     for(int j=startSiteIndex;j<numSites && j<endSiteIndex;++j){
       site = sites.getSite(j);
       // make and initialize the haz function
       ArbitrarilyDiscretizedFunc hazFunction = new ArbitrarilyDiscretizedFunc();
       initX_Values(hazFunction,xValues);
       hazCurveCalc.getHazardCurve(hazFunction,site,imr,eqkRupForecast);
       String lat = decimalFormat.format(site.getLocation().getLatitude());
       String lon = decimalFormat.format(site.getLocation().getLongitude());
       hazFunction = toggleHazFuncLogValues(hazFunction, xValues);

       // write the result to the file
       FileWriter fr = new FileWriter(lat + "_" + lon + ".txt");
       for (int i = 0; i < numPoints; ++i)
         fr.write(hazFunction.getX(i) + " " + hazFunction.getY(i) + "\n");
       fr.close();
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
 private void initX_Values(DiscretizedFuncAPI arb, double[] xValues) {
   // take log only if it is PGA, PGV or SA
   if (this.xLogFlag) {
     for (int i = 0; i < xValues.length; ++i)
       arb.set(Math.log(xValues[i]), 1);
   }
   else
     throw new RuntimeException("Unsupported IMT");
 }

 /**
  * set x values back from the log space to the original linear values
  * for Hazard Function after completion of the Hazard Calculations
  * if the selected IMT are SA , PGA or PGV
  * It accepts 1 parameters
  *
  * @param hazFunction :  this is the function with X values set
  */
 private ArbitrarilyDiscretizedFunc toggleHazFuncLogValues(
     ArbitrarilyDiscretizedFunc hazFunc, double[] xValues) {
   int numPoints = hazFunc.getNum();
   DiscretizedFuncAPI tempFunc = hazFunc.deepClone();
   hazFunc = new ArbitrarilyDiscretizedFunc();
   // take log only if it is PGA, PGV or SA
   if (this.xLogFlag) {
     for (int i = 0; i < numPoints; ++i)
       hazFunc.set(xValues[i], tempFunc.getY(i));
     return hazFunc;
   }
   else
     throw new RuntimeException("Unsupported IMT");
 }

 /**
   * Creates a class instance from a string of the full class name including packages.
   * This is how you dynamically make objects at runtime if you don't know which\
   * class beforehand. For example, if you wanted to create a BJF_1997_AttenRel you can do
   * it the normal way:<P>
   *
   * <code>BJF_1997_AttenRel imr = new BJF_1997_AttenRel()</code><p>
   *
   * If your not sure the user wants this one or AS_1997_AttenRel you can use this function
   * instead to create the same class by:<P>
   *
   * <code>BJF_1997_AttenRel imr =
   * (BJF_1997_AttenRel)ClassUtils.createNoArgConstructorClassInstance("org.opensha.sha.imt.attenRelImpl.BJF_1997_AttenRel");
   * </code><p>
   *
   */
 public Object createIMRClassInstance( String className, org.opensha.commons.param.event.ParameterChangeWarningListener listener){
   try {

     Class listenerClass = Class.forName( "org.opensha.commons.param.event.ParameterChangeWarningListener" );
     Object[] paramObjects = new Object[]{ listener };
     Class[] params = new Class[]{ listenerClass };
     Class imrClass = Class.forName( className );
     Constructor con = imrClass.getConstructor( params );
     Object obj = con.newInstance( paramObjects );
     return obj;
   } catch ( Exception e ) {
     e.printStackTrace();
   }
   return null;
 }



}
