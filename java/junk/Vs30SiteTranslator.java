package junk;

import org.opensha.commons.param.ParameterAPI;
import org.opensha.commons.param.WarningDoubleParameter;
import org.opensha.sha.imr.attenRelImpl.AS_1997_AttenRel;
import org.opensha.sha.imr.attenRelImpl.Abrahamson_2000_AttenRel;
import org.opensha.sha.imr.attenRelImpl.CB_2003_AttenRel;
import org.opensha.sha.imr.attenRelImpl.CS_2005_AttenRel;
import org.opensha.sha.imr.attenRelImpl.Campbell_1997_AttenRel;
import org.opensha.sha.imr.attenRelImpl.Field_2000_AttenRel;
import org.opensha.sha.imr.attenRelImpl.SadighEtAl_1997_AttenRel;
import org.opensha.sha.imr.attenRelImpl.ShakeMap_2003_AttenRel;
import org.opensha.sha.imr.param.SiteParams.DepthTo2pt5kmPerSecParam;
import org.opensha.sha.imr.param.SiteParams.Vs30_Param;



/**
 * <p>Title: SiteTranslator</p>
 * <p>Description: Translation is performed on the following scale:
 * Converting from Vs30 & Basin-Depth-2.5 to the above:

 Abrahamson & Silva (1997) & Abrahamson (2000):
 ----------------------------------------------

 NA 				if Vs30�180
 Deep-Soil			if Vs30 � 400 m/s & Basin-Depth-2.5 � 100 m
 Rock/Shallow-Soil		otherwise

 Sadigh et al. (1997):
 ---------------------

 NA 				if Vs30�180
 Deep-Soil			if Vs30 � 400 m/s & Basin-Depth-2.5 � 100 m
 Rock				otherwise

 Boore et al. (1997)
 -------------------

 Vs30 = Vs30			(if Vs30 > 180; NA otherwise)

 Campbell (1997)
 ---------------

 NA 				if Vs30�180
 Firm-Soil			if 180<Vs30�400
 Soft-Rock			if 400<Vs30�500
 Hard-Rock			if 500>Vs30

 Campbell-Basin-Depth = 0                    		if Vs30 � 400
 Campbell-Basin-Depth = Basin-Depth-2.5      	if Vs30 < 400

 Field (2000)
 ------------

 Vs30 = Vs30			(if Vs30 > 180; NA otherwise)
 Basin-Depth-2.5 = Basin-Depth-2.5

 Campbell & Bozorgnia (2003)
 ---------------------------

 NA 			if Vs30�180
 Firm-Soil		if 180<Vs30�300
 Very-Firm-Soil	        if 300<Vs30�400
 Soft-Rock		if 400<Vs30�500
 Firm-Rock		if 500>Vs30

 ShakeMap (2003)
 ---------------
Unfortunately Wills et al. (2000) do not give a unique mapping between Vs30 and their classification.
The following is based on the average value for each class (their Table 4). If it's not exactly one of these, NA is returned.
Note that we couldn't just use mid points because Vs30 for BC is greater than for B.


 E                      if Vs30 = 163
 DE                     if Vs30 = 298
 D                      if Vs30 = 301
 CD                     if Vs30 = 372
 C                      if Vs30 = 464
 BC                     if Vs30 = 724
 B                      if Vs30 = 686
 NA                     if anything else


 * <p>Copyright: Copyright (c) 2002</p>
 * <p>Company: </p>
 * @author: Ned Field & Nitin Gupta & Vipin Gupta
 * @version 1.0
 */
@Deprecated
public class Vs30SiteTranslator implements java.io.Serializable{
	/* 
	 * ***** DEPRICATED *****
	 * send Vs30 SiteDataValue object o SiteTranslator instead
	 */

  private final static String C = "SiteTranslator";
  private final static boolean D = false;


  public Vs30SiteTranslator() {
  }


