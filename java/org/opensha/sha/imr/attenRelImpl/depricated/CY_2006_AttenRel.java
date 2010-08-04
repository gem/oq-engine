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

package org.opensha.sha.imr.attenRelImpl.depricated;

import java.net.MalformedURLException;
import java.net.URL;
import java.util.HashMap;

import org.opensha.commons.data.NamedObjectAPI;
import org.opensha.commons.data.Site;
import org.opensha.commons.exceptions.InvalidRangeException;
import org.opensha.commons.exceptions.ParameterException;
import org.opensha.commons.param.DoubleConstraint;
import org.opensha.commons.param.DoubleDiscreteConstraint;
import org.opensha.commons.param.StringConstraint;
import org.opensha.commons.param.event.ParameterChangeEvent;
import org.opensha.commons.param.event.ParameterChangeListener;
import org.opensha.commons.param.event.ParameterChangeWarningListener;
import org.opensha.sha.earthquake.EqkRupture;
import org.opensha.sha.faultSurface.EvenlyGriddedSurfaceAPI;
import org.opensha.sha.imr.AttenuationRelationship;
import org.opensha.sha.imr.ScalarIntensityMeasureRelationshipAPI;
import org.opensha.sha.imr.param.EqkRuptureParams.DipParam;
import org.opensha.sha.imr.param.EqkRuptureParams.FaultTypeParam;
import org.opensha.sha.imr.param.EqkRuptureParams.MagParam;
import org.opensha.sha.imr.param.EqkRuptureParams.RupTopDepthParam;
import org.opensha.sha.imr.param.EqkRuptureParams.RupWidthParam;
import org.opensha.sha.imr.param.IntensityMeasureParams.DampingParam;
import org.opensha.sha.imr.param.IntensityMeasureParams.PGA_Param;
import org.opensha.sha.imr.param.IntensityMeasureParams.PeriodParam;
import org.opensha.sha.imr.param.IntensityMeasureParams.SA_Param;
import org.opensha.sha.imr.param.OtherParams.ComponentParam;
import org.opensha.sha.imr.param.OtherParams.StdDevTypeParam;
import org.opensha.sha.imr.param.PropagationEffectParams.DistRupMinusJB_OverRupParameter;
import org.opensha.sha.imr.param.PropagationEffectParams.DistanceRupParameter;
import org.opensha.sha.imr.param.SiteParams.Vs30_Param;

/**
 * <b>Title:</b> CY_2006_AttenRel<p>
 *
 * <b>Description:</b> This implements the Attenuation Relationship
 * developed by Chiou & Youngs (2006).  Their documentation is available at
 * http://peer.berkeley.edu/lifelines/nga_docs/nov_13_06/Chiou_Youngs_NGA_2006.html <p>
 *
 * Supported Intensity-Measure Parameters:  BELOW NEEDS TO BE UPDATED<p>
 * <UL>
 * <LI>pgaParam - Peak Ground Acceleration
 * <LI>saParam - Response Spectral Acceleration
 * </UL><p>
 * Other Independent Parameters:<p>
 * <UL>
 * <LI>magParam - moment Magnitude
 * <LI>fltTypeParam - Style of faulting
 * <LI>rupTopDepthParam - depth to top of rupture
 * <LI>dipParam - rupture surface dip
 * <LI>rupWidthParam - down dip width of rupture
 * <LI>distanceRupParam - closest distance to surface projection of fault
 * <li>distRupMinusJB_OverRupParam - used as a proxy for hanging wall effect
 * <LI>vs30Param 
 * <LI>componentParam - Component of shaking
 * <LI>stdDevTypeParam - The type of standard deviation
 * </UL></p>
 *<p>
 * NOTES: distRupMinusJB_OverRupParam is used rather than distancJBParameter because the latter 
 * should not be held constant when distanceRupParameter is changed (e.g., in the 
 * AttenuationRelationshipApplet).
 * <p>
 * Verification :This model has been tested with the data provided by Chiou and Young in their NGA report Table 6.
 * I took values as provided in the file and created a text file where each line has following info:<br>
 * Period (sec) 	M 	RRUP	 VS30	 RJB 	Width (km) 	FRV	 FNM	 ZTOR 	DIP	SA1130 (g) 	SA (g) <br>
 * Each element of the line is seperated by space. I read this file and provide the input parameters in
 * OpenSHA with these values. Then I compare the OpenSHA result with that given by Chiou and Young NGA report.
 * I am using JUnit testing to validate the implementation of the Chiou and Young model. One can run the JUnit test
 * and compare the OpenSHA results with the Chiou and Young NGA model. If any of the result show discrepancy then
 * JUnit test will fail. When it fails it will also show for which input parameters the test failed.
 * 
 *</p>
 * @author     Edward H. Field
 * @created    April, 2002
 * @version    1.0
 */


