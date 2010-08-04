/*******************************************************************************
 * Copyright 2009 OpenSHA.org in partnership with
 * the Southern California Earthquake Center (SCEC, http://www.scec.org)
 * at the University of Southern California and the UnitedStates Geological
 * Survey (USGS; http://www.usgs.gov)
 * 
 * Licensed under the Apache License, Version 2.0 (the "License");
 * you may not use this file except in compliance with the License.
 * You may obtain a copy of the License at
 * 
 *   http://www.apache.org/licenses/LICENSE-2.0
 * 
 * Unless required by applicable law or agreed to in writing, software
 * distributed under the License is distributed on an "AS IS" BASIS,
 * WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
 * See the License for the specific language governing permissions and
 * limitations under the License.
 ******************************************************************************/

package org.opensha.sha.util;

import org.opensha.commons.param.ParameterAPI;
import org.opensha.commons.param.WarningDoubleParameter;
import org.opensha.sha.imr.AttenuationRelationship;
import org.opensha.sha.imr.attenRelImpl.AS_1997_AttenRel;
import org.opensha.sha.imr.attenRelImpl.Abrahamson_2000_AttenRel;
import org.opensha.sha.imr.attenRelImpl.BJF_1997_AttenRel;
import org.opensha.sha.imr.attenRelImpl.CB_2003_AttenRel;
import org.opensha.sha.imr.attenRelImpl.CS_2005_AttenRel;
import org.opensha.sha.imr.attenRelImpl.Campbell_1997_AttenRel;
import org.opensha.sha.imr.attenRelImpl.Field_2000_AttenRel;
import org.opensha.sha.imr.attenRelImpl.SadighEtAl_1997_AttenRel;
import org.opensha.sha.imr.attenRelImpl.ShakeMap_2003_AttenRel;
import org.opensha.sha.imr.attenRelImpl.USGS_Combined_2004_AttenRel;
import org.opensha.sha.imr.param.SiteParams.DepthTo2pt5kmPerSecParam;
import org.opensha.sha.imr.param.SiteParams.Vs30_Param;

