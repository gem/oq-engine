package org.gem.engine;

import java.io.BufferedInputStream;
import java.io.BufferedReader;
import java.io.ByteArrayInputStream;
import java.io.File;
import java.io.FileInputStream;
import java.io.FileNotFoundException;
import java.io.IOException;
import java.io.InputStream;
import java.io.InputStreamReader;
import java.lang.reflect.Constructor;
import java.util.HashMap;
import java.util.Map;
import java.util.StringTokenizer;

import org.apache.commons.logging.Log;
import org.apache.commons.logging.LogFactory;
import org.gem.engine.hazard.redis.Cache;
import org.gem.engine.logictree.LogicTree;
import org.gem.engine.logictree.LogicTreeBranch;
import org.gem.engine.logictree.LogicTreeBranchingLevel;
import org.opensha.commons.param.event.ParameterChangeWarningEvent;
import org.opensha.commons.param.event.ParameterChangeWarningListener;
import org.opensha.sha.imr.AttenuationRelationship;
import org.opensha.sha.imr.ScalarIntensityMeasureRelationshipAPI;
import org.opensha.sha.imr.param.IntensityMeasureParams.DampingParam;
import org.opensha.sha.imr.param.IntensityMeasureParams.PeriodParam;
import org.opensha.sha.imr.param.IntensityMeasureParams.SA_Param;
import org.opensha.sha.imr.param.OtherParams.ComponentParam;
import org.opensha.sha.imr.param.OtherParams.SigmaTruncLevelParam;
import org.opensha.sha.imr.param.OtherParams.SigmaTruncTypeParam;
import org.opensha.sha.imr.param.OtherParams.StdDevTypeParam;
import org.opensha.sha.util.TectonicRegionType;

/**
 * Instantiates {@link LogicTree} objects for ground motion prediction equations
 * (GMPEs). Each {@link LogicTree} is associated to a {@link TectonicRegionType}
 * and contains {@link AttenuationRelationship} objects. Logic tree data can be
 * read from cache or file and are expected to be in nrML format. The specified
 * GMPEs are expected to be the class names of the attenuation relationships
 * defined in org.opensha.sha.imr.attenRelImpl package in OpenSHA-lite. From the
 * GMPE name the corresponding {@link AttenuationRelationship} class is created
 * through reflection. GMPE parameters are requested for setting
 * {@link AttenuationRelationship} parameters.
 */
public class GmpeLogicTreeData {

    private static Log logger = LogFactory.getLog(GmpeLogicTreeData.class);

    private final ParameterChangeWarningListener warningListener = null;

    private BufferedReader bufferedReader;

    private HashMap<TectonicRegionType, LogicTree<ScalarIntensityMeasureRelationshipAPI>> gmpeLogicTreeHashMap;

    private static final String packageName =
            "org.opensha.sha.imr.attenRelImpl.";

    /**
     * Creates a new {@link GmpeLogicTreeData} given cache and key to read from.
     */
    public GmpeLogicTreeData(Cache cache, String key) throws IOException {

        String source = (String) cache.get(key);
        byte[] bytevals = source.getBytes();
        InputStream byteis = new ByteArrayInputStream(bytevals);
        BufferedInputStream oBIS = new BufferedInputStream(byteis);
        this.bufferedReader = new BufferedReader(new InputStreamReader(oBIS));
        gmpeLogicTreeHashMap =
                new HashMap<TectonicRegionType, LogicTree<ScalarIntensityMeasureRelationshipAPI>>();
    }

    /**
     * Creates a new {@link GmpeLogicTreeData} given the path of the file to
     * read from.
     */
    public GmpeLogicTreeData(String path) throws FileNotFoundException {

        File file = new File(path);
        FileInputStream oFIS = new FileInputStream(file.getPath());
        BufferedInputStream oBIS = new BufferedInputStream(oFIS);
        this.bufferedReader = new BufferedReader(new InputStreamReader(oBIS));
        gmpeLogicTreeHashMap =
                new HashMap<TectonicRegionType, LogicTree<ScalarIntensityMeasureRelationshipAPI>>();
    }

    public GmpeLogicTreeData ()
    {
        
    }
    
