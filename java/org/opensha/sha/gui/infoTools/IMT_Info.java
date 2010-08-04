                                                                                                               package org.opensha.sha.gui.infoTools;

import java.text.DecimalFormat;

import org.opensha.commons.data.function.ArbitrarilyDiscretizedFunc;
import org.opensha.commons.param.ParameterAPI;
import org.opensha.sha.imr.attenRelImpl.ShakeMap_2003_AttenRel;
import org.opensha.sha.imr.attenRelImpl.WC94_DisplMagRel;
import org.opensha.sha.imr.param.IntensityMeasureParams.IA_Param;
import org.opensha.sha.imr.param.IntensityMeasureParams.MMI_Param;
import org.opensha.sha.imr.param.IntensityMeasureParams.PGA_Param;
import org.opensha.sha.imr.param.IntensityMeasureParams.PGV_Param;
import org.opensha.sha.imr.param.IntensityMeasureParams.SA_InterpolatedParam;
import org.opensha.sha.imr.param.IntensityMeasureParams.SA_Param;
/**
 * <p>Title: IMT_Info</p>
 * <p>Description: This class provides the default X values for the selected
 * IMT. The discretization is done in the </p>
 * @author : Edward (Ned) Field and Nitin  Gupta
 * @created : Nov 24,2003
 * @version 1.0
 */

public final class IMT_Info {

  private String S = "IMT_Info()";

  //Default values for the SA and PGA
  public final static double MIN_SA = .0001;
  public final static double MAX_SA = 10;
  public final static double NUM_SA = 51;
  public final static double DEFAULT_SA = 0.1;

  //Default values for the PGA
  public final static double MIN_PGA = .0001;
  public final static double MAX_PGA = 10;
  public final static double NUM_PGA = 51;
  public final static double DEFAULT_PGA = 0.1;


  //Default values for the PGV
  public final static double MIN_PGV = .01;
  public final static double MAX_PGV = 1000;
  public final static double NUM_PGV = 51;
  public final static double DEFAULT_PGV = 50;

  // default values for WC94_DisplMagRel FAULT_DISPL_NAME
  public final static double MIN_FAULT_DISPL = .001;
  public final static double MAX_FAULT_DISPL = 100;
  public final static double NUM_FAULT_DISPL = 51;
  public final static double DEFAULT_FAULT_DISPL = 1.0;


  //default values for the ShakeMapAttenRel MMI
  public final static double MIN_MMI = 1;
  public final static double MAX_MMI = 10;
  public final static double NUM_MMI = 51;
  public final static double DEFAULT_MMI = 7.0;

//Default values for the IA
  public final static double MIN_IA = .0001;
  public final static double MAX_IA = 1000;
  public final static double NUM_IA = 51;
  public final static double DEFAULT_IA = 0.1;

  
  public double discretization_pga;
  public double discretization_sa;
  public double discretization_pgv;
  public double discretization_fault_displ;
  public double discretization_mmi;
  public double discretization_ia;
  
  private DecimalFormat format = new DecimalFormat("0.00000##");

  public IMT_Info() {
    discretization_pga = (Math.log(MAX_PGA) - Math.log(MIN_PGA))/(NUM_PGA-1);
    discretization_sa = (Math.log(MAX_SA) - Math.log(MIN_SA))/(NUM_SA-1);
    discretization_pgv = (Math.log(MAX_PGV) - Math.log(MIN_PGV))/(NUM_PGV-1);
    discretization_fault_displ = (Math.log(MAX_FAULT_DISPL) - Math.log(MIN_FAULT_DISPL))/(NUM_FAULT_DISPL-1);
    discretization_mmi = (Math.log(MAX_MMI) - Math.log(MIN_MMI))/(NUM_MMI-1);
    discretization_ia = (Math.log(MAX_IA) - Math.log(MIN_IA))/(NUM_IA-1);
    format.setMaximumFractionDigits(5);
  }

  /**
   * This function returns the ArbitrarilyDiscretizedFunc X values for the Hazard
   * Curve in the linear space after discretizing them in the log space.
   * @param param : Selected IMT Param
   * @return
   */
  public  ArbitrarilyDiscretizedFunc getDefaultHazardCurve(ParameterAPI imtParam){
    String paramVal =(String)imtParam.getValue();
   return getDefaultHazardCurve(paramVal);
  }

