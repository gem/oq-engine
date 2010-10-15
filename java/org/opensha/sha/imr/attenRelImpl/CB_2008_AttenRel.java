/*******************************************************************************
 * Copyright 2009 OpenSHA.org in partnership with the Southern California
 * Earthquake Center (SCEC, http://www.scec.org) at the University of Southern
 * California and the UnitedStates Geological Survey (USGS; http://www.usgs.gov)
 * 
 * Licensed under the Apache License, Version 2.0 (the "License"); you may not
 * use this file except in compliance with the License. You may obtain a copy of
 * the License at
 * 
 * http://www.apache.org/licenses/LICENSE-2.0
 * 
 * Unless required by applicable law or agreed to in writing, software
 * distributed under the License is distributed on an "AS IS" BASIS, WITHOUT
 * WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied. See the
 * License for the specific language governing permissions and limitations under
 * the License.
 ******************************************************************************/

package org.opensha.sha.imr.attenRelImpl;

import java.net.MalformedURLException;
import java.net.URL;
import java.util.ArrayList;
import java.util.HashMap;
import java.util.StringTokenizer;

import org.opensha.commons.data.NamedObjectAPI;
import org.opensha.commons.data.Site;
import org.opensha.commons.exceptions.InvalidRangeException;
import org.opensha.commons.exceptions.ParameterException;
import org.opensha.commons.geo.Location;
import org.opensha.commons.param.DoubleConstraint;
import org.opensha.commons.param.DoubleDiscreteConstraint;
import org.opensha.commons.param.StringConstraint;
import org.opensha.commons.param.event.ParameterChangeEvent;
import org.opensha.commons.param.event.ParameterChangeListener;
import org.opensha.commons.param.event.ParameterChangeWarningListener;
import org.opensha.commons.util.FileUtils;
import org.opensha.sha.earthquake.EqkRupture;
import org.opensha.sha.faultSurface.EvenlyGriddedSurfaceAPI;
// import org.opensha.sha.faultSurface.FaultTrace;
// import org.opensha.sha.faultSurface.StirlingGriddedSurface;
import org.opensha.sha.imr.AttenuationRelationship;
import org.opensha.sha.imr.PropagationEffect;
import org.opensha.sha.imr.ScalarIntensityMeasureRelationshipAPI;
import org.opensha.sha.imr.param.EqkRuptureParams.DipParam;
import org.opensha.sha.imr.param.EqkRuptureParams.FaultTypeParam;
import org.opensha.sha.imr.param.EqkRuptureParams.MagParam;
import org.opensha.sha.imr.param.EqkRuptureParams.RupTopDepthParam;
import org.opensha.sha.imr.param.IntensityMeasureParams.DampingParam;
import org.opensha.sha.imr.param.IntensityMeasureParams.PGA_Param;
import org.opensha.sha.imr.param.IntensityMeasureParams.PGD_Param;
import org.opensha.sha.imr.param.IntensityMeasureParams.PGV_Param;
import org.opensha.sha.imr.param.IntensityMeasureParams.PeriodParam;
import org.opensha.sha.imr.param.IntensityMeasureParams.SA_Param;
import org.opensha.sha.imr.param.OtherParams.ComponentParam;
import org.opensha.sha.imr.param.OtherParams.StdDevTypeParam;
import org.opensha.sha.imr.param.PropagationEffectParams.DistRupMinusJB_OverRupParameter;
import org.opensha.sha.imr.param.PropagationEffectParams.DistanceJBParameter;
import org.opensha.sha.imr.param.PropagationEffectParams.DistanceRupParameter;
import org.opensha.sha.imr.param.SiteParams.DepthTo2pt5kmPerSecParam;
import org.opensha.sha.imr.param.SiteParams.Vs30_Param;

/**
 * <b>Title:</b> CB_2008_AttenRel
 * <p>
 * 
 * <b>Description:</b> This implements the Attenuation Relationship published by
 * Campbell & Bozorgnia (2008, "NGA Ground Motion Model for the Geometric Mean
 * Horizontal Component of PGA, PGV, PGD and 5% Damped Linear Elastic Response
 * Spectra for Periods Ranging from 0.01 to 10 s", Earthquake Spectra, Volume
 * 24, Number 1, pp. 139-171)
 * <p>
 * 
 * Supported Intensity-Measure Parameters:
 * <p>
 * <UL>
 * <LI>pgaParam - Peak Ground Acceleration
 * <LI>pgvParam - Peak Ground Velocity
 * <LI>pgdParam - Peak Ground Displacement
 * <LI>saParam - Response Spectral Acceleration
 * </UL>
 * <p>
 * Other Independent Parameters:
 * <p>
 * <UL>
 * <LI>magParam - moment Magnitude
 * <LI>fltTypeParam - Style of faulting
 * <LI>rupTopDepthParam - depth to top of rupture
 * <LI>dipParam - rupture surface dip
 * <LI>distanceRupParam - closest distance to surface projection of fault
 * <li>distRupMinusJB_OverRupParam - used as a proxy for hanging wall effect
 * <LI>vs30Param - average Vs over top 30 meters
 * <li>depthTo2pt5kmPerSecParam - depth to where Vs30 equals 2.5 km/sec
 * <LI>componentParam - Component of shaking
 * <LI>stdDevTypeParam - The type of standard deviation
 * </UL>
 * </p>
 * <p>
 * NOTES: distRupMinusJB_OverRupParam is used rather than distancJBParameter
 * because the latter should not be held constant when distanceRupParameter is
 * changed (e.g., in the AttenuationRelationshipApplet). This includes the
 * stipulation that the mean of 0.2-sec (or less) SA should not be less than
 * that of PGA (the latter being given if so). If depthTo2pt5kmPerSec is null
 * (unknown), it is set as 2 km if vs30 <= 2500, and zero otherwise.
 * <p>
 * Verification - This model has been tested against: 1) a verification file
 * generated independently by Ken Campbell, implemented in the JUnit test class
 * CB_2008_test; and 2) by the test class NGA08_Site_EqkRup_Tests, which makes
 * sure parameters are set properly when Site and EqkRupture objects are passed
 * in.
 * </p>
 * 
 * @author Ned Field
 * @created Oct., 2008
 * @version 1.0
 */

