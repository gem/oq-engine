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

   package org.opensha.sha.imr.attenRelImpl.calc;

/**
 * <p>Title: Wald_MMI_Calc </p>
 * <b>Description:</b> This computes MMI (from PGA and PGV) using the relationship given by
 * Wald et al. (1999, Earthquake Spectra, vol 15, p 557-564).  The code is a modified version
 * of what Bruce Worden sent me (Ned) on 12/04/03.  This code has been validated
 * against some of the values listed in the USGS on-line data archive for the Puente Hills event:
 * http://www.trinet.org/shake/Puente_Hills_se/download/grid.xyz.zip <p>
 *
 *
 * @author Ned Field
 * @created    May, 2004
 * @version 1.0
 */

public final class Wald_MMI_Calc {

  static double sma     =  3.6598;
  static double ba      = -1.6582;
  static double sma_low =  2.1987;
  static double ba_low  =  1;

  static double smv     =  3.4709;
  static double bv      =  2.3478;
  static double smv_low =  2.0951;
  static double bv_low  =  3.3991;

  /**
   *
   * @param pga - peak ground acceleration (g)
   * @param pgv - peak ground velocity (cm/sec)
   * @return
   */
  public static double getMMI(double pga, double pgv){
    String S = ".getMMI()";

    // Convert pga to gals as needed below
    pga *= 980.0;

    double scale;
    double ammi; // Intensity from acceleration
    double vmmi; // Intensity from velocity

    ammi = (0.43429*Math.log(pga) * sma) + ba;
    if (ammi <= 5.0)
      ammi = (0.43429*Math.log(pga) * sma_low) + ba_low;

    vmmi = (0.43429*Math.log(pgv) * smv) + bv;
    if (vmmi <= 5.0)
      vmmi = (0.43429*Math.log(pgv) * smv_low) + bv_low;

    if (ammi < 1) ammi = 1;
    if (vmmi < 1) vmmi = 1;

    // use linear ramp between MMI 5 & 7 (ammi below and vmmi above, respectively)
    scale = (ammi - 5) / 2; // ramp
    if (scale > 1.0) scale = 1.0;
    if (scale < 0.0) scale = 0.0;

    double mmi = ((1.0-scale) * ammi) + (scale * vmmi);
    if (mmi < 1.0) mmi = 1.0 ;
    if (mmi > 10.0) mmi = 10.0;
//      return (double)((int) (mmi * 100)) / 100.;
    return mmi;
    }




    /**
     * This main method tests the calculations against some of the values listed
     * in the USGS on-line data archive for the Puente Hills event:
     * http://www.trinet.org/shake/Puente_Hills_se/download/grid.xyz.zip <p>
     * The differences of 0.01 result from differences in how the values are rounded.
     * @param args
     */
/* commented out until needed again
    public static void main(String[] args) {

      System.out.println("Comparison of values:");
      System.out.println((float) Wald_MMI_Calc.getMMI(4.922/100, 4.3774) + " 4.7");
      System.out.println((float) Wald_MMI_Calc.getMMI(5.164/100, 4.5989) + " 4.74");
      System.out.println((float) Wald_MMI_Calc.getMMI(5.454/100, 4.8645) + " 4.8");
      System.out.println((float) Wald_MMI_Calc.getMMI(6.0587/100, 5.42) + " 4.9");
      System.out.println((float) Wald_MMI_Calc.getMMI(7.3959/100, 6.6554) + " 5.15");
      System.out.println((float) Wald_MMI_Calc.getMMI(8.0925/100, 7.3029) + " 5.3");
      System.out.println((float) Wald_MMI_Calc.getMMI(9.1612/100, 8.3022) + " 5.5");
      System.out.println((float) Wald_MMI_Calc.getMMI(9.8223/100, 8.923) + " 5.61");
      System.out.println((float) Wald_MMI_Calc.getMMI(11.2098/100, 10.2373) + " 5.82");
      System.out.println((float) Wald_MMI_Calc.getMMI(12.6785/100, 11.6435) + " 6.02");
      System.out.println((float) Wald_MMI_Calc.getMMI(17.6332/100, 16.4121) + " 6.55");
      System.out.println((float) Wald_MMI_Calc.getMMI(24.3042/100, 28.9529) + " 7.42");
      System.out.println((float) Wald_MMI_Calc.getMMI(28.7264/100, 41.9774) + " 7.98");
      System.out.println((float) Wald_MMI_Calc.getMMI(32.0077/100, 44.5101) + " 8.06");
      System.out.println((float) Wald_MMI_Calc.getMMI(34.3796/100, 48.8414) + " 8.2");
      System.out.println((float) Wald_MMI_Calc.getMMI(37.7906/100, 69.7778) + " 8.74");
      System.out.println((float) Wald_MMI_Calc.getMMI(41.2803/100, 80.9729) + " 8.97");
      System.out.println((float) Wald_MMI_Calc.getMMI(42.2048/100, 85.205) + " 9.04");
      System.out.println((float) Wald_MMI_Calc.getMMI(47.0372/100, 104.926) + " 9.36");

      System.out.println("Difference in values:");
      System.out.println((float) Wald_MMI_Calc.getMMI(4.922/100, 4.3774) - 4.7);
      System.out.println((float) Wald_MMI_Calc.getMMI(5.164/100, 4.5989) - 4.74);
      System.out.println((float) Wald_MMI_Calc.getMMI(5.454/100, 4.8645) - 4.8);
      System.out.println((float) Wald_MMI_Calc.getMMI(6.0587/100, 5.42) - 4.9);
      System.out.println((float) Wald_MMI_Calc.getMMI(7.3959/100, 6.6554) - 5.15);
      System.out.println((float) Wald_MMI_Calc.getMMI(8.0925/100, 7.3029) - 5.3);
      System.out.println((float) Wald_MMI_Calc.getMMI(9.1612/100, 8.3022) - 5.5);
      System.out.println((float) Wald_MMI_Calc.getMMI(9.8223/100, 8.923) - 5.61);
      System.out.println((float) Wald_MMI_Calc.getMMI(11.2098/100, 10.2373) - 5.82);
      System.out.println((float) Wald_MMI_Calc.getMMI(12.6785/100, 11.6435) - 6.02);
      System.out.println((float) Wald_MMI_Calc.getMMI(17.6332/100, 16.4121) - 6.55);
      System.out.println((float) Wald_MMI_Calc.getMMI(24.3042/100, 28.9529) - 7.42);
      System.out.println((float) Wald_MMI_Calc.getMMI(28.7264/100, 41.9774) - 7.98);
      System.out.println((float) Wald_MMI_Calc.getMMI(32.0077/100, 44.5101) - 8.06);
      System.out.println((float) Wald_MMI_Calc.getMMI(34.3796/100, 48.8414) - 8.2);
      System.out.println((float) Wald_MMI_Calc.getMMI(37.7906/100, 69.7778) - 8.74);
      System.out.println((float) Wald_MMI_Calc.getMMI(41.2803/100, 80.9729) - 8.97);
      System.out.println((float) Wald_MMI_Calc.getMMI(42.2048/100, 85.205) - 9.04);
      System.out.println((float) Wald_MMI_Calc.getMMI(47.0372/100, 104.926) - 9.36);
    }
    */

}