  /**
   * This function returns the ArbitrarilyDiscretizedFunc X values for the Hazard
   * Curve in the linear space after discretizing them in the log space.
   * @param imtName : Name of the selected IMT
   * @return
   */
  public ArbitrarilyDiscretizedFunc getDefaultHazardCurve(String imtName){
    ArbitrarilyDiscretizedFunc function = new ArbitrarilyDiscretizedFunc();
    if(imtName.equals(SA_Param.NAME) || imtName.equals(SA_InterpolatedParam.NAME)){
      for(int i=0; i < NUM_SA ;++i){
        double xVal =Double.parseDouble(format.format(Math.exp(Math.log(MIN_SA)+i*discretization_sa)));
        function.set(xVal,1.0);
      }
      return function;
    }
    else if(imtName.equals(PGA_Param.NAME)){
      for(int i=0; i < NUM_PGA ;++i){
        double xVal =Double.parseDouble(format.format(Math.exp(Math.log(MIN_PGA)+i*discretization_pga)));
        function.set(xVal,1.0);
      }
      return function;
    }
    else if((imtName.equals(PGV_Param.NAME))){
      for(int i=0; i < NUM_PGV ;++i){
        double xVal = Double.parseDouble(format.format(Math.exp(Math.log(MIN_PGV)+i*discretization_pgv)));
        function.set(xVal,1.0);
      }
      return function;
    }
    else if((imtName.equals(WC94_DisplMagRel.FAULT_DISPL_NAME))){
      for(int i=0; i < NUM_FAULT_DISPL ;++i){
        double xVal = Double.parseDouble(format.format(Math.exp(Math.log(MIN_FAULT_DISPL)+i*discretization_fault_displ)));
        function.set(xVal,1.0);
      }
      return function;
    }
    else if((imtName.equals(MMI_Param.NAME))){
      for(int i=0; i < NUM_MMI ;++i){
        double xVal = Double.parseDouble(format.format(Math.exp(Math.log(MIN_MMI)+i*discretization_mmi)));
        function.set(xVal,1.0);
      }
      return function;
    }
      else if(imtName.equals(IA_Param.NAME)){
          for(int i=0; i < NUM_IA ;++i){
            double xVal =Double.parseDouble(format.format(Math.exp(Math.log(MIN_IA)+i*discretization_ia)));
            function.set(xVal,1.0);
          }
          return function;
    }
    return null;
  }





  /**
   *  Returns the minimum default value for the selectd IMT
   * @param imt: Selected IMT
   * @return
   */
  public static double getMinIMT_Val(String imt){
    if(imt.equals(SA_Param.NAME))
      return MIN_SA;
    else if(imt.equals(PGA_Param.NAME))
      return MIN_PGA;
    else if(imt.equals(PGV_Param.NAME))
      return MIN_PGV;
    else if(imt.equals(WC94_DisplMagRel.FAULT_DISPL_NAME))
      return MIN_FAULT_DISPL;
    else if(imt.equals(MMI_Param.NAME))
      return MIN_MMI;
    else if(imt.equals(IA_Param.NAME))
        return MIN_IA;
    return 0;
  }

  /**
   *  Returns the maximum default value for the selectd IMT
   * @param imt: Selected IMT
   * @return
   */
  public static double getMaxIMT_Val(String imt){
    if(imt.equals(SA_Param.NAME))
      return MAX_SA;
    else if(imt.equals(PGA_Param.NAME))
      return MAX_PGA;
    else if(imt.equals(PGV_Param.NAME))
      return MAX_PGV;
    else if(imt.equals(WC94_DisplMagRel.FAULT_DISPL_NAME))
      return MAX_FAULT_DISPL;
    else if(imt.equals(MMI_Param.NAME))
      return MAX_MMI;
    if(imt.equals(IA_Param.NAME))
        return MAX_IA;
    return 0;
  }

  /**
   * Returns the total number of values for the selectd IMT
   * @param imt: Selected IMT
   * @return
   */
  public static double getNumIMT_Val(String imt){
    if(imt.equals(SA_Param.NAME))
      return NUM_SA;
    else if(imt.equals(PGA_Param.NAME))
      return NUM_PGA;
    else if(imt.equals(PGV_Param.NAME))
      return NUM_PGV;
    else if(imt.equals(WC94_DisplMagRel.FAULT_DISPL_NAME))
      return NUM_FAULT_DISPL;
    else if(imt.equals(MMI_Param.NAME))
      return NUM_MMI;
    if(imt.equals(IA_Param.NAME))
        return NUM_IA;
    return 0;
  }

  /**
   * Returns the default values for the selectd IMT
   * @param imt: Selected IMT
   * @return
   */
  public static double getDefaultIMT_VAL(String imt){
    if(imt.equals(SA_Param.NAME))
      return DEFAULT_SA;
    else if(imt.equals(PGA_Param.NAME))
      return DEFAULT_PGA;
    else if(imt.equals(PGV_Param.NAME))
      return DEFAULT_PGV;
    else if(imt.equals(WC94_DisplMagRel.FAULT_DISPL_NAME))
      return DEFAULT_FAULT_DISPL;
    else if(imt.equals(MMI_Param.NAME))
      return DEFAULT_MMI;
    if(imt.equals(IA_Param.NAME))
        return DEFAULT_IA;
    return 0;
  }


