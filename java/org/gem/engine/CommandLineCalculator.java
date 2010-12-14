package org.gem.engine;

import java.io.IOException;
import java.lang.reflect.Type;
import java.util.ArrayList;
import java.util.HashMap;
import java.util.Iterator;
import java.util.Properties;
import java.util.Random;

import org.apache.commons.configuration.AbstractFileConfiguration;
import org.apache.commons.configuration.Configuration;
import org.apache.commons.configuration.ConfigurationConverter;
import org.apache.commons.configuration.ConfigurationException;
import org.apache.commons.configuration.PropertiesConfiguration;
import org.apache.commons.io.FilenameUtils;
import org.apache.commons.logging.Log;
import org.apache.commons.logging.LogFactory;
import org.gem.JsonSerializer;
import org.gem.ScalarIMRJsonAdapter;
import org.gem.engine.CalculatorConfigHelper.ConfigItems;
import org.gem.engine.hazard.GEM1ERF;
import org.gem.engine.hazard.redis.Cache;
import org.gem.engine.logictree.LogicTree;
import org.gem.engine.logictree.LogicTreeBranch;
import org.gem.engine.logictree.LogicTreeRule;
import org.gem.engine.logictree.LogicTreeRuleParam;
import org.opensha.commons.data.TimeSpan;
import org.opensha.sha.earthquake.rupForecastImpl.GEM1.SourceData.GEMAreaSourceData;
import org.opensha.sha.earthquake.rupForecastImpl.GEM1.SourceData.GEMFaultSourceData;
import org.opensha.sha.earthquake.rupForecastImpl.GEM1.SourceData.GEMPointSourceData;
import org.opensha.sha.earthquake.rupForecastImpl.GEM1.SourceData.GEMSourceData;
import org.opensha.sha.earthquake.rupForecastImpl.GEM1.SourceData.GEMSubductionFaultSourceData;
import org.opensha.sha.imr.ScalarIntensityMeasureRelationshipAPI;
import org.opensha.sha.magdist.GutenbergRichterMagFreqDist;
import org.opensha.sha.magdist.IncrementalMagFreqDist;
import org.opensha.sha.util.TectonicRegionType;

import com.google.gson.Gson;
import com.google.gson.GsonBuilder;
import com.google.gson.reflect.TypeToken;

public class CommandLineCalculator {

    /*
     * Apache commons logging, not log4j specifically Note that for application
     * code, declaring the log member as "static" is more efficient as one Log
     * object is created per class, and is recommended. However this is not safe
     * to do for a class which may be deployed via a "shared" classloader in a
     * servlet or j2ee container or similar environment. If the class may end up
     * invoked with different thread-context-classloader values set then the
     * member must not be declared static. The use of "static" should therefore
     * be avoided in code within any "library" type project.
     */
    private static Log logger = LogFactory.getLog(CommandLineCalculator.class);

    private final Configuration config;
    private boolean hasPath;
    private Cache kvs;

    public CommandLineCalculator(Properties p) {
        config = ConfigurationConverter.getConfiguration(p);
    }

    public CommandLineCalculator(String calcConfigFile)
            throws ConfigurationException {
        config = new PropertiesConfiguration();
        ((PropertiesConfiguration) config).load(calcConfigFile);
        System.out.println(config);
        hasPath = true;
    }

    public CommandLineCalculator(Cache cache, String key) {
        kvs = cache;
        Properties properties =
                new Gson().fromJson((String) cache.get(key), Properties.class);

        config = ConfigurationConverter.getConfiguration(properties);
    }

    private String configFilesPath() {
        return FilenameUtils.getFullPath(((AbstractFileConfiguration) config)
                .getPath());
    }

    private String getRelativePath(String key) {
        return configFilesPath() + config.getString(key);
    }

    /**
     * Two calculators are equal when have the same configuration.
     * 
     * @param obj
     *            the calculator to compare on
     * @return true if the calculators are equal, false otherwise
     */
    @Override
    public boolean equals(Object obj) {
        if (!(obj instanceof CommandLineCalculator)) {
            return false;
        }

        CommandLineCalculator other = (CommandLineCalculator) obj;

        Properties thisConfig = ConfigurationConverter.getProperties(config);

        Properties otherConfig =
                ConfigurationConverter.getProperties(other.config);

        return thisConfig.equals(otherConfig);
    }

