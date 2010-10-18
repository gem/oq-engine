package org.opensha.gem.GEM1.calc.gemCommandLineCalculator;

import java.io.BufferedOutputStream;
import java.io.BufferedWriter;
import java.io.File;
import java.io.FileNotFoundException;
import java.io.FileOutputStream;
import java.io.IOException;
import java.io.InputStream;
import java.io.OutputStreamWriter;
import java.io.Reader;
import java.lang.reflect.InvocationTargetException;
import java.util.ArrayList;
import java.util.HashMap;
import java.util.Iterator;
import java.util.Properties;

import org.apache.commons.configuration.AbstractFileConfiguration;
import org.apache.commons.configuration.Configuration;
import org.apache.commons.configuration.ConfigurationConverter;
import org.apache.commons.configuration.ConfigurationException;
import org.apache.commons.configuration.PropertiesConfiguration;
import org.apache.commons.io.FilenameUtils;
import org.apache.commons.logging.Log;
import org.apache.commons.logging.LogFactory;
import org.opensha.commons.data.Site;
import org.opensha.commons.data.TimeSpan;
import org.opensha.commons.data.function.ArbitrarilyDiscretizedFunc;
import org.opensha.commons.geo.BorderType;
import org.opensha.commons.geo.GriddedRegion;
import org.opensha.commons.geo.Location;
import org.opensha.commons.geo.LocationList;
import org.opensha.gem.GEM1.calc.gemCommandLineCalculator.CalculatorConfigHelper.ConfigItems;
import org.opensha.gem.GEM1.calc.gemHazardCalculator.GemComputeHazard;
import org.opensha.gem.GEM1.calc.gemLogicTree.GemLogicTree;
import org.opensha.gem.GEM1.calc.gemLogicTree.GemLogicTreeBranch;
import org.opensha.gem.GEM1.calc.gemLogicTree.GemLogicTreeRule;
import org.opensha.gem.GEM1.calc.gemLogicTree.GemLogicTreeRuleParam;
import org.opensha.gem.GEM1.calc.gemOutput.GEMHazardCurveRepository;
import org.opensha.gem.GEM1.calc.gemOutput.GEMHazardCurveRepositoryList;
import org.opensha.gem.GEM1.commons.UnoptimizedDeepCopy;
import org.opensha.sha.earthquake.rupForecastImpl.GEM1.GEM1ERF;
import org.opensha.sha.earthquake.rupForecastImpl.GEM1.SourceData.GEMAreaSourceData;
import org.opensha.sha.earthquake.rupForecastImpl.GEM1.SourceData.GEMFaultSourceData;
import org.opensha.sha.earthquake.rupForecastImpl.GEM1.SourceData.GEMPointSourceData;
import org.opensha.sha.earthquake.rupForecastImpl.GEM1.SourceData.GEMSourceData;
import org.opensha.sha.earthquake.rupForecastImpl.GEM1.SourceData.GEMSubductionFaultSourceData;
import org.opensha.sha.imr.ScalarIntensityMeasureRelationshipAPI;
import org.opensha.sha.magdist.GutenbergRichterMagFreqDist;
import org.opensha.sha.magdist.IncrementalMagFreqDist;
import org.opensha.sha.util.TectonicRegionType;

public class CommandLineCalculator {
    //
    // Apache commons logging, not log4j specifically
    // Note that for application code, declaring the log member as "static" is
    // more efficient as one Log object is created per class, and is
    // recommended. However this is not safe to do for a class which may be
    // deployed via a "shared" classloader in a servlet or j2ee container or
    // similar environment. If the class may end up invoked with different
    // thread-context-classloader values set then the member must not be
    // declared static. The use of "static" should therefore be avoided in
    // code within any "library" type project.
    private static Log logger = LogFactory.getLog(CommandLineCalculator.class);
    private Configuration config;
    private PropertiesConfiguration propsConfig;
    // keyword
    private static String MONTE_CARLO = "Monte Carlo";
    private static String FULL_CALCULATION = "Full Calculation";
    // for debugging
    private static Boolean D = false;

    /**
     * 
     * @param inStream
     *            e.g. the file input stream
     * @throws ConfigurationException
     */
    public CommandLineCalculator(final InputStream inStream)
            throws ConfigurationException {
        // load calculation configuration data
        config = new PropertiesConfiguration();
        ((PropertiesConfiguration) config).load(inStream, null);
    } // constructor

    public CommandLineCalculator(Reader reader) throws ConfigurationException {
        config = new PropertiesConfiguration();
        // load calculation configuration data
        ((PropertiesConfiguration) config).load(reader);
    } // constructor

    public CommandLineCalculator(Properties p) {
        config = ConfigurationConverter.getConfiguration(p);
    } // constructor

    public CommandLineCalculator(String calcConfigFile)
            throws ConfigurationException {
        config = new PropertiesConfiguration();
        ((PropertiesConfiguration) config).load(calcConfigFile);
    } // constructor

    public void setConfig(Properties p) {
        config = ConfigurationConverter.getConfiguration(p);
    } // setConfig()

    public void setConfig(Configuration c) {
        config = c;
    }

    /**
     * If the property with given key already exists, this adds a property, and
     * does not replace it. So this can result in multi valued properties.
     * properties.
     * 
     * @param key
     * @param value
     */
    public void addConfigItem(String key, String value) {
        // the member is private and not null
        config.addProperty(key, value);
    }

    /**
     * If the property with given key already exists, its value will be replaced
     * by the one passed in.
     * 
     * @param key
     * @param value
     */
    public void setConfigItem(String key, String value) {
        // the member is private and not null
        config.setProperty(key, value);
    }

    private String getRelativePath(String key) {
        return (FilenameUtils.getFullPath(((AbstractFileConfiguration) config)
                .getPath())) + config.getString(key);
    }

    /**
     * This is the main method that do the calculations. According to the
     * specifications in the configuration file the method will do the required
     * calculations.
     */
    public void doCalculation() {
        StringBuffer logMsg = new StringBuffer();
        // start chronometer
        long startTimeMs = System.currentTimeMillis();
        // get calculation mode
        String calculationMode =
                config.getString(ConfigItems.CALCULATION_MODE.name());
        if (calculationMode.equalsIgnoreCase(MONTE_CARLO)) {
            // do calculation by random sampling end-branch models
            doCalculationThroughMonteCarloApproach();
        } else if (calculationMode.equalsIgnoreCase(FULL_CALCULATION)) {
            // do calculation for each end branch model
            doFullCalculation();
        } else {
            logMsg.append("Calculation mode: "
                    + config.getString(ConfigItems.CALCULATION_MODE.name())
                    + " not recognized. Check the configuration file!\n"
                    + "Execution stops!");
            logger.info(logMsg);
            // System.out.println("Calculation mode: " +
            // config.getString(ConfigItems.CALCULATION_MODE.name())
            // + " not recognized. Check the configuration file!\n" +
            // "Execution stops!");
            System.exit(0);
        }
        // calculate elapsed time
        long taskTimeMs = System.currentTimeMillis() - startTimeMs;
        logMsg.append("Wall clock time (including time for saving output files)\n");
        // System.out.println("Wall clock time (including time for saving output files)");
        // 1h = 60*60*10^3 ms
        logMsg.append(String.format("hours  : %6.3f\n", taskTimeMs
                / (60 * 60 * Math.pow(10, 3))));
        // System.out.printf("hours  : %6.3f\n", taskTimeMs / (60 * 60 *
        // Math.pow(10, 3)));
        // 1 min = 60*10^3 ms
        logMsg.append(String.format("minutes: %6.3f\n",
                taskTimeMs / (60 * Math.pow(10, 3))));
        // System.out.printf("minutes: %6.3f\n", taskTimeMs / (60 * Math.pow(10,
        // 3)));
        logger.info(logMsg);
    } // doCalculation()