    /**
     * Reads logic tree data and instantiates {@link LogicTree} objects for each
     * {@link TectonicRegionType}. Each {@link LogicTree} contains
     * {@link AttenuationRelationship} objects with the given parameters set up.
     */
    public void parse_tree(String component, String intensityMeasureType,
            double period, double damping, String truncType, double truncLevel,
            String stdType, double vs30) {

        LogicTreeReader logicTreeReader = new LogicTreeReader(bufferedReader);

        Map<String, LogicTree> logicTreeMap = logicTreeReader.read();

        if (logicTreeMap.get(TectonicRegionType.ACTIVE_SHALLOW.toString()) != null) {
            setGMPELogicTree(TectonicRegionType.ACTIVE_SHALLOW.toString(),
                    component, intensityMeasureType, period, damping,
                    truncType, truncLevel, stdType, vs30, logicTreeMap);
        }

        if (logicTreeMap.get(TectonicRegionType.STABLE_SHALLOW.toString()) != null) {
            setGMPELogicTree(TectonicRegionType.STABLE_SHALLOW.toString(),
                    component, intensityMeasureType, period, damping,
                    truncType, truncLevel, stdType, vs30, logicTreeMap);
        }

        if (logicTreeMap
                .get(TectonicRegionType.SUBDUCTION_INTERFACE.toString()) != null) {
            setGMPELogicTree(
                    TectonicRegionType.SUBDUCTION_INTERFACE.toString(),
                    component, intensityMeasureType, period, damping,
                    truncType, truncLevel, stdType, vs30, logicTreeMap);
        }

        if (logicTreeMap.get(TectonicRegionType.SUBDUCTION_SLAB.toString()) != null) {
            setGMPELogicTree(TectonicRegionType.SUBDUCTION_SLAB.toString(),
                    component, intensityMeasureType, period, damping,
                    truncType, truncLevel, stdType, vs30, logicTreeMap);
        }

    }

    /**
     * Instantiates logic tree for a given tectonic region type
     */
    private void setGMPELogicTree(String tectReg, String component,
            String intensityMeasureType, double period, double damping,
            String truncType, double truncLevel, String stdType, double vs30,
            Map<String, LogicTree> logicTreeMap) {
        LogicTree logicTree = logicTreeMap.get(tectReg);
        String gmpeNames = "";
        String weights = "";
        for (int i = 0; i < logicTree.getBranchingLevelAt(0).getBranchList()
                .size(); i++) {
            gmpeNames =
                    gmpeNames
                            + logicTree.getBranchingLevelAt(0).getBranch(i)
                                    .getBranchingValue() + " ";
            weights =
                    weights
                            + logicTree.getBranchingLevelAt(0).getBranch(i)
                                    .getWeight() + " ";
        }
        gmpeNames = gmpeNames.trim();
        weights = weights.trim();
        gmpeLogicTreeHashMap.put(
                TectonicRegionType.getTypeForName(tectReg),
                createGmpeLogicTree(gmpeNames, weights, component,
                        intensityMeasureType, period, damping, truncType,
                        truncLevel, stdType, vs30));
    }

    /**
     * create GMPE logic tree from string of names and string of weights
     */
    private LogicTree<ScalarIntensityMeasureRelationshipAPI>
            createGmpeLogicTree(String gmpeNames, String gmpeWeights,
                    String component, String intensityMeasureType,
                    double period, double damping, String truncType,
                    double truncLevel, String stdType, double vs30) {

        ParameterChangeWarningEvent event = null;

        StringTokenizer name = new StringTokenizer(gmpeNames);
        StringTokenizer weight = new StringTokenizer(gmpeWeights);
        if (name.countTokens() != weight.countTokens()) {
            String msg =
                    "Number of gmpes do not corresponds to number of weights!\n"
                            + "Check your input!\n" + "Execution stopped!\n";
            logger.fatal(msg);
            throw new IllegalArgumentException(msg);
        }

        // create logic tree structure consisting of only one branching level
        // the number of branches in the branching level corresponds to the
        // number of gmpes defined
        LogicTree<ScalarIntensityMeasureRelationshipAPI> gmpeLogicTree =
                new LogicTree<ScalarIntensityMeasureRelationshipAPI>();
        LogicTreeBranchingLevel branchingLevel =
                new LogicTreeBranchingLevel(1, "", 0);
        LogicTreeBranch branch = null;
        int numBranch = name.countTokens();
        for (int i = 0; i < numBranch; i++) {
            String gmpeName = name.nextToken();
            double gmpeWeight = Double.parseDouble(weight.nextToken());
            branch = new LogicTreeBranch((i + 1), gmpeName, gmpeWeight);
            branchingLevel.addBranch(branch);
        }
        gmpeLogicTree.appendBranchingLevel(branchingLevel);

        // instantiate GMPE for each branch through reflection
        for (int i = 0; i < numBranch; i++) {
            String gmpeName =
                    gmpeLogicTree.getBranchingLevelAt(0).getBranch(i)
                            .getBranchingValue();
            Class cl = null;
            Constructor cstr = null;
            AttenuationRelationship ar = null;
            try {
                cl = Class.forName(packageName + gmpeName);
                cstr =
                        cl.getConstructor(new Class[] { ParameterChangeWarningListener.class });
                ar =
                        (AttenuationRelationship) cstr
                                .newInstance(warningListener);
            } catch (Exception e) {
                throw new RuntimeException(e);
            }
            ar.setParamDefaults();
            setGmpeParams(component, intensityMeasureType, period, damping,
                    truncType, truncLevel, stdType, vs30, ar);
            gmpeLogicTree.getEBMap().put(
                    Integer.toString(gmpeLogicTree.getBranchingLevelAt(0)
                            .getBranch(i).getRelativeID()), ar);
        }
        return gmpeLogicTree;
    }