    public void sampleAndSaveERFTree(Cache cache, String key, long seed)
            throws IOException {
        logger.warn("Random seed for ERFLT is " + Long.toString(seed));
        ArrayList<GEMSourceData> sources =
                sampleSourceModelLogicTree(createErfLogicTreeData()
                        .getErfLogicTree(), seed);
        JsonSerializer.serializeSourceList(cache, key, sources);
    }

    public void sampleAndSaveGMPETree(Cache cache, String key, long seed)
            throws IOException {
        logger.warn("Random seed for GMPELT is " + Long.toString(seed));
        HashMap<TectonicRegionType, ScalarIntensityMeasureRelationshipAPI> gmpe_map =
                sampleGemLogicTreeGMPE(createGmpeLogicTreeData()
                        .getGmpeLogicTreeHashMap(), seed);

        GsonBuilder gson = new GsonBuilder();
        gson.registerTypeAdapter(ScalarIntensityMeasureRelationshipAPI.class,
                new ScalarIMRJsonAdapter());

        Type hashType =
                new TypeToken<HashMap<TectonicRegionType, ScalarIntensityMeasureRelationshipAPI>>() {
                }.getType();
        logger.debug("GMPE HASHMAP: " + gmpe_map);
        String json = gson.create().toJson(gmpe_map, hashType);
        cache.set(key, json);
    }

    /**
     * Generate N source models (each represented by an array list of
     * GEMSourceData objects), by randomly sampling the source model logic tree.
     * 
     * @param lt
     *            : source model logic tree
     * @param N
     *            : number of models to be generated
     * @param seed
     *            : seed number for the random number generator
     * @return
     */
    public ArrayList<GEMSourceData> sampleSourceModelLogicTree(
            LogicTree<ArrayList<GEMSourceData>> lt, long seed) {

        ArrayList<GEMSourceData> srcList = null;
        Random rn = new Random(seed);

        // sample first branching level to get the starting source model
        int branchNumber = lt.sampleBranchingLevel(0, rn);
        LogicTreeBranch branch =
                lt.getBranchingLevel(0).getBranch(branchNumber - 1);
        if (branch.getNameInputFile() != null) {
            String sourceName = configFilesPath() + branch.getNameInputFile();

            InputModelData inputModelData =
                    new InputModelData(sourceName, config
                            .getDouble(ConfigItems.WIDTH_OF_MFD_BIN.name()));
            // load sources
            srcList = inputModelData.getSourceList();
        } else {
            String msg =
                    "The first branching level of the ERF logic tree does"
                            + " not contain a source model!!\n"
                            + "Please correct your input!\n Execution stopped!";
            logger.info(msg);
            throw new IllegalArgumentException(msg);
        }

        // loop over sources
        // for each source, loop over remaining branching levels and apply
        // uncertainties
        int numBranchingLevels = lt.getBranchingLevelsList().size();
        int sourceIndex = 0;
        for (GEMSourceData src : srcList) {
            for (int i = 1; i < numBranchingLevels; i++) {
                // sample the current branching level
                branchNumber = lt.sampleBranchingLevel(i, rn);
                // get the sampled branch
                branch = lt.getBranchingLevel(i).getBranch(branchNumber - 1);
                if (branch.getRule() != null) {
                    // at the moment we apply rules to all source
                    // typologies. In
                    // the future we may want
                    // to apply some filter (i.e. apply rule to this source
                    // type
                    // only...)
                    // if area source
                    if (src instanceof GEMAreaSourceData) {
                        // replace the old source with the new source
                        // accordingly to the rule
                        srcList.set(sourceIndex, applyRuleToAreaSource(
                                (GEMAreaSourceData) src, branch.getRule()));
                    }
                    // if point source
                    if (src instanceof GEMPointSourceData) {
                        // replace the old source with the new source
                        // accordingly to the rule
                        srcList.set(sourceIndex, applyRuleToPointSource(
                                (GEMPointSourceData) src, branch.getRule()));
                    }
                    // if fault source
                    if (src instanceof GEMFaultSourceData) {
                        // replace the old source with the new source
                        // accordingly to the rule
                        srcList.set(sourceIndex, applyRuleToFaultSource(
                                (GEMFaultSourceData) src, branch.getRule()));
                    }
                    // if subduction source
                    if (src instanceof GEMSubductionFaultSourceData) {
                        // replace the old source with the new source
                        // accordingly to the rule
                        srcList.set(sourceIndex,
                                applyRuleToSubductionFaultSource(
                                        (GEMSubductionFaultSourceData) src,
                                        branch.getRule()));
                    }
                } else {
                    // rule is not defined:
                    String msg =
                            "No rule is defined at branching level: " + i
                                    + "\n" + "Please correct your input!\n"
                                    + "Execution stopped!";
                    logger.info(msg);
                    throw new IllegalArgumentException(msg);
                } // end if no rule is defined
            } // end loop over branching levels
            sourceIndex = sourceIndex + 1;
        } // end loop over sources
        return srcList;
    }