    private void doCalculationThroughMonteCarloApproach() {
        logger.info("Performing calculation through Monte Carlo Approach.\n");
        // System.out.println("Performing calculation through Monte Carlo Approach.\n");
        // load ERF logic tree data
        ErfLogicTreeData erfLogicTree =
                new ErfLogicTreeData(
                        getRelativePath(ConfigItems.ERF_LOGIC_TREE_FILE.name()));
        // load GMPE logic tree data
        GmpeLogicTreeData gmpeLogicTree =
                new GmpeLogicTreeData(
                        getRelativePath(ConfigItems.GMPE_LOGIC_TREE_FILE.name()),
                        config.getString(ConfigItems.COMPONENT.name()), config
                                .getString(ConfigItems.INTENSITY_MEASURE_TYPE
                                        .name()), config
                                .getDouble(ConfigItems.PERIOD.name()), config
                                .getDouble(ConfigItems.DAMPING.name()), config
                                .getString(ConfigItems.GMPE_TRUNCATION_TYPE
                                        .name()),
                        config.getDouble(ConfigItems.TRUNCATION_LEVEL.name()),
                        config.getString(ConfigItems.STANDARD_DEVIATION_TYPE
                                .name()), config
                                .getDouble(ConfigItems.REFERENCE_VS30_VALUE
                                        .name()));
        // instantiate the repository for the results
        GEMHazardCurveRepositoryList hcRepList =
                new GEMHazardCurveRepositoryList();
        // sites for calculation
        ArrayList<Site> sites = createSiteList(config);
        // number of hazard curves to be generated for each point
        int numHazCurves =
                config.getInt(ConfigItems.NUMBER_OF_HAZARD_CURVE_CALCULATIONS
                        .name());

        // loop over number of hazard curves to be generated
        // The properties are not changed in this loop so it is allowed to
        // retrieve them before.
        int numOfThreads =
                config.getInt(ConfigItems.NUMBER_OF_PROCESSORS.name());
        ArbitrarilyDiscretizedFunc imlList =
                CalculatorConfigHelper.makeImlList(config);
        double maxDistance =
                config.getDouble(ConfigItems.MAXIMUM_DISTANCE.name());
        for (int i = 0; i < numHazCurves; i++) {
            logger.info("Realization number: " + (i + 1) + ", of: "
                    + numHazCurves);
            // System.out.println("Realization number: " + (i + 1) + ", of: " +
            // numHazCurves);
            // do calculation
            // run sampleGemLogicTreeERF() and sampleGemLogicTreeGMPE() for
            // every iteration. This is necessary because both, ERF and GMPEs
            // change because they are randomly sampled
            GemComputeHazard compHaz =
                    new GemComputeHazard(numOfThreads, sites,
                            sampleGemLogicTreeERF(
                                    erfLogicTree.getErfLogicTree(), config),
                            sampleGemLogicTreeGMPE(gmpeLogicTree
                                    .getGmpeLogicTreeHashMap()), imlList,
                            maxDistance);
            // store results
            hcRepList.add(compHaz.getValues(), Integer.toString(i));
        } // for
          // save hazard curves
        if (D)
            saveHazardCurveRepositoryListToAsciiFile(
                    config.getString(ConfigItems.OUTPUT_DIR.name()), hcRepList);
        // create the requested output
        if (config.getBoolean(ConfigItems.MEAN_GROUND_MOTION_MAP.name())) {
            // calculate mean ground motion map for the given prob of exceedance
            ArrayList<Double> meanGroundMotionMap =
                    hcRepList.getMeanGrounMotionMap(config
                            .getDouble(ConfigItems.PROBABILITY_OF_EXCEEDANCE
                                    .name()));
            // save mean ground motion map
            // as an example: here we read from Configuration object
            String outfile =
                    config.getString((ConfigItems.OUTPUT_DIR.name()))
                            + "meanGroundMotionMap_"
                            + config.getDouble(ConfigItems.PROBABILITY_OF_EXCEEDANCE
                                    .name())
                            * 100
                            + "%"
                            + config.getString(ConfigItems.INVESTIGATION_TIME
                                    .name()) + "yr.dat";
            saveGroundMotionMapToAsciiFile(outfile, meanGroundMotionMap,
                    hcRepList.getHcRepList().get(0).getGridNode());
        }
        if (config.getBoolean(ConfigItems.INDIVIDUAL_GROUND_MOTION_MAP.name())) {
            // loop over end-branches
            int indexLabel = 0;
            for (GEMHazardCurveRepository hcRep : hcRepList.getHcRepList()) {
                // calculate ground motion map
                ArrayList<Double> groundMotionMap =
                        hcRep.getHazardMap(config
                                .getDouble(ConfigItems.PROBABILITY_OF_EXCEEDANCE
                                        .name()));
                // define file name
                String outfile =
                        config.getString(ConfigItems.OUTPUT_DIR.name())
                                + "groundMotionMap_"
                                + hcRepList.getEndBranchLabels()
                                        .get(indexLabel)
                                + "_"
                                + config.getDouble(ConfigItems.PROBABILITY_OF_EXCEEDANCE
                                        .name())
                                * 100
                                + "%"
                                + config.getString(ConfigItems.INVESTIGATION_TIME
                                        .name()) + "yr.dat";
                saveGroundMotionMapToAsciiFile(outfile, groundMotionMap,
                        hcRepList.getHcRepList().get(0).getGridNode());
                indexLabel = indexLabel + 1;
            }
        }
        if (config.getBoolean(ConfigItems.MEAN_HAZARD_CURVES.name())) {
            GEMHazardCurveRepository meanHazardCurves =
                    hcRepList.getMeanHazardCurves();
            String outfile =
                    config.getString(ConfigItems.OUTPUT_DIR.name())
                            + "meanHazardCurves.dat";
            saveHazardCurveRepositoryToAsciiFile(outfile, meanHazardCurves);
        }
        if (config.getBoolean(ConfigItems.INDIVIDUAL_HAZARD_CURVES.name())) {
            String outfile =
                    config.getString(ConfigItems.OUTPUT_DIR.name())
                            + "individualHazardCurves.dat";
            saveHazardCurveRepositoryListToAsciiFile(outfile, hcRepList);
        }

    } // doCalculationThroughMonteCarloApproach()

