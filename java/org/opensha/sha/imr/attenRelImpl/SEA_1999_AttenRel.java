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
import java.util.Enumeration;
import java.util.Hashtable;
import java.util.Iterator;
import java.util.TreeSet;

import org.opensha.commons.data.NamedObjectAPI;
import org.opensha.commons.data.Site;
import org.opensha.commons.exceptions.IMRException;
import org.opensha.commons.exceptions.InvalidRangeException;
import org.opensha.commons.exceptions.ParameterException;
import org.opensha.commons.param.DoubleConstraint;
import org.opensha.commons.param.DoubleDiscreteConstraint;
import org.opensha.commons.param.StringConstraint;
import org.opensha.commons.param.StringParameter;
import org.opensha.commons.param.event.ParameterChangeWarningListener;
import org.opensha.sha.earthquake.EqkRupture;
import org.opensha.sha.imr.AttenuationRelationship;
import org.opensha.sha.imr.PropagationEffect;
import org.opensha.sha.imr.ScalarIntensityMeasureRelationshipAPI;
import org.opensha.sha.imr.param.EqkRuptureParams.MagParam;
import org.opensha.sha.imr.param.IntensityMeasureParams.DampingParam;
import org.opensha.sha.imr.param.IntensityMeasureParams.PGA_Param;
import org.opensha.sha.imr.param.IntensityMeasureParams.PeriodParam;
import org.opensha.sha.imr.param.IntensityMeasureParams.SA_Param;
import org.opensha.sha.imr.param.OtherParams.ComponentParam;
import org.opensha.sha.imr.param.OtherParams.StdDevTypeParam;
import org.opensha.sha.imr.param.PropagationEffectParams.DistanceJBParameter;

/**
 * <b>Title:</b> SEA_1999_AttenRel
 * <p>
 * 
 * <b>Description:</b> This implements the Attenuation Relationship developed by
 * Spudich, P., W.B. Joyner, A.G. Lindh, D.M. Boore, B.M. Margaris, and J.B.
 * Fletcher (1999, "SEA99: A revised ground motion prediction relation for use
 * in Extensional tectonic regimes," Bull. Seism. Soc. Am., v. 89, 1156-1170).
 * <p>
 * 
 * Supported Intensity-Measure Parameters:
 * <p>
 * <UL>
 * <LI>pgaParam - Peak Ground Acceleration
 * <LI>saParam - Response Spectral Acceleration
 * </UL>
 * <p>
 * Other Independent Parameters:
 * <p>
 * <UL>
 * <LI>magParam - moment Magnitude
 * <LI>distanceJBParam - closest distance to surface projection of fault
 * <LI>siteTypeParam - "Rock" or "Soil"
 * <LI>componentParam - Component of shaking (Average and Random Horizontal)
 * <LI>stdDevTypeParam - The type of standard deviation
 * </UL>
 * <p>
 * 
 * This has been tested against the values listed in Table 3 of the paper
 * referenced above (see the runTest() method).
 * 
 * @author Edward H. Field
 * @created May, 2004
 * @version 1.0
 */

