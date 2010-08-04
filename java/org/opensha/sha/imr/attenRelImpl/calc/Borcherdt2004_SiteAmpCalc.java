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

 import org.opensha.commons.data.function.EvenlyDiscretizedFunc;

/**
 * <p>Title: Borcherdt2004_SiteAmpCalc </p>
 * <b>Description:</b> This computes amplification factors using equations
 * 7a and 7b in the Appendix of Borecherdt (1994, Earthquake Spectra, Vol. 10,
 * No. 4, 617-653).  Note that the ma and mv coefficients are linearly interpolated
 * at intermediate input ground motions (PGA).
 *
 * @author Ned Field
 * @created    May, 2004
 * @version 1.0
 */

public class Borcherdt2004_SiteAmpCalc implements java.io.Serializable{

  private EvenlyDiscretizedFunc ma_func, mv_func;

  public Borcherdt2004_SiteAmpCalc() {

     ma_func = new EvenlyDiscretizedFunc(0.1,0.4,4);
//for(int i = 0; i < ma_func.getNum(); i++)
//  System.out.println(ma_func.getX(i));
     ma_func.set(0, 0.35);
     ma_func.set(1, 0.25);
     ma_func.set(2, 0.10);
     ma_func.set(3,-0.05);

     mv_func = new EvenlyDiscretizedFunc(0.1,0.4,4);
     mv_func.set(0, 0.65);
     mv_func.set(1, 0.60);
     mv_func.set(2, 0.53);
     mv_func.set(3, 0.45);

  }

  /**
   * This returns the short-period amplification factor
   * @param vs30 - 30-meter-average shear wave velocity (m/sec)
   * @param vs30_ref - reference Vs30
   * @param pga - peak ground acceleration (g)
   * @return
   */
  public double getShortPeriodAmp(double vs30, double vs30_ref, double pga){
    String S = ".getMMI()";

    // set ma
    double ma;
    if(pga <= 0.1)
      ma = ma_func.getY(0);
    else if (pga >= 0.4)
      ma = ma_func.getY(3);
    else
      ma = ma_func.getInterpolatedY(pga);

//System.out.println("shPer"+"\t"+vs30+"\t"+pga+"\t"+ma+"\t"+Math.pow(vs30_ref/vs30,ma));
    return Math.pow(vs30_ref/vs30,ma);
 }