    private void doFullCalculation() {
        logger.info("Performing full calculation. \n");
        // System.out.println("Performing full calculation. \n");
        // load ERF logic tree data
        ErfLogicTreeData erfLogicTree =
                new ErfLogicTreeData(
                        config.getString(ConfigItems.ERF_LOGIC_TREE_FILE.name()));
        // load GMPE logic tree data
        String gmpeLogicTreeFile =
                config.getString(ConfigItems.GMPE_LOGIC_TREE_FILE.name());
        String component = config.getString(ConfigItems.COMPONENT.name());
        String intensityMeasureType =
                config.getString(ConfigItems.INTENSITY_MEASURE_TYPE.name());
        double period = config.getDouble(ConfigItems.PERIOD.name());
        double damping = config.getDouble(ConfigItems.DAMPING.name());
        String truncationType =
                config.getString(ConfigItems.GMPE_TRUNCATION_TYPE.name());
        double truncationLevel =
                config.getDouble(ConfigItems.TRUNCATION_LEVEL.name());
        String standardDeviationType =
                config.getString(ConfigItems.STANDARD_DEVIATION_TYPE.name());
        double vs30Reference =
                config.getDouble(ConfigItems.REFERENCE_VS30_VALUE.name());
        GmpeLogicTreeData gmpeLogicTree =
                new GmpeLogicTreeData(gmpeLogicTreeFile, component,
                        intensityMeasureType, period, damping, truncationType,
                        truncationLevel, standardDeviationType, vs30Reference);
        // compute ERF logic tree end-branch models
        HashMap<String, ArrayList<GEMSourceData>> endBranchModels =
                computeErfLogicTreeEndBrancheModels(erfLogicTree
                        .getErfLogicTree());
        // log info
        logger.info("ERF logic tree end branch models (total number: "
                + endBranchModels.keySet().size() + ").\n");
        // System.out.println("ERF logic tree end branch models (total number: "
        // + endBranchModels.keySet().size()
        // + ").\n");
        Iterator<String> erfEndBranchLabelIter =
                endBranchModels.keySet().iterator();
        while (erfEndBranchLabelIter.hasNext()) {
            String erfEndBranchLabel = erfEndBranchLabelIter.next();
            logger.info("End branch label: " + erfEndBranchLabel + "\n");
            // System.out.println("End branch label: " + erfEndBranchLabel +
            // "\n");
        } // while
          // compute gmpe logic tree end-branch models
        HashMap<String, HashMap<TectonicRegionType, ScalarIntensityMeasureRelationshipAPI>> gmpeEndBranchModel =
                computeGmpeLogicTreeEndBrancheModels(gmpeLogicTree
                        .getGmpeLogicTreeHashMap());
        // log info
        logger.info("GMPE logic tree end branch models (total number: "
                + gmpeEndBranchModel.keySet().size() + ").\n");
        // System.out.println("GMPE logic tree end branch models (total number: "
        // + gmpeEndBranchModel.keySet().size()
        // + ").\n");
        Iterator<String> gmpeEndBranchLabelIter =
                gmpeEndBranchModel.keySet().iterator();
        while (gmpeEndBranchLabelIter.hasNext()) {
            String gmpeEndBranchLabel = gmpeEndBranchLabelIter.next();
            logger.info("End branch label: " + gmpeEndBranchLabel);
            // System.out.println("End branch label: " + gmpeEndBranchLabel);
            Iterator<TectonicRegionType> trtIter =
                    gmpeEndBranchModel.get(gmpeEndBranchLabel).keySet()
                            .iterator();
            while (trtIter.hasNext()) {
                TectonicRegionType trt = trtIter.next();
                logger.info("                  Tectonic region type: "
                        + trt.toString()
                        + " --> GMPE: "
                        + gmpeEndBranchModel.get(gmpeEndBranchLabel).get(trt)
                                .getName());
                // System.out.println("                  Tectonic region type: "
                // + trt.toString() + " --> GMPE: "
                // +
                // gmpeEndBranchModel.get(gmpeEndBranchLabel).get(trt).getName());
            } // while
              // TODO:
              // O.k., here, the intention is to insert a one line gap after
              // a "block" logging messages. But is this the way?
            logger.info("\n");
            // System.out.println("\n");
        } // while gmpeEndBranchLabelIter
          // instantiate the repository for the results
        GEMHazardCurveRepositoryList hcRepList =
                new GEMHazardCurveRepositoryList();
        // sites for calculation
        ArrayList<Site> sites = createSiteList(config);
        // number of threads
        int numThreads = config.getInt(ConfigItems.NUMBER_OF_PROCESSORS.name());
        // IML list
        ArbitrarilyDiscretizedFunc imlList =
                CalculatorConfigHelper.makeImlList(config);
        // maximum integration distance
        double maxDist = config.getDouble(ConfigItems.MAXIMUM_DISTANCE.name());
        // loop over ERF end-branch models
        Iterator<String> endBranchLabels = endBranchModels.keySet().iterator();
        while (endBranchLabels.hasNext()) {
            // current erf end-branch model label
            String erfLabel = endBranchLabels.next();
            logger.info("Processing end-branch model: " + erfLabel);
            // System.out.println("Processing end-branch model: " + erfLabel);
            // instantiate GEM1ERF with the source model corresponding
            // to the current label
            GEM1ERF erf = new GEM1ERF(endBranchModels.get(erfLabel));
            // set ERF parameters
            setGEM1ERFParams(erf, config);
            // loop over GMPE end-branch models
            Iterator<String> gmpeEndBranchLabels =
                    gmpeEndBranchModel.keySet().iterator();
            while (gmpeEndBranchLabels.hasNext()) {
                String gmpeLabel = gmpeEndBranchLabels.next();
                logger.info("Processing gmpe end-branch model: " + gmpeLabel);
                // System.out.println("Processing gmpe end-branch model: " +
                // gmpeLabel);
                // do calculation
                GemComputeHazard compHaz =
                        new GemComputeHazard(numThreads, sites, erf,
                                gmpeEndBranchModel.get(gmpeLabel), imlList,
                                maxDist);
                // store results
                hcRepList.add(compHaz.getValues(), erfLabel + "-" + gmpeLabel);
            } // while gmpeEndBranchLabels
              // create the requested output
            if (config.getBoolean(ConfigItems.MEAN_GROUND_MOTION_MAP.name())) {
                // calculate mean hazard map for the given prob of exceedance
                ArrayList<Double> meanGroundMotionMap =
                        hcRepList
                                .getMeanGroundMotionMap(
                                        config.getDouble(ConfigItems.PROBABILITY_OF_EXCEEDANCE
                                                .name()), erfLogicTree
                                                .getErfLogicTree(),
                                        gmpeLogicTree.getGmpeLogicTreeHashMap());
                // save mean ground motion map
                String outfile =
                        config.getString(ConfigItems.OUTPUT_DIR.name())
                                + "meanGroundMotionMap_"
                                + config.getDouble(ConfigItems.PROBABILITY_OF_EXCEEDANCE
                                        .name())
                                * 100
                                + "%"
                                + config.getString(ConfigItems.INVESTIGATION_TIME
                                        .name()) + "yr.dat";
                saveGroundMotionMapToAsciiFile(outfile, meanGroundMotionMap,
                        hcRepList.getHcRepList().get(0).getGridNode());
            }
            if (config.getBoolean(ConfigItems.INDIVIDUAL_GROUND_MOTION_MAP
                    .name())) {
                // loop over end-branches
                int indexLabel = 0;
                for (GEMHazardCurveRepository hcRep : hcRepList.getHcRepList()) {
                    // calculate ground motion map
                    ArrayList<Double> groundMotionMap =
                            hcRep.getHazardMap(config
                                    .getDouble(ConfigItems.PROBABILITY_OF_EXCEEDANCE
                                            .name()));
                    // define file name
                    String outfile =
                            config.getString(ConfigItems.OUTPUT_DIR.name())
                                    + "groundMotionMap_"
                                    + hcRepList.getEndBranchLabels().get(
                                            indexLabel)
                                    + "_"
                                    + config.getDouble(ConfigItems.PROBABILITY_OF_EXCEEDANCE
                                            .name())
                                    * 100
                                    + "%"
                                    + config.getString(ConfigItems.INVESTIGATION_TIME
                                            .name()) + "yr.dat";
                    saveGroundMotionMapToAsciiFile(outfile, groundMotionMap,
                            hcRepList.getHcRepList().get(0).getGridNode());
                    indexLabel = indexLabel + 1;
                } // for GEMHazardCurveRepository
            }
            if (config.getBoolean(ConfigItems.MEAN_HAZARD_CURVES.name())) {
                GEMHazardCurveRepository meanHazardCurves =
                        hcRepList.getMeanHazardCurves(
                                erfLogicTree.getErfLogicTree(),
                                gmpeLogicTree.getGmpeLogicTreeHashMap());
                String outfile =
                        config.getString(ConfigItems.OUTPUT_DIR.name())
                                + "meanHazardCurves.dat";
                saveHazardCurveRepositoryToAsciiFile(outfile, meanHazardCurves);
            }
            if (config.getBoolean(ConfigItems.INDIVIDUAL_HAZARD_CURVES.name())) {
                String outfile =
                        config.getString(ConfigItems.OUTPUT_DIR.name())
                                + "individualHazardCurves.dat";
                saveHazardCurveRepositoryListToAsciiFile(outfile, hcRepList);
            }
        } // while endBranchLabels
    } // doFullCalculation()