public class CY_2006_AttenRel
    extends AttenuationRelationship implements
    ScalarIntensityMeasureRelationshipAPI,
    NamedObjectAPI, ParameterChangeListener {

  // Debugging stuff
  private final static String C = "CY_2006_AttenRel";
  private final static boolean D = false;

  // Name of IMR
  public final static String NAME = "Chiou & Youngs (2006)";
  public final static String SHORT_NAME = "CY2006";
  private static final long serialVersionUID = 1234567890987654360L;


  // coefficients:
  private double[] period = {
		  0.01,0.02,0.022,0.025,0.029,0.03,0.032,0.035,0.036,0.04,0.042,0.044,0.045,0.046,
		  0.048,0.05,0.055,0.06,0.065,0.067,0.07,0.075,0.08,0.085,0.09,0.095,0.1,0.11,0.12,0.13,0.133,0.14,0.15,
		  0.16,0.17,0.18,0.19,0.2,0.22,0.24,0.25,0.26,0.28,0.29,0.3,0.32,0.34,0.35,0.36,0.38,0.4,0.42,0.44,
		  0.45,0.46,0.48,0.5,0.55,0.6,0.65,0.667,0.7,0.75,0.8,0.85,0.9,0.95,1,1.1,1.2,1.3,1.4,1.5,1.6,1.7,
		  1.8,1.9,2,2.2,2.4,2.5,2.6,2.8,3,3.2,3.4,3.5,3.6,3.8,4,4.2,4.4,4.6,4.8,5,5.5,6,6.5,7,7.5,8,8.5,9,9.5,10
		  };
 private double[] c1= {
		 -1.2686,-1.2474,-1.2308,-1.2064,-1.1716,-1.1622,-1.1432,-1.1136,-1.1032,-1.0598,-1.0341,-1.008,
		 -0.9961,-0.9845,-0.9606,-0.9363,-0.8686,-0.809,-0.7487,-0.7296,-0.7065,-0.6661,-0.6329,
		 -0.5993,-0.5678,-0.5408,-0.5207,-0.4899,-0.4535,-0.4365,-0.435,-0.4487,-0.4658,-0.4782,-0.4933,
		 -0.5191,-0.5455,-0.5698,-0.6372,-0.7017,-0.7267,-0.7519,-0.8115,-0.8394,-0.8667,-0.9306,-0.9978,
		 -1.0268,-1.0589,-1.1152,-1.1649,-1.2189,-1.2742,-1.2996,-1.3257,-1.3752,-1.4201,-1.5247,-1.6343,-1.7303,
		 -1.764,-1.8214,-1.8933,-1.9712,-2.0411,-2.1069,-2.1716,-2.2326,-2.3433,-2.4313,-2.5399,-2.6311,-2.7212,-2.8125,
		 -2.8974,-2.9774,-3.0531,-3.1249,-3.2583,-3.3802,-3.4373,-3.4922,-3.596,-3.6926,-3.7829,-3.8678,-3.9084,-3.9478,
		 -4.0235,-4.0953,-4.1636,-4.2288,-4.291,-4.3506,-4.4077,-4.5412,-4.663,-4.775,-4.8788,-4.9754,-5.0657,-5.1506,
		 -5.2306,-5.3063,-5.382
 };
 private double[]  c1a= {
		 0.1,0.1,0.1,0.1,0.1,0.1,0.1,0.1,0.1,0.1,0.1,0.1,0.1,0.1,0.1,0.1,0.1,0.1,0.1,
		 0.1,0.1,0.1,0.1,0.1,0.1,0.1,0.1,0.1,0.1,0.1,0.1,0.1,0.1,0.1,0.1,0.1,0.1,0.1,0.1,
		 0.1,0.1,0.1,0.1,0.1,0.1,0.1,0.1,0.1,0.1,0.0994,0.0987,0.0978,0.0967,0.096,0.0951,
		 0.0931,0.0906,0.0828,0.0744,0.0652,0.0617,0.0547,0.0435,0.0323,0.0214,0.0112,0.0018,
		 -0.0068,-0.021,-0.0328,-0.0432,-0.0525,-0.0602,-0.0661,-0.0707,-0.0746,-0.0784,-0.0821,
		 -0.0886,-0.0932,-0.0948,-0.0961,-0.0982,-0.0999,-0.1,-0.1,-0.1,-0.1,-0.1,-0.1,-0.1,-0.1,
		 -0.1,-0.1,-0.1,-0.1,-0.1,-0.1,-0.1,-0.1,-0.1,-0.1,-0.1,-0.1,-0.1
 };
 private double[] c1b ={
		 -0.2554,-0.2554,-0.2554,-0.2554,-0.2554,-0.2554,-0.2554,-0.2554,-0.2554,-0.2554,
		 -0.2554,-0.2554,-0.2554,-0.2554,-0.2554,-0.2554,-0.2554,-0.2554,-0.2554,-0.2554,-0.2554,
		 -0.2554,-0.2554,-0.2554,-0.2554,-0.2554,-0.2554,-0.2554,-0.2554,-0.2554,-0.2554,-0.2554,
		 -0.2554,-0.2543,-0.2527,-0.2511,-0.2495,-0.2478,-0.2442,-0.2405,-0.2385,-0.2366,-0.2327,
		 -0.2308,-0.2288,-0.225,-0.2211,-0.2192,-0.2173,-0.2135,-0.2098,-0.2061,-0.2025,-0.2007,
		 -0.199,-0.1955,-0.192,-0.1839,-0.1768,-0.1705,-0.1686,-0.1651,-0.1603,-0.1562,-0.1525,
		 -0.1491,-0.1461,-0.1433,-0.1384,-0.1342,-0.1306,-0.1274,-0.1247,-0.1221,-0.1199,-0.1177,
		 -0.1158,-0.114,-0.1107,-0.108,-0.1067,-0.1056,-0.1036,-0.1019,-0.1006,-0.1,-0.1,-0.1,-0.1,-0.1,
		 -0.1,-0.1,-0.1,-0.1,-0.1,-0.1,-0.1,-0.1,-0.1,-0.1,-0.1,-0.1,-0.1,-0.1,-0.1
 };
 private double[] c2={
		 1.06,1.06,1.06,1.06,1.06,1.06,1.06,1.06,1.06,1.06,1.06,1.06,1.06,1.06,1.06,1.06,
		 1.06,1.06,1.06,1.06,1.06,1.06,1.06,1.06,1.06,1.06,1.06,1.06,1.06,1.06,1.06,1.06,
		 1.06,1.06,1.06,1.06,1.06,1.06,1.06,1.06,1.06,1.06,1.06,1.06,1.06,1.06,1.06,1.06,
		 1.06,1.06,1.06,1.06,1.06,1.06,1.06,1.06,1.06,1.06,1.06,1.06,1.06,1.06,1.06,1.06,
		 1.06,1.06,1.06,1.06,1.06,1.06,1.06,1.06,1.06,1.06,1.06,1.06,1.06,1.06,1.06,1.06,
		 1.06,1.06,1.06,1.06,1.06,1.06,1.06,1.06,1.06,1.06,1.06,1.06,1.06,1.06,1.06,1.06,
		 1.06,1.06,1.06,1.06,1.06,1.06,1.06,1.06,1.06
 };
 private double[] c3={
		 3.45,3.45,3.45,3.45,3.45,3.45,3.45,3.45,3.45,3.45,3.45,3.45,3.45,3.45,3.45,3.45,3.45,
		 3.45,3.45,3.45,3.45,3.45,3.45,3.45,3.45,3.45,3.45,3.45,3.45,3.45,3.45,3.45,3.45,3.45,
		 3.45,3.45,3.45,3.45,3.45,3.45,3.45,3.45,3.45,3.45,3.45,3.45,3.45,3.45,3.45,3.45,3.45,
		 3.45,3.45,3.45,3.45,3.45,3.45,3.45,3.45,3.45,3.45,3.45,3.45,3.45,3.45,3.45,3.45,3.45,
		 3.45,3.45,3.45,3.45,3.45,3.45,3.45,3.45,3.45,3.45,3.45,3.45,3.45,3.45,3.45,3.45,3.45,
		 3.45,3.45,3.45,3.45,3.45,3.45,3.45,3.45,3.45,3.45,3.45,3.45,3.45,3.45,3.45,3.45,3.45,3.45,3.45,3.45
 };
 private double[] cn={
		 2.996,3.292,3.352,3.429,3.501,3.514,3.533,3.551,3.555,3.563,3.563,3.561,3.559,3.557,3.553,
		 3.547,3.531,3.513,3.493,3.484,3.471,3.448,3.423,3.397,3.369,3.341,3.312,3.255,3.199,3.145,
		 3.129,3.093,3.044,2.997,2.952,2.91,2.87,2.831,2.76,2.692,2.658,2.626,2.564,2.533,2.505,2.449,
		 2.397,2.372,2.348,2.303,2.261,2.222,2.185,2.167,2.15,2.118,2.087,2.017,1.957,1.904,1.887,1.855,
		 1.812,1.773,1.737,1.704,1.675,1.648,1.605,1.572,1.546,1.526,1.511,1.498,1.489,1.481,1.474,1.47,1.463,
		 1.458,1.456,1.456,1.455,1.456,1.457,1.458,1.459,1.461,1.463,1.465,1.468,1.47,1.473,1.475,1.478,1.483,1.488,
		 1.492,1.496,1.498,1.499,1.5,1.501,1.501,1.502
 };
 private double[] cM= {
		 4.184,4.188,4.183,4.173,4.159,4.156,4.148,4.138,4.135,4.123,4.117,4.112,4.11,4.108,4.104,4.101,
		 4.094,4.089,4.087,4.086,4.086,4.086,4.087,4.09,4.094,4.099,4.103,4.114,4.128,4.142,4.146,4.156,
		 4.172,4.187,4.202,4.217,4.232,4.248,4.276,4.304,4.318,4.332,4.358,4.371,4.384,4.409,4.432,4.444,
		 4.456,4.477,4.498,4.517,4.536,4.545,4.554,4.571,4.588,4.627,4.663,4.696,4.707,4.728,4.757,4.785,
		 4.811,4.836,4.86,4.882,4.925,4.964,5.001,5.037,5.07,5.102,5.133,5.162,5.191,5.217,5.269,5.317,5.339,
		 5.361,5.401,5.439,5.474,5.507,5.523,5.538,5.569,5.598,5.625,5.652,5.678,5.703,5.728,5.786,5.84,5.892,
		 5.942,5.989,6.034,6.077,6.117,6.156,6.193
 };
  private double[] c4 ={
		  -2.1,-2.1,-2.1,-2.1,-2.1,-2.1,-2.1,-2.1,-2.1,-2.1,-2.1,-2.1,-2.1,-2.1,-2.1,-2.1,-2.1,-2.1,-2.1,-2.1,
		  -2.1,-2.1,-2.1,-2.1,-2.1,-2.1,-2.1,-2.1,-2.1,-2.1,-2.1,-2.1,-2.1,-2.1,-2.1,-2.1,-2.1,-2.1,-2.1,
		  -2.1,-2.1,-2.1,-2.1,-2.1,-2.1,-2.1,-2.1,-2.1,-2.1,-2.1,-2.1,-2.1,-2.1,-2.1,-2.1,-2.1,-2.1,-2.1,-2.1,
		  -2.1,-2.1,-2.1,-2.1,-2.1,-2.1,-2.1,-2.1,-2.1,-2.1,-2.1,-2.1,-2.1,-2.1,-2.1,-2.1,-2.1,-2.1,-2.1,-2.1,
		  -2.1,-2.1,-2.1,-2.1,-2.1,-2.1,-2.1,-2.1,-2.1,-2.1,-2.1,-2.1,-2.1,-2.1,-2.1,-2.1,-2.1,-2.1,-2.1,-2.1,-2.1,
		  -2.1,-2.1,-2.1,-2.1,-2.1
  };
  private double[] c4a ={
		  -0.5,-0.5,-0.5,-0.5,-0.5,-0.5,-0.5,-0.5,-0.5,-0.5,-0.5,-0.5,-0.5,-0.5,-0.5,-0.5,-0.5,-0.5,-0.5,-0.5,-0.5,
		  -0.5,-0.5,-0.5,-0.5,-0.5,-0.5,-0.5,-0.5,-0.5,-0.5,-0.5,-0.5,-0.5,-0.5,-0.5,-0.5,-0.5,-0.5,-0.5,-0.5,-0.5,
		  -0.5,-0.5,-0.5,-0.5,-0.5,-0.5,-0.5,-0.5,-0.5,-0.5,-0.5,-0.5,-0.5,-0.5,-0.5,-0.5,-0.5,-0.5,-0.5,-0.5,-0.5,
		  -0.5,-0.5,-0.5,-0.5,-0.5,-0.5,-0.5,-0.5,-0.5,-0.5,-0.5,-0.5,-0.5,-0.5,-0.5,-0.5,-0.5,-0.5,-0.5,-0.5,-0.5,
		  -0.5,-0.5,-0.5,-0.5,-0.5,-0.5,-0.5,-0.5,-0.5,-0.5,-0.5,-0.5,-0.5,-0.5,-0.5,-0.5,-0.5,-0.5,-0.5,-0.5,-0.5
  };
  private double[] cRB ={
		  50,50,50,50,50,50,50,50,50,50,50,50,50,50,50,50,50,50,50,50,50,50,50,50,50,50,50,50,50,50,50,50,50,50,50,50,
		  50,50,50,50,50,50,50,50,50,50,50,50,50,50,50,50,50,50,50,50,50,50,50,50,50,50,50,50,50,50,50,50,50,50,50,50,
		  50,50,50,50,50,50,50,50,50,50,50,50,50,50,50,50,50,50,50,50,50,50,50,50,50,50,50,50,50,50,50,50,50
  };
  private double[] c5={
		  6.16,6.158,6.158,6.159,6.16,6.16,6.16,6.16,6.16,6.16,6.16,6.16,6.16,6.16,6.16,6.16,6.16,6.157,6.151,6.149,
		  6.145,6.137,6.128,6.118,6.107,6.094,6.082,6.055,6.028,6,5.992,5.972,5.946,5.92,5.896,5.873,5.851,5.83,5.793,
		  5.758,5.742,5.726,5.695,5.68,5.665,5.636,5.608,5.595,5.581,5.555,5.531,5.507,5.484,5.473,5.463,5.444,5.425,
		  5.382,5.344,5.311,5.301,5.282,5.256,5.233,5.211,5.192,5.173,5.155,5.123,5.096,5.072,5.052,5.037,5.024,5.016,
		  5.01,5.006,5.003,5,5,5,5,5,5,5,5,5,5,5,5,5,5,5,5,5,5,5,5,5,5,5,5,5,5,5
  };
  private double[] c6={
		  0.4893,0.4893,0.4893,0.4893,0.4893,0.4893,0.4893,0.4893,0.4893,0.4893,0.4893,0.4893,0.4893,0.4893,
		  0.4893,0.4893,0.4893,0.4893,0.4893,0.4892,0.489,0.4886,0.4882,0.4878,0.4872,0.4867,0.4861,0.4849,0.4835,
		  0.4822,0.4818,0.481,0.4797,0.4784,0.4772,0.476,0.4749,0.4739,0.4721,0.4707,0.47,0.4694,0.4682,0.4676,0.4671,
		  0.466,0.4649,0.4644,0.4639,0.4629,0.4619,0.4609,0.4601,0.4597,0.4593,0.4586,0.4578,0.4564,0.4553,0.4544,0.4541,
		  0.4536,0.453,0.4525,0.4521,0.4517,0.4513,0.4511,0.4508,0.4506,0.4505,0.4505,0.4504,0.4504,0.4503,0.4503,0.4503,
		  0.4503,0.4502,0.4502,0.4502,0.4502,0.4501,0.4501,0.4501,0.4501,0.4501,0.4501,0.45,0.45,0.45,0.45,0.45,0.45,0.45,
		  0.45,0.45,0.45,0.45,0.45,0.45,0.45,0.45,0.45,0.45
  };
  private double[] cHM= {3,3,3,3,3,3,3,3,3,3,3,3,3,3,3,3,3,3,3,3,3,3,3,3,3,3,3,3,3,3,3,3,3,3,3,3,3,3,3,3,3,3,3,3,3,3,3,3,3,3,3,3,
		  3,3,3,3,3,3,3,3,3,3,3,3,3,3,3,3,3,3,3,3,3,3,3,3,3,3,3,3,3,3,3,3,3,3,3,3,3,3,3,3,3,3,3,3,3,3,3,3,3,3,3,3,3
  };
  private double[] c7={
		  0.0512,0.0512,0.0512,0.0512,0.0512,0.0511,0.0511,0.051,0.0509,0.0508,0.0507,0.0506,0.0506,0.0505,0.0505,0.0504,
		  0.0502,0.05,0.0499,0.0498,0.0497,0.0495,0.0494,0.0492,0.0491,0.049,0.0488,0.0486,0.0484,0.0482,0.0482,0.0481,
		  0.0479,0.0477,0.0476,0.0474,0.0473,0.0471,0.0468,0.0466,0.0464,0.0463,0.046,0.0459,0.0458,0.0455,0.0453,0.0452,
		  0.045,0.0448,0.0445,0.0442,0.0439,0.0437,0.0436,0.0432,0.0429,0.0421,0.0412,0.0404,0.0401,0.0395,0.0387,0.0379,
		  0.0372,0.0364,0.0357,0.035,0.0336,0.0322,0.0308,0.0294,0.028,0.0266,0.0253,0.024,0.0226,0.0214,0.0188,0.0165,0.0154,
		  0.0143,0.0124,0.0106,0.009,0.0076,0.0069,0.0063,0.0052,0.0041,0.0033,0.0025,0.0019,0.0014,0.001,0.0002,0,0,0,0,0,0,0,0,0
  };
  private double[] c9 ={
		  1.048,1.083,1.099,1.125,1.157,1.165,1.177,1.194,1.199,1.215,1.221,1.227,1.229,1.232,1.235,1.238,1.244,1.248,1.249,
		  1.25,1.25,1.249,1.248,1.245,1.243,1.239,1.235,1.226,1.215,1.204,1.201,1.193,1.182,1.17,1.159,1.147,1.136,1.124,
		  1.102,1.081,1.07,1.059,1.039,1.029,1.019,1,0.9813,0.9722,0.9632,0.9458,0.9288,0.9123,0.8963,0.8885,0.8809,0.8658,
		  0.8513,0.8167,0.7846,0.7542,0.7443,0.7256,0.6982,0.6721,0.6471,0.6229,0.5996,0.5771,0.5346,0.4951,0.4584,0.4244,
		  0.393,0.3639,0.3369,0.312,0.2889,0.2675,0.2294,0.1965,0.1818,0.168,0.1431,0.121,0.1016,0.0846,0.0769,0.0698,0.0569,
		  0.0459,0.0364,0.0283,0.0213,0.0154,0.0104,0.0012,0,0,0,0,0,0,0,0,0
  };
  private double[] gamma1={
		  -0.00804,-0.008113,-0.008155,-0.00823,-0.008351,-0.008387,-0.008454,-0.008564,-0.008599,-0.008754,-0.008833,-0.008906,
		  -0.008945,-0.008984,-0.00905,-0.009121,-0.009288,-0.009433,-0.009561,-0.009603,-0.009656,-0.009733,-0.009782,-0.009808,
		  -0.009809,-0.009788,-0.009753,-0.009627,-0.00946,-0.009269,-0.009205,-0.009054,-0.008832,-0.00861,-0.008398,
		  -0.008183,-0.007976,-0.007776,-0.007397,-0.007044,-0.006877,-0.006715,-0.006408,-0.006263,-0.006123,-0.005859,-0.005614,
		  -0.005497,-0.005386,-0.005175,-0.00498,-0.004799,-0.004632,-0.004552,-0.004477,-0.004332,-0.004199,-0.003903,-0.003652,
		  -0.003435,-0.003368,-0.003246,-0.003078,-0.002929,-0.002795,-0.002674,-0.002564,-0.002464,-0.002287,-0.002138,-0.00201,
		  -0.001898,-0.001802,-0.001717,-0.001643,-0.001578,-0.001519,-0.001467,-0.001381,-0.001311,-0.001281,-0.001255,-0.001209,
		  -0.001172,-0.001142,-0.001117,-0.001106,-0.001096,-0.001079,-0.001065,-0.001052,-0.001042,-0.001032,-0.001024,-0.001016,
		  -0.000999,-0.000987,-0.000977,-0.000968,-0.000961,-0.000955,-0.00095,-0.000945,-0.000941,-0.000937
  };
  private double[] gamma2={
		  -0.00785,-0.007921,-0.007962,-0.008035,-0.008154,-0.008189,-0.008255,-0.008362,-0.008396,-0.008547,-0.008624,
		  -0.008696,-0.008734,-0.008771,-0.008836,-0.008906,-0.009068,-0.00921,-0.009335,-0.009376,-0.009428,-0.009503,
		  -0.00955,-0.009577,-0.009577,-0.009557,-0.009522,-0.0094,-0.009236,-0.00905,-0.008988,-0.00884,-0.008623,-0.008406,
		  -0.008199,-0.007989,-0.007787,-0.007592,-0.007222,-0.006878,-0.006714,-0.006556,-0.006257,-0.006115,-0.005979,-0.00572,
		  -0.005481,-0.005368,-0.005259,-0.005053,-0.004862,-0.004686,-0.004522,-0.004445,-0.004371,-0.00423,-0.0041,-0.003811,
		  -0.003565,-0.003354,-0.003288,-0.003169,-0.003005,-0.00286,-0.002729,-0.002611,-0.002504,-0.002406,-0.002233,-0.002087,
		  -0.001962,-0.001854,-0.001759,-0.001677,-0.001604,-0.00154,-0.001483,-0.001433,-0.001348,-0.00128,-0.001251,-0.001225,
		  -0.001181,-0.001145,-0.001115,-0.001091,-0.00108,-0.001071,-0.001054,-0.00104,-0.001027,-0.001017,-0.001007,-0.001,
		  -0.000992,-0.000976,-0.000964,-0.000954,-0.000945,-0.000938,-0.000933,-0.000927,-0.000923,-0.000919,-0.000914
  };
  private double[] gM={
		  4,4,4,4,4,4,4,4,4,4,4,4,4,4,4,4,4,4,4,4,4,4,4,4,4,4,4,4,4,4,4,4,4,4,4,4,4,4,4,4,4,4,4,4,4,4,4,4,4,4,4,4,
		  4,4,4,4,4,4,4,4,4,4,4,4,4,4,4,4,4,4,4,4,4,4,4,4,4,4,4,4,4,4,4,4,4,4,4,4,4,4,4,4,4,4,4,4,4,4,4,4,4,4,4,4,4
  };
  private double[] phi1={
		  -0.4823,-0.4723,-0.4691,-0.4639,-0.4566,-0.4548,-0.4513,-0.4463,-0.4447,-0.4385,-0.4357,-0.4331,-0.4318,
		  -0.4306,-0.4284,-0.4263,-0.4222,-0.4195,-0.4183,-0.4182,-0.4185,-0.4199,-0.4226,-0.4263,-0.431,-0.4363,
		  -0.4421,-0.4548,-0.4679,-0.4811,-0.485,-0.4939,-0.5061,-0.5176,-0.5283,-0.5385,-0.5479,-0.5568,-0.5731,
		  -0.5877,-0.5944,-0.6008,-0.6128,-0.6185,-0.6238,-0.6339,-0.6432,-0.6476,-0.6518,-0.6599,-0.6675,-0.6746,
		  -0.6813,-0.6845,-0.6876,-0.6937,-0.6995,-0.7128,-0.7248,-0.7357,-0.7393,-0.7458,-0.7551,-0.7637,-0.7718,
		  -0.7793,-0.7864,-0.7931,-0.8054,-0.8165,-0.8265,-0.8359,-0.8444,-0.8523,-0.8595,-0.8664,-0.8727,-0.8786,
		  -0.8891,-0.8981,-0.9021,-0.9057,-0.9122,-0.9173,-0.9215,-0.9246,-0.9259,-0.9268,-0.9282,-0.9286,-0.9281,
		  -0.9269,-0.9249,-0.9222,-0.9188,-0.9075,-0.8929,-0.8758,-0.8569,-0.837,-0.8165,-0.7959,-0.7757,-0.756,-0.7372
  };
  private double[] phi2={
		  -0.1928,-0.1895,-0.1909,-0.1941,-0.2006,-0.2026,-0.2071,-0.2144,-0.2169,-0.2275,-0.2329,-0.2383,-0.241,-0.2437,-0.2491,
		  -0.2544,-0.2671,-0.2789,-0.2895,-0.2934,-0.2987,-0.3066,-0.3132,-0.3187,-0.3231,-0.3266,-0.3293,-0.3328,-0.3343,-0.3343,
		  -0.3341,-0.3333,-0.3314,-0.3288,-0.3257,-0.3224,-0.3186,-0.3147,-0.306,-0.2967,-0.2919,-0.2868,-0.2765,-0.2713,-0.266,-0.2554,
		  -0.2449,-0.2396,-0.2344,-0.224,-0.2139,-0.2039,-0.1943,-0.1896,-0.185,-0.1761,-0.1676,-0.148,-0.1311,-0.1164,-0.112,-0.1039,
		  -0.0931,-0.08377,-0.07564,-0.06854,-0.06226,-0.05669,-0.04724,-0.0395,-0.03308,-0.02768,-0.02314,-0.01929,-0.01603,-0.01327,
		  -0.01092,-0.008925,-0.005808,-0.00358,-0.002728,-0.002017,-0.00093,-0.00019,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0
  };
  private double[] phi3={
		  -0.005911,-0.005864,-0.005817,-0.00573,-0.005578,-0.005533,-0.005451,-0.005316,-0.005274,-0.005087,-0.005002,
		  -0.004917,-0.004873,-0.004834,-0.004758,-0.004682,-0.004517,-0.004374,-0.004266,-0.004228,-0.004182,-0.00412,
		  -0.004079,-0.004058,-0.00405,-0.004058,-0.004075,-0.004136,-0.004228,-0.004348,-0.004383,-0.004476,-0.004617,
		  -0.004762,-0.004903,-0.005047,-0.005185,-0.005316,-0.005572,-0.005799,-0.005905,-0.006006,-0.006195,-0.006289,
		  -0.006371,-0.006532,-0.006678,-0.006745,-0.006812,-0.006943,-0.007055,-0.007162,-0.007263,-0.007314,-0.007365,
		  -0.007447,-0.007529,-0.007712,-0.007868,-0.008003,-0.008043,-0.008115,-0.008213,-0.008304,-0.008379,-0.008438,
		  -0.008497,-0.008548,-0.008626,-0.008695,-0.008747,-0.008791,-0.008818,-0.008835,-0.008862,-0.008871,-0.00888,
		  -0.00888,-0.008888,-0.008888,-0.008888,-0.008888,-0.008888,-0.008888,-0.008888,-0.00888,-0.00888,-0.00888,-0.00888,
		  -0.00888,-0.00888,-0.00888,-0.00888,-0.00888,-0.00888,-0.00888,-0.00888,-0.00888,-0.00888,-0.00888,-0.00888,-0.00888,
		  -0.00888,-0.00888,-0.00888
  };
  private double[] phi4 ={0.100359,0.103066,0.104269,0.106074,0.109583,0.110415,0.112089,0.114716,0.115598,0.120311,0.122617,
		  0.125023,0.126226,0.127429,0.129935,0.132442,0.138858,0.145375,0.151892,0.153998,0.158309,0.164525,0.17054,
		  0.176355,0.181769,0.186983,0.191795,0.200518,0.207736,0.213752,0.215456,0.218464,0.222073,0.22458,0.226284,
		  0.227086,0.227187,0.226685,0.224279,0.220469,0.218013,0.215557,0.209942,0.207035,0.204027,0.197811,0.191494,
		  0.188386,0.185278,0.179163,0.173147,0.167332,0.161718,0.159011,0.156304,0.15109,0.146177,0.134547,0.124221,
		  0.114997,0.11219,0.106776,0.099377,0.092739,0.086744,0.08133,0.076427,0.071956,0.064146,0.057579,0.051984,0.047192,
		  0.043041,0.039412,0.036234,0.033426,0.03094,0.028714,0.024924,0.021826,0.020553,0.01927,0.017114,0.0153,0.013745,
		  0.012402,0.011821,0.011239,0.010226,0.009334,0.008552,0.00785,0.007229,0.006677,0.006176,0.005133,0.004311,0.003659,
		  0.003128,0.002697,0.002346,0.002045,0.001795,0.001584,0.001404
  };
  private double[] tau ={
		  0.3024,0.3034,0.3089,0.3151,0.3235,0.3257,0.3303,0.3339,0.3346,0.3384,0.3432,0.3468,0.3476,
		  0.3493,0.3551,0.3634,0.3856,0.3913,0.4036,0.4092,0.4065,0.4101,0.412,0.4131,0.42,0.4243,0.423,
		  0.4126,0.4243,0.4088,0.4055,0.4012,0.3929,0.3778,0.3652,0.3526,0.338,0.3234,0.3189,0.3087,0.3075,0.3018,
		  0.2871,0.2876,0.2902,0.2836,0.2879,0.2931,0.2959,0.3009,0.3088,0.3175,0.3232,0.3215,0.3173,0.3063,0.3038,
		  0.3095,0.317,0.3205,0.3224,0.3203,0.3029,0.3086,0.2934,0.2999,0.3106,0.3165,0.3421,0.351,0.3494,0.3469,0.3513,
		  0.3591,0.3655,0.3735,0.381,0.3818,0.3764,0.3889,0.3896,0.4008,0.4099,0.4045,0.4127,0.4195,0.4162,0.4158,
		  0.4215,0.4287,0.4648,0.452,0.4443,0.4466,0.4405,0.4379,0.4245,0.4414,0.4585,0.4888,0.5105,0.3588,0.3597,0.3528,0.2934
  };
  private double[] sigma={
		  0.472,0.4736,0.4747,0.4769,0.4815,0.4822,0.4835,0.4865,0.4879,0.4925,0.4945,0.4957,0.4962,0.4968,0.4985,
		  0.4989,0.4998,0.5029,0.5027,0.5012,0.5036,0.5043,0.5068,0.5091,0.5092,0.5084,0.5104,0.5125,0.5148,0.515,
		  0.5141,0.5109,0.5096,0.5111,0.5117,0.5168,0.5182,0.5154,0.511,0.5123,0.5129,0.5159,0.5256,0.5303,0.5343,
		  0.5426,0.5429,0.5428,0.5408,0.537,0.5373,0.539,0.5395,0.5397,0.5398,0.5419,0.5461,0.5511,0.5614,0.5638,0.5652,
		  0.5661,0.5641,0.5621,0.5605,0.5578,0.554,0.5477,0.5442,0.5381,0.5383,0.5374,0.5379,0.544,0.5447,0.544,0.5413,
		  0.5439,0.546,0.5442,0.5431,0.5381,0.5321,0.5397,0.548,0.5524,0.5532,0.5549,0.5547,0.5563,0.5521,0.5609,0.5709,
		  0.5782,0.5837,0.5894,0.5997,0.611,0.6038,0.6048,0.6156,0.611,0.6264,0.6357,0.6445
  };
  private double[] totalsigma={
		  0.5606,0.5624,0.5664,0.5716,0.5801,0.5819,0.5855,0.5901,0.5916,0.5976,0.602,0.605,0.6059,0.6073,0.612,0.6172,0.6313,
		  0.6372,0.6447,0.647,0.6472,0.65,0.6532,0.6556,0.6601,0.6621,0.6629,0.6579,0.6672,0.6575,0.6547,0.6496,0.6435,
		  0.6356,0.6287,0.6256,0.6186,0.6085,0.6024,0.5981,0.5981,0.5977,0.5989,0.6032,0.6081,0.6123,0.6145,0.6169,0.6165,
		  0.6155,0.6197,0.6255,0.6288,0.6282,0.6261,0.6224,0.6249,0.632,0.6447,0.6485,0.6507,0.6504,0.6403,0.6412,0.6326,
		  0.6333,0.6352,0.6326,0.6428,0.6425,0.6418,0.6397,0.6424,0.6518,0.6559,0.6599,0.6619,0.6645,0.6632,0.6689,0.6684,
		  0.6709,0.6717,0.6744,0.686,0.6937,0.6922,0.6934,0.6967,0.7023,0.7217,0.7204,0.7234,0.7306,0.7313,0.7343,0.7348,
		  0.7538,0.7582,0.7776,0.7997,0.7085,0.7223,0.7271,0.7081
  };
  protected final static Double PERIOD_DEFAULT = new Double(1.0);
  private HashMap indexFromPerHashMap;

  private int iper;
  private double vs30, rRup, distanceJB, distRupMinusJB_OverRup, dip, mag, f_rv, f_nm, depthTop,ruptureWidth;
  private String stdDevType;
  private boolean parameterChange;

  // from page 66 of their report
  protected final static Double MAG_WARN_MIN = new Double(4.);
  protected final static Double MAG_WARN_MAX = new Double(8.5);
  protected final static Double DISTANCE_RUP_WARN_MIN = new Double(0.0);
  protected final static Double DISTANCE_RUP_WARN_MAX = new Double(200.0);
  protected final static Double DISTANCE_MINUS_WARN_MIN = new Double(0.0);
  protected final static Double DISTANCE_MINUS_WARN_MAX = new Double(50.0);
  protected final static Double VS30_WARN_MIN = new Double(150.0);
  protected final static Double VS30_WARN_MAX = new Double(1500.0);
  protected final static Double RUP_TOP_WARN_MIN = new Double(0);
  protected final static Double RUP_TOP_WARN_MAX = new Double(20);
  
  // style of faulting options
  public final static String FLT_TYPE_STRIKE_SLIP = "Strike-Slip";
  public final static String FLT_TYPE_REVERSE = "Reverse";
  public final static String FLT_TYPE_NORMAL = "Normal";
 
  // for issuing warnings:
  private transient ParameterChangeWarningListener warningListener = null;

  /**
   *  This initializes several ParameterList objects.
   */
  public CY_2006_AttenRel(ParameterChangeWarningListener warningListener) {

    super();

    this.warningListener = warningListener;

    initSupportedIntensityMeasureParams();
    indexFromPerHashMap = new HashMap();
    for (int i = 0; i < period.length; i++) {
      indexFromPerHashMap.put(new Double(period[i]), new Integer(i));
    }

    initEqkRuptureParams();
    initPropagationEffectParams();
    initSiteParams();
    initOtherParams();

    initIndependentParamLists(); // This must be called after the above
    initParameterEventListeners(); //add the change listeners to the parameters

  }

  /**
   *  This sets the eqkRupture related parameters (magParam
   *  and fltTypeParam) based on the eqkRupture passed in.
   *  The internally held eqkRupture object is also set as that
   *  passed in.  Warning constrains are ingored.
   *
   * @param  eqkRupture  The new eqkRupture value
   * @throws InvalidRangeException thrown if rake is out of bounds
   */
  public void setEqkRupture(EqkRupture eqkRupture) throws InvalidRangeException {
	  
	  magParam.setValueIgnoreWarning(new Double(eqkRupture.getMag()));
	  
	  double rake = eqkRupture.getAveRake();
	  if(rake >30 && rake <150) {
		  fltTypeParam.setValue(FLT_TYPE_REVERSE);
	  }
	  else if(rake >-120 && rake<-60) {
		  fltTypeParam.setValue(FLT_TYPE_NORMAL);
	  }
	  else { // strike slip
		  fltTypeParam.setValue(FLT_TYPE_STRIKE_SLIP);
	  }    
	  
	  EvenlyGriddedSurfaceAPI surface = eqkRupture.getRuptureSurface();
	  dipParam.setValue(surface.getAveDip());
	  double depth = surface.getLocation(0, 0).getDepth();
	  rupTopDepthParam.setValue(depth);
	  double rupDownDipWidth = eqkRupture.getRuptureSurface().getSurfaceWidth();
	  if(rupDownDipWidth ==0)
		  rupDownDipWidth = 1;
	  rupWidthParam.setValue(rupDownDipWidth);
//	  setFaultTypeFromRake(eqkRupture.getAveRake());
	  this.eqkRupture = eqkRupture;
	  setPropagationEffectParams();
	  
  }

  /**
   *  This sets the site-related parameter (siteTypeParam) based on what is in
   *  the Site object passed in (the Site object must have a parameter with
   *  the same name as that in siteTypeParam).  This also sets the internally held
   *  Site object as that passed in.
   *
   * @param  site             The new site object
   * @throws ParameterException Thrown if the Site object doesn't contain a
   * Vs30 parameter
   */
  public void setSite(Site site) throws ParameterException {

    vs30Param.setValue((Double)site.getParameter(Vs30_Param.NAME).getValue());
    this.site = site;
    setPropagationEffectParams();

  }

  /**
   * This sets the two propagation-effect parameters (distanceRupParam and
   * isOnHangingWallParam) based on the current site and eqkRupture.  The
   * hanging-wall term is rake independent (i.e., it can apply to strike-slip or
   * normal faults as well as reverse and thrust).  However, it is turned off if
   * the dip is greater than 70 degrees.  It is also turned off for point sources
   * regardless of the dip.  These specifications were determined from a series of
   * discussions between Ned Field, Norm Abrahamson, and Ken Campbell.
   */
  protected void setPropagationEffectParams() {

    if ( (this.site != null) && (this.eqkRupture != null)) {

      distanceRupParam.setValue(eqkRupture, site);
      distRupMinusJB_OverRupParam.setValue(eqkRupture, site);

    }
  }

  
  
  /**
   * This function returns the array index for the coeffs corresponding to the chosen IMT
   */
  protected void setCoeffIndex() throws ParameterException {

    // Check that parameter exists
    if (im == null) {
      throw new ParameterException(C +
                                   ": updateCoefficients(): " +
                                   "The Intensity Measusre Parameter has not been set yet, unable to process."
          );
    }

    if (im.getName().equalsIgnoreCase(SA_Param.NAME)) {
      iper = ( (Integer) indexFromPerHashMap.get(saPeriodParam.getValue())).
          intValue();
    }
    else {
      iper = 0;
    }
    parameterChange = true;
    intensityMeasureChanged = false;

  }

  /**
   * Calculates the mean of the exceedence probability distribution. <p>
   * @return    The mean value
   */
  public double getMean() {
	  
	  // check if distance is beyond the user specified max
	  if (rRup > USER_MAX_DISTANCE) {
		  return VERY_SMALL_MEAN;
	  }
	  
	  if (intensityMeasureChanged) {
		  setCoeffIndex();// intensityMeasureChanged is set to false in this method
	  }
	  
	  // compute rJB
	  distanceJB = rRup - distRupMinusJB_OverRup*rRup;
	  
	  //please uncomment the below commented code to test the Ken's CY06 model because he assume if
	  //mean of any SA Period less then of equal to 0.2 is below PGA then PGA value should be used, same 
	  // thing as he assumes for his relationship.
	  //if(iper < 1 || iper > 38)
	    return getMean(iper, vs30, f_rv, f_nm, rRup, distanceJB, ruptureWidth, dip, mag, depthTop);
	 // else{
		//  double pga_mean = getMean(0, vs30, f_rv, f_nm, rRup, distanceJB, ruptureWidth, dip, mag, depthTop);
		 // double mean = getMean(iper, vs30, f_rv, f_nm, rRup, distanceJB, ruptureWidth, dip, mag, depthTop);
		 // return Math.max(pga_mean, mean);
	 // }
  }

  /**
   * @return    The stdDev value
   */
  public double getStdDev() {
    if (intensityMeasureChanged) {
      setCoeffIndex();// intensityMeasureChanged is set to false in this method
    }

    return getStdDev(iper, stdDevType);
  }

  /**
   * Allows the user to set the default parameter values for the selected Attenuation
   * Relationship.
   */
  public void setParamDefaults() {

    vs30Param.setValueAsDefault();
    magParam.setValueAsDefault();
    fltTypeParam.setValueAsDefault();
	dipParam.setValueAsDefault();
    rupTopDepthParam.setValueAsDefault();
    distanceRupParam.setValueAsDefault();
    distRupMinusJB_OverRupParam.setValueAsDefault();
    saParam.setValueAsDefault();
    saPeriodParam.setValueAsDefault();
    saDampingParam.setValueAsDefault();
    pgaParam.setValueAsDefault();
    componentParam.setValueAsDefault();
    stdDevTypeParam.setValueAsDefault();
	rupWidthParam.setValueAsDefault();
    
    vs30 = ( (Double) vs30Param.getValue()).doubleValue(); 
    mag = ( (Double) magParam.getValue()).doubleValue();
    stdDevType = (String) stdDevTypeParam.getValue();

  }

  /**
   * This creates the lists of independent parameters that the various dependent
   * parameters (mean, standard deviation, exceedance probability, and IML at
   * exceedance probability) depend upon. NOTE: these lists do not include anything
   * about the intensity-measure parameters or any of thier internal
   * independentParamaters.
   */
  protected void initIndependentParamLists() {

    // params that the mean depends upon
    meanIndependentParams.clear();
    meanIndependentParams.addParameter(distanceRupParam);
    meanIndependentParams.addParameter(distRupMinusJB_OverRupParam);
    meanIndependentParams.addParameter(vs30Param);
    meanIndependentParams.addParameter(magParam);
    meanIndependentParams.addParameter(fltTypeParam);
    meanIndependentParams.addParameter(dipParam);
    meanIndependentParams.addParameter(rupTopDepthParam);
    meanIndependentParams.addParameter(rupWidthParam);
    meanIndependentParams.addParameter(componentParam);

    // params that the stdDev depends upon
    stdDevIndependentParams.clear();
    stdDevIndependentParams.addParameter(stdDevTypeParam);
    stdDevIndependentParams.addParameter(componentParam);

    // params that the exceed. prob. depends upon
    exceedProbIndependentParams.clear();
    exceedProbIndependentParams.addParameterList(meanIndependentParams);
    exceedProbIndependentParams.addParameter(stdDevTypeParam);
    exceedProbIndependentParams.addParameter(sigmaTruncTypeParam);
    exceedProbIndependentParams.addParameter(sigmaTruncLevelParam);

    // params that the IML at exceed. prob. depends upon
    imlAtExceedProbIndependentParams.addParameterList(
        exceedProbIndependentParams);
    imlAtExceedProbIndependentParams.addParameter(exceedProbParam);
  }

  /**
   *  Creates the Site-Type parameter and adds it to the siteParams list.
   *  Makes the parameters noneditable.
   */
  protected void initSiteParams() {

	vs30Param = new Vs30_Param(VS30_WARN_MIN, VS30_WARN_MAX);

    siteParams.clear();
    siteParams.addParameter(vs30Param);

  }

  /**
   *  Creates the two Potential Earthquake parameters (magParam and
   *  fltTypeParam) and adds them to the eqkRuptureParams
   *  list. Makes the parameters noneditable.
   */
  protected void initEqkRuptureParams() {

	magParam = new MagParam(MAG_WARN_MIN, MAG_WARN_MAX);
	dipParam = new DipParam();
	rupTopDepthParam = new RupTopDepthParam(RUP_TOP_WARN_MIN, RUP_TOP_WARN_MAX);
	rupWidthParam = new RupWidthParam();
    
    StringConstraint constraint = new StringConstraint();
    constraint.addString(FLT_TYPE_STRIKE_SLIP);
    constraint.addString(FLT_TYPE_NORMAL);
    constraint.addString(FLT_TYPE_REVERSE);
    constraint.setNonEditable();
    fltTypeParam = new FaultTypeParam(constraint,FLT_TYPE_STRIKE_SLIP);

    
    eqkRuptureParams.clear();
    eqkRuptureParams.addParameter(magParam);
    eqkRuptureParams.addParameter(dipParam);
    eqkRuptureParams.addParameter(fltTypeParam);
    eqkRuptureParams.addParameter(rupTopDepthParam);
    eqkRuptureParams.addParameter(rupWidthParam);
  }

  /**
   *  Creates the Propagation Effect parameters and adds them to the
   *  propagationEffectParams list. Makes the parameters noneditable.
   */
  protected void initPropagationEffectParams() {

    distanceRupParam = new DistanceRupParameter(0.0);
    distanceRupParam.addParameterChangeWarningListener(warningListener);
    DoubleConstraint warn = new DoubleConstraint(DISTANCE_RUP_WARN_MIN,
                                                 DISTANCE_RUP_WARN_MAX);
    warn.setNonEditable();
    distanceRupParam.setWarningConstraint(warn);
    distanceRupParam.setNonEditable();

    //create distRupMinusJB_OverRupParam
    distRupMinusJB_OverRupParam = new DistRupMinusJB_OverRupParameter(0.0);
    DoubleConstraint warn2 = new DoubleConstraint(DISTANCE_MINUS_WARN_MIN, DISTANCE_MINUS_WARN_MAX);
    distRupMinusJB_OverRupParam.addParameterChangeWarningListener(warningListener);
    warn.setNonEditable();
    distRupMinusJB_OverRupParam.setWarningConstraint(warn2);
    distRupMinusJB_OverRupParam.setNonEditable();
    
    propagationEffectParams.addParameter(distanceRupParam);
    propagationEffectParams.addParameter(distRupMinusJB_OverRupParam);

  }

  /**
   *  Creates the two supported IM parameters (PGA and SA), as well as the
   *  independenParameters of SA (periodParam and dampingParam) and adds
   *  them to the supportedIMParams list. Makes the parameters noneditable.
   */
  protected void initSupportedIntensityMeasureParams() {

    // Create saParam:
    DoubleDiscreteConstraint periodConstraint = new DoubleDiscreteConstraint();
    for (int i = 0; i < period.length; i++) {
      periodConstraint.addDouble(new Double(period[i]));
    }
    periodConstraint.setNonEditable();
	saPeriodParam = new PeriodParam(periodConstraint);
	saDampingParam = new DampingParam();
	saParam = new SA_Param(saPeriodParam, saDampingParam);
	saParam.setNonEditable();

	//  Create PGA Parameter (pgaParam):
	pgaParam = new PGA_Param();
	pgaParam.setNonEditable();

    // Add the warning listeners:
    saParam.addParameterChangeWarningListener(warningListener);
    pgaParam.addParameterChangeWarningListener(warningListener);

    // Put parameters in the supportedIMParams list:
    supportedIMParams.clear();
    supportedIMParams.addParameter(saParam);
    supportedIMParams.addParameter(pgaParam);

  }

  /**
   *  Creates other Parameters that the mean or stdDev depends upon,
   *  such as the Component or StdDevType parameters.
   */
  protected void initOtherParams() {

    // init other params defined in parent class
    super.initOtherParams();

    // the Component Parameter
    StringConstraint constraint = new StringConstraint();
    constraint.addString(ComponentParam.COMPONENT_GMRotI50);
    constraint.setNonEditable();
    componentParam = new ComponentParam(constraint,ComponentParam.COMPONENT_GMRotI50);

    // the stdDevType Parameter
    StringConstraint stdDevTypeConstraint = new StringConstraint();
    stdDevTypeConstraint.addString(StdDevTypeParam.STD_DEV_TYPE_TOTAL);
    stdDevTypeConstraint.addString(StdDevTypeParam.STD_DEV_TYPE_NONE);
    stdDevTypeConstraint.addString(StdDevTypeParam.STD_DEV_TYPE_INTER);
    stdDevTypeConstraint.addString(StdDevTypeParam.STD_DEV_TYPE_INTRA);
    stdDevTypeConstraint.setNonEditable();
    stdDevTypeParam = new StdDevTypeParam(stdDevTypeConstraint);

    // add these to the list
    otherParams.addParameter(componentParam);
    otherParams.addParameter(stdDevTypeParam);

  }

  /**
   * get the name of this IMR
   *
   * @returns the name of this IMR
   */
  public String getName() {
    return NAME;
  }

  /**
   * Returns the Short Name of each AttenuationRelationship
   * @return String
   */
  public String getShortName() {
    return SHORT_NAME;
  }

  /**
   * 
   * @param iper
   * @param vs30
   * @param f_rv
   * @param f_nm
   * @param distanceJB
   * @param ruptureWidth
   * @param dip
   * @param rake
   * @param mag
   * @param depthTop
   * @return
   */
  public double getMean(int iper, double vs30, double f_rv, double f_nm, double rRup, double distanceJB,
		  double ruptureWidth, double dip, double mag, double depthTop) {
	  	  
	  double cc = c5[iper]* Math.cosh(c6[iper] * Math.max(mag-cHM[iper],0));
	  
	  double gamma = gamma1[iper] + gamma2[iper]/Math.cosh(Math.max(mag-gM[iper],0));
	  
	  double pi = Math.atan(1.0)*4;
	  double d2r = pi/180;
	  double cosDELTA = Math.cos(dip*d2r);
	  
	  //Magnitude scaling
	  
	  double r1 = c1[iper] + c2[iper] * (mag-6.0) + ((c2[iper]-c3[iper])/cn[iper]) * Math.log(1.0 + Math.exp(-cn[iper]*(mag-cM[iper])));
	  
	  //Near-field magnitude and distance scaling
	  
	  double r2 = c4[iper] * Math.log(rRup + cc);
	  
	  // Distance scaling at large distance
	  
	  double r3 = ((c4a[iper]-c4[iper])/2.0) * Math.log( rRup*rRup +cRB[iper]*cRB[iper] ) + rRup * gamma;
	  
	  // More source scaling
	  
	  double r4 = c1a[iper]*f_rv +c1b[iper]*f_nm +c7[iper]*(depthTop - 4);
	  
	  //HW effect
	  double hw = c9[iper] * cosDELTA*cosDELTA * (1.0 -distanceJB/(rRup + 0.001)) *
	  Math.atan(ruptureWidth*0.5*cosDELTA/(depthTop+1))/(pi/2.0) * Math.tanh(0.5*rRup);
	  
	  
	  //  Predicted median Sa on reference condition (Vs=1130 m/sec)
	  double psa_ref = r1+r2+r3+r4+hw;
	  
	  // Linear soil amplification
	  double a = phi1[iper] * Math.min(Math.log(vs30/1130), 0);
	  
	  
	  //Nonlinear soil amplification
	  
	  double b = phi2[iper] *(Math.exp(phi3[iper]*(Math.min(vs30,1130)-360)) - Math.exp(phi3[iper]*(1130-360)));
	  
	  double c = phi4[iper];
	  
	  //Sa on soil condition
	  double psa = psa_ref + (a + b * Math.log((Math.exp(psa_ref)+c)/c));
	  
	  return psa;
  }
  
  
  
  public double getStdDev(int iper, String stdDevType) {
	  
	  if (stdDevType.equals(StdDevTypeParam.STD_DEV_TYPE_TOTAL))
		  return Math.sqrt(tau[iper] * tau[iper] + sigma[iper] * sigma[iper]);
	  else if (stdDevType.equals(StdDevTypeParam.STD_DEV_TYPE_NONE))
		  return 0;
	  else if (stdDevType.equals(StdDevTypeParam.STD_DEV_TYPE_INTRA))
		  return sigma[iper];
	  else if (stdDevType.equals(StdDevTypeParam.STD_DEV_TYPE_INTER))
		  return tau[iper];
	  else 
		  return Double.NaN;
  }

  /**
   * This listens for parameter changes and updates the primitive parameters accordingly
   * @param e ParameterChangeEvent
   */
  public void parameterChange(ParameterChangeEvent e) {
	  
	  String pName = e.getParameterName();
	  Object val = e.getNewValue();
	  parameterChange = true;
	  if (pName.equals(DistanceRupParameter.NAME)) {
		  rRup = ( (Double) val).doubleValue();
	  }
	  else if (pName.equals(DistRupMinusJB_OverRupParameter.NAME)) {
		  distRupMinusJB_OverRup = ( (Double) val).doubleValue();
	  }
	  else if (pName.equals(Vs30_Param.NAME)) {
		  vs30 = ( (Double) val).doubleValue();
	  }
	  else if (pName.equals(DipParam.NAME)) {
		  dip = ( (Double) val).doubleValue();
	  }
	  else if (pName.equals(magParam.NAME)) {
		  mag = ( (Double) val).doubleValue();
	  }
	  else if (pName.equals(FaultTypeParam.NAME)) {
		  String fltType = (String)fltTypeParam.getValue();
		  if (fltType.equals(FLT_TYPE_NORMAL)) {
			  f_rv = 0 ;
			  f_nm = 1;
		  }
		  else if (fltType.equals(FLT_TYPE_REVERSE)) {
			  f_rv = 1;
			  f_nm = 0;
		  }
		  else {
			  f_rv =0 ;
			  f_nm = 0;
		  }
	  }
	  else if (pName.equals(RupTopDepthParam.NAME)) {
		  depthTop = ( (Double) val).doubleValue();
	  }
	  else if (pName.equals(StdDevTypeParam.NAME)) {
		  stdDevType = (String) val;
	  }
	  else if(pName.equals(RupWidthParam.NAME)){
		  ruptureWidth = ((Double)val).doubleValue();
	  }
	  else if (pName.equals(PeriodParam.NAME) ) {
		  intensityMeasureChanged = true;
	  }
  }

  /**
   * Allows to reset the change listeners on the parameters
   */
  public void resetParameterEventListeners(){
    distanceRupParam.removeParameterChangeListener(this);
    distRupMinusJB_OverRupParam.removeParameterChangeListener(this);
    vs30Param.removeParameterChangeListener(this);
    dipParam.removeParameterChangeListener(this);
    magParam.removeParameterChangeListener(this);
    rupWidthParam.removeParameterChangeListener(this);
    fltTypeParam.removeParameterChangeListener(this);
    rupTopDepthParam.removeParameterChangeListener(this);
    stdDevTypeParam.removeParameterChangeListener(this);
    saPeriodParam.removeParameterChangeListener(this);
    this.initParameterEventListeners();
  }

  /**
   * Adds the parameter change listeners. This allows to listen to when-ever the
   * parameter is changed.
   */
  protected void initParameterEventListeners() {

    distanceRupParam.addParameterChangeListener(this);
    distRupMinusJB_OverRupParam.addParameterChangeListener(this);
    vs30Param.addParameterChangeListener(this);
    dipParam.addParameterChangeListener(this);
    magParam.addParameterChangeListener(this);
    rupWidthParam.addParameterChangeListener(this);
    fltTypeParam.addParameterChangeListener(this);
    rupTopDepthParam.addParameterChangeListener(this);
    stdDevTypeParam.addParameterChangeListener(this);
    saPeriodParam.addParameterChangeListener(this);
  }

  /**
   * 
   * @throws MalformedURLException if returned URL is not a valid URL.
   * @returns the URL to the AttenuationRelationship document on the Web.
   */
  public URL getInfoURL() throws MalformedURLException{
	  return new URL("http://www.opensha.org/documentation/modelsImplemented/attenRel/CY_2006.html");
  }     
  
}
