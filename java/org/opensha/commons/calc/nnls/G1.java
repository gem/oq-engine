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

package org.opensha.commons.calc.nnls;


import org.netlib.util.Dsign;
import org.netlib.util.doubleW;


class G1 {

// C      IMPLICIT DOUBLE PRECISION (A-H,O-Z) 
// C$$$$$ CALLS NO OTHER ROUTINES 
// C 
// C 
// C 
// C 
// C  FROM LAWSON+HANSON -SOLVING LEAST SQUARES PROBLEMS- 1974 P 309. 
// C  COMPUTES AN ORTHOGONAL MATRIX TO ROTATE (A,B) INTO (SQRT(A*A+B*B
// C  MATRIX IN FORM (COSA, SINA/-SINA, COSA) AND SIG HOLDS MAGNITUDE OF 
// C  (A,B).  SIG IS ALLOWED TO OVERWRITE A OR B IN CALLING ROUTINE. 
// C 
static double xr;
static double yr;

public static void g1 (double a,
double b,
doubleW cosa,
doubleW sina,
doubleW sig)  {

double as = Math.abs(a), bs = Math.abs(b);

if (as > bs)
{
xr = b/a;
yr = Math.sqrt(1.0+xr*xr);
cosa.val = (double)(Dsign.dsign(1.0/yr,a));
sina.val = cosa.val*xr;
sig.val = as*yr;
}
else
{
if (b==0)
{sig.val = 0.0;
 cosa.val = 0.0;
 sina.val = 1.0;
}
else
{
xr = a/b;
yr = Math.sqrt(1.0+xr*xr);
sina.val = (double)(Dsign.dsign(1.0/yr,b));
cosa.val = sina.val*xr;
sig.val = bs*yr;
}
}
}

} // End class.