/**
 * <p>Title: SiteTranslator</p>
 * <p>Description: This object sets the value of a site parameter from the
 * Wills Site Type (Wills et al., 2000, BSSA, v. 90, S187-S208) and (optionally) from
 * Basin-Depth-2.5 (the depth in m where the shear-wave velocity equals 2.5 km/sec).
 * The conversions from the Wills Site Types (E, DE, D, CD, C, BC, B) and basin-depth
 * are given below (NA means nothing is set).  All of these translations were authorized
 * by the attenuation-rlationship authors (except for Sadigh, who used a dataset similar
 * to Abrahamson & Silve (1997) so that translation is applied).  The main method tests
 * the translations of all currently implemented attenuation-relationship site-related
 * parameters.<p>
 *
 *
 * AS_1997_AttenRel.SITE_TYPE_NAME (Abrahamson & Silva (1997) & Abrahamson (2000))<p>
 * <UL>
 * <LI> NA 				if E
 * <LI> Deep-Soil			if DE, D, or CD
 * <LI> Rock/Shallow-Soil		if C, BC, or B
 * </UL>
 *
 * SCEMY_1997_AttenRel.SITE_TYPE_NAME (Sadigh et al. (1997)):<p>
 * <UL>
 * <LI> NA 				if E
 * <LI> Deep-Soil			if DE, D, or CD
 * <LI> Rock		                if C, BC, or B
 * </UL>
 *
 * Vs30_Param.NAME (Boore et al. (1997) & Field (2000))<p>
 * <LI> <UL>
 * <LI> Vs30 = NA			if E
 * <LI> Vs30 = 180			if DE
 * <LI> Vs30 = 270			if D
 * <LI> Vs30 = 360			if CD
 * <LI> Vs30 = 560			if C
 * <LI> Vs30 = 760			if BC
 * <LI> Vs30 = 1000			if B
 * <LI> </UL>
 *
 * Campbell_1997_AttenRel.SITE_TYPE_NAME (Campbell (1997))<p>
 * <UL>
 * <LI> NA 				if E
 * <LI> Firm-Soil			if DE, D, or CD
 * <LI> Soft-Rock			if C
 * <LI> Hard-Rock			if BC or B
 * </UL>
 *
 * Campbell_1997_AttenRel.BASIN_DEPTH_NAME (Campbell (1997))<p>
 * <UL>
 * <LI> Campbell-Basin-Depth = NaN      if E
 * <LI> Campbell-Basin-Depth = 0.0      if B or BC
 * <LI> Campbell-Basin-Depth = 1.0      if C
 * <LI> Campbell-Basin-Depth = 5.0      if CD, D, or DE
 * </UL>
 *
 * Field_2000_AttenRel.BASIN_DEPTH_NAME (Field (2000))<p>
 * <UL>
 * <LI> Basin-Depth-2.5 = Basin-Depth-2.5
 * </UL>
 *
 * CB_2003_AttenRel.SITE_TYPE_NAME (Campbell & Bozorgnia (2003))<p>
 * <UL>
 * <LI> NA 			if E
 * <LI> Firm-Soil		if DE or D
 * <LI> Very-Firm-Soil	        if CD
 * <LI> Soft-Rock		if C
 * <LI> BC-Bounday              if BC
 * <LI> Firm-Rock		if B�
 * </UL>
 *
 * ShakeMap_2003_AttenRel.WILLS_SITE_NAME (ShakeMap (2003))<p>
 * <LI> <UL>
 * <LI> E                      if E
 * <LI> DE                     if DE
 * <LI> D                      if D
 * <LI> CD                     if CD
 * <LI> C                      if C
 * <LI> BC                     if BC
 * <LI> B                      if B
 * </UL>
 *
 * <p>Copyright: Copyright (c) 2002</p>
 * <p>Company: </p>
 * @author: Ned Field & Nitin Gupta & Vipin Gupta
 * @version 1.0
 */