 /**
  * This returns the mid-period amplification factor
  * @param vs30 - 30-meter-average shear wave velocity (m/sec)
  * @param vs30_ref - reference Vs30
  * @param pga - peak ground acceleration (g)
  * @return
  */
 public double getMidPeriodAmp(double vs30, double vs30_ref, double pga){
   String S = ".getMMI()";

   // set mv
   double mv;
   if(pga <= 0.1)
     mv = mv_func.getY(0);
   else if (pga >= 0.4)
     mv = mv_func.getY(3);
   else
     mv = mv_func.getInterpolatedY(pga);

//System.out.println("midPer"+"\t"+vs30+"\t"+pga+"\t"+mv+"\t"+Math.pow(vs30_ref/vs30,mv));
   return Math.pow(vs30_ref/vs30,mv);
}

/* this check the calculations against the ShakeMap (2003) Atten. Rel. Values (all are good)
  public static void main(String[] args) {

    Borcherdt2004_SiteAmpCalc calc = new Borcherdt2004_SiteAmpCalc();

    System.out.print(calc.getShortPeriodAmp(163.0,686.0,0.1)+"  ");
    System.out.print(calc.getShortPeriodAmp(163.0,686.0,0.2)+"  ");
    System.out.print(calc.getShortPeriodAmp(163.0,686.0,0.3)+"  ");
    System.out.print(calc.getShortPeriodAmp(163.0,686.0,0.4)+"  ");
    System.out.print("\n");
    System.out.print(calc.getShortPeriodAmp(298.0,686.0,0.1)+"  ");
    System.out.print(calc.getShortPeriodAmp(298.0,686.0,0.2)+"  ");
    System.out.print(calc.getShortPeriodAmp(298.0,686.0,0.3)+"  ");
    System.out.print(calc.getShortPeriodAmp(298.0,686.0,0.4)+"  ");
    System.out.print("\n");
    System.out.print(calc.getShortPeriodAmp(301.0,686.0,0.1)+"  ");
    System.out.print(calc.getShortPeriodAmp(301.0,686.0,0.2)+"  ");
    System.out.print(calc.getShortPeriodAmp(301.0,686.0,0.3)+"  ");
    System.out.print(calc.getShortPeriodAmp(301.0,686.0,0.4)+"  ");
    System.out.print("\n");
    System.out.print(calc.getShortPeriodAmp(372.0,686.0,0.1)+"  ");
    System.out.print(calc.getShortPeriodAmp(372.0,686.0,0.2)+"  ");
    System.out.print(calc.getShortPeriodAmp(372.0,686.0,0.3)+"  ");
    System.out.print(calc.getShortPeriodAmp(372.0,686.0,0.4)+"  ");
    System.out.print("\n");
    System.out.print(calc.getShortPeriodAmp(464.0,686.0,0.1)+"  ");
    System.out.print(calc.getShortPeriodAmp(464.0,686.0,0.2)+"  ");
    System.out.print(calc.getShortPeriodAmp(464.0,686.0,0.3)+"  ");
    System.out.print(calc.getShortPeriodAmp(464.0,686.0,0.4)+"  ");
    System.out.print("\n");
    System.out.print(calc.getShortPeriodAmp(724.0,686.0,0.1)+"  ");
    System.out.print(calc.getShortPeriodAmp(724.0,686.0,0.2)+"  ");
    System.out.print(calc.getShortPeriodAmp(724.0,686.0,0.3)+"  ");
    System.out.print(calc.getShortPeriodAmp(724.0,686.0,0.4)+"  ");
    System.out.print("\n");
    System.out.print(calc.getShortPeriodAmp(686.0,686.0,0.1)+"  ");
    System.out.print(calc.getShortPeriodAmp(686.0,686.0,0.2)+"  ");
    System.out.print(calc.getShortPeriodAmp(686.0,686.0,0.3)+"  ");
    System.out.print(calc.getShortPeriodAmp(686.0,686.0,0.4)+"  ");
    System.out.print("\n");
    System.out.print("\n");

    System.out.print(calc.getMidPeriodAmp(163.0,686.0,0.1)+"  ");
    System.out.print(calc.getMidPeriodAmp(163.0,686.0,0.2)+"  ");
    System.out.print(calc.getMidPeriodAmp(163.0,686.0,0.3)+"  ");
    System.out.print(calc.getMidPeriodAmp(163.0,686.0,0.4)+"  ");
    System.out.print("\n");
    System.out.print(calc.getMidPeriodAmp(298.0,686.0,0.1)+"  ");
    System.out.print(calc.getMidPeriodAmp(298.0,686.0,0.2)+"  ");
    System.out.print(calc.getMidPeriodAmp(298.0,686.0,0.3)+"  ");
    System.out.print(calc.getMidPeriodAmp(298.0,686.0,0.4)+"  ");
    System.out.print("\n");
    System.out.print(calc.getMidPeriodAmp(301.0,686.0,0.1)+"  ");
    System.out.print(calc.getMidPeriodAmp(301.0,686.0,0.2)+"  ");
    System.out.print(calc.getMidPeriodAmp(301.0,686.0,0.3)+"  ");
    System.out.print(calc.getMidPeriodAmp(301.0,686.0,0.4)+"  ");
    System.out.print("\n");
    System.out.print(calc.getMidPeriodAmp(372.0,686.0,0.1)+"  ");
    System.out.print(calc.getMidPeriodAmp(372.0,686.0,0.2)+"  ");
    System.out.print(calc.getMidPeriodAmp(372.0,686.0,0.3)+"  ");
    System.out.print(calc.getMidPeriodAmp(372.0,686.0,0.4)+"  ");
    System.out.print("\n");
    System.out.print(calc.getMidPeriodAmp(464.0,686.0,0.1)+"  ");
    System.out.print(calc.getMidPeriodAmp(464.0,686.0,0.2)+"  ");
    System.out.print(calc.getMidPeriodAmp(464.0,686.0,0.3)+"  ");
    System.out.print(calc.getMidPeriodAmp(464.0,686.0,0.4)+"  ");
    System.out.print("\n");
    System.out.print(calc.getMidPeriodAmp(724.0,686.0,0.1)+"  ");
    System.out.print(calc.getMidPeriodAmp(724.0,686.0,0.2)+"  ");
    System.out.print(calc.getMidPeriodAmp(724.0,686.0,0.3)+"  ");
    System.out.print(calc.getMidPeriodAmp(724.0,686.0,0.4)+"  ");
    System.out.print("\n");
    System.out.print(calc.getMidPeriodAmp(686.0,686.0,0.1)+"  ");
    System.out.print(calc.getMidPeriodAmp(686.0,686.0,0.2)+"  ");
    System.out.print(calc.getMidPeriodAmp(686.0,686.0,0.3)+"  ");
    System.out.print(calc.getMidPeriodAmp(686.0,686.0,0.4)+"  ");

  }
*/
}