    /**
     * This method applies an "uncertainty" rule to an area source data object
     * 
     * @param areaSrc
     *            : source data object subject to uncertainty
     * @param rule
     *            : GEMLogicTreeRule specifing parameter uncertainty
     * @return: a new GEMAreaSourceData object with the parameter subject to the
     *          uncertainty changed according to the rule. In case the rule is
     *          not recognized an error is thrown and execution stops
     */
    private static GEMAreaSourceData applyRuleToAreaSource(
            GEMAreaSourceData areaSrc, LogicTreeRule rule) {
        // define new area source
        GEMAreaSourceData newAreaSrc = areaSrc;
        // if uncertainties on GR Mmax or GR b value
        if (rule.getRuleName().toString().equalsIgnoreCase(
                LogicTreeRuleParam.mMaxGRRelative.toString())
                || rule.getRuleName().toString().equalsIgnoreCase(
                        LogicTreeRuleParam.bGRRelative.toString())) {
            // loop over mfds
            // mfd index
            int mfdIndex = 0;
            for (IncrementalMagFreqDist mfd : areaSrc.getMagfreqDistFocMech()
                    .getMagFreqDistList()) {
                if (mfd instanceof GutenbergRichterMagFreqDist) {
                    // new mfd
                    GutenbergRichterMagFreqDist newMfdGr = null;
                    if (rule.getRuleName().toString().equalsIgnoreCase(
                            LogicTreeRuleParam.mMaxGRRelative.toString())) {
                        // uncertainties on Mmax
                        newMfdGr =
                                applyMmaxGrRelative(
                                        (GutenbergRichterMagFreqDist) mfd, rule
                                                .getVal(), areaSrc.getName());
                    } else if (rule.getRuleName().toString().equalsIgnoreCase(
                            LogicTreeRuleParam.bGRRelative.toString())) {
                        // uncertainties on b value
                        newMfdGr =
                                applybGrRelative(
                                        (GutenbergRichterMagFreqDist) mfd, rule
                                                .getVal(), areaSrc.getName());
                    }
                    // substitute old mfd with new mfd
                    newAreaSrc.getMagfreqDistFocMech().getMagFreqDistList()[mfdIndex] =
                            newMfdGr;
                } // end if mfd is GR
                mfdIndex = mfdIndex + 1;
            } // for (loop over mfds)
            // return new area source
            return newAreaSrc;
        } else {
            // not(rule == mMaxGRRelative || == bGRRelative)
            String msg =
                    "Rule: " + rule.getRuleName().toString()
                            + " not supported.\n"
                            + "Check your input. Execution is stopped.";
            logger.info(msg);
            throw new IllegalArgumentException(msg);
        }
    } // applyRuleToAreaSource()