public class SEA_1999_AttenRel extends AttenuationRelationship implements
        ScalarIntensityMeasureRelationshipAPI, NamedObjectAPI {

    // debugging stuff:
    private final static String C = "SEA_1999_AttenRel";
    private final static boolean D = false;
    public final static String NAME = "SEA (Spudich et al., 1999)";
    public final static String SHORT_NAME = "Spudich1999";
    private static final long serialVersionUID = 1234567890987654367L;

    // warning constraint fields:
    protected final static Double MAG_WARN_MIN = new Double(5.0);
    protected final static Double MAG_WARN_MAX = new Double(7.7);

    /**
     * Joyner-Boore Distance parameter
     */
    protected final static Double DISTANCE_JB_WARN_MIN = new Double(0.0);
    protected final static Double DISTANCE_JB_WARN_MAX = new Double(100.0);

    /**
     * Site Type Parameter ("Rock" versus "Soil")
     */
    private StringParameter siteTypeParam = null;
    public final static String SITE_TYPE_NAME = "SEA Site Type";
    // no units
    public final static String SITE_TYPE_INFO =
            "Geological conditions at the site";
    public final static String SITE_TYPE_ROCK = "Rock";
    public final static String SITE_TYPE_SOIL = "Soil";
    public final static String SITE_TYPE_DEFAULT = SITE_TYPE_ROCK;

    // log() to ln() conversion
    private double log2ln = 2.302585;

    /**
     * The current set of coefficients based on the selected intensityMeasure
     */
    private SEA_1999_AttenRelCoefficients coeff = null;

    /**
     * Hashtable of coefficients for the supported intensityMeasures
     */
    protected Hashtable coefficients = new Hashtable();

    // for issuing warnings:
    private transient ParameterChangeWarningListener warningListener = null;

    /**
     * This sets the eqkRupture related parameter (magParam) based on the
     * eqkRupture passed in. The internally held eqkRupture object is also set
     * as that passed in. Warning constraints are ingored.
     * 
     * @param eqkRupture
     *            The new eqkRupture value
     * @throws InvalidRangeException
     *             thrown if rake is out of bounds
     */
    public void setEqkRupture(EqkRupture eqkRupture)
            throws InvalidRangeException {

        magParam.setValueIgnoreWarning(new Double(eqkRupture.getMag()));
        this.eqkRupture = eqkRupture;
        setPropagationEffectParams();

    }

    /**
     * This sets the site-related parameter (siteTypeParam) based on what is in
     * the Site object passed in (the Site object must have a parameter with the
     * same name as that in siteTypeParam). This also sets the internally held
     * Site object as that passed in. WarningExceptions are ingored
     * 
     * @param site
     *            The new site
     * @throws ParameterException
     *             Thrown if the Site object doesn't contain the parameter
     */
    public void setSite(Site site) throws ParameterException {

        siteTypeParam.setValue((String) site.getParameter(SITE_TYPE_NAME)
                .getValue());
        this.site = site;
        setPropagationEffectParams();

    }

    /**
     * This sets the site and eqkRupture, and the related parameters, from the
     * propEffect object passed in. Warning constrains are ingored.
     * 
     * @param propEffect
     * @throws ParameterException
     *             Thrown if the Site object doesn't contain a Vs30 parameter
     * @throws InvalidRangeException
     *             thrown if rake is out of bounds
     */
    public void setPropagationEffect(PropagationEffect propEffect)
            throws InvalidRangeException, ParameterException {

        this.site = propEffect.getSite();
        this.eqkRupture = propEffect.getEqkRupture();

        siteTypeParam.setValue((String) site.getParameter(SITE_TYPE_NAME)
                .getValue());

        magParam.setValueIgnoreWarning(new Double(eqkRupture.getMag()));

        propEffect.setParamValue(distanceJBParam);

    }

    /**
     * This calculates the Distance JB propagation effect parameter based on the
     * current site and eqkRupture.
     * <P>
     */
    protected void setPropagationEffectParams() {

        if ((this.site != null) && (this.eqkRupture != null)) {
            distanceJBParam.setValue(eqkRupture, site);
        }
    }

    /**
     * This function determines which set of coefficients in the HashMap are to
     * be used given the current intensityMeasure (im) Parameter. The lookup is
     * done keyed on the name of the im, plus the period value if im.getName()
     * == "SA" (seperated by "/").
     * 
     * SWR: I choose the name <code>update</code> instead of set, because set is
     * so common to java bean fields, i.e. getters and setters, that set()
     * usually implies passing in a new value to the java bean field. I prefer
     * update or refresh to functions that change internal values internally
     */
    protected void updateCoefficients() throws ParameterException {

        // Check that parameter exists
        if (im == null) {
            throw new ParameterException(
                    C
                            + ": updateCoefficients(): "
                            + "The Intensity Measusre Parameter has not been set yet, unable to process.");
        }

        StringBuffer key = new StringBuffer(im.getName());
        if (im.getName().equalsIgnoreCase(SA_Param.NAME)) {
            key.append("/" + saPeriodParam.getValue());
        }
        coeff =
                (SEA_1999_AttenRelCoefficients) coefficients
                        .get(key.toString());
    }

    /**
     * No-Arg constructor. This initializes several ParameterList objects.
     */
    public SEA_1999_AttenRel(ParameterChangeWarningListener warningListener) {

        super();

        this.warningListener = warningListener;

        initCoefficients(); // This must be called before the next one
        initSupportedIntensityMeasureParams();

        initEqkRuptureParams();
        initPropagationEffectParams();
        initSiteParams();
        initOtherParams();

        initIndependentParamLists(); // Do this after the above

        // this runs the test to reproduce Table 3
        // runTest();
    }

    /**
     * Calculates the mean of the exceedence probability distribution. The exact
     * formula is:
     * <p>
     * 
     * double mean = b1 + <br>
     * coeff.b2 * ( mag - 6 ) + <br>
     * coeff.b3 * ( Math.pow( ( mag - 6 ), 2 ) ) + <br>
     * coeff.b5 * ( Math.log( Math.pow( ( distanceJB * distanceJB + coeff.h *
     * coeff.h ), 0.5 ) ) ) + <br>
     * coeff.bv * ( Math.log( vs30 / coeff.va ) ) <br>
     * 
     * @return The mean value
     */
    public double getMean() throws IMRException {

        double mag, distanceJB;
        String siteTypeValue;

        try {
            mag = ((Double) magParam.getValue()).doubleValue();
            siteTypeValue = (String) siteTypeParam.getValue();
            distanceJB = ((Double) distanceJBParam.getValue()).doubleValue();
        } catch (NullPointerException e) {
            throw new IMRException(C + ": getMean(): " + ERR);
        }

        // check if distance is beyond the user specified max
        if (distanceJB > USER_MAX_DISTANCE) {
            return VERY_SMALL_MEAN;
        }

        // the following is inefficient if the im Parameter has not been changed
        // in any way
        updateCoefficients();

        // Calculate the log10 mean
        double mean =
                coeff.b1
                        + coeff.b2
                        * (mag - 6)
                        + coeff.b3
                        * Math.pow((mag - 6), 2)
                        + coeff.b5
                        * Math.log(Math.pow((distanceJB * distanceJB + coeff.h
                                * coeff.h), 0.5)) / log2ln;

        // add site correction
        if (siteTypeValue.equals(SITE_TYPE_SOIL)) {
            mean += coeff.b6;
        }

        // convert to ln()
        mean *= log2ln;

        // make the PSV to SA correction (and cm/s-sq to g)
        if (im.getName().equals(SA_Param.NAME)) {
            if (coeff.period != 0.0) {
                mean += Math.log(2.0 * Math.PI / (coeff.period * 980));
            }
        }

        // return the result
        return mean;
    }

    /**
     * @return The stdDev value
     */
    public double getStdDev() throws IMRException {

        String stdDevType = stdDevTypeParam.getValue().toString();
        String component = componentParam.getValue().toString();

        // this is inefficient if the im has not been changed in any way
        updateCoefficients();

        // set the correct standard deviation depending on component and type
        if (component.equals(ComponentParam.COMPONENT_AVE_HORZ)) {

            if (stdDevType.equals(StdDevTypeParam.STD_DEV_TYPE_TOTAL)) { // "Total"
                return log2ln
                        * Math.pow((coeff.sigma1 * coeff.sigma1 + coeff.sigma2
                                * coeff.sigma2), 0.5);
            } else if (stdDevType.equals(StdDevTypeParam.STD_DEV_TYPE_INTER)) { // "Inter-Event"
                return log2ln * coeff.sigma2;
            } else if (stdDevType.equals(StdDevTypeParam.STD_DEV_TYPE_INTRA)) { // "Intra-Event"
                return log2ln * coeff.sigma1;
            } else if (stdDevType.equals(StdDevTypeParam.STD_DEV_TYPE_NONE)) { // "None (zero)"
                return 0;
            } else {
                throw new ParameterException(C
                        + ": getStdDev(): Invalid StdDevType");
            }
        } else if (component.equals(ComponentParam.COMPONENT_RANDOM_HORZ)) {

            if (stdDevType.equals(StdDevTypeParam.STD_DEV_TYPE_TOTAL)) { // "Total"
                return log2ln
                        * Math.pow((coeff.sigma1 * coeff.sigma1 + coeff.sigma2
                                * coeff.sigma2 + coeff.sigma3 * coeff.sigma3),
                                0.5);
            } else if (stdDevType.equals(StdDevTypeParam.STD_DEV_TYPE_INTER)) { // "Inter-Event"
                return log2ln * coeff.sigma2;
            } else if (stdDevType.equals(StdDevTypeParam.STD_DEV_TYPE_INTRA)) { // "Intra-Event"
                return log2ln
                        * Math.pow((coeff.sigma1 * coeff.sigma1 + coeff.sigma3
                                * coeff.sigma3), 0.5);
            } else if (stdDevType.equals(StdDevTypeParam.STD_DEV_TYPE_NONE)) { // "None (zero)"
                return 0;
            } else {
                throw new ParameterException(C
                        + ": getStdDev(): Invalid StdDevType");
            }
        } else {
            throw new ParameterException(C
                    + ": getStdDev(): Invalid component type");
        }

    }

    public void setParamDefaults() {

        // ((ParameterAPI)this.iml).setValue( IML_DEFAULT );
        siteTypeParam.setValue(SITE_TYPE_DEFAULT);
        magParam.setValueAsDefault();
        distanceJBParam.setValueAsDefault();
        saParam.setValueAsDefault();
        saPeriodParam.setValueAsDefault();
        saDampingParam.setValueAsDefault();
        pgaParam.setValueAsDefault();
        componentParam.setValueAsDefault();
        stdDevTypeParam.setValueAsDefault();

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
        meanIndependentParams.addParameter(distanceJBParam);
        meanIndependentParams.addParameter(siteTypeParam);
        meanIndependentParams.addParameter(magParam);
        meanIndependentParams.addParameter(componentParam);

        // params that the stdDev depends upon
        stdDevIndependentParams.clear();
        stdDevIndependentParams.addParameter(stdDevTypeParam);
        stdDevIndependentParams.addParameter(componentParam);

        // params that the exceed. prob. depends upon
        exceedProbIndependentParams.clear();
        exceedProbIndependentParams.addParameter(distanceJBParam);
        exceedProbIndependentParams.addParameter(siteTypeParam);
        exceedProbIndependentParams.addParameter(magParam);
        exceedProbIndependentParams.addParameter(componentParam);
        exceedProbIndependentParams.addParameter(stdDevTypeParam);
        exceedProbIndependentParams.addParameter(sigmaTruncTypeParam);
        exceedProbIndependentParams.addParameter(sigmaTruncLevelParam);

        // params that the IML at exceed. prob. depends upon
        imlAtExceedProbIndependentParams
                .addParameterList(exceedProbIndependentParams);
        imlAtExceedProbIndependentParams.addParameter(exceedProbParam);

    }

    /**
     * Creates the Vs30 site parameter and adds it to the siteParams list. Makes
     * the parameters noneditable.
     */
    protected void initSiteParams() {

        StringConstraint siteConstraint = new StringConstraint();
        siteConstraint.addString(SITE_TYPE_ROCK);
        siteConstraint.addString(SITE_TYPE_SOIL);
        siteConstraint.setNonEditable();
        siteTypeParam =
                new StringParameter(SITE_TYPE_NAME, siteConstraint, null);
        siteTypeParam.setInfo(SITE_TYPE_INFO);
        siteTypeParam.setNonEditable();

        siteParams.clear();
        siteParams.addParameter(siteTypeParam);

    }

    /**
     * Creates the two Potential Earthquake parameters (magParam and
     * fltTypeParam) and adds them to the eqkRuptureParams list. Makes the
     * parameters noneditable.
     */
    protected void initEqkRuptureParams() {

        magParam = new MagParam(MAG_WARN_MIN, MAG_WARN_MAX);

        eqkRuptureParams.clear();
        eqkRuptureParams.addParameter(magParam);

    }

    /**
     * Creates the single Propagation Effect parameter and adds it to the
     * propagationEffectParams list. Makes the parameters noneditable.
     */
    protected void initPropagationEffectParams() {
        distanceJBParam = new DistanceJBParameter(0.0);
        distanceJBParam.addParameterChangeWarningListener(warningListener);
        DoubleConstraint warn =
                new DoubleConstraint(DISTANCE_JB_WARN_MIN, DISTANCE_JB_WARN_MAX);
        warn.setNonEditable();
        distanceJBParam.setWarningConstraint(warn);
        distanceJBParam.setNonEditable();
        propagationEffectParams.addParameter(distanceJBParam);
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
        TreeSet set = new TreeSet();
        Enumeration keys = coefficients.keys();
        while (keys.hasMoreElements()) {
            SEA_1999_AttenRelCoefficients coeff =
                    (SEA_1999_AttenRelCoefficients) coefficients.get(keys
                            .nextElement());
            if (coeff.period >= 0) {
                set.add(new Double(coeff.period));
            }
        }
        Iterator it = set.iterator();
        while (it.hasNext()) {
            periodConstraint.addDouble((Double) it.next());
        }
        periodConstraint.setNonEditable();
        saPeriodParam = new PeriodParam(periodConstraint);
        saDampingParam = new DampingParam();
        saParam = new SA_Param(saPeriodParam, saDampingParam);
        saParam.setNonEditable();

        // Create PGA Parameter (pgaParam):
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
     * Creates other Parameters that the mean or stdDev depends upon, such as
     * the Component or StdDevType parameters.
     */
    protected void initOtherParams() {

        // init other params defined in parent class
        super.initOtherParams();

        // the Component Parameter
        StringConstraint constraint = new StringConstraint();
        constraint.addString(ComponentParam.COMPONENT_AVE_HORZ);
        constraint.addString(ComponentParam.COMPONENT_RANDOM_HORZ);
        constraint.setNonEditable();
        componentParam =
                new ComponentParam(constraint,
                        componentParam.COMPONENT_AVE_HORZ);

        // the stdDevType Parameter
        StringConstraint stdDevTypeConstraint = new StringConstraint();
        stdDevTypeConstraint.addString(StdDevTypeParam.STD_DEV_TYPE_TOTAL);
        stdDevTypeConstraint.addString(StdDevTypeParam.STD_DEV_TYPE_INTER);
        stdDevTypeConstraint.addString(StdDevTypeParam.STD_DEV_TYPE_INTRA);
        stdDevTypeConstraint.addString(StdDevTypeParam.STD_DEV_TYPE_NONE);
        stdDevTypeConstraint.setNonEditable();
        stdDevTypeParam = new StdDevTypeParam(stdDevTypeConstraint);

        // add these to the list
        otherParams.addParameter(componentParam);
        otherParams.addParameter(stdDevTypeParam);

    }

    /**
     * This test reproduces the values listed in Table 3 of the original paper
     * referenced above.
     */
    private void runTest() {
        this.setParamDefaults();
        double per;
        System.out.println("\nRepreduction of Table 3:");
        for (double mag = 5.5; mag <= 7.5; mag += 1.0) {
            this.magParam.setValue(mag);
            for (double dist = 0; dist <= 70.0; dist += 70) {

                distanceJBParam.setValue(new Double(dist));

                siteTypeParam.setValue(SITE_TYPE_ROCK);

                System.out.print(mag + "\t" + dist + "\t" + SITE_TYPE_ROCK);
                setIntensityMeasure(PGA_Param.NAME);
                System.out.print("\t" + (float) Math.exp(getMean()));

                setIntensityMeasure(SA_Param.NAME);
                per = 0.1;
                this.saPeriodParam.setValue(new Double(per));
                System.out
                        .print("\t"
                                + (float) (Math.exp(getMean()) * (980 * per) / (2.0 * Math.PI)));

                setIntensityMeasure(SA_Param.NAME);
                per = 0.5;
                this.saPeriodParam.setValue(new Double(per));
                System.out
                        .print("\t"
                                + (float) (Math.exp(getMean()) * (980 * per) / (2.0 * Math.PI)));

                setIntensityMeasure(SA_Param.NAME);
                per = 2.0;
                this.saPeriodParam.setValue(new Double(per));
                System.out
                        .print("\t"
                                + (float) (Math.exp(getMean()) * (980 * per) / (2.0 * Math.PI))
                                + "\n");

                siteTypeParam.setValue(SITE_TYPE_SOIL);

                System.out.print(mag + "\t" + dist + "\t" + SITE_TYPE_SOIL);
                setIntensityMeasure(PGA_Param.NAME);
                System.out.print("\t" + (float) (Math.exp(getMean())));

                setIntensityMeasure(SA_Param.NAME);
                per = 0.1;
                this.saPeriodParam.setValue(new Double(per));
                System.out
                        .print("\t"
                                + (float) (Math.exp(getMean()) * (980 * per) / (2.0 * Math.PI)));

                setIntensityMeasure(SA_Param.NAME);
                per = 0.5;
                this.saPeriodParam.setValue(new Double(per));
                System.out
                        .print("\t"
                                + (float) (Math.exp(getMean()) * (980 * per) / (2.0 * Math.PI)));

                setIntensityMeasure(SA_Param.NAME);
                per = 2.0;
                this.saPeriodParam.setValue(new Double(per));
                System.out
                        .print("\t"
                                + (float) (Math.exp(getMean()) * (980 * per) / (2.0 * Math.PI))
                                + "\n");

            }
        }
        System.out.print("sigma_ave_horz\t\t");
        setIntensityMeasure(PGA_Param.NAME);
        System.out.print("\t" + (float) (getStdDev() / log2ln));

        setIntensityMeasure(SA_Param.NAME);
        per = 0.1;
        this.saPeriodParam.setValue(new Double(per));
        System.out.print("\t" + (float) (getStdDev() / log2ln));

        setIntensityMeasure(SA_Param.NAME);
        per = 0.5;
        this.saPeriodParam.setValue(new Double(per));
        System.out.print("\t" + (float) (getStdDev() / log2ln));

        setIntensityMeasure(SA_Param.NAME);
        per = 2.0;
        this.saPeriodParam.setValue(new Double(per));
        System.out.print("\t" + (float) (getStdDev() / log2ln) + "\n");

        System.out.print("sigma_rand_horz\t\t");
        this.componentParam.setValue(ComponentParam.COMPONENT_RANDOM_HORZ);
        setIntensityMeasure(PGA_Param.NAME);
        System.out.print("\t" + (float) (getStdDev() / log2ln));

        setIntensityMeasure(SA_Param.NAME);
        per = 0.1;
        this.saPeriodParam.setValue(new Double(per));
        System.out.print("\t" + (float) (getStdDev() / log2ln));

        setIntensityMeasure(SA_Param.NAME);
        per = 0.5;
        this.saPeriodParam.setValue(new Double(per));
        System.out.print("\t" + (float) (getStdDev() / log2ln));

        setIntensityMeasure(SA_Param.NAME);
        per = 2.0;
        this.saPeriodParam.setValue(new Double(per));
        System.out.print("\t" + (float) (getStdDev() / log2ln));
    }

    // this is temporary for testing purposes
    public static void main(String[] args) {
        new SEA_1999_AttenRel(null);
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
     * This creates the hashtable of coefficients for the supported
     * intensityMeasures (im). The key is the im parameter name, plus the period
     * value for SA (separated by "/"). For example, the key for SA at 1.0
     * second period is "SA/1.0".
     */
    protected void initCoefficients() {

        String S = C + ": initCoefficients():";
        if (D) {
            System.out.println(S + "Starting");
        }

        coefficients.clear();

        SEA_1999_AttenRelCoefficients coeff =
                new SEA_1999_AttenRelCoefficients(PGA_Param.NAME, 0.0, 0.299,
                        0.229, 0, -1.052, 0.112, 7.27, 0.172, 0.108, 0.094);

        SEA_1999_AttenRelCoefficients coeff0 =
                new SEA_1999_AttenRelCoefficients(SA_Param.NAME + '/'
                        + (new Double("0.00")).doubleValue(), 0.00, 0.299,
                        0.229, 0, -1.052, 0.112, 7.27, 0.172, 0.108, 0.094);
        SEA_1999_AttenRelCoefficients coeff1 =
                new SEA_1999_AttenRelCoefficients(SA_Param.NAME + '/'
                        + (new Double("0.100")).doubleValue(), 0.100, 2.144,
                        0.327, -0.098, -1.250, 0.064, 9.99, 0.205, 0.181, 0.110);
        SEA_1999_AttenRelCoefficients coeff2 =
                new SEA_1999_AttenRelCoefficients(SA_Param.NAME + '/'
                        + (new Double("0.110")).doubleValue(), 0.110, 2.155,
                        0.318, -0.100, -1.207, 0.064, 9.84, 0.205, 0.168, 0.111);
        SEA_1999_AttenRelCoefficients coeff3 =
                new SEA_1999_AttenRelCoefficients(SA_Param.NAME + '/'
                        + (new Double("0.120")).doubleValue(), 0.120, 2.165,
                        0.313, -0.101, -1.173, 0.065, 9.69, 0.204, 0.156, 0.113);
        SEA_1999_AttenRelCoefficients coeff4 =
                new SEA_1999_AttenRelCoefficients(SA_Param.NAME + '/'
                        + (new Double("0.130")).doubleValue(), 0.130, 2.174,
                        0.309, -0.101, -1.145, 0.067, 9.54, 0.205, 0.146, 0.114);
        SEA_1999_AttenRelCoefficients coeff5 =
                new SEA_1999_AttenRelCoefficients(SA_Param.NAME + '/'
                        + (new Double("0.140")).doubleValue(), 0.140, 2.183,
                        0.307, -0.100, -1.122, 0.069, 9.39, 0.205, 0.137, 0.115);
        SEA_1999_AttenRelCoefficients coeff6 =
                new SEA_1999_AttenRelCoefficients(SA_Param.NAME + '/'
                        + (new Double("0.150")).doubleValue(), 0.150, 2.191,
                        0.305, -0.099, -1.103, 0.072, 9.25, 0.205, 0.129, 0.116);
        SEA_1999_AttenRelCoefficients coeff7 =
                new SEA_1999_AttenRelCoefficients(SA_Param.NAME + '/'
                        + (new Double("0.160")).doubleValue(), 0.160, 2.199,
                        0.305, -0.098, -1.088, 0.075, 9.12, 0.206, 0.122, 0.117);
        SEA_1999_AttenRelCoefficients coeff8 =
                new SEA_1999_AttenRelCoefficients(SA_Param.NAME + '/'
                        + (new Double("0.170")).doubleValue(), 0.170, 2.206,
                        0.305, -0.096, -1.075, 0.078, 8.99, 0.207, 0.116, 0.118);
        SEA_1999_AttenRelCoefficients coeff9 =
                new SEA_1999_AttenRelCoefficients(SA_Param.NAME + '/'
                        + (new Double("0.180")).doubleValue(), 0.180, 2.212,
                        0.306, -0.094, -1.064, 0.081, 8.86, 0.208, 0.110, 0.119);
        SEA_1999_AttenRelCoefficients coeff10 =
                new SEA_1999_AttenRelCoefficients(SA_Param.NAME + '/'
                        + (new Double("0.190")).doubleValue(), 0.190, 2.218,
                        0.308, -0.092, -1.055, 0.085, 8.74, 0.209, 0.105, 0.119);
        SEA_1999_AttenRelCoefficients coeff11 =
                new SEA_1999_AttenRelCoefficients(SA_Param.NAME + '/'
                        + (new Double("0.200")).doubleValue(), 0.200, 2.224,
                        0.309, -0.090, -1.047, 0.088, 8.63, 0.210, 0.100, 0.120);
        SEA_1999_AttenRelCoefficients coeff12 =
                new SEA_1999_AttenRelCoefficients(SA_Param.NAME + '/'
                        + (new Double("0.220")).doubleValue(), 0.220, 2.234,
                        0.313, -0.086, -1.036, 0.095, 8.41, 0.212, 0.092, 0.121);
        SEA_1999_AttenRelCoefficients coeff13 =
                new SEA_1999_AttenRelCoefficients(SA_Param.NAME + '/'
                        + (new Double("0.240")).doubleValue(), 0.240, 2.242,
                        0.318, -0.082, -1.029, 0.102, 8.22, 0.214, 0.086, 0.122);
        SEA_1999_AttenRelCoefficients coeff14 =
                new SEA_1999_AttenRelCoefficients(SA_Param.NAME + '/'
                        + (new Double("0.260")).doubleValue(), 0.260, 2.250,
                        0.323, -0.078, -1.024, 0.108, 8.04, 0.216, 0.081, 0.123);
        SEA_1999_AttenRelCoefficients coeff15 =
                new SEA_1999_AttenRelCoefficients(SA_Param.NAME + '/'
                        + (new Double("0.280")).doubleValue(), 0.280, 2.257,
                        0.329, -0.073, -1.021, 0.115, 7.87, 0.218, 0.076, 0.124);
        SEA_1999_AttenRelCoefficients coeff16 =
                new SEA_1999_AttenRelCoefficients(SA_Param.NAME + '/'
                        + (new Double("0.300")).doubleValue(), 0.300, 2.263,
                        0.334, -0.070, -1.020, 0.121, 7.72, 0.220, 0.073, 0.125);
        SEA_1999_AttenRelCoefficients coeff17 =
                new SEA_1999_AttenRelCoefficients(SA_Param.NAME + '/'
                        + (new Double("0.320")).doubleValue(), 0.320, 2.268,
                        0.340, -0.066, -1.019, 0.126, 7.58, 0.221, 0.070, 0.126);
        SEA_1999_AttenRelCoefficients coeff18 =
                new SEA_1999_AttenRelCoefficients(SA_Param.NAME + '/'
                        + (new Double("0.340")).doubleValue(), 0.340, 2.272,
                        0.345, -0.062, -1.020, 0.132, 7.45, 0.223, 0.067, 0.126);
        SEA_1999_AttenRelCoefficients coeff19 =
                new SEA_1999_AttenRelCoefficients(SA_Param.NAME + '/'
                        + (new Double("0.360")).doubleValue(), 0.360, 2.276,
                        0.350, -0.059, -1.021, 0.137, 7.33, 0.225, 0.065, 0.127);
        SEA_1999_AttenRelCoefficients coeff20 =
                new SEA_1999_AttenRelCoefficients(SA_Param.NAME + '/'
                        + (new Double("0.380")).doubleValue(), 0.380, 2.279,
                        0.356, -0.055, -1.023, 0.142, 7.22, 0.227, 0.064, 0.128);
        SEA_1999_AttenRelCoefficients coeff21 =
                new SEA_1999_AttenRelCoefficients(SA_Param.NAME + '/'
                        + (new Double("0.400")).doubleValue(), 0.400, 2.282,
                        0.361, -0.052, -1.025, 0.147, 7.11, 0.228, 0.063, 0.128);
        SEA_1999_AttenRelCoefficients coeff22 =
                new SEA_1999_AttenRelCoefficients(SA_Param.NAME + '/'
                        + (new Double("0.420")).doubleValue(), 0.420, 2.285,
                        0.365, -0.049, -1.027, 0.151, 7.02, 0.230, 0.062, 0.129);
        SEA_1999_AttenRelCoefficients coeff23 =
                new SEA_1999_AttenRelCoefficients(SA_Param.NAME + '/'
                        + (new Double("0.440")).doubleValue(), 0.440, 2.287,
                        0.370, -0.047, -1.030, 0.155, 6.93, 0.231, 0.061, 0.129);
        SEA_1999_AttenRelCoefficients coeff24 =
                new SEA_1999_AttenRelCoefficients(SA_Param.NAME + '/'
                        + (new Double("0.460")).doubleValue(), 0.460, 2.289,
                        0.375, -0.044, -1.032, 0.159, 6.85, 0.233, 0.061, 0.129);
        SEA_1999_AttenRelCoefficients coeff25 =
                new SEA_1999_AttenRelCoefficients(SA_Param.NAME + '/'
                        + (new Double("0.480")).doubleValue(), 0.480, 2.291,
                        0.379, -0.042, -1.035, 0.163, 6.77, 0.234, 0.060, 0.130);
        SEA_1999_AttenRelCoefficients coeff26 =
                new SEA_1999_AttenRelCoefficients(SA_Param.NAME + '/'
                        + (new Double("0.500")).doubleValue(), 0.500, 2.292,
                        0.384, -0.039, -1.038, 0.166, 6.70, 0.235, 0.061, 0.130);
        SEA_1999_AttenRelCoefficients coeff27 =
                new SEA_1999_AttenRelCoefficients(SA_Param.NAME + '/'
                        + (new Double("0.550")).doubleValue(), 0.550, 2.294,
                        0.394, -0.034, -1.044, 0.174, 6.55, 0.238, 0.061, 0.131);
        SEA_1999_AttenRelCoefficients coeff28 =
                new SEA_1999_AttenRelCoefficients(SA_Param.NAME + '/'
                        + (new Double("0.600")).doubleValue(), 0.600, 2.295,
                        0.403, -0.030, -1.051, 0.181, 6.42, 0.241, 0.063, 0.132);
        SEA_1999_AttenRelCoefficients coeff29 =
                new SEA_1999_AttenRelCoefficients(SA_Param.NAME + '/'
                        + (new Double("0.650")).doubleValue(), 0.650, 2.295,
                        0.411, -0.026, -1.057, 0.187, 6.32, 0.243, 0.065, 0.132);
        SEA_1999_AttenRelCoefficients coeff30 =
                new SEA_1999_AttenRelCoefficients(SA_Param.NAME + '/'
                        + (new Double("0.700")).doubleValue(), 0.700, 2.294,
                        0.418, -0.023, -1.062, 0.192, 6.23, 0.245, 0.068, 0.133);
        SEA_1999_AttenRelCoefficients coeff31 =
                new SEA_1999_AttenRelCoefficients(SA_Param.NAME + '/'
                        + (new Double("0.750")).doubleValue(), 0.750, 2.292,
                        0.425, -0.020, -1.067, 0.197, 6.17, 0.247, 0.071, 0.133);
        SEA_1999_AttenRelCoefficients coeff32 =
                new SEA_1999_AttenRelCoefficients(SA_Param.NAME + '/'
                        + (new Double("0.800")).doubleValue(), 0.800, 2.290,
                        0.431, -0.018, -1.071, 0.200, 6.11, 0.249, 0.074, 0.134);
        SEA_1999_AttenRelCoefficients coeff33 =
                new SEA_1999_AttenRelCoefficients(SA_Param.NAME + '/'
                        + (new Double("0.850")).doubleValue(), 0.850, 2.287,
                        0.437, -0.016, -1.075, 0.203, 6.07, 0.250, 0.077, 0.134);
        SEA_1999_AttenRelCoefficients coeff34 =
                new SEA_1999_AttenRelCoefficients(SA_Param.NAME + '/'
                        + (new Double("0.900")).doubleValue(), 0.900, 2.284,
                        0.442, -0.015, -1.078, 0.206, 6.04, 0.251, 0.081, 0.134);
        SEA_1999_AttenRelCoefficients coeff35 =
                new SEA_1999_AttenRelCoefficients(SA_Param.NAME + '/'
                        + (new Double("0.950")).doubleValue(), 0.950, 2.280,
                        0.446, -0.014, -1.081, 0.208, 6.02, 0.253, 0.085, 0.135);
        SEA_1999_AttenRelCoefficients coeff36 =
                new SEA_1999_AttenRelCoefficients(SA_Param.NAME + '/'
                        + (new Double("1.000")).doubleValue(), 1.0, 2.276,
                        0.450, -0.014, -1.083, 0.210, 6.01, 0.254, 0.089, 0.135);
        SEA_1999_AttenRelCoefficients coeff37 =
                new SEA_1999_AttenRelCoefficients(SA_Param.NAME + '/'
                        + (new Double("1.100")).doubleValue(), 1.1, 2.267,
                        0.457, -0.013, -1.085, 0.213, 6.01, 0.255, 0.097, 0.135);
        SEA_1999_AttenRelCoefficients coeff38 =
                new SEA_1999_AttenRelCoefficients(SA_Param.NAME + '/'
                        + (new Double("1.200")).doubleValue(), 1.2, 2.258,
                        0.462, -0.014, -1.086, 0.214, 6.03, 0.257, 0.106, 0.136);
        SEA_1999_AttenRelCoefficients coeff39 =
                new SEA_1999_AttenRelCoefficients(SA_Param.NAME + '/'
                        + (new Double("1.300")).doubleValue(), 1.3, 2.248,
                        0.466, -0.015, -1.085, 0.214, 6.07, 0.258, 0.115, 0.136);
        SEA_1999_AttenRelCoefficients coeff40 =
                new SEA_1999_AttenRelCoefficients(SA_Param.NAME + '/'
                        + (new Double("1.400")).doubleValue(), 1.4, 2.237,
                        0.469, -0.017, -1.083, 0.213, 6.13, 0.258, 0.123, 0.136);
        SEA_1999_AttenRelCoefficients coeff41 =
                new SEA_1999_AttenRelCoefficients(SA_Param.NAME + '/'
                        + (new Double("1.500")).doubleValue(), 1.5, 2.226,
                        0.471, -0.019, -1.079, 0.212, 6.21, 0.259, 0.132, 0.137);
        SEA_1999_AttenRelCoefficients coeff42 =
                new SEA_1999_AttenRelCoefficients(SA_Param.NAME + '/'
                        + (new Double("1.600")).doubleValue(), 1.6, 2.215,
                        0.472, -0.022, -1.075, 0.210, 6.29, 0.259, 0.141, 0.137);
        SEA_1999_AttenRelCoefficients coeff43 =
                new SEA_1999_AttenRelCoefficients(SA_Param.NAME + '/'
                        + (new Double("1.700")).doubleValue(), 1.7, 2.203,
                        0.473, -0.025, -1.070, 0.207, 6.39, 0.259, 0.150, 0.137);
        SEA_1999_AttenRelCoefficients coeff44 =
                new SEA_1999_AttenRelCoefficients(SA_Param.NAME + '/'
                        + (new Double("1.800")).doubleValue(), 1.8, 2.192,
                        0.472, -0.029, -1.063, 0.204, 6.49, 0.259, 0.158, 0.137);
        SEA_1999_AttenRelCoefficients coeff45 =
                new SEA_1999_AttenRelCoefficients(SA_Param.NAME + '/'
                        + (new Double("1.900")).doubleValue(), 1.9, 2.180,
                        0.472, -0.032, -1.056, 0.201, 6.60, 0.258, 0.167, 0.137);
        SEA_1999_AttenRelCoefficients coeff46 =
                new SEA_1999_AttenRelCoefficients(SA_Param.NAME + '/'
                        + (new Double("2.000")).doubleValue(), 2.0, 2.168,
                        0.471, -0.037, -1.049, 0.197, 6.71, 0.258, 0.175, 0.137);

        coefficients.put(coeff.getName(), coeff);
        coefficients.put(coeff0.getName(), coeff0);
        coefficients.put(coeff1.getName(), coeff1);
        coefficients.put(coeff2.getName(), coeff2);
        coefficients.put(coeff3.getName(), coeff3);
        coefficients.put(coeff4.getName(), coeff4);
        coefficients.put(coeff5.getName(), coeff5);
        coefficients.put(coeff6.getName(), coeff6);
        coefficients.put(coeff7.getName(), coeff7);
        coefficients.put(coeff8.getName(), coeff8);
        coefficients.put(coeff9.getName(), coeff9);

        coefficients.put(coeff10.getName(), coeff10);
        coefficients.put(coeff11.getName(), coeff11);
        coefficients.put(coeff12.getName(), coeff12);
        coefficients.put(coeff13.getName(), coeff13);
        coefficients.put(coeff14.getName(), coeff14);
        coefficients.put(coeff15.getName(), coeff15);
        coefficients.put(coeff16.getName(), coeff16);
        coefficients.put(coeff17.getName(), coeff17);
        coefficients.put(coeff18.getName(), coeff18);
        coefficients.put(coeff19.getName(), coeff19);

        coefficients.put(coeff20.getName(), coeff20);
        coefficients.put(coeff21.getName(), coeff21);
        coefficients.put(coeff22.getName(), coeff22);
        coefficients.put(coeff23.getName(), coeff23);
        coefficients.put(coeff24.getName(), coeff24);
        coefficients.put(coeff25.getName(), coeff25);
        coefficients.put(coeff26.getName(), coeff26);
        coefficients.put(coeff27.getName(), coeff27);
        coefficients.put(coeff28.getName(), coeff28);
        coefficients.put(coeff29.getName(), coeff29);

        coefficients.put(coeff30.getName(), coeff30);
        coefficients.put(coeff31.getName(), coeff31);
        coefficients.put(coeff32.getName(), coeff32);
        coefficients.put(coeff33.getName(), coeff33);
        coefficients.put(coeff34.getName(), coeff34);
        coefficients.put(coeff35.getName(), coeff35);
        coefficients.put(coeff36.getName(), coeff36);
        coefficients.put(coeff37.getName(), coeff37);
        coefficients.put(coeff38.getName(), coeff38);
        coefficients.put(coeff39.getName(), coeff39);

        coefficients.put(coeff40.getName(), coeff40);
        coefficients.put(coeff41.getName(), coeff41);
        coefficients.put(coeff42.getName(), coeff42);
        coefficients.put(coeff43.getName(), coeff43);
        coefficients.put(coeff44.getName(), coeff44);
        coefficients.put(coeff45.getName(), coeff45);
        coefficients.put(coeff46.getName(), coeff46);

    }

    /**
     * <b>Title:</b> SEA_1999_AttenRelCoefficients<br>
     * <b>Description:</b> This class encapsulates all the coefficients needed
     * to calculate the Mean and StdDev for the SEA_1999_AttenRel. One instance
     * of this class holds the set of coefficients for each period (one row of
     * their table 8).<br>
     * <b>Copyright:</b> Copyright (c) 2001 <br>
     * <b>Company:</b> <br>
     */

    class SEA_1999_AttenRelCoefficients implements NamedObjectAPI {

        protected final static String C = "SEA_1999_AttenRelCoefficients";
        protected final static boolean D = false;
        /** For serialization. */
        private static final long serialVersionUID = 1234567890987654329L;

        protected String name;
        protected double period = -1;
        protected double b1;
        protected double b2;
        protected double b3;
        protected double b5;
        protected double b6;
        protected double h;
        protected double sigma1;
        protected double sigma2;
        protected double sigma3; // this is listed as sigma4 in the on-line
                                 // table of coefficients

        /**
         * Constructor for the SEA_1999_AttenRelCoefficients object that sets
         * all values at once
         * 
         * @param name
         *            Description of the Parameter
         */
        public SEA_1999_AttenRelCoefficients(String name, double period,
                double b1, double b2, double b3, double b5, double b6,
                double h, double sigma1, double sigma2, double sigma3) {

            this.name = name;
            this.period = period;
            this.b1 = b1;
            this.b2 = b2;
            this.b3 = b3;
            this.b5 = b5;
            this.b6 = b6;
            this.h = h;
            this.sigma1 = sigma1;
            this.sigma2 = sigma2;
            this.sigma3 = sigma3;
        }

        /**
         * Gets the name attribute of the BJF_1997_AttenRelCoefficients object
         * 
         * @return The name value
         */
        public String getName() {
            return name;
        }

        /**
         * Debugging - prints out all cefficient names and values
         * 
         * @return Description of the Return Value
         */
        public String toString() {

            StringBuffer b = new StringBuffer();
            b.append(C);
            b.append("\n  Name = " + name);
            b.append("\n  Period = " + period);
            b.append("\n  b1 = " + b1);
            b.append("\n  b2 = " + b2);
            b.append("\n  b3 = " + b3);
            b.append("\n  b5 = " + b5);
            b.append("\n  b6 = " + b6);
            b.append("\n  h = " + h);
            b.append("\n  sigma1 = " + sigma1);
            b.append("\n  sigma2 = " + sigma2);
            b.append("\n  sigma3 = " + sigma3);
            return b.toString();
        }
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
                "http://www.opensha.org/documentation/modelsImplemented/attenRel/SEA_1999.html");
    }

}