    /**
     * @param gmpeLogicTreeHashMap
     *            : this is an hash map relating a set of tectonic settings with
     *            a set of logic trees for gmpes. The idea is the user can
     *            define, for each tectonic setting, a different logic tree for
     *            the gmpes.
     * @return an hash map relating an end branch label with an hash map that
     *         relates different tectonic settings with different gmpes. For
     *         instance if there are two logic tree for gmpes: Stable Region
     *         (branch 1: D&M2008, weight: 0.5; branch 2: M&P2008, weight: 0.5)
     *         Active Region (branch 1: B&A2008, weight: 0.5; branch 2: C&B2008,
     *         weight: 0.5) then the method will result in a hash map containing
     *         four end branch labels: Stable Region_1-ActiveRegion_1 (referring
     *         to an hash map: {(Stable Region: D&M2008),(Active Region:
     *         B&A2008)} Stable Region_1-ActiveRegion_2 (referring to an hash
     *         map: {(Stable Region: D&M2008),(Active Region: C&B2008)} Stable
     *         Region_2-ActiveRegion_1 (referring to an hash map: {(Stable
     *         Region: M&P2008),(Active Region: B&A2008)} Stable
     *         Region_2-ActiveRegion_2 (referring to an hash map: {(Stable
     *         Region: M&P2008),(Active Region: C&B2008)} NOTE: the major
     *         assumption in this method is that the logic tree for the Gmpes
     *         contains only one branching level.
     */
    private
            HashMap<String, HashMap<TectonicRegionType, ScalarIntensityMeasureRelationshipAPI>>
            computeGmpeLogicTreeEndBrancheModels(
                    HashMap<TectonicRegionType, GemLogicTree<ScalarIntensityMeasureRelationshipAPI>> gmpeLogicTreeHashMap) {
        // make deep copy
        HashMap<TectonicRegionType, GemLogicTree<ScalarIntensityMeasureRelationshipAPI>> gmpeLogicTreeHashMapCopy =
                (HashMap<TectonicRegionType, GemLogicTree<ScalarIntensityMeasureRelationshipAPI>>) UnoptimizedDeepCopy
                        .copy(gmpeLogicTreeHashMap);
        // hash map containing gmpe end branch models
        HashMap<String, HashMap<TectonicRegionType, ScalarIntensityMeasureRelationshipAPI>> endBranchModels =
                new HashMap<String, HashMap<TectonicRegionType, ScalarIntensityMeasureRelationshipAPI>>();
        // tectonic region types
        Iterator<TectonicRegionType> trtIter =
                gmpeLogicTreeHashMapCopy.keySet().iterator();
        ArrayList<TectonicRegionType> trtList =
                new ArrayList<TectonicRegionType>();
        while (trtIter.hasNext()) {
            trtList.add(trtIter.next());
        }
        // load gmpe models from first tectonic region type
        if (endBranchModels.isEmpty()) {
            // number of branches for the first tectonic region type
            int numBranch =
                    gmpeLogicTreeHashMapCopy.get(trtList.get(0))
                            .getBranchingLevel(0).getBranchList().size();
            // loop over branches
            for (int i = 0; i < numBranch; i++) {
                // get current branch
                GemLogicTreeBranch branch =
                        gmpeLogicTreeHashMapCopy.get(trtList.get(0))
                                .getBranchingLevel(0).getBranch(i);
                // define label from branch ID number
                String label =
                        trtList.get(0) + "_"
                                + Integer.toString(branch.getRelativeID());
                // get gmpe
                ScalarIntensityMeasureRelationshipAPI gmpe =
                        gmpeLogicTreeHashMapCopy.get(trtList.get(0)).getEBMap()
                                .get(Integer.toString(branch.getRelativeID()));
                HashMap<TectonicRegionType, ScalarIntensityMeasureRelationshipAPI> newHashMap =
                        new HashMap<TectonicRegionType, ScalarIntensityMeasureRelationshipAPI>();
                newHashMap.put(trtList.get(0), gmpe);
                // save in the hash map
                endBranchModels.put(label, newHashMap);
            }
            // remove processed tectonic setting
            gmpeLogicTreeHashMapCopy.remove(trtList.get(0));
            trtList.remove(0);
        }
        if (!endBranchModels.isEmpty()) {
            // while there are additional tectonic settings
            while (!gmpeLogicTreeHashMapCopy.keySet().isEmpty()) {
                // loop over current end branch models
                Iterator<String> endBranchModelLabels =
                        endBranchModels.keySet().iterator();
                ArrayList<String> labels = new ArrayList<String>();
                while (endBranchModelLabels.hasNext())
                    labels.add(endBranchModelLabels.next());
                for (String label : labels) {
                    // number of branches in the first branching level of the
                    // current tectonic setting
                    int numBranch =
                            gmpeLogicTreeHashMapCopy.get(trtList.get(0))
                                    .getBranchingLevel(0).getBranchList()
                                    .size();
                    // loop over branches
                    for (int i = 0; i < numBranch; i++) {
                        // get current branch
                        GemLogicTreeBranch branch =
                                gmpeLogicTreeHashMapCopy.get(trtList.get(0))
                                        .getBranchingLevel(0).getBranch(i);
                        // new label
                        String newLabel =
                                label + "-" + trtList.get(0) + "_"
                                        + branch.getRelativeID();
                        // get gmpe
                        ScalarIntensityMeasureRelationshipAPI gmpe =
                                gmpeLogicTreeHashMapCopy
                                        .get(trtList.get(0))
                                        .getEBMap()
                                        .get(Integer.toString(branch
                                                .getRelativeID()));
                        // add tectonic setting - gmpe
                        // current end branch model
                        HashMap<TectonicRegionType, ScalarIntensityMeasureRelationshipAPI> newHashMap =
                                new HashMap<TectonicRegionType, ScalarIntensityMeasureRelationshipAPI>();
                        // copy previous entries
                        Iterator<TectonicRegionType> iterTrt =
                                endBranchModels.get(label).keySet().iterator();
                        while (iterTrt.hasNext()) {
                            TectonicRegionType trt = iterTrt.next();
                            ScalarIntensityMeasureRelationshipAPI ar =
                                    endBranchModels.get(label).get(trt);
                            newHashMap.put(trt, ar);
                        }
                        // add new entry
                        newHashMap.put(trtList.get(0), gmpe);
                        // add new entry in the end branch hash map
                        endBranchModels.put(newLabel, newHashMap);
                    }
                    // from the hash map remove the entry corresponding
                    // to the current model
                    endBranchModels.remove(label);
                } // end loop over current end-branch models
                  // remove processed tectonic setting
                gmpeLogicTreeHashMapCopy.remove(trtList.get(0));
                trtList.remove(0);
            } // end while !gmpeLogicTreeHashMapCopy.keySet().isEmpty()
        } // end if !endBranchModels.isEmpty()
        return endBranchModels;
    } // computeGmpeLogicTreeEndBranchModels()