    /**
     * Set GMPE parameters
     */
    public static void setGmpeParams(String component, String intensityMeasureType,
            double period, double damping, String truncType, double truncLevel,
            String stdType, double vs30, AttenuationRelationship ar) {
        String gmpeName = ar.getClass().getCanonicalName();

        ar.setComponentParameter(component, intensityMeasureType);
        
        if (ar.getSupportedIntensityMeasuresList().containsParameter(
                intensityMeasureType)) {
            ar.setIntensityMeasure(intensityMeasureType);
        } else {
            String msg =
                    "The chosen intensity measure type: "
                            + intensityMeasureType + " is not supported by "
                            + gmpeName + "\n"
                            + "The supported types are the following:\n"
                            + ar.getSupportedIntensityMeasuresList().toString()
                            + "\n" + "Check your input file!\n"
                            + "Execution stopped.";
            logger.error(msg);
            throw new IllegalArgumentException(msg);
        }
        if (intensityMeasureType.equalsIgnoreCase(SA_Param.NAME)) {
            if (ar.getParameter(PeriodParam.NAME).isAllowed(period)) {
                ar.getParameter(PeriodParam.NAME).setValue(period);
            } else {
                String msg =
                        "The chosen period: "
                                + period
                                + " is not supported by "
                                + gmpeName
                                + "\n"
                                + "The allowed values are the following:\n"
                                + ar.getParameter(PeriodParam.NAME)
                                        .getConstraint() + "\n"
                                + "Check your input file\n"
                                + "Execution stopped.";
                logger.error(msg);
                new IllegalArgumentException(msg);
            }
            if (ar.getParameter(DampingParam.NAME).isAllowed(damping)) {
                ar.getParameter(DampingParam.NAME).setValue(damping);
            } else {
                String msg =
                        "The chosen damping: "
                                + damping
                                + " is not supported by "
                                + gmpeName
                                + "\n"
                                + "The allowed values are the following:\n"
                                + ar.getParameter(DampingParam.NAME)
                                        .getConstraint() + "\n"
                                + "Check your input file\n"
                                + "Execution stopped.";
                logger.error(msg);
                throw new IllegalArgumentException(msg);
            }
        }
        if (ar.getParameter(SigmaTruncTypeParam.NAME).isAllowed(truncType)) {
            ar.getParameter(SigmaTruncTypeParam.NAME).setValue(truncType);
        } else {
            String msg =
                    "The chosen truncation type: "
                            + truncType
                            + " is not supported.\n"
                            + "The allowed values are the following:\n"
                            + ar.getParameter(SigmaTruncTypeParam.NAME)
                                    .getConstraint() + "\n"
                            + "Check your input file\n" + "Execution stopped.";
            logger.error(msg);
            throw new IllegalArgumentException(msg);
        }
        if (ar.getParameter(SigmaTruncLevelParam.NAME).isAllowed(truncLevel)) {
            ar.getParameter(SigmaTruncLevelParam.NAME).setValue(truncLevel);
        } else {
            String msg =
                    "The chosen truncation level: "
                            + truncLevel
                            + " is not supported.\n"
                            + "The allowed values are the following: \n"
                            + ar.getParameter(SigmaTruncLevelParam.NAME)
                                    .getConstraint() + "\n"
                            + "Check your input file\n" + "Execution stopped.";
            logger.error(msg);
            throw new IllegalArgumentException(msg);
        }
        if (ar.getParameter(StdDevTypeParam.NAME).isAllowed(stdType)) {
            ar.getParameter(StdDevTypeParam.NAME).setValue(stdType);
        } else {
            String msg =
                    "The chosen standard deviation type: "
                            + stdType
                            + " is not supported by "
                            + gmpeName
                            + "\n"
                            + "The allowed values are the following: \n"
                            + ar.getParameter(StdDevTypeParam.NAME)
                                    .getConstraint() + "\n"
                            + "Check your input file\n" + "Execution stopped.";
            logger.error(msg);
            new IllegalArgumentException(msg);
        }
    }

    /**
     * Returns map of GMPE {@link LogicTree} with {@link TectonicRegionType} as
     * keys
     */
    public
            HashMap<TectonicRegionType, LogicTree<ScalarIntensityMeasureRelationshipAPI>>
            getGmpeLogicTreeHashMap() {
        return this.gmpeLogicTreeHashMap;
    }

}
