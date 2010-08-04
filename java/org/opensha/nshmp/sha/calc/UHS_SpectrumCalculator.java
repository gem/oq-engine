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

import org.opensha.commons.data.function.ArbitrarilyDiscretizedFunc;
import org.opensha.commons.data.function.DiscretizedFuncList;
import org.opensha.nshmp.util.GlobalConstants;
import org.opensha.nshmp.util.ui.DataDisplayFormatter;

/**
 * <p>Title: UHS_SpectrumCalculator</p>
 * <p>Description: This class calculates the Uniform Hazard Spectrum values.</p>
 * @author Ned Field, Nitin Gupta and Vipin Gupta
 * @version 1.0
 */
public class UHS_SpectrumCalculator
    extends SpectrumCalculator {

  /**
   *
   * @param saVals ArbitrarilyDiscretizedFunc
   * @return DiscretizedFuncList
   */
  public DiscretizedFuncList calculateApproxUHSSpectrum(
      ArbitrarilyDiscretizedFunc pgaVals) {

    float fa = 1.0f;
    float fv = 1.0f;

    double tAcc = pgaVals.getX(1);
    double sAcc = fa * pgaVals.getY(1);
    double sVel = fv * pgaVals.getY(2);
    double sPGA = fa * pgaVals.getY(0);
    DiscretizedFuncList funcList = approxSaSd(tAcc, sAcc, sVel, sPGA);

    saTfunction.setName(GlobalConstants.APPROX_UNIFORM_HAZARD_SPECTRUM_NAME +
                        " of " +
                        GlobalConstants.SA_Vs_T_GRAPH_NAME);
    saSdfunction.setName(GlobalConstants.APPROX_UNIFORM_HAZARD_SPECTRUM_NAME +
                         " of " +
                         GlobalConstants.SA_Vs_SD_GRAPH_NAME);
    String title = "Approx. UHS";
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
  public DiscretizedFuncList calculateSMS_UHSpectrum(ArbitrarilyDiscretizedFunc
      pgaVals,
      float fa, float fv, String siteClass) {

    double tAcc = pgaVals.getX(1);
    double sAcc = fa * pgaVals.getY(1);
    double sVel = fv * pgaVals.getY(2);
    double sPga = fa * pgaVals.getY(0);
    DiscretizedFuncList funcList = approxSaSd(tAcc, sAcc, sVel, sPga);

    saTfunction.setName(GlobalConstants.SITE_MODIFIED_SA_Vs_T_GRAPH);
    saSdfunction.setName(GlobalConstants.SITE_MODIFIED_SD_Vs_T_GRAPH);
    String title = "Site Modified Response Spectra for Site Class " + siteClass;
    String subTitle = "SMs = FaSs and SM1 = FvS1";

    String info = "";
    info += title + "\n";
    info +=
        DataDisplayFormatter.createSubTitleString(subTitle, siteClass,
                                                  fa, fv);

    info +=
        DataDisplayFormatter.createFunctionInfoString(funcList, siteClass);
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
  public DiscretizedFuncList calculateSD_UHSpectrum(ArbitrarilyDiscretizedFunc
      pgaVals,
      float fa, float fv,
      String siteClass) {
    float faVal = (2.0f / 3.0f) * fa;
    float fvVal = (2.0f / 3.0f) * fv;

    double tAcc = pgaVals.getX(1);
    double sAcc = faVal * pgaVals.getY(1);
    double sVel = fvVal * pgaVals.getY(2);
    //Have to ask E.V about its formula
    //double sPga = faVal*pgaVals.getY(0);
    double sPga = (2.0f / 3.0f) * sAcc;
    DiscretizedFuncList funcList = approxSaSd(tAcc, sAcc, sVel, sPga);

    saTfunction.setName(GlobalConstants.DESIGN_SPECTRUM_SA_Vs_T_GRAPH);
    saSdfunction.setName(GlobalConstants.DESIGN_SPECTRUM_SD_Vs_T_GRAPH);

    String title = "Design Response Spectra for Site Class " + siteClass;
    String subTitle = "SDs = 2/3 x SMs and SD1 = 2/3 x SM1";

    String info = "";
    info += title + "\n";
    info +=
        DataDisplayFormatter.createSubTitleString(subTitle, siteClass,
                                                  faVal, fvVal);

    info +=
        DataDisplayFormatter.createFunctionInfoString(funcList, siteClass);
    funcList.setInfo(info);

    return funcList;
  }

}