public class OldSiteTranslator
    implements java.io.Serializable {

  private final static String C = "SiteTranslator";
  private final static boolean D = false;

  public final static String WILLS_B = "B";
  public final static String WILLS_BC = "BC";
  public final static String WILLS_C = "C";
  public final static String WILLS_CD = "CD";
  public final static String WILLS_D = "D";
  public final static String WILLS_DE = "DE";
  public final static String WILLS_E = "E";

  public OldSiteTranslator() {
  }

  /**
   * @param parameter: the parameter object to be set
   * @param willsClass - a String with one of the folowing ("E", "DE", "D", "CD", "C", "BC", or "B")
   * @param basinDepth - Depth (in meters) to where Vs = 2.5-km/sec
   *
   * @returns a boolean to tell if setting the value was successful (if false
   * it means the parameter value was not changed).  A basinDepth value of NaN is allowed
   * (it will not cause the returned value to be false).
   * 
   * ***NOTE: THIS NEEDS TO FIXED TO HANDLE THE SOFT SOIL CASE FOR CHOI AND STEWART MODEL 
   */
  public boolean setParameterValue(ParameterAPI param, String willsClass,
                                   double basinDepth) {

    // shorten name for convenience
    String wc = willsClass;

    // AS_1997_AttenRel.SITE_TYPE_NAME
    // (e.g., used by Abrahamson & Silva (1997) & Abrahamson (2000))
    if (param.getName().equals(AS_1997_AttenRel.SITE_TYPE_NAME)) {

      if (wc.equals(WILLS_DE) || wc.equals(WILLS_D) || wc.equals(WILLS_CD)) {
        param.setValue(AS_1997_AttenRel.SITE_TYPE_SOIL);
        return true;
      }
      else if (wc.equals(WILLS_C) || wc.equals(WILLS_BC) || wc.equals(WILLS_B)) {
        param.setValue(AS_1997_AttenRel.SITE_TYPE_ROCK);
        return true;
      }
      else {
        return false;
      }
    }

    // SCEMY_1997_AttenRel.SITE_TYPE_NAME
    else if (param.getName().equals(SadighEtAl_1997_AttenRel.SITE_TYPE_NAME)) {

      if (wc.equals(WILLS_DE) || wc.equals(WILLS_D) || wc.equals(WILLS_CD)) {
        param.setValue(SadighEtAl_1997_AttenRel.SITE_TYPE_SOIL);
        return true;
      }
      else if (wc.equals(WILLS_C) || wc.equals(WILLS_BC) || wc.equals(WILLS_B)) {
        param.setValue(SadighEtAl_1997_AttenRel.SITE_TYPE_ROCK);
        return true;
      }
      else {
        return false;
      }
    }

    // Vs30_Param.NAME
    // (e.g., used by BJF-1997 and Field-2000) site type
    else if (param.getName().equals(Vs30_Param.NAME)) {
      if (wc.equals(WILLS_DE)) {
        param.setValue(new Double(180));
        return true;
      }
      else if (wc.equals(WILLS_D)) {
        param.setValue(new Double(270));
        return true;
      }
      else if (wc.equals(WILLS_CD)) {
        param.setValue(new Double(360));
        return true;
      }
      else if (wc.equals(WILLS_C)) {
        param.setValue(new Double(560));
        return true;
      }
      else if (wc.equals(WILLS_BC)) {
        param.setValue(new Double(760));
        return true;
      }
      else if (wc.equals(WILLS_B)) {
        param.setValue(new Double(1000));
        return true;
      }
      else {
        return false;
      }
    }

    // Campbell_1997_AttenRel.BASIN_DEPTH_NAME
    // (these are as Ken Campbell requested)
    else if (param.getName().equals(Campbell_1997_AttenRel.BASIN_DEPTH_NAME)) {
      if (wc.equals(WILLS_DE) || wc.equals(WILLS_D) || wc.equals(WILLS_CD)) {
        param.setValue(new Double(5.0));
        return true;
      }
      else if (wc.equals(WILLS_C)) {
        param.setValue(new Double(1.0));
        return true;
      }
      else if (wc.equals(WILLS_BC) || wc.equals(WILLS_B)) {
        param.setValue(new Double(0.0));
        return true;
      }
      else {
        return false;
      }
    }

    // Campbell_1997_AttenRel.SITE_TYPE_NAME
    else if (param.getName().equals(Campbell_1997_AttenRel.SITE_TYPE_NAME)) {

      if (wc.equals(WILLS_DE) || wc.equals(WILLS_D) || wc.equals(WILLS_CD)) {
        param.setValue(Campbell_1997_AttenRel.SITE_TYPE_FIRM_SOIL);
        return true;
      }
      else if (wc.equals(WILLS_C)) {
        param.setValue(Campbell_1997_AttenRel.SITE_TYPE_SOFT_ROCK);
        return true;
      }
      else if (wc.equals(WILLS_BC) || wc.equals(WILLS_B)) {
        param.setValue(Campbell_1997_AttenRel.SITE_TYPE_HARD_ROCK);
        return true;
      }
      else {
        return false;
      }
    }

    // CB_2003_AttenRel.SITE_TYPE_NAME
    else if (param.getName().equals(CB_2003_AttenRel.SITE_TYPE_NAME)) {
      if (wc.equals(WILLS_DE) || wc.equals(WILLS_D)) {
        param.setValue(CB_2003_AttenRel.SITE_TYPE_FIRM_SOIL);
        return true;
      }
      else if (wc.equals(WILLS_CD)) {
        param.setValue(CB_2003_AttenRel.SITE_TYPE_VERY_FIRM_SOIL);
        return true;
      }
      else if (wc.equals(WILLS_C)) {
        param.setValue(CB_2003_AttenRel.SITE_TYPE_SOFT_ROCK);
        return true;
      }
      else if (wc.equals(WILLS_BC)) {
        param.setValue(CB_2003_AttenRel.SITE_TYPE_NEHRP_BC);
        return true;
      }
      else if (wc.equals(WILLS_B)) {
        param.setValue(CB_2003_AttenRel.SITE_TYPE_FIRM_ROCK);
        return true;
      }
      else {
        return false;
      }
    }

    // Field_2000_AttenRel.BASIN_DEPTH_NAME
    else if (param.getName().equals(Field_2000_AttenRel.BASIN_DEPTH_NAME)) {
      // set basin depth in kms
      if(Double.isNaN(basinDepth)) param.setValue(null);
      else  param.setValue(new Double(basinDepth/1000));
      return true;
    }
    // Depth 2.5 km/sec Parameter
    else if (param.getName().equals(DepthTo2pt5kmPerSecParam.NAME)) {
      // set Depth 2.5 km/sec in kms
      if (Double.isNaN(basinDepth)) param.setValue(null);
      else ((WarningDoubleParameter)param).setValueIgnoreWarning(new Double(basinDepth / 1000));
      return true;
    }
    // ShakeMap_2003_AttenRel.WILLS_SITE_NAME
    else if (param.getName().equals(ShakeMap_2003_AttenRel.WILLS_SITE_NAME)) {

      if (param.isAllowed(wc)) {
        param.setValue(wc);
        return true;
      }
      else {
        return false;
      }
    }
    //CS_2005.SOFT_SOIL_CASE
    else if(param.getName().equals(CS_2005_AttenRel.SOFT_SOIL_NAME)){
    	if (wc.equals(WILLS_E))
    		param.setValue(new Boolean(true));
    	else
    		param.setValue(new Boolean(false));
        return true;
    }

    // site type not found
    else {
      throw new RuntimeException(C + " does not support the site type: " +
                                 param.getName());
    }
  }



  /**
   * This will test the translation from all wills categories for the parameter given
   * @param param
   */
  public void test(ParameterAPI param) {
    System.out.println(param.getName() + "  Parameter (basin depth = NaN):");
    if (setParameterValue(param, WILLS_B, Double.NaN)) {
      System.out.println("\t" + WILLS_B + " --> " + param.getValue());
    }
    else {
      System.out.println("\t" + WILLS_B + " --> " + "*** can't set ***");
    }
    if (setParameterValue(param, WILLS_BC, Double.NaN)) {
      System.out.println("\t" + WILLS_BC + " --> " + param.getValue());
    }
    else {
      System.out.println("\t" + WILLS_BC + " --> " + "*** can't set ***");
    }
    if (setParameterValue(param, WILLS_C, Double.NaN)) {
      System.out.println("\t" + WILLS_C + " --> " + param.getValue());
    }
    else {
      System.out.println("\t" + WILLS_C + " --> " + "*** can't set ***");
    }
    if (setParameterValue(param, WILLS_CD, Double.NaN)) {
      System.out.println("\t" + WILLS_CD + " --> " + param.getValue());
    }
    else {
      System.out.println("\t" + WILLS_CD + " --> " + "*** can't set ***");
    }
    if (setParameterValue(param, WILLS_D, Double.NaN)) {
      System.out.println("\t" + WILLS_D + " --> " + param.getValue());
    }
    else {
      System.out.println("\t" + WILLS_D + " --> " + "*** can't set ***");
    }
    if (setParameterValue(param, WILLS_DE, Double.NaN)) {
      System.out.println("\t" + WILLS_DE + " --> " + param.getValue());
    }
    else {
      System.out.println("\t" + WILLS_DE + " --> " + "*** can't set ***");
    }
    if (setParameterValue(param, WILLS_E, Double.NaN)) {
      System.out.println("\t" + WILLS_E + " --> " + param.getValue());
    }
    else {
      System.out.println("\t" + WILLS_E + " --> " + "*** can't set ***");
    }

    System.out.println(param.getName() + "  Parameter (basin depth = 1.0):");
    if (setParameterValue(param, WILLS_B, 1.0)) {
      System.out.println("\t" + WILLS_B + " --> " + param.getValue());
    }
    else {
      System.out.println("\t" + WILLS_B + " --> " + "*** can't set ***");
    }
    if (setParameterValue(param, WILLS_BC, 1.0)) {
      System.out.println("\t" + WILLS_BC + " --> " + param.getValue());
    }
    else {
      System.out.println("\t" + WILLS_BC + " --> " + "*** can't set ***");
    }
    if (setParameterValue(param, WILLS_C, 1.0)) {
      System.out.println("\t" + WILLS_C + " --> " + param.getValue());
    }
    else {
      System.out.println("\t" + WILLS_C + " --> " + "*** can't set ***");
    }
    if (setParameterValue(param, WILLS_CD, 1.0)) {
      System.out.println("\t" + WILLS_CD + " --> " + param.getValue());
    }
    else {
      System.out.println("\t" + WILLS_CD + " --> " + "*** can't set ***");
    }
    if (setParameterValue(param, WILLS_D, 1.0)) {
      System.out.println("\t" + WILLS_D + " --> " + param.getValue());
    }
    else {
      System.out.println("\t" + WILLS_D + " --> " + "*** can't set ***");
    }
    if (setParameterValue(param, WILLS_DE, 1.0)) {
      System.out.println("\t" + WILLS_DE + " --> " + param.getValue());
    }
    else {
      System.out.println("\t" + WILLS_DE + " --> " + "*** can't set ***");
    }
    if (setParameterValue(param, WILLS_E, 1.0)) {
      System.out.println("\t" + WILLS_E + " --> " + param.getValue());
    }
    else {
      System.out.println("\t" + WILLS_E + " --> " + "*** can't set ***");
    }
  }

  /**
   * This main method tests the translation of all currently implemented attenuation
   * relationship site-dependent parameters.
   * @param args
   */
  public static void main(String args[]) {
	  OldSiteTranslator siteTrans = new OldSiteTranslator();

    AttenuationRelationship ar;
    ar = new AS_1997_AttenRel(null);
    siteTrans.test(ar.getParameter(AS_1997_AttenRel.SITE_TYPE_NAME));

    ar = new SadighEtAl_1997_AttenRel(null);
    siteTrans.test(ar.getParameter(SadighEtAl_1997_AttenRel.SITE_TYPE_NAME));

    ar = new BJF_1997_AttenRel(null);
    siteTrans.test(ar.getParameter(Vs30_Param.NAME));

    ar = new Campbell_1997_AttenRel(null);
    siteTrans.test(ar.getParameter(Campbell_1997_AttenRel.SITE_TYPE_NAME));
    siteTrans.test(ar.getParameter(Campbell_1997_AttenRel.BASIN_DEPTH_NAME));

    ar = new Field_2000_AttenRel(null);
    siteTrans.test(ar.getParameter(Vs30_Param.NAME));
    siteTrans.test(ar.getParameter(Field_2000_AttenRel.BASIN_DEPTH_NAME));

    ar = new Abrahamson_2000_AttenRel(null);
    siteTrans.test(ar.getParameter(Abrahamson_2000_AttenRel.SITE_TYPE_NAME));

    ar = new CB_2003_AttenRel(null);
    siteTrans.test(ar.getParameter(CB_2003_AttenRel.SITE_TYPE_NAME));

    ar = new ShakeMap_2003_AttenRel(null);
    siteTrans.test(ar.getParameter(ShakeMap_2003_AttenRel.WILLS_SITE_NAME));

    ar = new USGS_Combined_2004_AttenRel(null);
    siteTrans.test(ar.getParameter(Vs30_Param.NAME));

//  ar = new SEA_1999_AttenRel(null);
//  siteTrans.test(ar.getParameter(SEA_1999_AttenRel.SITE_TYPE_NAME));


  }

}