  /**
   * @param s : site Object
   * @param vs30
   * @param basinDepth
   *
   * @returns the boolean which is required in the case of the HazardCurveApp
   * to tell the user that site is in the water.
   */
  public boolean setSiteParams(ParameterAPI tempParam, double vs30,double basinDepth ){
    boolean isDefaultVs30 = false;

    //if(D) System.out.println("Site: "+s.getLocation().toString()+"; vs30: "+vs30+"; basinDepth: "+basinDepth);

    // set Vs30 to default if it's less than 180 m/sec or NaN
    if(vs30 <=180 || Double.isNaN(vs30)){
      isDefaultVs30= true;
    }


      //Abrahamson & Silva (1997) site type
      if(tempParam.getName().equalsIgnoreCase(AS_1997_AttenRel.SITE_TYPE_NAME)){
        if(Double.isNaN(basinDepth)){
          if(vs30 <=400)
            tempParam.setValue(AS_1997_AttenRel.SITE_TYPE_SOIL);
          else
            tempParam.setValue(AS_1997_AttenRel.SITE_TYPE_ROCK);
        }
        else {
          if(vs30 <=400 && basinDepth > 100)
            tempParam.setValue(AS_1997_AttenRel.SITE_TYPE_SOIL);
          else
            tempParam.setValue(AS_1997_AttenRel.SITE_TYPE_ROCK);
        }
      }

      // Vs30 site type (e.g., BJF-1997 and Field-2000) site type
      else if(tempParam.getName().equalsIgnoreCase(Vs30_Param.NAME)){
        if(vs30>180)
          tempParam.setValue(new Double(vs30));
      }
//    Depth 2.5 km/sec Parameter
      else if (tempParam.getName().equals(DepthTo2pt5kmPerSecParam.NAME)) {
        // set Depth 2.5 km/sec in kms
        if (Double.isNaN(basinDepth)) tempParam.setValue(null);
        else ((WarningDoubleParameter)tempParam).setValueIgnoreWarning(new Double(basinDepth / 1000));
        return true;
      }
      //Cambell 1997 basin depth
      else if(tempParam.getName().equalsIgnoreCase(Campbell_1997_AttenRel.BASIN_DEPTH_NAME)){
        if(vs30>=400)
          tempParam.setValue(new Double(0));
        else {
          // set basin depth in kms
          if (D) System.out.println("BasinDEpth:"+basinDepth);
          if(Double.isNaN(basinDepth)) tempParam.setValue(null);
          else  tempParam.setValue(new Double(basinDepth/1000));
        }
      }

      //Cambell (1997) site type
      else if(tempParam.getName().equalsIgnoreCase(Campbell_1997_AttenRel.SITE_TYPE_NAME)){
        if(vs30>180 && vs30<=400)
          tempParam.setValue(Campbell_1997_AttenRel.SITE_TYPE_FIRM_SOIL);
        else if(vs30>400 && vs30<=500)
          tempParam.setValue(Campbell_1997_AttenRel.SITE_TYPE_SOFT_ROCK);
        else if(vs30>500)
          tempParam.setValue(Campbell_1997_AttenRel.SITE_TYPE_HARD_ROCK);
      }

      //Campbell & Bozorgnia (2003) site type
      else if(tempParam.getName().equalsIgnoreCase(CB_2003_AttenRel.SITE_TYPE_NAME)){
        if(vs30>180 && vs30<=300)
          tempParam.setValue(CB_2003_AttenRel.SITE_TYPE_FIRM_SOIL);
        if(vs30>300 && vs30<=400)
          tempParam.setValue(CB_2003_AttenRel.SITE_TYPE_VERY_FIRM_SOIL);
        if(vs30 >400 && vs30 <=500)
          tempParam.setValue(CB_2003_AttenRel.SITE_TYPE_SOFT_ROCK);
        if(vs30 >500)
          tempParam.setValue(CB_2003_AttenRel.SITE_TYPE_FIRM_ROCK);
      }

      //Abrahamson (2000) site type - not needed because same as Abrahamson & Silva (1997)
      else if(tempParam.getName().equalsIgnoreCase(Abrahamson_2000_AttenRel.SITE_TYPE_NAME)){
        if(Double.isNaN(basinDepth)){
          if(vs30 <=400)
            tempParam.setValue(Abrahamson_2000_AttenRel.SITE_TYPE_SOIL);
          else
            tempParam.setValue(Abrahamson_2000_AttenRel.SITE_TYPE_ROCK);
        }
        else {
          if(vs30 <=400 && basinDepth > 100)
            tempParam.setValue(Abrahamson_2000_AttenRel.SITE_TYPE_SOIL);
          else
            tempParam.setValue(Abrahamson_2000_AttenRel.SITE_TYPE_ROCK);
        }
      }

      //SCEMY Site type
      else if(tempParam.getName().equalsIgnoreCase(SadighEtAl_1997_AttenRel.SITE_TYPE_NAME)){
        if(Double.isNaN(basinDepth)){
          if(vs30 <=400)
            tempParam.setValue(SadighEtAl_1997_AttenRel.SITE_TYPE_SOIL);
          else
            tempParam.setValue(SadighEtAl_1997_AttenRel.SITE_TYPE_ROCK);
        }
        else {
          if(vs30 <=400 && basinDepth > 100)
            tempParam.setValue(SadighEtAl_1997_AttenRel.SITE_TYPE_SOIL);
          else
            tempParam.setValue(SadighEtAl_1997_AttenRel.SITE_TYPE_ROCK);
        }
      }

      //Field basin-depth site type
      else if(tempParam.getName().equalsIgnoreCase(Field_2000_AttenRel.BASIN_DEPTH_NAME)){
        // set basin depth in kms
          if(Double.isNaN(basinDepth)) tempParam.setValue(null);
          else  tempParam.setValue(new Double(basinDepth/1000));
      }

      //The Wills site classification used by the ShakeMap (2003) relationship
      else if(tempParam.getName().equalsIgnoreCase(ShakeMap_2003_AttenRel.WILLS_SITE_NAME)){
        if      (vs30 == 163)  tempParam.setValue(ShakeMap_2003_AttenRel.WILLS_SITE_E);
        else if (vs30 == 298)  tempParam.setValue(ShakeMap_2003_AttenRel.WILLS_SITE_DE);
        else if (vs30 == 301)  tempParam.setValue(ShakeMap_2003_AttenRel.WILLS_SITE_D);
        else if (vs30 == 372)  tempParam.setValue(ShakeMap_2003_AttenRel.WILLS_SITE_CD);
        else if (vs30 == 464)  tempParam.setValue(ShakeMap_2003_AttenRel.WILLS_SITE_C);
        else if (vs30 == 724)  tempParam.setValue(ShakeMap_2003_AttenRel.WILLS_SITE_BC);
        else if (vs30 == 686)  tempParam.setValue(ShakeMap_2003_AttenRel.WILLS_SITE_B);
        else {
          throw new RuntimeException(" That Vs30 is not allowed for "+ShakeMap_2003_AttenRel.WILLS_SITE_NAME);
        }
      }
//      CS_2005.SOFT_SOIL_CASE
       else if(tempParam.getName().equals(CS_2005_AttenRel.SOFT_SOIL_NAME)){
            if (vs30 < 180)
        		tempParam.setValue(new Boolean(true));
        	else
        		tempParam.setValue(new Boolean(false));
            return true;
        }
      else {
        throw new RuntimeException(C+" does not support the site type: "+tempParam.getName());
      }
    return isDefaultVs30;
  }
}
