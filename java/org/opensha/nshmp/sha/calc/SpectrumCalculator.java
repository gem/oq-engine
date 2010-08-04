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

package org.opensha.nshmp.sha.calc;

import java.text.DecimalFormat;

import org.opensha.commons.data.function.ArbitrarilyDiscretizedFunc;
import org.opensha.commons.data.function.DiscretizedFuncList;
import org.opensha.nshmp.util.GlobalConstants;
import org.opensha.nshmp.util.ui.DataDisplayFormatter;

/**
 * <p>Title: SpectrumCalculator</p>
 *
 * <p>Description: </p>
 * @author Ned Field,Nitin Gupta, E.V.Leyendecker
 * @version 1.0
 */
public class SpectrumCalculator {

  private double tPga, tPgaTransition, tVelTransition;

  protected ArbitrarilyDiscretizedFunc saSdfunction;
  protected ArbitrarilyDiscretizedFunc saTfunction;

  private DecimalFormat tFormat = new DecimalFormat("0.0");

  /**
   *
   * @param periodVal double
   * @param sPGA double
   * @param sAccerlation double
   * @param fa float
   * @param fv float
   * @return DiscretizedFuncList
   */
  protected DiscretizedFuncList approxSaSd(double periodVal,
                                           double sAccerlation,
                                           double sVelocity, double sPGA) {
    DiscretizedFuncList funcList = new DiscretizedFuncList();
    saTfunction = new ArbitrarilyDiscretizedFunc();

    double tAcc = periodVal;
    tPga = 0;
    double tMaxVel = 2;
    double tInc = 0.1;
    tVelTransition = sVelocity / sAccerlation;
    tPgaTransition = 0.2 * tVelTransition;

    saTfunction.set(tPga, sPGA);
    saTfunction.set(tPgaTransition, sAccerlation);

    if (tPgaTransition <= tAcc) {
      saTfunction.set(tAcc, sAccerlation);
    }
    saTfunction.set(tVelTransition, sAccerlation);
    double lastT = ( (int) (tVelTransition * 10.0)) / 10.0;
    double nextT = lastT + tInc;

    while (nextT <= tMaxVel) {
      saTfunction.set(nextT, sVelocity / nextT);
      nextT += tInc;
      String nextTString = tFormat.format(nextT);
      nextT = Double.parseDouble(nextTString);
    }
    StdDisplacementCalc calc = new StdDisplacementCalc();
    saSdfunction = calc.getStdDisplacement(saTfunction);

    funcList.add(saSdfunction);
    funcList.add(saTfunction);
    return funcList;
  }

  /**
   *
   * @param saVals ArbitrarilyDiscretizedFunc
   * @return DiscretizedFuncList
   */
  public DiscretizedFuncList calculateMapSpectrum(ArbitrarilyDiscretizedFunc
                                                  saVals) {

    float fa = 1.0f;
    float fv = 1.0f;

    double tAcc = saVals.getX(0);
    double sAcc = fa * saVals.getY(0);
    double sVel = fv * saVals.getY(1);
    double sPGA = 0.4 * sAcc;

    DiscretizedFuncList funcList = approxSaSd(tAcc, sAcc, sVel, sPGA);

    saTfunction.setName(GlobalConstants.MCE_SPECTRUM_SA_Vs_T_GRAPH);
    saSdfunction.setName(GlobalConstants.MCE_SPECTRUM_SD_Vs_T_GRAPH);
    String title = "MCE Response Spectrum for Site Class B";
    String subTitle = "Ss and S1 = Mapped Spectral Acceleration Values";

    String info = "";
    info += title + "\n";

    info +=
        DataDisplayFormatter.createSubTitleString(subTitle,
                                                  GlobalConstants.SITE_CLASS_B,
                                                  1, 1);
    info +=
        DataDisplayFormatter.createFunctionInfoString(funcList,
        GlobalConstants.SITE_CLASS_B);
    funcList.setInfo(info);
    return funcList;
  }

  /**
   *
   * @param saVals ArbitrarilyDiscretizedFunc
   * @param fa float
   * @param fv float
   * @return DiscretizedFuncList
   */
  public DiscretizedFuncList calculateSMSpectrum(ArbitrarilyDiscretizedFunc
                                                 saVals,
                                                 float fa, float fv,
                                                 String siteClass, String edition) {

    double tAcc = saVals.getX(0);
    double sAcc = fa * saVals.getY(0);
    double sVel = fv * saVals.getY(1);
    double sPGA = 0.4 * sAcc;
    boolean is2009 = GlobalConstants.NEHRP_2009.equals(edition);
    DiscretizedFuncList funcList = approxSaSd(tAcc, sAcc, sVel, sPGA);

    saTfunction.setName(GlobalConstants.SITE_MODIFIED_SA_Vs_T_GRAPH);
    saSdfunction.setName(GlobalConstants.SITE_MODIFIED_SD_Vs_T_GRAPH);

    String title = "Site Modified Response Spectrum for " + siteClass;
    if (is2009) { title = "RTE Reponse Spectrum for " + siteClass + "\n" +
    	"SRs = 1.5 * SDs and SR1 = 1.5 * SD1";
    }
    String subTitle = "SMs = FaSs and SM1 = FvS1";

    String info = "";
    info += title + "\n";
    if (!is2009) {
    	info += DataDisplayFormatter.createSubTitleString(subTitle, siteClass,
                                                  fa, fv);
        info +=
            DataDisplayFormatter.createFunctionInfoString(funcList, siteClass);
        funcList.setInfo(info);
    } else {
    	saTfunction.setName("MCE_R Spectrum Sa Vs T");
    	//saTfunction.setName("RTE Spectrum Sa Vs T");
	    info +=
	        DataDisplayFormatter.createFunctionInfoString(funcList, siteClass, true);
    }
	funcList.setInfo(info);
    return funcList;
  }

  /**
   *
   * @param saVals ArbitrarilyDiscretizedFunc
   * @param fa float
   * @param fv float
   * @return DiscretizedFuncList
   */
  public DiscretizedFuncList calculateSDSpectrum(ArbitrarilyDiscretizedFunc
                                                 saVals,
                                                 float fa, float fv,
                                                 String siteClass, String edition) {
    float faVal = (2.0f / 3.0f) * fa;
    float fvVal = (2.0f / 3.0f) * fv;

    double tAcc = saVals.getX(0);
    double sAcc = faVal * saVals.getY(0);
    double sVel = fvVal * saVals.getY(1);
    double sPGA = 0.4 * sAcc;
    boolean is2009 = GlobalConstants.NEHRP_2009.equals(edition);

    DiscretizedFuncList funcList = approxSaSd(tAcc, sAcc, sVel, sPGA);

    saTfunction.setName(GlobalConstants.DESIGN_SPECTRUM_SA_Vs_T_GRAPH);
    saSdfunction.setName(GlobalConstants.DESIGN_SPECTRUM_SD_Vs_T_GRAPH);

    String title = "Design Response Spectrum for " + siteClass;
    String subTitle = "SDs = 2/3 x SMs and SD1 = 2/3 x SM1";

    String info = "";
    info += title + "\n";
    if (!is2009) {
    	info += DataDisplayFormatter.createSubTitleString(subTitle, siteClass,
                                                  fa, fv);
	    info +=
	        DataDisplayFormatter.createFunctionInfoString(funcList, siteClass);
    } else {
	    info +=
	        DataDisplayFormatter.createFunctionInfoString(funcList, siteClass, true);
    }
    funcList.setInfo(info);

    return funcList;
  }
}