    /**
     * This method applies an "uncertainty" rule to a point source data object
     * 
     * @param pntSrc
     *            : source data object subject to uncertainty
     * @param rule
     *            : GEMLogicTreeRule specifing parameter uncertainty
     * @return: a new GEMPointSourceData object with the parameter subject to
     *          the uncertainty changed according to the rule. In case the rule
     *          is not recognized an error is thrown and execution stops
     */
    private static GEMPointSourceData applyRuleToPointSource(
            GEMPointSourceData pntSrc, LogicTreeRule rule) {
        // new point source
        GEMPointSourceData newPntSource = pntSrc;
        // if uncertainties on GR Mmax or GR b value
        if (rule.getRuleName().toString().equalsIgnoreCase(
                LogicTreeRuleParam.mMaxGRRelative.toString())
                || rule.getRuleName().toString().equalsIgnoreCase(
                        LogicTreeRuleParam.bGRRelative.toString())) {
            // loop over mfds
            // mfd index
            int mfdIndex = 0;
            for (IncrementalMagFreqDist mfd : pntSrc.getHypoMagFreqDistAtLoc()
                    .getMagFreqDistList()) {
                if (mfd instanceof GutenbergRichterMagFreqDist) {
                    GutenbergRichterMagFreqDist newMfdGr = null;
                    // create new mfd by applying rule
                    if (rule.getRuleName().toString().equalsIgnoreCase(
                            LogicTreeRuleParam.mMaxGRRelative.toString())) {
                        newMfdGr =
                                applyMmaxGrRelative(
                                        (GutenbergRichterMagFreqDist) mfd, rule
                                                .getVal(), pntSrc.getName());
                    } else if (rule.getRuleName().toString().equalsIgnoreCase(
                            LogicTreeRuleParam.bGRRelative.toString())) {
                        newMfdGr =
                                applybGrRelative(
                                        (GutenbergRichterMagFreqDist) mfd, rule
                                                .getVal(), pntSrc.getName());
                    }
                    // substitute old mfd with new mfd
                    newPntSource.getHypoMagFreqDistAtLoc().getMagFreqDistList()[mfdIndex] =
                            newMfdGr;
                } // if mfd is GR
                mfdIndex = mfdIndex + 1;
            } // for (loop over mfd)
            return newPntSource;
        } else {
            // not(rule == mMaxGRRelative || == bGRRelative)
            String msg =
                    "Rule: " + rule.getRuleName().toString()
                            + " not supported.\n"
                            + "Check your input. Execution is stopped.";
            logger.info(msg);
            throw new IllegalArgumentException(msg);
        }
    } // applyRuleToPointSource()

    /**
     * This method applies an "uncertainty" rule to a fault source data object
     * 
     * @param faultSrc
     *            : source data object subject to uncertainty
     * @param rule
     *            : GEMLogicTreeRule specifing parameter uncertainty
     * @return: a new GEMFaultSourceData object with the parameter subject to
     *          the uncertainty changed according to the rule. In case the rule
     *          is not recognized an error is thrown and execution stops
     */
    private static GEMFaultSourceData applyRuleToFaultSource(
            GEMFaultSourceData faultSrc, LogicTreeRule rule) {
        // if uncertainties on GR Mmax or GR b value
        if (rule.getRuleName().toString().equalsIgnoreCase(
                LogicTreeRuleParam.mMaxGRRelative.toString())
                || rule.getRuleName().toString().equalsIgnoreCase(
                        LogicTreeRuleParam.bGRRelative.toString())) {
            // mfd
            IncrementalMagFreqDist mfd = faultSrc.getMfd();
            if (mfd instanceof GutenbergRichterMagFreqDist) {
                GutenbergRichterMagFreqDist newMfdGr = null;
                // create new mfd by applying rule
                if (rule.getRuleName().toString().equalsIgnoreCase(
                        LogicTreeRuleParam.mMaxGRRelative.toString())) {
                    newMfdGr =
                            applyMmaxGrRelative(
                                    (GutenbergRichterMagFreqDist) mfd, rule
                                            .getVal(), faultSrc.getName());
                } else if (rule.getRuleName().toString().equalsIgnoreCase(
                        LogicTreeRuleParam.bGRRelative.toString())) {
                    newMfdGr =
                            applybGrRelative((GutenbergRichterMagFreqDist) mfd,
                                    rule.getVal(), faultSrc.getName());
                }
                // return new fault source with new mfd
                return new GEMFaultSourceData(faultSrc.getID(), faultSrc
                        .getName(), faultSrc.getTectReg(), newMfdGr, faultSrc
                        .getTrace(), faultSrc.getDip(), faultSrc.getDip(),
                        faultSrc.getSeismDepthLow(), faultSrc
                                .getSeismDepthUpp(), faultSrc
                                .getFloatRuptureFlag());
            } else {
                // mfd is not GR
                // if the uncertainty do not apply return the unchanged object
                return faultSrc;
            }
        } else {
            // not(rule == mMaxGRRelative || == bGRRelative)
            String msg =
                    "Rule: " + rule.getRuleName().toString()
                            + " not supported.\n"
                            + "Check your input. Execution is stopped.";
            logger.info(msg);
            throw new IllegalArgumentException(msg);
        }
    } // applyRuleToFaultSource()