    private HashMap<String, ArrayList<GEMSourceData>>
            computeErfLogicTreeEndBrancheModels(
                    GemLogicTree<ArrayList<GEMSourceData>> erfLogicTree) {
        // make deep copy
        GemLogicTree<ArrayList<GEMSourceData>> erfLogicTreeCopy =
                (GemLogicTree<ArrayList<GEMSourceData>>) UnoptimizedDeepCopy
                        .copy(erfLogicTree);
        HashMap<String, ArrayList<GEMSourceData>> endBranchModels =
                new HashMap<String, ArrayList<GEMSourceData>>();
        // load source models from first branching level
        if (endBranchModels.isEmpty()) {
            // number of branches in the first branching level
            int numBranch =
                    erfLogicTreeCopy.getBranchingLevel(0).getBranchList()
                            .size();
            // loop over branches of the first branching level
            for (int i = 0; i < numBranch; i++) {
                // get current branch
                GemLogicTreeBranch branch =
                        erfLogicTreeCopy.getBranchingLevel(0).getBranch(i);
                // define label from branch ID number
                String label = Integer.toString(branch.getRelativeID());
                // read the corresponding source model
                ArrayList<GEMSourceData> srcList =
                        new InputModelData(branch.getNameInputFile(),
                                config.getDouble(ConfigItems.WIDTH_OF_MFD_BIN
                                        .name())).getSourceList();
                // save in the hash map
                endBranchModels.put(label, srcList);
            }
            // remove processed branching level
            erfLogicTreeCopy.getBranchingLevelsList().remove(0);
        }
        // if the hash map already contains the models from the
        // first branching levels go through the remaining
        // branching levels (if they exist) and create the new models
        if (!endBranchModels.isEmpty()) {
            // while there are additional branching levels
            while (!erfLogicTreeCopy.getBranchingLevelsList().isEmpty()) {
                // loop over current end branch models
                Iterator<String> endBranchModelLabels =
                        endBranchModels.keySet().iterator();
                ArrayList<String> labels = new ArrayList<String>();
                while (endBranchModelLabels.hasNext())
                    labels.add(endBranchModelLabels.next());
                for (String label : labels) {
                    // current end branch model
                    ArrayList<GEMSourceData> srcList =
                            endBranchModels.get(label);
                    // from the current end branch model create
                    // models corresponding to the branches in
                    // the first branching level of the current logic tree
                    // number of branches in the first branching level
                    int numBranch =
                            erfLogicTreeCopy.getBranchingLevel(0)
                                    .getBranchList().size();
                    // loop over branches of the first branching level
                    for (int i = 0; i < numBranch; i++) {
                        // get current branch
                        GemLogicTreeBranch branch =
                                erfLogicTreeCopy.getBranchingLevel(0)
                                        .getBranch(i);
                        // new label
                        String newLabel = label + "_" + branch.getRelativeID();
                        // new source model
                        ArrayList<GEMSourceData> newSrcList =
                                applyRuleToSourceList(srcList, branch.getRule());
                        // add new entry
                        endBranchModels.put(newLabel, newSrcList);
                    }
                    // from the hash map remove the entry corresponding
                    // to the current model
                    endBranchModels.remove(label);
                } // end loop over current end-branch models
                  // remove processed branching level
                erfLogicTreeCopy.getBranchingLevelsList().remove(0);
            } // end while !erfLogicTreeCopy.getBranchingLevelsList().isEmpty()
        } // end if !endBranchModels.isEmpty()
        return endBranchModels;
    }

    private void saveGroundMotionMapToAsciiFile(String outfile,
            ArrayList<Double> map, ArrayList<Site> siteList) {
        try {
            FileOutputStream oOutFIS = new FileOutputStream(outfile);
            BufferedOutputStream oOutBIS = new BufferedOutputStream(oOutFIS);
            BufferedWriter oWriter =
                    new BufferedWriter(new OutputStreamWriter(oOutBIS));
            // loop over grid points
            for (int i = 0; i < siteList.size(); i++) {
                double lon = siteList.get(i).getLocation().getLongitude();
                double lat = siteList.get(i).getLocation().getLatitude();
                double gmv = map.get(i);
                oWriter.write(String.format("%+8.4f %+7.4f %7.4e \n", lon, lat,
                        gmv));
            }
            oWriter.close();
            oOutBIS.close();
            oOutFIS.close();
        } catch (FileNotFoundException e) {
            // TODO Auto-generated catch block
            e.printStackTrace();
        } catch (IOException e) {
            // TODO Auto-generated catch block
            e.printStackTrace();
        }
    } // saveGroundMotionMapToGMTAsciiFile()

    private static void saveHazardCurveRepositoryListToAsciiFile(
            String outfile, GEMHazardCurveRepositoryList hazardCurves) {
        try {
            FileOutputStream oOutFIS = new FileOutputStream(outfile);
            BufferedOutputStream oOutBIS = new BufferedOutputStream(oOutFIS);
            BufferedWriter oWriter =
                    new BufferedWriter(new OutputStreamWriter(oOutBIS));
            // first line contains ground motion values
            // loop over ground motion values
            oWriter.write(String.format("%8s %8s ", " ", " "));
            for (int igmv = 0; igmv < hazardCurves.getHcRepList().get(0)
                    .getGmLevels().size(); igmv++) {
                double gmv =
                        hazardCurves.getHcRepList().get(0).getGmLevels()
                                .get(igmv);
                gmv = Math.exp(gmv);
                oWriter.write(String.format("%7.4e ", gmv));
            } // for
            oWriter.write("\n");
            // loop over grid points
            for (int igp = 0; igp < hazardCurves.getHcRepList().get(0)
                    .getNodesNumber(); igp++) {
                // loop over hazard curve realizations
                for (int ihc = 0; ihc < hazardCurves.getHcRepList().size(); ihc++) {
                    double lat =
                            hazardCurves.getHcRepList().get(0).getGridNode()
                                    .get(igp).getLocation().getLatitude();
                    double lon =
                            hazardCurves.getHcRepList().get(0).getGridNode()
                                    .get(igp).getLocation().getLongitude();
                    oWriter.write(String.format("%+8.4f %+7.4f ", lon, lat));
                    GEMHazardCurveRepository hcRep =
                            hazardCurves.getHcRepList().get(ihc);
                    // loop over ground motion values
                    for (int igmv = 0; igmv < hcRep.getGmLevels().size(); igmv++) {
                        double probEx = hcRep.getProbExceedanceList(igp)[igmv];
                        oWriter.write(String.format("%7.4e ", probEx));
                    } // for
                    oWriter.write("\n");
                } // for
            } // for
            oWriter.close();
            oOutBIS.close();
            oOutFIS.close();
        } catch (FileNotFoundException e) {
            // TODO use log4j
            File tmp =
                    new File(System.getProperties().getProperty("user.home"));

            e.printStackTrace();
        } catch (IOException e) {
            // TODO use log4j
            e.printStackTrace();
        }
    } // saveHazardCurves()

    private static void saveHazardCurveRepositoryToAsciiFile(String outfile,
            GEMHazardCurveRepository rep) {
        try {
            FileOutputStream oOutFIS = new FileOutputStream(outfile);
            BufferedOutputStream oOutBIS = new BufferedOutputStream(oOutFIS);
            BufferedWriter oWriter =
                    new BufferedWriter(new OutputStreamWriter(oOutBIS));
            // first line contains ground motion values
            // loop over ground motion values
            oWriter.write(String.format("%8s %8s ", " ", " "));
            for (int igmv = 0; igmv < rep.getGmLevels().size(); igmv++) {
                double gmv = rep.getGmLevels().get(igmv);
                gmv = Math.exp(gmv);
                oWriter.write(String.format("%7.4e ", gmv));
            } // for
            oWriter.write("\n");
            // loop over grid points
            for (int igp = 0; igp < rep.getNodesNumber(); igp++) {
                double lat =
                        rep.getGridNode().get(igp).getLocation().getLatitude();
                double lon =
                        rep.getGridNode().get(igp).getLocation().getLongitude();
                oWriter.write(String.format("%+8.4f %+7.4f ", lon, lat));
                // loop over ground motion values
                for (int igmv = 0; igmv < rep.getGmLevels().size(); igmv++) {
                    double probEx = rep.getProbExceedanceList(igp)[igmv];
                    oWriter.write(String.format("%7.4e ", probEx));
                } // for
                oWriter.write("\n");
            } // for
            oWriter.close();
            oOutBIS.close();
            oOutFIS.close();
        } catch (FileNotFoundException e) {
            // TODO use log4j
            e.printStackTrace();
        } catch (IOException e) {
            // TODO use log4j
            e.printStackTrace();
        }
    } // saveFractiles()

    private static ArrayList<Site> createSiteList(Configuration calcConfig) {
        // arraylist of sites storing locations where hazard curves must be
        // calculated
        ArrayList<Site> sites = new ArrayList<Site>();
        // create gridded region from borders coordinates and grid spacing
        // GriddedRegion gridReg = new
        // GriddedRegion(calcConfig.getRegionBoundary(),BorderType.MERCATOR_LINEAR,calcConfig.getGridSpacing(),null);
        LocationList locations =
                CalculatorConfigHelper.makeRegionboundary(calcConfig);
        // old style: "properties" - going to be deleted
        // double gridSpacing =
        // Double.parseDouble(calcConfig.getProperty(ConfigItems.REGION_GRID_SPACING.name()));
        double gridSpacing =
                calcConfig.getDouble(ConfigItems.REGION_GRID_SPACING.name());
        GriddedRegion gridReg =
                new GriddedRegion(locations, BorderType.MERCATOR_LINEAR,
                        gridSpacing, null);
        // get list of locations in the region
        LocationList locList = gridReg.getNodeList();
        // store locations as sites
        Iterator<Location> iter = locList.iterator();
        while (iter.hasNext()) {
            sites.add(new Site(iter.next()));
        }
        // return array list of sites
        return sites;
    } // createSiteList()