public class CB_2008_AttenRel extends AttenuationRelationship implements
        ScalarIntensityMeasureRelationshipAPI, NamedObjectAPI,
        ParameterChangeListener {

    // Debugging stuff
    private final static String C = "CB_2006_AttenRel";
    private final static boolean D = false;
    public final static String SHORT_NAME = "CB2008";
    private static final long serialVersionUID = 1234567890987654358L;

    // Name of IMR
    public final static String NAME = "Campbell & Bozorgnia (2008)";
    private final static String CB_2008_CoeffFile = "campbell_2008_coeff.txt";

    double[] per, c0, c1, c2, c3, c4, c5, c6, c7, c8, c9, c10, c11, c12, k1,
            k2, k3, s_lny, t_lny, s_c, rho;

    double s_lnAF = 0.3;
    double n = 1.18;
    double c = 1.88;

    private HashMap indexFromPerHashMap;

    private int iper;
    private double vs30, rJB, rRup, distRupMinusJB_OverRup, f_rv, f_nm, mag,
            depthTop, depthTo2pt5kmPerSec, dip;
    private String stdDevType, component;
    private boolean magSaturation;
    private boolean parameterChange;

    private PropagationEffect propagationEffect;

    // values for warning parameters
    protected final static Double MAG_WARN_MIN = new Double(4.0);
    protected final static Double MAG_WARN_MAX = new Double(8.5);
    protected final static Double DISTANCE_RUP_WARN_MIN = new Double(0.0);
    protected final static Double DISTANCE_RUP_WARN_MAX = new Double(200.0);
    protected final static Double DISTANCE_MINUS_WARN_MIN = new Double(0.0);
    protected final static Double DISTANCE_MINUS_WARN_MAX = new Double(50.0);
    protected final static Double VS30_WARN_MIN = new Double(150.0);
    protected final static Double VS30_WARN_MAX = new Double(1500.0);
    protected final static Double DEPTH_2pt5_WARN_MIN = new Double(0);
    protected final static Double DEPTH_2pt5_WARN_MAX = new Double(10);
    protected final static Double DIP_WARN_MIN = new Double(15);
    protected final static Double DIP_WARN_MAX = new Double(90);
    protected final static Double RUP_TOP_WARN_MIN = new Double(0);
    protected final static Double RUP_TOP_WARN_MAX = new Double(15);

    // style of faulting options
    public final static String FLT_TYPE_STRIKE_SLIP = "Strike-Slip";
    public final static String FLT_TYPE_REVERSE = "Reverse";
    public final static String FLT_TYPE_NORMAL = "Normal";

    // for issuing warnings:
    private transient ParameterChangeWarningListener warningListener = null;

    /**
     * This initializes several ParameterList objects.
     */
    public CB_2008_AttenRel(ParameterChangeWarningListener warningListener) {

        super();

        this.warningListener = warningListener;
        readCoeffFile();
        initSupportedIntensityMeasureParams();
        indexFromPerHashMap = new HashMap();
        for (int i = 3; i < per.length; i++) {
            indexFromPerHashMap.put(new Double(per[i]), new Integer(i));
        }

        initEqkRuptureParams();
        initPropagationEffectParams();
        initSiteParams();
        initOtherParams();

        initIndependentParamLists(); // This must be called after the above
        initParameterEventListeners(); // add the change listeners to the
                                       // parameters

        propagationEffect = new PropagationEffect();
        propagationEffect.fixDistanceJB(true); // this ensures that it's exatly
                                               // zero over the discretized
                                               // rupture surfaces

        // write coeffs as a check
        // per,c0,c1,c2,c3,c4,c5,c6,c7,c8,c9,c10,c11,c12,k1,k2,k3,s_lny,t_lny,s_c,rho
        /*
         * System.out.print("\nper"); for(int i=0; i<per.length;i++)
         * System.out.print("\t"+per[i]); System.out.print("\nc0"); for(int i=0;
         * i<c0.length;i++) System.out.print("\t"+c0[i]);
         * System.out.print("\nc1"); for(int i=0; i<c1.length;i++)
         * System.out.print("\t"+c1[i]); System.out.print("\nc2"); for(int i=0;
         * i<c2.length;i++) System.out.print("\t"+c2[i]);
         * System.out.print("\nc3"); for(int i=0; i<c3.length;i++)
         * System.out.print("\t"+c3[i]); System.out.print("\nc4"); for(int i=0;
         * i<c4.length;i++) System.out.print("\t"+c4[i]);
         * System.out.print("\nc5"); for(int i=0; i<c5.length;i++)
         * System.out.print("\t"+c5[i]); System.out.print("\nc6"); for(int i=0;
         * i<c6.length;i++) System.out.print("\t"+c6[i]);
         * System.out.print("\nc7"); for(int i=0; i<c7.length;i++)
         * System.out.print("\t"+c7[i]); System.out.print("\nc8"); for(int i=0;
         * i<c8.length;i++) System.out.print("\t"+c8[i]);
         * System.out.print("\nc9"); for(int i=0; i<c9.length;i++)
         * System.out.print("\t"+c9[i]); System.out.print("\nc10"); for(int i=0;
         * i<c10.length;i++) System.out.print("\t"+c10[i]);
         * System.out.print("\nc11"); for(int i=0; i<c11.length;i++)
         * System.out.print("\t"+c11[i]); System.out.print("\nc12"); for(int
         * i=0; i<c12.length;i++) System.out.print("\t"+c12[i]);
         * System.out.print("\nk1"); for(int i=0; i<k1.length;i++)
         * System.out.print("\t"+k1[i]); System.out.print("\nk2"); for(int i=0;
         * i<k2.length;i++) System.out.print("\t"+k2[i]);
         * System.out.print("\nk3"); for(int i=0; i<k3.length;i++)
         * System.out.print("\t"+k3[i]); System.out.print("\ns_lny"); for(int
         * i=0; i<s_lny.length;i++) System.out.print("\t"+s_lny[i]);
         * System.out.print("\nt_lny"); for(int i=0; i<t_lny.length;i++)
         * System.out.print("\t"+t_lny[i]); System.out.print("\ns_c"); for(int
         * i=0; i<s_c.length;i++) System.out.print("\t"+s_c[i]);
         * System.out.print("\nrho"); for(int i=0; i<rho.length;i++)
         * System.out.print("\t"+rho[i]);
         */

    }

    private void readCoeffFile() {
        try {
            // ArrayList<String> coeff=
            // FileUtils.loadJarFile(CB_2008_CoeffFile);
            ArrayList<String> coeff =
                    FileUtils.loadFile(this.getClass().getResource(
                            CB_2008_CoeffFile));
            // reading the Period
            String perLine = coeff.get(0);
            ArrayList period = new ArrayList<Double>();
            StringTokenizer st = new StringTokenizer(perLine);
            int size = loadCoeffInArray(st, period);
            per = new double[size];
            this.createCoeffArray(period, per);
            period = null;

            // reading c0
            String c0Line = coeff.get(1);
            ArrayList c0List = new ArrayList<Double>();
            st = new StringTokenizer(c0Line);
            size = loadCoeffInArray(st, c0List);
            c0 = new double[size];
            this.createCoeffArray(c0List, c0);
            c0List = null;

            // reading c1
            String c1Line = coeff.get(2);
            ArrayList c1List = new ArrayList<Double>();
            st = new StringTokenizer(c1Line);
            size = loadCoeffInArray(st, c1List);
            c1 = new double[size];
            this.createCoeffArray(c1List, c1);
            c1List = null;

            // reading c2
            String c2Line = coeff.get(3);
            ArrayList c2List = new ArrayList<Double>();
            st = new StringTokenizer(c2Line);
            size = loadCoeffInArray(st, c2List);
            c2 = new double[size];
            this.createCoeffArray(c2List, c2);
            c2List = null;

            // reading c3
            String c3Line = coeff.get(4);
            ArrayList c3List = new ArrayList<Double>();
            st = new StringTokenizer(c3Line);
            size = loadCoeffInArray(st, c3List);
            c3 = new double[size];
            this.createCoeffArray(c3List, c3);
            c3List = null;

            // reading c4
            String c4Line = coeff.get(5);
            ArrayList c4List = new ArrayList<Double>();
            st = new StringTokenizer(c4Line);
            size = loadCoeffInArray(st, c4List);
            c4 = new double[size];
            this.createCoeffArray(c4List, c4);
            c4List = null;

            // reading c5
            String c5Line = coeff.get(6);
            ArrayList c5List = new ArrayList<Double>();
            st = new StringTokenizer(c5Line);
            size = loadCoeffInArray(st, c5List);
            c5 = new double[size];
            this.createCoeffArray(c5List, c5);
            c5List = null;

            // reading c6
            String c6Line = coeff.get(7);
            ArrayList c6List = new ArrayList<Double>();
            st = new StringTokenizer(c6Line);
            size = loadCoeffInArray(st, c6List);
            c6 = new double[size];
            this.createCoeffArray(c6List, c6);
            c6List = null;

            // reading c7
            String c7Line = coeff.get(8);
            ArrayList c7List = new ArrayList<Double>();
            st = new StringTokenizer(c7Line);
            size = loadCoeffInArray(st, c7List);
            c7 = new double[size];
            this.createCoeffArray(c7List, c7);
            c7List = null;

            // reading c8
            String c8Line = coeff.get(9);
            ArrayList c8List = new ArrayList<Double>();
            st = new StringTokenizer(c8Line);
            size = loadCoeffInArray(st, c8List);
            c8 = new double[size];
            this.createCoeffArray(c8List, c8);
            c8List = null;

            // reading c9
            String c9Line = coeff.get(10);
            ArrayList c9List = new ArrayList<Double>();
            st = new StringTokenizer(c9Line);
            size = loadCoeffInArray(st, c9List);
            c9 = new double[size];
            this.createCoeffArray(c9List, c9);
            c9List = null;

            // reading c10
            String c10Line = coeff.get(11);
            ArrayList c10List = new ArrayList<Double>();
            st = new StringTokenizer(c10Line);
            size = loadCoeffInArray(st, c10List);
            c10 = new double[size];
            this.createCoeffArray(c10List, c10);
            c10List = null;

            // reading c11
            String c11Line = coeff.get(12);
            ArrayList c11List = new ArrayList<Double>();
            st = new StringTokenizer(c11Line);
            size = loadCoeffInArray(st, c11List);
            c11 = new double[size];
            this.createCoeffArray(c11List, c11);
            c11List = null;

            // reading c12
            String c12Line = coeff.get(13);
            ArrayList c12List = new ArrayList<Double>();
            st = new StringTokenizer(c12Line);
            size = loadCoeffInArray(st, c12List);
            c12 = new double[size];
            this.createCoeffArray(c12List, c12);
            c12List = null;

            // reading k1
            String k1Line = coeff.get(14);
            ArrayList k1List = new ArrayList<Double>();
            st = new StringTokenizer(k1Line);
            size = loadCoeffInArray(st, k1List);
            k1 = new double[size];
            this.createCoeffArray(k1List, k1);
            k1List = null;

            // reading k2
            String k2Line = coeff.get(15);
            ArrayList k2List = new ArrayList<Double>();
            st = new StringTokenizer(k2Line);
            size = loadCoeffInArray(st, k2List);
            k2 = new double[size];
            this.createCoeffArray(k2List, k2);
            k2List = null;

            // reading k3
            String k3Line = coeff.get(16);
            ArrayList k3List = new ArrayList<Double>();
            st = new StringTokenizer(k3Line);
            size = loadCoeffInArray(st, k3List);
            k3 = new double[size];
            this.createCoeffArray(k3List, k3);
            k3List = null;

            // reading s_lny
            String s_lnyLine = coeff.get(17);
            ArrayList s_lnyList = new ArrayList<Double>();
            st = new StringTokenizer(s_lnyLine);
            size = loadCoeffInArray(st, s_lnyList);
            s_lny = new double[size];
            this.createCoeffArray(s_lnyList, s_lny);
            s_lnyList = null;

            // reading t_lny
            String t_lnyLine = coeff.get(18);
            ArrayList t_lnyList = new ArrayList<Double>();
            st = new StringTokenizer(t_lnyLine);
            size = loadCoeffInArray(st, t_lnyList);
            t_lny = new double[size];
            this.createCoeffArray(t_lnyList, t_lny);
            t_lnyList = null;

            // reading s_c
            String c_lnyLine = coeff.get(19);
            ArrayList c_lnyList = new ArrayList<Double>();
            st = new StringTokenizer(c_lnyLine);
            size = loadCoeffInArray(st, c_lnyList);
            s_c = new double[size];
            this.createCoeffArray(c_lnyList, s_c);
            c_lnyList = null;

            // reading rho
            String rho_sLine = coeff.get(20);
            ArrayList rho_sList = new ArrayList<Double>();
            st = new StringTokenizer(rho_sLine);
            size = loadCoeffInArray(st, rho_sList);
            rho = new double[size];
            this.createCoeffArray(rho_sList, rho);
            rho_sList = null;

        } catch (Exception e) {
            throw new RuntimeException(CB_2008_CoeffFile + " file Not Found", e);
        }
    }

    private int loadCoeffInArray(StringTokenizer st, ArrayList<Double> coeff) {
        st.nextToken();
        while (st.hasMoreTokens())
            coeff.add(Double.parseDouble(st.nextToken().trim()));
        return coeff.size();
    }

    private void createCoeffArray(ArrayList<Double> coeff, double c[]) {
        for (int i = 0; i < c.length; ++i)
            c[i] = coeff.get(i);
    }

    /**
     * This sets the eqkRupture related parameters (magParam and fltTypeParam)
     * based on the eqkRupture passed in. The internally held eqkRupture object
     * is also set as that passed in. Warning constraints are ingored.
     * 
     * @param eqkRupture
     *            The new eqkRupture value
     * @throws InvalidRangeException
     *             thrown if rake is out of bounds
     */
    public void setEqkRupture(EqkRupture eqkRupture)
            throws InvalidRangeException {

        magParam.setValueIgnoreWarning(new Double(eqkRupture.getMag()));

        double rake = eqkRupture.getAveRake();
        if (rake > 30 && rake < 150) {
            fltTypeParam.setValue(FLT_TYPE_REVERSE);
        } else if (rake > -150 && rake < -30) {
            fltTypeParam.setValue(FLT_TYPE_NORMAL);
        } else { // strike slip
            fltTypeParam.setValue(FLT_TYPE_STRIKE_SLIP);
        }

        EvenlyGriddedSurfaceAPI surface = eqkRupture.getRuptureSurface();
        double depth = surface.getLocation(0, 0).getDepth();
        rupTopDepthParam.setValueIgnoreWarning(depth);

        dipParam.setValueIgnoreWarning(surface.getAveDip());

        // setFaultTypeFromRake(eqkRupture.getAveRake());
        this.eqkRupture = eqkRupture;
        setPropagationEffectParams();

    }

    /**
     * This sets the site-related parameter (siteTypeParam) based on what is in
     * the Site object passed in (the Site object must have a parameter with the
     * same name as that in siteTypeParam). This also sets the internally held
     * Site object as that passed in.
     * 
     * @param site
     *            The new site object
     * @throws ParameterException
     *             Thrown if the Site object doesn't contain a Vs30 parameter
     */
    public void setSite(Site site) throws ParameterException {

        vs30Param.setValue((Double) site.getParameter(Vs30_Param.NAME)
                .getValue());
        depthTo2pt5kmPerSecParam.setValueIgnoreWarning((Double) site
                .getParameter(DepthTo2pt5kmPerSecParam.NAME).getValue());
        this.site = site;
        setPropagationEffectParams();

    }

    /**
     * This sets the two propagation-effect parameters (distanceRupParam and
     * distRupMinusJB_OverRupParam) based on the current site and eqkRupture.
     */
    protected void setPropagationEffectParams() {

        if ((this.site != null) && (this.eqkRupture != null)) {

            propagationEffect.setAll(this.eqkRupture, this.site); // use this
                                                                  // for
                                                                  // efficiency
            // System.out.println(propagationEffect.getParamValue(distanceRupParam.NAME));
            distanceRupParam.setValueIgnoreWarning(propagationEffect
                    .getParamValue(distanceRupParam.NAME)); // this sets rRup
                                                            // too
            double dist_jb =
                    ((Double) propagationEffect
                            .getParamValue(DistanceJBParameter.NAME))
                            .doubleValue();
            if (rRup == 0)
                distRupMinusJB_OverRupParam.setValueIgnoreWarning(0.0);
            else
                distRupMinusJB_OverRupParam
                        .setValueIgnoreWarning((rRup - dist_jb) / rRup);
        }
    }

    /**
     * This function returns the array index for the coeffs corresponding to the
     * chosen IMT
     */
    protected void setCoeffIndex() throws ParameterException {

        // Check that parameter exists
        if (im == null) {
            throw new ParameterException(
                    C
                            + ": updateCoefficients(): "
                            + "The Intensity Measusre Parameter has not been set yet, unable to process.");
        }

        if (im.getName().equalsIgnoreCase(SA_Param.NAME)) {
            iper =
                    ((Integer) indexFromPerHashMap
                            .get(saPeriodParam.getValue())).intValue();
        } else if (im.getName().equalsIgnoreCase(PGV_Param.NAME)) {
            iper = 1;
        } else if (im.getName().equalsIgnoreCase(PGA_Param.NAME)) {
            iper = 2;
        } else if (im.getName().equalsIgnoreCase(PGD_Param.NAME)) {
            iper = 0;
        }
        parameterChange = true;
        intensityMeasureChanged = false;

    }

    /**
     * Calculates the mean of the exceedence probability distribution.
     * <p>
     * 
     * @return The mean value
     */
    public double getMean() {

        // check if distance is beyond the user specified max
        if (rRup > USER_MAX_DISTANCE) {
            return VERY_SMALL_MEAN;
        }

        if (intensityMeasureChanged) {
            setCoeffIndex(); // intensityMeasureChanged is set to false in this
                             // method
        }

        // compute rJB
        rJB = rRup - distRupMinusJB_OverRup * rRup;

        // set default value of basin depth based on the final value of vs30
        // (must do this here because we get pga_rock below by passing in 1100
        // m/s)
        if (Double.isNaN(depthTo2pt5kmPerSec)) {
            if (vs30 <= 2500)
                depthTo2pt5kmPerSec = 2;
            else
                depthTo2pt5kmPerSec = 0;
        }

        double pga_rock =
                Math.exp(getMean(2, 1100, rRup, rJB, f_rv, f_nm, mag, dip,
                        depthTop, depthTo2pt5kmPerSec, magSaturation, 0));

        double mean =
                getMean(iper, vs30, rRup, rJB, f_rv, f_nm, mag, dip, depthTop,
                        depthTo2pt5kmPerSec, magSaturation, pga_rock);

        // System.out.println(mean+"\t"+iper+"\t"+vs30+"\t"+rRup+"\t"+rJB+"\t"+f_rv+"\t"+f_nm+"\t"+mag+"\t"+dip+"\t"+depthTop+"\t"+depthTo2pt5kmPerSec+"\t"+magSaturation+"\t"+pga_rock);

        // make sure SA does not exceed PGA if per < 0.2 (page 11 of pre-print)
        if (iper < 3 || iper > 11) // not SA period between 0.02 and 0.15
            return mean;
        else {
            double pga_mean =
                    getMean(2, vs30, rRup, rJB, f_rv, f_nm, mag, dip, depthTop,
                            depthTo2pt5kmPerSec, magSaturation, pga_rock); // mean
                                                                           // for
                                                                           // PGA
            return Math.max(mean, pga_mean);
        }
    }

    /**
     * @return The stdDev value
     */
    public double getStdDev() {
        if (intensityMeasureChanged) {
            setCoeffIndex(); // intensityMeasureChanged is set to false in this
                             // method
        }

        // compute rJB
        rJB = rRup - distRupMinusJB_OverRup * rRup;

        // set default value of basin depth based on the final value of vs30
        // (must do this here because we get pga_rock below by passing in 1100
        // m/s)
        if (Double.isNaN(depthTo2pt5kmPerSec)) {
            if (vs30 <= 2500)
                depthTo2pt5kmPerSec = 2;
            else
                depthTo2pt5kmPerSec = 0;
        }

        double pga_rock = Double.NaN;
        if (vs30 < k1[iper])
            pga_rock =
                    Math.exp(getMean(2, 1100, rRup, rJB, f_rv, f_nm, mag, dip,
                            depthTop, depthTo2pt5kmPerSec, magSaturation, 0));

        component = (String) componentParam.getValue();

        double stdDev = getStdDev(iper, stdDevType, component, vs30, pga_rock);

        // System.out.println(stdDev+"\t"+iper+"\t"+stdDevType+"\t"+component+"\t"+vs30+"\t"+pga_rock);

        return stdDev;
    }

    /**
     * Allows the user to set the default parameter values for the selected
     * Attenuation Relationship.
     */
    public void setParamDefaults() {

        vs30Param.setValueAsDefault();
        magParam.setValueAsDefault();
        fltTypeParam.setValueAsDefault();
        rupTopDepthParam.setValueAsDefault();
        distanceRupParam.setValueAsDefault();
        distRupMinusJB_OverRupParam.setValueAsDefault();
        saParam.setValueAsDefault();
        saPeriodParam.setValueAsDefault();
        saDampingParam.setValueAsDefault();
        pgaParam.setValueAsDefault();
        pgvParam.setValueAsDefault();
        pgdParam.setValueAsDefault();
        componentParam.setValueAsDefault();
        stdDevTypeParam.setValueAsDefault();
        depthTo2pt5kmPerSecParam.setValueAsDefault();
        dipParam.setValueAsDefault();
        vs30 = ((Double) vs30Param.getValue()).doubleValue();
        mag = ((Double) magParam.getValue()).doubleValue();
        stdDevType = (String) stdDevTypeParam.getValue();

    }

    /**
     * This creates the lists of independent parameters that the various
     * dependent parameters (mean, standard deviation, exceedance probability,
     * and IML at exceedance probability) depend upon. NOTE: these lists do not
     * include anything about the intensity-measure parameters or any of thier
     * internal independentParamaters.
     */
    protected void initIndependentParamLists() {

        // params that the mean depends upon
        meanIndependentParams.clear();
        meanIndependentParams.addParameter(distanceRupParam);
        meanIndependentParams.addParameter(distRupMinusJB_OverRupParam);
        meanIndependentParams.addParameter(vs30Param);
        meanIndependentParams.addParameter(depthTo2pt5kmPerSecParam);
        meanIndependentParams.addParameter(magParam);
        meanIndependentParams.addParameter(fltTypeParam);
        meanIndependentParams.addParameter(rupTopDepthParam);
        meanIndependentParams.addParameter(dipParam);
        meanIndependentParams.addParameter(componentParam);

        // params that the stdDev depends upon
        stdDevIndependentParams.clear();
        stdDevIndependentParams.addParameterList(meanIndependentParams);
        stdDevIndependentParams.addParameter(stdDevTypeParam);

        // params that the exceed. prob. depends upon
        exceedProbIndependentParams.clear();
        exceedProbIndependentParams.addParameterList(stdDevIndependentParams);
        exceedProbIndependentParams.addParameter(sigmaTruncTypeParam);
        exceedProbIndependentParams.addParameter(sigmaTruncLevelParam);

        // params that the IML at exceed. prob. depends upon
        imlAtExceedProbIndependentParams
                .addParameterList(exceedProbIndependentParams);
        imlAtExceedProbIndependentParams.addParameter(exceedProbParam);
    }

    /**
     * Creates the Site-Type parameter and adds it to the siteParams list. Makes
     * the parameters noneditable.
     */
    protected void initSiteParams() {

        vs30Param = new Vs30_Param(VS30_WARN_MIN, VS30_WARN_MAX);
        depthTo2pt5kmPerSecParam =
                new DepthTo2pt5kmPerSecParam(DEPTH_2pt5_WARN_MIN,
                        DEPTH_2pt5_WARN_MAX);

        siteParams.clear();
        siteParams.addParameter(vs30Param);
        siteParams.addParameter(depthTo2pt5kmPerSecParam);

    }

    /**
     * Creates the two Potential Earthquake parameters (magParam and
     * fltTypeParam) and adds them to the eqkRuptureParams list. Makes the
     * parameters noneditable.
     */
    protected void initEqkRuptureParams() {

        magParam = new MagParam(MAG_WARN_MIN, MAG_WARN_MAX);
        dipParam = new DipParam(DIP_WARN_MIN, DIP_WARN_MAX);
        rupTopDepthParam =
                new RupTopDepthParam(RUP_TOP_WARN_MIN, RUP_TOP_WARN_MAX);

        StringConstraint constraint = new StringConstraint();
        constraint.addString(FLT_TYPE_STRIKE_SLIP);
        constraint.addString(FLT_TYPE_NORMAL);
        constraint.addString(FLT_TYPE_REVERSE);
        constraint.setNonEditable();
        fltTypeParam = new FaultTypeParam(constraint, FLT_TYPE_STRIKE_SLIP);

        eqkRuptureParams.clear();
        eqkRuptureParams.addParameter(magParam);
        eqkRuptureParams.addParameter(fltTypeParam);
        eqkRuptureParams.addParameter(dipParam);
        eqkRuptureParams.addParameter(rupTopDepthParam);
    }

    /**
     * Creates the Propagation Effect parameters and adds them to the
     * propagationEffectParams list. Makes the parameters noneditable.
     */
    protected void initPropagationEffectParams() {

        distanceRupParam = new DistanceRupParameter(0.0);
        DoubleConstraint warn =
                new DoubleConstraint(DISTANCE_RUP_WARN_MIN,
                        DISTANCE_RUP_WARN_MAX);
        warn.setNonEditable();
        distanceRupParam.setWarningConstraint(warn);
        distanceRupParam.addParameterChangeWarningListener(warningListener);

        distanceRupParam.setNonEditable();

        // create distRupMinusJB_OverRupParam
        distRupMinusJB_OverRupParam = new DistRupMinusJB_OverRupParameter(0.0);
        DoubleConstraint warnJB =
                new DoubleConstraint(DISTANCE_MINUS_WARN_MIN,
                        DISTANCE_MINUS_WARN_MAX);
        distRupMinusJB_OverRupParam
                .addParameterChangeWarningListener(warningListener);
        warn.setNonEditable();
        distRupMinusJB_OverRupParam.setWarningConstraint(warnJB);
        distRupMinusJB_OverRupParam.setNonEditable();

        propagationEffectParams.addParameter(distanceRupParam);
        propagationEffectParams.addParameter(distRupMinusJB_OverRupParam);

    }

    /**
     * Creates the two supported IM parameters (PGA and SA), as well as the
     * independenParameters of SA (periodParam and dampingParam) and adds them
     * to the supportedIMParams list. Makes the parameters noneditable.
     */
    protected void initSupportedIntensityMeasureParams() {

        // Create saParam:
        DoubleDiscreteConstraint periodConstraint =
                new DoubleDiscreteConstraint();
        for (int i = 3; i < per.length; i++) {
            periodConstraint.addDouble(new Double(per[i]));
        }
        periodConstraint.setNonEditable();
        saPeriodParam = new PeriodParam(periodConstraint);
        saDampingParam = new DampingParam();
        saParam = new SA_Param(saPeriodParam, saDampingParam);
        saParam.setNonEditable();

        // Create PGA Parameter (pgaParam):
        pgaParam = new PGA_Param();
        pgaParam.setNonEditable();

        // Create PGV Parameter (pgvParam):
        pgvParam = new PGV_Param();
        pgvParam.setNonEditable();

        // Create PGD Parameter (pgdParam):
        pgdParam = new PGD_Param();
        pgdParam.setNonEditable();

        // Add the warning listeners:
        saParam.addParameterChangeWarningListener(warningListener);
        pgaParam.addParameterChangeWarningListener(warningListener);
        pgvParam.addParameterChangeWarningListener(warningListener);
        pgdParam.addParameterChangeWarningListener(warningListener);

        // Put parameters in the supportedIMParams list:
        supportedIMParams.clear();
        supportedIMParams.addParameter(saParam);
        supportedIMParams.addParameter(pgaParam);
        supportedIMParams.addParameter(pgvParam);
        supportedIMParams.addParameter(pgdParam);
    }

    /**
     * Creates other Parameters that the mean or stdDev depends upon, such as
     * the Component or StdDevType parameters.
     */
    protected void initOtherParams() {

        // init other params defined in parent class
        super.initOtherParams();

        // the Component Parameter
        StringConstraint constraint = new StringConstraint();
        constraint.addString(ComponentParam.COMPONENT_GMRotI50);
        constraint.addString(ComponentParam.COMPONENT_RANDOM_HORZ);
        componentParam =
                new ComponentParam(constraint,
                        ComponentParam.COMPONENT_GMRotI50);

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
     * 
     * @return String
     */
    public String getShortName() {
        return SHORT_NAME;
    }

    /**
     * 
     * @param iper
     * @param vs30
     * @param rRup
     * @param distJB
     * @param f_rv
     * @param f_nm
     * @param mag
     * @param depthTop
     * @param depthTo2pt5kmPerSec
     * @param magSaturation
     * @param pga_rock
     * @return
     */
    public double getMean(int iper, double vs30, double rRup, double distJB,
            double f_rv, double f_nm, double mag, double dip, double depthTop,
            double depthTo2pt5kmPerSec, boolean magSaturation, double pga_rock) {

        double fmag, fdis, fflt, fhng, fsite, fsed;

        // modeling depence on magnitude
        if (mag <= 5.5)
            fmag = c0[iper] + c1[iper] * mag;
        else if (mag > 5.5 && mag <= 6.5)
            fmag = c0[iper] + c1[iper] * mag + c2[iper] * (mag - 5.5);
        else
            fmag =
                    c0[iper] + c1[iper] * mag + c2[iper] * (mag - 5.5)
                            + c3[iper] * (mag - 6.5);

        // source to site distance
        fdis =
                (c4[iper] + c5[iper] * mag)
                        * Math.log(Math.sqrt(rRup * rRup + c6[iper] * c6[iper]));

        // style of faulting
        double ffltz; // getting the depth top or also called Ztor in Campbell's
                      // paper
        if (depthTop < 1)
            ffltz = depthTop;
        else
            ffltz = 1;

        // fault-style term
        fflt = c7[iper] * f_rv * ffltz + c8[iper] * f_nm;

        // hanging wall effects
        double fhngr;
        if (distJB == 0)
            fhngr = 1;
        else if (depthTop < 1 && distJB > 0)
            fhngr =
                    (Math.max(rRup, Math.sqrt(distJB * distJB + 1)) - distJB)
                            / Math.max(rRup, Math.sqrt(distJB * distJB + 1));
        else
            fhngr = (rRup - distJB) / rRup;

        // if(pga_rock !=0)
        // System.out.print((float)distJB+"\t"+(float)rRup+"\t"+fhngr+"\n");

        double fhngm;
        if (mag <= 6.0)
            fhngm = 0;
        else if (mag > 6.0 && mag < 6.5)
            fhngm = 2 * (mag - 6);
        else
            fhngm = 1;

        double fhngz;
        if (depthTop >= 20)
            fhngz = 0;
        else
            fhngz = (20 - depthTop) / 20;

        double fhngd;
        if (dip <= 70)
            fhngd = 1;
        else
            fhngd = (90 - dip) / 20;

        fhng = c9[iper] * fhngr * fhngm * fhngz * fhngd;

        // modelling dependence on linear and non-linear site conditions
        if (vs30 < k1[iper])
            fsite =
                    c10[iper]
                            * Math.log(vs30 / k1[iper])
                            + k2[iper]
                            * (Math.log(pga_rock + c
                                    * Math.pow(vs30 / k1[iper], n)) - Math
                                    .log(pga_rock + c));
        else if (vs30 < 1100)
            fsite = (c10[iper] + k2[iper] * n) * Math.log(vs30 / k1[iper]);
        else
            fsite = (c10[iper] + k2[iper] * n) * Math.log(1100 / k1[iper]);

        // modelling depence on shallow sediments effects and 3-D basin effects
        if (depthTo2pt5kmPerSec < 1)
            fsed = c11[iper] * (depthTo2pt5kmPerSec - 1);
        else if (depthTo2pt5kmPerSec <= 3)
            fsed = 0;
        else
            fsed =
                    c12[iper] * k3[iper] * Math.exp(-0.75)
                            * (1 - Math.exp(-0.25 * (depthTo2pt5kmPerSec - 3)));

        return fmag + fdis + fflt + fhng + fsite + fsed;
    }

    /**
     * 
     * @param iper
     * @param stdDevType
     * @param component
     * @return
     */
    public double getStdDev(int iper, String stdDevType, String component,
            double vs30, double rock_pga) {

        if (stdDevType.equals(StdDevTypeParam.STD_DEV_TYPE_NONE))
            return 0.0;
        else {

            // get tau - inter-event term
            double tau = t_lny[iper];

            // compute intra-event sigma
            double sigma;
            if (vs30 >= k1[iper])
                sigma = s_lny[iper];
            else {
                double s_lnYb =
                        Math.sqrt(s_lny[iper] * s_lny[iper] - s_lnAF * s_lnAF);
                double s_lnAb =
                        Math.sqrt(s_lny[2] * s_lny[2] - s_lnAF * s_lnAF); // iper=2
                                                                          // is
                                                                          // for
                                                                          // PGA
                double alpha =
                        k2[iper]
                                * rock_pga
                                * ((1 / (rock_pga + c
                                        * Math.pow(vs30 / k1[iper], n))) - 1 / (rock_pga + c));
                sigma =
                        Math.sqrt(s_lnYb * s_lnYb + s_lnAF * s_lnAF + alpha
                                * alpha * s_lnAb * s_lnAb + 2 * alpha
                                * rho[iper] * s_lnYb * s_lnAb);
            }

            // compute total sigma
            double sigma_total = Math.sqrt(tau * tau + sigma * sigma);

            // compute multiplicative factor in case component is random
            // horizontal
            double random_ratio;
            if (component.equals(ComponentParam.COMPONENT_RANDOM_HORZ))
                random_ratio =
                        Math.sqrt(1 + (s_c[iper] * s_c[iper])
                                / (sigma_total * sigma_total));
            else
                random_ratio = 1;

            // return appropriate value
            if (stdDevType.equals(StdDevTypeParam.STD_DEV_TYPE_TOTAL))
                return sigma_total * random_ratio;
            else if (stdDevType.equals(StdDevTypeParam.STD_DEV_TYPE_INTRA))
                return sigma * random_ratio;
            else if (stdDevType.equals(StdDevTypeParam.STD_DEV_TYPE_INTER))
                return tau * random_ratio;
            else
                return Double.NaN; // just in case invalid stdDev given

        }
    }

    /**
     * This listens for parameter changes and updates the primitive parameters
     * accordingly
     * 
     * @param e
     *            ParameterChangeEvent
     */
    public void parameterChange(ParameterChangeEvent e) {

        String pName = e.getParameterName();
        Object val = e.getNewValue();
        parameterChange = true;
        if (pName.equals(DistanceRupParameter.NAME)) {
            rRup = ((Double) val).doubleValue();
        } else if (pName.equals(DistRupMinusJB_OverRupParameter.NAME)) {
            distRupMinusJB_OverRup = ((Double) val).doubleValue();
        } else if (pName.equals(Vs30_Param.NAME)) {
            vs30 = ((Double) val).doubleValue();
        } else if (pName.equals(DepthTo2pt5kmPerSecParam.NAME)) {
            if (val == null)
                depthTo2pt5kmPerSec = Double.NaN; // can't set the defauly here
                                                  // because vs30 could still
                                                  // change
            else
                depthTo2pt5kmPerSec = ((Double) val).doubleValue();
        } else if (pName.equals(magParam.NAME)) {
            mag = ((Double) val).doubleValue();
        } else if (pName.equals(FaultTypeParam.NAME)) {
            String fltType = (String) fltTypeParam.getValue();
            if (fltType.equals(FLT_TYPE_NORMAL)) {
                f_rv = 0;
                f_nm = 1;
            } else if (fltType.equals(FLT_TYPE_REVERSE)) {
                f_rv = 1;
                f_nm = 0;
            } else {
                f_rv = 0;
                f_nm = 0;
            }
        } else if (pName.equals(RupTopDepthParam.NAME)) {
            depthTop = ((Double) val).doubleValue();
        } else if (pName.equals(StdDevTypeParam.NAME)) {
            stdDevType = (String) val;
        } else if (pName.equals(DipParam.NAME)) {
            dip = ((Double) val).doubleValue();
        } else if (pName.equals(ComponentParam.NAME)) {
            component = (String) componentParam.getValue();
        } else if (pName.equals(PeriodParam.NAME)) {
            intensityMeasureChanged = true;
        }
    }

    /**
     * Allows to reset the change listeners on the parameters
     */
    public void resetParameterEventListeners() {
        distanceRupParam.removeParameterChangeListener(this);
        distRupMinusJB_OverRupParam.removeParameterChangeListener(this);
        vs30Param.removeParameterChangeListener(this);
        depthTo2pt5kmPerSecParam.removeParameterChangeListener(this);
        magParam.removeParameterChangeListener(this);
        fltTypeParam.removeParameterChangeListener(this);
        rupTopDepthParam.removeParameterChangeListener(this);
        dipParam.removeParameterChangeListener(this);
        stdDevTypeParam.removeParameterChangeListener(this);
        saPeriodParam.removeParameterChangeListener(this);

        this.initParameterEventListeners();
    }

    /**
     * Adds the parameter change listeners. This allows to listen to when-ever
     * the parameter is changed.
     */
    protected void initParameterEventListeners() {

        distanceRupParam.addParameterChangeListener(this);
        distRupMinusJB_OverRupParam.addParameterChangeListener(this);
        vs30Param.addParameterChangeListener(this);
        depthTo2pt5kmPerSecParam.addParameterChangeListener(this);
        magParam.addParameterChangeListener(this);
        fltTypeParam.addParameterChangeListener(this);
        rupTopDepthParam.addParameterChangeListener(this);
        stdDevTypeParam.addParameterChangeListener(this);
        saPeriodParam.addParameterChangeListener(this);
        dipParam.addParameterChangeListener(this);
    }

    /**
     * This provides a URL where more info on this model can be obtained
     * 
     * @throws MalformedURLException
     *             if returned URL is not a valid URL.
     * @returns the URL to the AttenuationRelationship document on the Web.
     */
    public URL getInfoURL() throws MalformedURLException {
        return new URL(
                "http://www.opensha.org/documentation/modelsImplemented/attenRel/CB_2008.html");
    }

    /**
     * This tests DistJB numerical precision with respect to the f_hngR term.
     * Looks OK now.
     * 
     * @param args
     */
    // public static void main(String[] args) {
    //
    // Location loc1 = new Location(-0.1, 0.0, 0);
    // Location loc2 = new Location(+0.1, 0.0, 0);
    // FaultTrace faultTrace = new FaultTrace("test");
    // faultTrace.add(loc1);
    // faultTrace.add(loc2);
    // StirlingGriddedSurface surface = new StirlingGriddedSurface(faultTrace,
    // 45.0,0,10,1);
    // EqkRupture rup = new EqkRupture();
    // rup.setMag(7);
    // rup.setAveRake(90);
    // rup.setRuptureSurface(surface);
    //
    // CB_2008_AttenRel attenRel = new CB_2008_AttenRel(null);
    // attenRel.setParamDefaults();
    // attenRel.setIntensityMeasure("PGA");
    // attenRel.setEqkRupture(rup);
    //
    // Site site = new Site();
    // site.addParameter(attenRel.getParameter(Vs30_Param.NAME));
    // site.addParameter(attenRel.getParameter(DepthTo2pt5kmPerSecParam.NAME));
    //
    // Location loc;
    // for(double dist=-0.3; dist<=0.3; dist+=0.01) {
    // loc = new Location(0,dist);
    // site.setLocation(loc);
    // attenRel.setSite(site);
    // // System.out.print((float)dist+"\t");
    // attenRel.getMean();
    // }
    //
    // }

}