  /**
   *
   * @param imt : Name of the seleceted IMT
   * @return true if the selected IMT is PGA, PGV or SA
   * else returns false
   */
  public static boolean isIMT_LogNormalDist(String imt){
    if(imt.equalsIgnoreCase(PGA_Param.NAME) ||
       imt.equalsIgnoreCase(PGV_Param.NAME) ||
       imt.equalsIgnoreCase(SA_Param.NAME)  ||
       imt.equalsIgnoreCase(SA_InterpolatedParam.NAME)  ||
       imt.equalsIgnoreCase(MMI_Param.NAME)  ||
       imt.equalsIgnoreCase(WC94_DisplMagRel.FAULT_DISPL_NAME)  ||
       imt.equalsIgnoreCase(IA_Param.NAME))
      return true;
    return false;
  }

 
  /**
   * initialises the function with the x and y values if the user has chosen the USGS-PGA X Vals
   * the y values are modified with the values entered by the user
   */
  public static ArbitrarilyDiscretizedFunc getUSGS_PGA_Function(){
	ArbitrarilyDiscretizedFunc function= new ArbitrarilyDiscretizedFunc();
    function.set(.005,1);
    function.set(.007,1);
    function.set(.0098,1);
    function.set(.0137,1);
    function.set(.0192,1);
    function.set(.0269,1);
    function.set(.0376,1);
    function.set(.0527,1);
    function.set(.0738,1);
    function.set(.103,1);
    function.set(.145,1);
    function.set(.203,1);
    function.set(.284,1);
    function.set(.397,1);
    function.set(.556,1);
    function.set(.778,1);
    function.set(1.09,1);
    function.set(1.52,1);
    function.set(2.13,1);
    return function;
  }

  
  /**
   * initialises the function with the x and y values if the user has chosen the USGS-PGA X Vals
   * the y values are modified with the values entered by the user
   */
  public static ArbitrarilyDiscretizedFunc getUSGS_SA_01_AND_02_Function(){
	ArbitrarilyDiscretizedFunc function= new ArbitrarilyDiscretizedFunc();
    function.set(.005,1);
    function.set(.0075,1);
    function.set(.0113 ,1);
    function.set(.0169,1);
    function.set(.0253,1);
    function.set(.0380,1);
    function.set(.0570,1);
    function.set(.0854,1);
    function.set(.128,1);
    function.set(.192,1);
    function.set(.288,1);
    function.set(.432,1);
    function.set(.649,1);
    function.set(.973,1);
    function.set(1.46,1);
    function.set(2.19,1);
    function.set(3.28,1);
    function.set(4.92,1);
    function.set(7.38,1);
    return function;
    
  }
  
  /**
   * initialises the function with the x and y values if the user has chosen the USGS SA 0.3,0.4,0.5 and 1.0sec
   *  X Vals ,the y values are modified with the values entered by the user
   */
  public static ArbitrarilyDiscretizedFunc getUSGS_SA_Function(){
	 ArbitrarilyDiscretizedFunc function= new ArbitrarilyDiscretizedFunc();
 
    function.set(.0025,1);
    function.set(.00375,1);
    function.set(.00563 ,1);
    function.set(.00844,1);
    function.set(.0127,1);
    function.set(.0190,1);
    function.set(.0285,1);
    function.set(.0427,1);
    function.set(.0641,1);
    function.set(.0961,1);
    function.set(.144,1);
    function.set(.216,1);
    function.set(.324,1);
    function.set(.487,1);
    function.set(.730,1);
    function.set(1.09,1);
    function.set(1.64,1);
    function.set(2.46,1);
    function.set(3.69,1);
    function.set(5.54,1);
    return function;
  }
   
  
  
  /**
   *
   * @param imtParam : IMT Parameter
   * @return true if the selected IMT is PGA, PGV or SA
   * else returns false
   */
  public static boolean isIMT_LogNormalDist(ParameterAPI imtParam){
     String paramVal =(String)imtParam.getValue();
    return isIMT_LogNormalDist(paramVal);
  }

  //added for debugging purposes
  public static void main(String args[]){
    IMT_Info hazardCurve = new IMT_Info();
    ArbitrarilyDiscretizedFunc func = hazardCurve.getDefaultHazardCurve("SA");
    System.out.println("For SA and PGA: ");
    System.out.println("Dis: "+hazardCurve.discretization_pga);
    System.out.println(func.toString());
    func = hazardCurve.getDefaultHazardCurve("PGV");
    System.out.println("For PGV: ");
    System.out.println("Dis: "+hazardCurve.discretization_pgv);
    System.out.println(func.toString());
  }
}