    /**
     * This method applies an "uncertainty" rule to a subduction source data
     * object
     * 
     * @param subFaultSrc
     *            : source data object subject to uncertainty
     * @param rule
     *            : GEMLogicTreeRule specifing parameter uncertainty
     * @return: a new GEMSubductionSourceData object with the parameter subject
     *          to uncertainty changed according to the rule. In case the rule
     *          is not recognized an error is thrown and execution stops
     */
    private static GEMSubductionFaultSourceData applyRuleToSubductionFaultSource(
            GEMSubductionFaultSourceData subFaultSrc, LogicTreeRule rule) {

        // if uncertainties on GR Mmax or GR b value
        if (rule.getRuleName().toString().equalsIgnoreCase(
                LogicTreeRuleParam.mMaxGRRelative.toString())
                || rule.getRuleName().toString().equalsIgnoreCase(
                        LogicTreeRuleParam.bGRRelative.toString())) {

            // mfd
            IncrementalMagFreqDist mfd = subFaultSrc.getMfd();

            if (mfd instanceof GutenbergRichterMagFreqDist) {

                GutenbergRichterMagFreqDist newMfdGr = null;

                // create new mfd by applying rule
                if (rule.getRuleName().toString().equalsIgnoreCase(
                        LogicTreeRuleParam.mMaxGRRelative.toString())) {
                    newMfdGr =
                            applyMmaxGrRelative(
                                    (GutenbergRichterMagFreqDist) mfd, rule
                                            .getVal(), subFaultSrc.getName());
                } else if (rule.getRuleName().toString().equalsIgnoreCase(
                        LogicTreeRuleParam.bGRRelative.toString())) {
                    newMfdGr =
                            applybGrRelative((GutenbergRichterMagFreqDist) mfd,
                                    rule.getVal(), subFaultSrc.getName());
                }

                // return new subduction fault source with the new mfd
                return new GEMSubductionFaultSourceData(subFaultSrc.getID(),
                        subFaultSrc.getName(), subFaultSrc.getTectReg(),
                        subFaultSrc.getTopTrace(),
                        subFaultSrc.getBottomTrace(), subFaultSrc.getRake(),
                        newMfdGr, subFaultSrc.getFloatRuptureFlag());

            } // end if mfd is GR
            // if uncertainty does not apply return unchanged object
            else {
                return subFaultSrc;
            }

        }// end if rule == mMaxGRRelative || == bGRRelative
        else {
            String msg =
                    "Rule: " + rule.getRuleName().toString()
                            + " not supported.\n"
                            + "Check your input. Execution is stopped.";
            logger.info(msg);
            throw new IllegalArgumentException(msg);
        }
    } // applyRuleToSubductionFaultSource()

    /**
     * 
     * @param mfdGR
     *            : original magnitude frequency distribution
     * @param deltaMmax
     *            : uncertainty on maximum magnitude
     * @param areaSrc
     *            : source
     * @return
     */
    private static GutenbergRichterMagFreqDist applyMmaxGrRelative(
            GutenbergRichterMagFreqDist mfdGR, double deltaMmax,
            String sourceName) {

        // minimum magnitude
        double mMin = mfdGR.getMagLower();
        // b value
        double bVal = mfdGR.get_bValue();
        // total moment rate
        double totMoRate = mfdGR.getTotalMomentRate();
        // deltaM
        double deltaM = mfdGR.getDelta();

        // calculate new mMax value
        // old mMax value
        double mMax = mfdGR.getMagUpper();
        // add uncertainty value (deltaM/2 is added because mMax
        // refers to bin center
        mMax = mMax + deltaM / 2 + deltaMmax;
        // round mMax with respect to deltaM
        mMax = Math.round(mMax / deltaM) * deltaM;
        // move back to bin center
        mMax = mMax - deltaM / 2;
        // System.out.println("New mMax: "+mMax);

        if (mMax - mMin >= deltaM) {

            // calculate number of magnitude values
            int numVal = (int) Math.round((mMax - mMin) / deltaM + 1);

            // create new GR mfd
            GutenbergRichterMagFreqDist newMfdGr =
                    new GutenbergRichterMagFreqDist(mMin, numVal, deltaM);
            newMfdGr.setAllButTotCumRate(mMin, mMax, totMoRate, bVal);

            // return new mfd
            return newMfdGr;

        } else {
            // stop execution and return null
            logger
                    .info("Uncertaintiy value: "
                            + deltaMmax
                            + " on maximum magnitude for source: "
                            + sourceName
                            + " give maximum magnitude smaller than minimum magnitude!\n"
                            + "Check your input. Execution stopped.");
            // System.out.println("Uncertaintiy value: " + deltaMmax +
            // " on maximum magnitude for source: " + sourceName
            // + " give maximum magnitude smaller than minimum magnitude!");
            // System.out.println("Check your input. Execution stopped.");
            return null;
        }

    }