    private GEM1ERF sampleGemLogicTreeERF(
            GemLogicTree<ArrayList<GEMSourceData>> ltERF,
            Configuration calcConfig) {
        // erf to be returned
        GEM1ERF erf = null;
        // array list of sources that will contain the samples sources
        ArrayList<GEMSourceData> srcList = new ArrayList<GEMSourceData>();
        // number of branching levels in the logic tree
        int numBranchingLevels = ltERF.getBranchingLevelsList().size();
        // sample first branching level to get the starting source model
        int branchNumber = ltERF.sampleBranchingLevel(0);
        // get the corresponding branch (the -1 is needed because branchNumber
        // is the
        // number of the branch (starting from 1) and not the index of the
        // branch
        GemLogicTreeBranch branch =
                ltERF.getBranchingLevel(0).getBranch(branchNumber - 1);
        if (branch.getNameInputFile() != null) {
            // read input file model
            // next line shows how to read from a Properties object (will be
            // deleted soon).
            // InputModelData inputModelData = new
            // InputModelData(branch.getNameInputFile(),
            // Double.parseDouble(calcConfig.getProperty(ConfigItems.WIDTH_OF_MFD_BIN.name())));
            // new here is the apache Configuration object
            InputModelData inputModelData =
                    new InputModelData(branch.getNameInputFile(),
                            calcConfig.getDouble(ConfigItems.WIDTH_OF_MFD_BIN
                                    .name()));
            // load sources
            srcList = inputModelData.getSourceList();
        } else {
            logger.info("The first branching level of the ERF logic tree does not contain a source model!!\n"
                    + "Please correct your input!\n" + "Execution stopped!");
            // System.out.println("The first branching level of the ERF logic tree does not contain a source model!!");
            // System.out.println("Please correct your input!");
            // System.out.println("Execution stopped!");
            System.exit(0);
        }
        // loop over sources
        // source index
        int sourceIndex = 0;
        for (GEMSourceData src : srcList) {
            // for each source, loop over remaining branching levels and apply
            // uncertainties
            for (int i = 1; i < numBranchingLevels; i++) {
                // sample the current branching level
                branchNumber = ltERF.sampleBranchingLevel(i);
                // get the sampled branch
                branch = ltERF.getBranchingLevel(i).getBranch(branchNumber - 1);
                if (branch.getRule() != null) {
                    // at the moment we apply rules to all source typologies. In
                    // the future we may want
                    // to apply some filter (i.e. apply rule to this source type
                    // only...)
                    // if area source
                    if (src instanceof GEMAreaSourceData) {
                        // replace the old source with the new source
                        // accordingly to the rule
                        srcList.set(
                                sourceIndex,
                                applyRuleToAreaSource((GEMAreaSourceData) src,
                                        branch.getRule()));
                    }
                    // if point source
                    if (src instanceof GEMPointSourceData) {
                        // replace the old source with the new source
                        // accordingly to the rule
                        srcList.set(
                                sourceIndex,
                                applyRuleToPointSource(
                                        (GEMPointSourceData) src,
                                        branch.getRule()));
                    }
                    // if fault source
                    if (src instanceof GEMFaultSourceData) {
                        // replace the old source with the new source
                        // accordingly to the rule
                        srcList.set(
                                sourceIndex,
                                applyRuleToFaultSource(
                                        (GEMFaultSourceData) src,
                                        branch.getRule()));
                    }
                    // if subduction source
                    if (src instanceof GEMSubductionFaultSourceData) {
                        // replace the old source with the new source
                        // accordingly to the rule
                        srcList.set(
                                sourceIndex,
                                applyRuleToSubductionFaultSource(
                                        (GEMSubductionFaultSourceData) src,
                                        branch.getRule()));
                    }
                } else {
                    // rule is not defined:
                    logger.info("No rule is defined at branching level: " + i
                            + "\n" + "Please correct your input!\n"
                            + "Execution stopped!");
                    // System.out.println("No rule is defined at branching level: "
                    // + i);
                    // System.out.println("Please correct your input!");
                    // System.out.println("Execution stopped!");
                    System.exit(0);
                } // end if no rule is defined
            } // end loop over branching levels
            sourceIndex = sourceIndex + 1;
        } // end loop over sources
          // instantiate ERF
        erf = new GEM1ERF(srcList);
        // set ERF parameters
        setGEM1ERFParams(erf, calcConfig);
        return erf;
    } // sampleGemLogicTreeERF()

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
            GEMAreaSourceData areaSrc, GemLogicTreeRule rule) {
        // define new area source
        GEMAreaSourceData newAreaSrc = areaSrc;
        // if uncertainties on GR Mmax or GR b value
        if (rule.getRuleName()
                .toString()
                .equalsIgnoreCase(
                        GemLogicTreeRuleParam.mMaxGRRelative.toString())
                || rule.getRuleName()
                        .toString()
                        .equalsIgnoreCase(
                                GemLogicTreeRuleParam.bGRRelative.toString())) {
            // loop over mfds
            // mfd index
            int mfdIndex = 0;
            for (IncrementalMagFreqDist mfd : areaSrc.getMagfreqDistFocMech()
                    .getMagFreqDistList()) {
                if (mfd instanceof GutenbergRichterMagFreqDist) {
                    // new mfd
                    GutenbergRichterMagFreqDist newMfdGr = null;
                    if (rule.getRuleName()
                            .toString()
                            .equalsIgnoreCase(
                                    GemLogicTreeRuleParam.mMaxGRRelative
                                            .toString())) {
                        // uncertainties on Mmax
                        newMfdGr =
                                applyMmaxGrRelative(
                                        (GutenbergRichterMagFreqDist) mfd,
                                        rule.getVal(), areaSrc.getName());
                    } else if (rule
                            .getRuleName()
                            .toString()
                            .equalsIgnoreCase(
                                    GemLogicTreeRuleParam.bGRRelative
                                            .toString())) {
                        // uncertainties on b value
                        newMfdGr =
                                applybGrRelative(
                                        (GutenbergRichterMagFreqDist) mfd,
                                        rule.getVal(), areaSrc.getName());
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
            logger.info("Rule: " + rule.getRuleName().toString()
                    + " not supported.\n"
                    + "Check your input. Execution is stopped.");
            // System.out.println("Rule: " + rule.getRuleName().toString() +
            // " not supported.");
            // System.out.println("Check your input. Execution is stopped.");
            System.exit(0);
        }
        return null;
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
            GEMPointSourceData pntSrc, GemLogicTreeRule rule) {
        // new point source
        GEMPointSourceData newPntSource = pntSrc;
        // if uncertainties on GR Mmax or GR b value
        if (rule.getRuleName()
                .toString()
                .equalsIgnoreCase(
                        GemLogicTreeRuleParam.mMaxGRRelative.toString())
                || rule.getRuleName()
                        .toString()
                        .equalsIgnoreCase(
                                GemLogicTreeRuleParam.bGRRelative.toString())) {
            // loop over mfds
            // mfd index
            int mfdIndex = 0;
            for (IncrementalMagFreqDist mfd : pntSrc.getHypoMagFreqDistAtLoc()
                    .getMagFreqDistList()) {
                if (mfd instanceof GutenbergRichterMagFreqDist) {
                    GutenbergRichterMagFreqDist newMfdGr = null;
                    // create new mfd by applying rule
                    if (rule.getRuleName()
                            .toString()
                            .equalsIgnoreCase(
                                    GemLogicTreeRuleParam.mMaxGRRelative
                                            .toString())) {
                        newMfdGr =
                                applyMmaxGrRelative(
                                        (GutenbergRichterMagFreqDist) mfd,
                                        rule.getVal(), pntSrc.getName());
                    } else if (rule
                            .getRuleName()
                            .toString()
                            .equalsIgnoreCase(
                                    GemLogicTreeRuleParam.bGRRelative
                                            .toString())) {
                        newMfdGr =
                                applybGrRelative(
                                        (GutenbergRichterMagFreqDist) mfd,
                                        rule.getVal(), pntSrc.getName());
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
            logger.info("Rule: " + rule.getRuleName().toString()
                    + " not supported.\n"
                    + "Check your input. Execution is stopped.");
            // System.out.println("Rule: " + rule.getRuleName().toString() +
            // " not supported.");
            // System.out.println("Check your input. Execution is stopped.");
            System.exit(0);
        }
        return null;
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
            GEMFaultSourceData faultSrc, GemLogicTreeRule rule) {
        // if uncertainties on GR Mmax or GR b value
        if (rule.getRuleName()
                .toString()
                .equalsIgnoreCase(
                        GemLogicTreeRuleParam.mMaxGRRelative.toString())
                || rule.getRuleName()
                        .toString()
                        .equalsIgnoreCase(
                                GemLogicTreeRuleParam.bGRRelative.toString())) {
            // mfd
            IncrementalMagFreqDist mfd = faultSrc.getMfd();
            if (mfd instanceof GutenbergRichterMagFreqDist) {
                GutenbergRichterMagFreqDist newMfdGr = null;
                // create new mfd by applying rule
                if (rule.getRuleName()
                        .toString()
                        .equalsIgnoreCase(
                                GemLogicTreeRuleParam.mMaxGRRelative.toString())) {
                    newMfdGr =
                            applyMmaxGrRelative(
                                    (GutenbergRichterMagFreqDist) mfd,
                                    rule.getVal(), faultSrc.getName());
                } else if (rule
                        .getRuleName()
                        .toString()
                        .equalsIgnoreCase(
                                GemLogicTreeRuleParam.bGRRelative.toString())) {
                    newMfdGr =
                            applybGrRelative((GutenbergRichterMagFreqDist) mfd,
                                    rule.getVal(), faultSrc.getName());
                }
                // return new fault source with new mfd
                return new GEMFaultSourceData(faultSrc.getID(),
                        faultSrc.getName(), faultSrc.getTectReg(), newMfdGr,
                        faultSrc.getTrace(), faultSrc.getDip(),
                        faultSrc.getDip(), faultSrc.getSeismDepthLow(),
                        faultSrc.getSeismDepthUpp(),
                        faultSrc.getFloatRuptureFlag());
            } else {
                // mfd is not GR
                // if the uncertainty do not apply return the unchanged object
                return faultSrc;
            }
        } else {
            // not(rule == mMaxGRRelative || == bGRRelative)
            logger.info("Rule: " + rule.getRuleName().toString()
                    + " not supported.\n"
                    + "Check your input. Execution is stopped.");
            // System.out.println("Rule: " + rule.getRuleName().toString() +
            // " not supported.");
            // System.out.println("Check your input. Execution is stopped.");
            System.exit(0);
        }
        return null;
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
    private static GEMSubductionFaultSourceData
            applyRuleToSubductionFaultSource(
                    GEMSubductionFaultSourceData subFaultSrc,
                    GemLogicTreeRule rule) {

        // if uncertainties on GR Mmax or GR b value
        if (rule.getRuleName()
                .toString()
                .equalsIgnoreCase(
                        GemLogicTreeRuleParam.mMaxGRRelative.toString())
                || rule.getRuleName()
                        .toString()
                        .equalsIgnoreCase(
                                GemLogicTreeRuleParam.bGRRelative.toString())) {

            // mfd
            IncrementalMagFreqDist mfd = subFaultSrc.getMfd();

            if (mfd instanceof GutenbergRichterMagFreqDist) {

                GutenbergRichterMagFreqDist newMfdGr = null;

                // create new mfd by applying rule
                if (rule.getRuleName()
                        .toString()
                        .equalsIgnoreCase(
                                GemLogicTreeRuleParam.mMaxGRRelative.toString())) {
                    newMfdGr =
                            applyMmaxGrRelative(
                                    (GutenbergRichterMagFreqDist) mfd,
                                    rule.getVal(), subFaultSrc.getName());
                } else if (rule
                        .getRuleName()
                        .toString()
                        .equalsIgnoreCase(
                                GemLogicTreeRuleParam.bGRRelative.toString())) {
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
            logger.info("Rule: " + rule.getRuleName().toString()
                    + " not supported.\n"
                    + "Check your input. Execution is stopped.");
            // System.out.println("Rule: " + rule.getRuleName().toString() +
            // " not supported.");
            // System.out.println("Check your input. Execution is stopped.");
            System.exit(0);
        }
        return null;
    } // applyRuleToSubductionFaultSource()

    private static ArrayList<GEMSourceData> applyRuleToSourceList(
            ArrayList<GEMSourceData> srcList, GemLogicTreeRule rule) {

        ArrayList<GEMSourceData> newSrcList = new ArrayList<GEMSourceData>();

        for (GEMSourceData src : srcList) {

            if (src instanceof GEMAreaSourceData) {
                newSrcList.add(applyRuleToAreaSource((GEMAreaSourceData) src,
                        rule));
            } else if (src instanceof GEMPointSourceData) {
                newSrcList.add(applyRuleToPointSource((GEMPointSourceData) src,
                        rule));
            } else if (src instanceof GEMFaultSourceData) {
                newSrcList.add(applyRuleToFaultSource((GEMFaultSourceData) src,
                        rule));
            } else if (src instanceof GEMSubductionFaultSourceData) {
                newSrcList.add(applyRuleToSubductionFaultSource(
                        (GEMSubductionFaultSourceData) src, rule));
            }

        }

        return newSrcList;

    }

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
            logger.info("Uncertaintiy value: "
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

    private static GutenbergRichterMagFreqDist
            applybGrRelative(GutenbergRichterMagFreqDist mfdGR, double deltaB,
                    String sourceName) {

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
            logger.info("Uncertaintiy value: " + deltaB
                    + " on b value for source: " + sourceName
                    + " give b value smaller than 0!\n"
                    + "Check your input. Execution stopped!");
            // System.out.println("Uncertaintiy value: " + deltaB +
            // " on b value for source: " + sourceName
            // + " give b value smaller than 0!");
            // System.out.println("Check your input. Execution stopped!");
            System.exit(0);
            return null;
        }

    }

    /**
     * Set the GEM1ERF params given the parameters defined in
     * 
     * @param erf
     *            : erf for which parameters have to be set
     * @param calcConfig
     *            : calculator configuration obejct containing parameters for
     *            the ERF
     */
    private void setGEM1ERFParams(GEM1ERF erf, Configuration calcConfig) {
        // set minimum magnitude
        /*
         * xxr: TODO: !!!type safety!!! apache's Configuration interface handles
         * a similar problem this way: Instead of defining one single method
         * like public void setParameter(String key, Object value) {...} there
         * is one method per type defined: setString(), setDouble(), setInt(),
         * ...
         */
        erf.setParameter(GEM1ERF.MIN_MAG_NAME,
                calcConfig.getDouble(ConfigItems.MINIMUM_MAGNITUDE.name()));
        // set time span
        TimeSpan timeSpan = new TimeSpan(TimeSpan.NONE, TimeSpan.YEARS);
        timeSpan.setDuration(calcConfig
                .getDouble(ConfigItems.INVESTIGATION_TIME.name()));
        erf.setTimeSpan(timeSpan);

        // params for area source
        // set inclusion of area sources in the calculation
        erf.setParameter(GEM1ERF.INCLUDE_AREA_SRC_PARAM_NAME,
                calcConfig.getBoolean(ConfigItems.INCLUDE_AREA_SOURCES.name()));
        // set rupture type ("area source rupture model /
        // area_source_rupture_model / AreaSourceRuptureModel)
        erf.setParameter(GEM1ERF.AREA_SRC_RUP_TYPE_NAME,
                calcConfig.getString(ConfigItems.TREAT_AREA_SOURCE_AS.name()));
        // set area discretization
        erf.setParameter(GEM1ERF.AREA_SRC_DISCR_PARAM_NAME, calcConfig
                .getDouble(ConfigItems.AREA_SOURCE_DISCRETIZATION.name()));
        // set mag-scaling relationship
        erf.setParameter(
                GEM1ERF.AREA_SRC_MAG_SCALING_REL_PARAM_NAME,
                calcConfig
                        .getString(ConfigItems.AREA_SOURCE_MAGNITUDE_SCALING_RELATIONSHIP
                                .name()));
        // params for grid source
        // inclusion of grid sources in the calculation
        erf.setParameter(GEM1ERF.INCLUDE_GRIDDED_SEIS_PARAM_NAME,
                calcConfig.getBoolean(ConfigItems.INCLUDE_GRID_SOURCES.name()));
        // rupture model
        erf.setParameter(GEM1ERF.GRIDDED_SEIS_RUP_TYPE_NAME,
                calcConfig.getString(ConfigItems.TREAT_GRID_SOURCE_AS.name()));
        // mag-scaling relationship
        erf.setParameter(
                GEM1ERF.GRIDDED_SEIS_MAG_SCALING_REL_PARAM_NAME,
                calcConfig
                        .getString(ConfigItems.AREA_SOURCE_MAGNITUDE_SCALING_RELATIONSHIP
                                .name()));

        // params for fault source
        // inclusion of fault sources in the calculation
        erf.setParameter(GEM1ERF.INCLUDE_FAULT_SOURCES_PARAM_NAME,
                calcConfig.getBoolean(ConfigItems.INCLUDE_FAULT_SOURCE.name()));
        // rupture offset
        erf.setParameter(GEM1ERF.FAULT_RUP_OFFSET_PARAM_NAME,
                calcConfig.getDouble(ConfigItems.FAULT_RUPTURE_OFFSET.name()));
        // surface discretization
        erf.setParameter(GEM1ERF.FAULT_DISCR_PARAM_NAME, calcConfig
                .getDouble(ConfigItems.FAULT_SURFACE_DISCRETIZATION.name()));
        // mag-scaling relationship
        erf.setParameter(GEM1ERF.FAULT_MAG_SCALING_REL_PARAM_NAME, calcConfig
                .getString(ConfigItems.FAULT_MAGNITUDE_SCALING_RELATIONSHIP
                        .name()));

        // mag-scaling sigma
        erf.setParameter(GEM1ERF.FAULT_SCALING_SIGMA_PARAM_NAME, calcConfig
                .getDouble(ConfigItems.FAULT_MAGNITUDE_SCALING_SIGMA.name()));
        // rupture aspect ratio
        erf.setParameter(GEM1ERF.FAULT_RUP_ASPECT_RATIO_PARAM_NAME,
                calcConfig.getDouble(ConfigItems.RUPTURE_ASPECT_RATIO.name()));
        // rupture floating type
        erf.setParameter(GEM1ERF.FAULT_FLOATER_TYPE_PARAM_NAME,
                calcConfig.getString(ConfigItems.RUPTURE_FLOATING_TYPE.name()));

        // params for subduction fault
        // inclusion of fault sources in the calculation
        erf.setParameter(GEM1ERF.INCLUDE_SUBDUCTION_SOURCES_PARAM_NAME,
                calcConfig
                        .getBoolean(ConfigItems.INCLUDE_SUBDUCTION_FAULT_SOURCE
                                .name()));
        // rupture offset
        erf.setParameter(GEM1ERF.SUB_RUP_OFFSET_PARAM_NAME, calcConfig
                .getDouble(ConfigItems.SUBDUCTION_FAULT_RUPTURE_OFFSET.name()));
        // surface discretization
        erf.setParameter(GEM1ERF.SUB_DISCR_PARAM_NAME, calcConfig
                .getDouble(ConfigItems.SUBDUCTION_FAULT_SURFACE_DISCRETIZATION
                        .name()));
        // mag-scaling relationship
        erf.setParameter(
                GEM1ERF.SUB_MAG_SCALING_REL_PARAM_NAME,
                calcConfig
                        .getString(ConfigItems.SUBDUCTION_FAULT_MAGNITUDE_SCALING_RELATIONSHIP
                                .name()));
        // mag-scaling sigma
        erf.setParameter(GEM1ERF.SUB_SCALING_SIGMA_PARAM_NAME, calcConfig
                .getDouble(ConfigItems.SUBDUCTION_FAULT_MAGNITUDE_SCALING_SIGMA
                        .name()));
        // rupture aspect ratio
        erf.setParameter(GEM1ERF.SUB_RUP_ASPECT_RATIO_PARAM_NAME, calcConfig
                .getDouble(ConfigItems.SUBDUCTION_RUPTURE_ASPECT_RATIO.name()));
        // rupture floating type
        erf.setParameter(GEM1ERF.SUB_FLOATER_TYPE_PARAM_NAME, calcConfig
                .getString(ConfigItems.SUBDUCTION_RUPTURE_FLOATING_TYPE.name()));

        // update
        erf.updateForecast();
    } // setGEM1ERFParams()

    private static
            HashMap<TectonicRegionType, ScalarIntensityMeasureRelationshipAPI>
            sampleGemLogicTreeGMPE(
                    HashMap<TectonicRegionType, GemLogicTree<ScalarIntensityMeasureRelationshipAPI>> listLtGMPE) {

        HashMap<TectonicRegionType, ScalarIntensityMeasureRelationshipAPI> hm =
                new HashMap<TectonicRegionType, ScalarIntensityMeasureRelationshipAPI>();

        // loop over tectonic regions
        Iterator<TectonicRegionType> iter = listLtGMPE.keySet().iterator();
        while (iter.hasNext()) {

            // get tectonic region type
            TectonicRegionType trt = iter.next();

            // get corresponding logic tree
            GemLogicTree<ScalarIntensityMeasureRelationshipAPI> ltGMPE =
                    listLtGMPE.get(trt);

            // sample the first branching level
            int branch = ltGMPE.sampleBranchingLevel(0);

            // select the corresponding gmpe from the end-branch mapping
            ScalarIntensityMeasureRelationshipAPI gmpe =
                    ltGMPE.getEBMap().get(Integer.toString(branch));

            hm.put(trt, gmpe);
        }

        return hm;

    }

    // for testing
    public static void main(String[] args) throws IOException,
            SecurityException, IllegalArgumentException,
            ClassNotFoundException, InstantiationException,
            IllegalAccessException, NoSuchMethodException,
            InvocationTargetException, ConfigurationException {
        // Uncomment to test the configuration of the logging appenders:
        // String msg =
        // "User directory to put the file CalculatorConfig.properties -> "
        // + System.getProperty("user.dir");
        // URL url =
        // Thread.currentThread().getContextClassLoader().getResource(".");
        // String workingDirectory = "working directory is : " + url.toString();
        // logger.trace(msg);
        // logger.trace(url);
        // logger.debug(msg);
        // logger.debug(url);
        // logger.info(msg);
        // logger.info(url);
        // logger.warn(msg);
        // logger.warn(url);
        // logger.error(msg);
        // logger.error(url);
        // logger.fatal(msg);
        // logger.fatal(url);

        CommandLineCalculator clc =
                new CommandLineCalculator("CalculatorConfig.properties");
        clc.doCalculation();
        // clc.doCalculationThroughMonteCarloApproach();
        // clc.saveMeanGroundMotionMapToGMTAsciiFile();
        System.exit(0);
    } // main()

} // class CommandLineCalculatorWithProperties