    private static GutenbergRichterMagFreqDist applybGrRelative(
            GutenbergRichterMagFreqDist mfdGR, double deltaB, String sourceName) {

        // minimum magnitude
        double mMin = mfdGR.getMagLower();
        // maximum magnitude
        double mMax = mfdGR.getMagUpper();
        // b value
        double bVal = mfdGR.get_bValue();
        // total moment rate
        double totMoRate = mfdGR.getTotalMomentRate();
        // deltaM
        double deltaM = mfdGR.getDelta();

        // calculate new b value
        bVal = bVal + deltaB;

        if (bVal >= 0.0) {

            // calculate number of magnitude values
            int numVal = (int) Math.round((mMax - mMin) / deltaM + 1);

            // create new GR mfd
            GutenbergRichterMagFreqDist newMfdGr =
                    new GutenbergRichterMagFreqDist(mMin, numVal, deltaM);
            newMfdGr.setAllButTotCumRate(mMin, mMax, totMoRate, bVal);

            // return new mfd
            return newMfdGr;

        } else {
            String msg =
                    "Uncertaintiy value: " + deltaB
                            + " on b value for source: " + sourceName
                            + " give b value smaller than 0!\n"
                            + "Check your input. Execution stopped!";
            logger.info(msg);
            // System.out.println("Uncertaintiy value: " + deltaB +
            // " on b value for source: " + sourceName
            // + " give b value smaller than 0!");
            // System.out.println("Check your input. Execution stopped!");
            throw new IllegalArgumentException(msg);
        }
    } // applybGrRelative()

    /**
     * Set the GEM1ERF params given the parameters defined in
     * 
     * @param erf
     *            : erf for which parameters have to be set
     * @param calcConfig
     *            : calculator configuration obejct containing parameters for
     *            the ERF
     */
    public void setGEM1ERFParams(GEM1ERF erf) {
        // set minimum magnitude
        /*
         * xxr: TODO: !!!type safety!!! apache's Configuration interface handles
         * a similar problem this way: Instead of defining one single method
         * like public void setParameter(String key, Object value) {...} there
         * is one method per type defined: setString(), setDouble(), setInt(),
         * ...
         */
        erf.setParameter(GEM1ERF.MIN_MAG_NAME, config
                .getDouble(ConfigItems.MINIMUM_MAGNITUDE.name()));
        // set time span
        TimeSpan timeSpan = new TimeSpan(TimeSpan.NONE, TimeSpan.YEARS);
        timeSpan.setDuration(config.getDouble(ConfigItems.INVESTIGATION_TIME
                .name()));
        erf.setTimeSpan(timeSpan);

        // params for area source
        // set inclusion of area sources in the calculation
        erf.setParameter(GEM1ERF.INCLUDE_AREA_SRC_PARAM_NAME, config
                .getBoolean(ConfigItems.INCLUDE_AREA_SOURCES.name()));
        // set rupture type ("area source rupture model /
        // area_source_rupture_model / AreaSourceRuptureModel)
        erf.setParameter(GEM1ERF.AREA_SRC_RUP_TYPE_NAME, config
                .getString(ConfigItems.TREAT_AREA_SOURCE_AS.name()));
        // set area discretization
        erf.setParameter(GEM1ERF.AREA_SRC_DISCR_PARAM_NAME, config
                .getDouble(ConfigItems.AREA_SOURCE_DISCRETIZATION.name()));
        // set mag-scaling relationship
        erf
                .setParameter(
                        GEM1ERF.AREA_SRC_MAG_SCALING_REL_PARAM_NAME,
                        config
                                .getString(ConfigItems.AREA_SOURCE_MAGNITUDE_SCALING_RELATIONSHIP
                                        .name()));
        // params for grid source
        // inclusion of grid sources in the calculation
        erf.setParameter(GEM1ERF.INCLUDE_GRIDDED_SEIS_PARAM_NAME, config
                .getBoolean(ConfigItems.INCLUDE_GRID_SOURCES.name()));
        // rupture model
        erf.setParameter(GEM1ERF.GRIDDED_SEIS_RUP_TYPE_NAME, config
                .getString(ConfigItems.TREAT_GRID_SOURCE_AS.name()));
        // mag-scaling relationship
        erf
                .setParameter(
                        GEM1ERF.GRIDDED_SEIS_MAG_SCALING_REL_PARAM_NAME,
                        config
                                .getString(ConfigItems.AREA_SOURCE_MAGNITUDE_SCALING_RELATIONSHIP
                                        .name()));

        // params for fault source
        // inclusion of fault sources in the calculation
        erf.setParameter(GEM1ERF.INCLUDE_FAULT_SOURCES_PARAM_NAME, config
                .getBoolean(ConfigItems.INCLUDE_FAULT_SOURCE.name()));
        // rupture offset
        erf.setParameter(GEM1ERF.FAULT_RUP_OFFSET_PARAM_NAME, config
                .getDouble(ConfigItems.FAULT_RUPTURE_OFFSET.name()));
        // surface discretization
        erf.setParameter(GEM1ERF.FAULT_DISCR_PARAM_NAME, config
                .getDouble(ConfigItems.FAULT_SURFACE_DISCRETIZATION.name()));
        // mag-scaling relationship
        erf.setParameter(GEM1ERF.FAULT_MAG_SCALING_REL_PARAM_NAME, config
                .getString(ConfigItems.FAULT_MAGNITUDE_SCALING_RELATIONSHIP
                        .name()));

        // mag-scaling sigma
        erf.setParameter(GEM1ERF.FAULT_SCALING_SIGMA_PARAM_NAME, config
                .getDouble(ConfigItems.FAULT_MAGNITUDE_SCALING_SIGMA.name()));
        // rupture aspect ratio
        erf.setParameter(GEM1ERF.FAULT_RUP_ASPECT_RATIO_PARAM_NAME, config
                .getDouble(ConfigItems.RUPTURE_ASPECT_RATIO.name()));
        // rupture floating type
        erf.setParameter(GEM1ERF.FAULT_FLOATER_TYPE_PARAM_NAME, config
                .getString(ConfigItems.RUPTURE_FLOATING_TYPE.name()));

        // params for subduction fault
        // inclusion of fault sources in the calculation
        erf
                .setParameter(
                        GEM1ERF.INCLUDE_SUBDUCTION_SOURCES_PARAM_NAME,
                        config
                                .getBoolean(ConfigItems.INCLUDE_SUBDUCTION_FAULT_SOURCE
                                        .name()));
        // rupture offset
        erf.setParameter(GEM1ERF.SUB_RUP_OFFSET_PARAM_NAME, config
                .getDouble(ConfigItems.SUBDUCTION_FAULT_RUPTURE_OFFSET.name()));
        // surface discretization
        erf.setParameter(GEM1ERF.SUB_DISCR_PARAM_NAME, config
                .getDouble(ConfigItems.SUBDUCTION_FAULT_SURFACE_DISCRETIZATION
                        .name()));
        // mag-scaling relationship
        erf
                .setParameter(
                        GEM1ERF.SUB_MAG_SCALING_REL_PARAM_NAME,
                        config
                                .getString(ConfigItems.SUBDUCTION_FAULT_MAGNITUDE_SCALING_RELATIONSHIP
                                        .name()));
        // mag-scaling sigma
        erf.setParameter(GEM1ERF.SUB_SCALING_SIGMA_PARAM_NAME, config
                .getDouble(ConfigItems.SUBDUCTION_FAULT_MAGNITUDE_SCALING_SIGMA
                        .name()));
        // rupture aspect ratio
        erf.setParameter(GEM1ERF.SUB_RUP_ASPECT_RATIO_PARAM_NAME, config
                .getDouble(ConfigItems.SUBDUCTION_RUPTURE_ASPECT_RATIO.name()));
        // rupture floating type
        erf
                .setParameter(GEM1ERF.SUB_FLOATER_TYPE_PARAM_NAME, config
                        .getString(ConfigItems.SUBDUCTION_RUPTURE_FLOATING_TYPE
                                .name()));

        // update
        erf.updateForecast();
    } // setGEM1ERFParams()

    public static HashMap<TectonicRegionType, ScalarIntensityMeasureRelationshipAPI> sampleGemLogicTreeGMPE(
            HashMap<TectonicRegionType, LogicTree<ScalarIntensityMeasureRelationshipAPI>> listLtGMPE,
            long seed) {
        // TODO(JMC): Do I do anything with the N?

        Random rn = null;
        if (seed != 0) {
            rn = new Random(seed);
        } else {
            rn = new Random();
        }

        HashMap<TectonicRegionType, ScalarIntensityMeasureRelationshipAPI> hm =
                new HashMap<TectonicRegionType, ScalarIntensityMeasureRelationshipAPI>();

        // loop over tectonic regions
        Iterator<TectonicRegionType> iter = listLtGMPE.keySet().iterator();
        while (iter.hasNext()) {

            // get tectonic region type
            TectonicRegionType trt = iter.next();

            // get corresponding logic tree
            LogicTree<ScalarIntensityMeasureRelationshipAPI> ltGMPE =
                    listLtGMPE.get(trt);

            // sample the first branching level
            int branch = ltGMPE.sampleBranchingLevel(0, rn);

            // select the corresponding gmpe from the end-branch mapping
            ScalarIntensityMeasureRelationshipAPI gmpe =
                    ltGMPE.getEBMap().get(Integer.toString(branch));

            hm.put(trt, gmpe);
        }

        return hm;

    }

    public ErfLogicTreeData createErfLogicTreeData() throws IOException {
        // load ERF logic tree data
        if (hasPath == true) {
            System.out.println(getRelativePath(ConfigItems.ERF_LOGIC_TREE_FILE
                    .name()));
            ErfLogicTreeData erfLogicTree =
                    new ErfLogicTreeData(
                            getRelativePath(ConfigItems.ERF_LOGIC_TREE_FILE
                                    .name()));
            return erfLogicTree;
        } else {
            return new ErfLogicTreeData(kvs, config
                    .getString(ConfigItems.ERF_LOGIC_TREE_FILE.name()));
        }
    } // createErfLogicTreeData()

    public GmpeLogicTreeData createGmpeLogicTreeData() throws IOException {
        // load GMPE logic tree data
        String component = config.getString(ConfigItems.COMPONENT.name());
        String intensityMeasureType =
                config.getString(ConfigItems.INTENSITY_MEASURE_TYPE.name());
        Double period = config.getDouble(ConfigItems.PERIOD.name());
        Double damping = config.getDouble(ConfigItems.DAMPING.name());
        String gmpeTruncationType =
                config.getString(ConfigItems.GMPE_TRUNCATION_TYPE.name());
        Double truncationLevel =
                config.getDouble(ConfigItems.TRUNCATION_LEVEL.name());
        String standardDeviationType =
                config.getString(ConfigItems.STANDARD_DEVIATION_TYPE.name());
        Double referenceVs30Value =
                config.getDouble(ConfigItems.REFERENCE_VS30_VALUE.name());
        // instantiate eventually
        GmpeLogicTreeData gmpeLogicTree = null;
        if (hasPath == true) {
            String relativePath =
                    getRelativePath(ConfigItems.GMPE_LOGIC_TREE_FILE.name());
            gmpeLogicTree =
                    new GmpeLogicTreeData(relativePath, component,
                            intensityMeasureType, period, damping,
                            gmpeTruncationType, truncationLevel,
                            standardDeviationType, referenceVs30Value);
        } else {
            String gmpeSha =
                    config.getString(ConfigItems.GMPE_LOGIC_TREE_FILE.name());
            logger.debug("Loading GMPE LT from " + gmpeSha);
            gmpeLogicTree =
                    new GmpeLogicTreeData(kvs, gmpeSha, component,
                            intensityMeasureType, period, damping,
                            gmpeTruncationType, truncationLevel,
                            standardDeviationType, referenceVs30Value);
        }

        return gmpeLogicTree;
    }

}
