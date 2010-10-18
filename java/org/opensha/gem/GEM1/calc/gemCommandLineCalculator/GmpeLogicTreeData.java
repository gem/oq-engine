package org.opensha.gem.GEM1.calc.gemCommandLineCalculator;

import java.io.BufferedInputStream;
import java.io.BufferedReader;
import java.io.File;
import java.io.FileInputStream;
import java.io.IOException;
import java.io.InputStreamReader;
import java.lang.reflect.Constructor;
import java.lang.reflect.InvocationTargetException;
import java.util.HashMap;
import java.util.Hashtable;
import java.util.StringTokenizer;

import org.apache.commons.logging.Log;
import org.apache.commons.logging.LogFactory;
import org.opensha.commons.param.event.ParameterChangeWarningEvent;
import org.opensha.commons.param.event.ParameterChangeWarningListener;
import org.opensha.gem.GEM1.calc.gemLogicTree.GemLogicTree;
import org.opensha.gem.GEM1.calc.gemLogicTree.GemLogicTreeBranch;
import org.opensha.gem.GEM1.calc.gemLogicTree.GemLogicTreeBranchingLevel;
import org.opensha.sha.imr.AttenuationRelationship;
import org.opensha.sha.imr.ScalarIntensityMeasureRelationshipAPI;
import org.opensha.sha.imr.param.IntensityMeasureParams.DampingParam;
import org.opensha.sha.imr.param.IntensityMeasureParams.PeriodParam;
import org.opensha.sha.imr.param.IntensityMeasureParams.SA_Param;
import org.opensha.sha.imr.param.OtherParams.ComponentParam;
import org.opensha.sha.imr.param.OtherParams.SigmaTruncLevelParam;
import org.opensha.sha.imr.param.OtherParams.SigmaTruncTypeParam;
import org.opensha.sha.imr.param.OtherParams.StdDevTypeParam;
import org.opensha.sha.imr.param.SiteParams.Vs30_Param;
import org.opensha.sha.util.TectonicRegionType;

public class GmpeLogicTreeData {

    // declaring the logger static here is more efficient for application code.
    // This is not safe for a class which may be deployed via a "shared"
    // classloader
    private static Log logger = LogFactory.getLog(GmpeLogicTreeData.class);

    // hash map of gmpe logic tree
    private HashMap<TectonicRegionType, GemLogicTree<ScalarIntensityMeasureRelationshipAPI>> gmpeLogicTreeHashMap;

    // comment line identifier
    private static String comment = "#";

    // package for gmpe
    private String packageName = "org.opensha.sha.imr.attenRelImpl.";

    // for debugging
    private static Boolean D = false;

    public GmpeLogicTreeData(String gmpeInputFile, String component,
            String intensityMeasureType, double period, double damping,
            String truncType, double truncLevel, String stdType, double vs30) {
        D = logger.isDebugEnabled();
        try {
            // instatiate hash map of gmpe logic tree
            gmpeLogicTreeHashMap =
                    new HashMap<TectonicRegionType, GemLogicTree<ScalarIntensityMeasureRelationshipAPI>>();

            String sRecord = null;

            String activeShallowGmpeNames = null;
            String activeShallowGmpeWeights = null;

            String stableShallowGmpeNames = null;
            String stableShallowGmpeWeights = null;

            String subductionInterfaceGmpeNames = null;
            String subductionInterfaceGmpeWeights = null;

            String subductionIntraSlabGmpeNames = null;
            String subductionIntraSlabGmpeWeights = null;

            // open file
            File file = new File(gmpeInputFile);
            FileInputStream oFIS = new FileInputStream(file.getPath());
            BufferedInputStream oBIS = new BufferedInputStream(oFIS);
            BufferedReader oReader =
                    new BufferedReader(new InputStreamReader(oBIS));

            if (D) {
                logger.debug("\n\n\nGMPE Logic Tree structure\n");
            }
            // if(D) System.out.println("\n\n");
            // if(D) System.out.println("GMPE Logic Tree structure");

            sRecord = oReader.readLine();
            // start reading the file
            while (sRecord != null) {

                // skip comments or empty lines
                while (sRecord.trim().startsWith(comment)
                        || sRecord.replaceAll(" ", "").isEmpty()) {
                    sRecord = oReader.readLine();
                    continue;
                }

                // if gmpes for Active shallow crust are defined
                if (sRecord.trim().equalsIgnoreCase(
                        TectonicRegionType.ACTIVE_SHALLOW.toString())) {

                    // read names
                    sRecord = oReader.readLine();
                    while (sRecord.trim().startsWith(comment)
                            || sRecord.replaceAll(" ", "").isEmpty()) {
                        sRecord = oReader.readLine();
                        continue;
                    }
                    activeShallowGmpeNames = sRecord.trim();

                    if (D) {
                        logger.debug("Gmpes for "
                                + TectonicRegionType.ACTIVE_SHALLOW + ": "
                                + activeShallowGmpeNames + "\n");
                    }
                    // if(D)
                    // System.out.println("Gmpes for "+TectonicRegionType.ACTIVE_SHALLOW+": "+activeShallowGmpeNames);

                    // read weights
                    sRecord = oReader.readLine();
                    while (sRecord.trim().startsWith(comment)
                            || sRecord.replaceAll(" ", "").isEmpty()) {
                        sRecord = oReader.readLine();
                        continue;
                    }
                    activeShallowGmpeWeights = sRecord.trim();

                    if (D) {
                        logger.debug("Gmpes weights: "
                                + activeShallowGmpeWeights + "\n");
                    }
                    // if(D)
                    // System.out.println("Gmpes weights: "+activeShallowGmpeWeights);
                }

                // if gmpes for stable continental crust are defined
                else if (sRecord.trim().equalsIgnoreCase(
                        TectonicRegionType.STABLE_SHALLOW.toString())) {

                    // read names
                    sRecord = oReader.readLine();
                    while (sRecord.trim().startsWith(comment)
                            || sRecord.replaceAll(" ", "").isEmpty()) {
                        sRecord = oReader.readLine();
                        continue;
                    }
                    stableShallowGmpeNames = sRecord.trim();

                    if (D) {
                        logger.debug("Gmpes for "
                                + TectonicRegionType.STABLE_SHALLOW + ": "
                                + stableShallowGmpeNames + "\n");
                    }
                    // if(D)
                    // System.out.println("Gmpes for "+TectonicRegionType.STABLE_SHALLOW+": "+stableShallowGmpeNames);

                    // read weights
                    sRecord = oReader.readLine();
                    while (sRecord.trim().startsWith(comment)
                            || sRecord.replaceAll(" ", "").isEmpty()) {
                        sRecord = oReader.readLine();
                        continue;
                    }
                    stableShallowGmpeWeights = sRecord.trim();

                    if (D) {
                        logger.debug("Gmpes weights: "
                                + stableShallowGmpeWeights + "\n");
                    }
                    // if(D)
                    // System.out.println("Gmpes weights: "+stableShallowGmpeWeights);
                }

                // if gmpes for subduction interface are defined
                else if (sRecord.trim().equalsIgnoreCase(
                        TectonicRegionType.SUBDUCTION_INTERFACE.toString())) {

                    // read names
                    sRecord = oReader.readLine();
                    while (sRecord.trim().startsWith(comment)
                            || sRecord.replaceAll(" ", "").isEmpty()) {
                        sRecord = oReader.readLine();
                        continue;
                    }
                    subductionInterfaceGmpeNames = sRecord.trim();

                    if (D) {
                        logger.debug("Gmpes for "
                                + TectonicRegionType.SUBDUCTION_INTERFACE
                                + ": " + subductionInterfaceGmpeNames + "\n");
                    }
                    // if(D)
                    // System.out.println("Gmpes for "+TectonicRegionType.SUBDUCTION_INTERFACE+": "+subductionInterfaceGmpeNames);

                    // read weights
                    sRecord = oReader.readLine();
                    while (sRecord.trim().startsWith(comment)
                            || sRecord.replaceAll(" ", "").isEmpty()) {
                        sRecord = oReader.readLine();
                        continue;
                    }
                    subductionInterfaceGmpeWeights = sRecord.trim();

                    if (D) {
                        logger.debug("Gmpes weights: "
                                + subductionInterfaceGmpeWeights);
                    }
                    // if(D)
                    // System.out.println("Gmpes weights: "+subductionInterfaceGmpeWeights);
                }

                // if gmpes for subduction intraslab are defined
                else if (sRecord.trim().equalsIgnoreCase(
                        TectonicRegionType.SUBDUCTION_SLAB.toString())) {

                    // read names
                    sRecord = oReader.readLine();
                    while (sRecord.trim().startsWith(comment)
                            || sRecord.replaceAll(" ", "").isEmpty()) {
                        sRecord = oReader.readLine();
                        continue;
                    }
                    subductionIntraSlabGmpeNames = sRecord.trim();

                    if (D) {
                        logger.debug("Gmpes for "
                                + TectonicRegionType.SUBDUCTION_SLAB + ": "
                                + subductionIntraSlabGmpeNames);
                    }
                    // if(D)
                    // System.out.println("Gmpes for "+TectonicRegionType.SUBDUCTION_SLAB+": "+subductionIntraSlabGmpeNames);

                    // read weights
                    sRecord = oReader.readLine();
                    while (sRecord.trim().startsWith(comment)
                            || sRecord.replaceAll(" ", "").isEmpty()) {
                        sRecord = oReader.readLine();
                        continue;
                    }
                    subductionIntraSlabGmpeWeights = sRecord.trim();

                    if (D) {
                        logger.debug("Gmpes weights: "
                                + subductionIntraSlabGmpeWeights);
                    }
                    // if(D)
                    // System.out.println("Gmpes weights: "+subductionIntraSlabGmpeWeights);

                }

                // continue reading until next keyword is found or end of file
                // skip comments or empty lines
                while ((sRecord = oReader.readLine()) != null) {
                    if (sRecord.trim().startsWith(comment)
                            || sRecord.replaceAll(" ", "").isEmpty())
                        continue;
                    else if (sRecord.trim().equalsIgnoreCase(
                            TectonicRegionType.ACTIVE_SHALLOW.toString())
                            || sRecord.trim().equalsIgnoreCase(
                                    TectonicRegionType.STABLE_SHALLOW
                                            .toString())
                            || sRecord.trim().equalsIgnoreCase(
                                    TectonicRegionType.SUBDUCTION_INTERFACE
                                            .toString())
                            || sRecord.trim().equalsIgnoreCase(
                                    TectonicRegionType.SUBDUCTION_SLAB
                                            .toString()))
                        break;
                }

            }// end if sRecord!=null

            // create logic tree structure for gmpe in active shallow region
            if (activeShallowGmpeNames != null) {
                // add logic tree to logic tree list
                gmpeLogicTreeHashMap.put(
                        TectonicRegionType.ACTIVE_SHALLOW,
                        createGmpeLogicTree(activeShallowGmpeNames,
                                activeShallowGmpeWeights, component,
                                intensityMeasureType, period, damping,
                                truncType, truncLevel, stdType, vs30));
            } // end active shallow

            // create logic tree structure for gmpe in stable shallow region
            if (stableShallowGmpeNames != null) {
                // add logic tree to logic tree list
                gmpeLogicTreeHashMap.put(
                        TectonicRegionType.STABLE_SHALLOW,
                        createGmpeLogicTree(stableShallowGmpeNames,
                                stableShallowGmpeWeights, component,
                                intensityMeasureType, period, damping,
                                truncType, truncLevel, stdType, vs30));
            } // end stable shallow

            // create logic tree structure for gmpe in subduction interface
            if (subductionInterfaceGmpeNames != null) {
                // add logic tree to logic tree list
                gmpeLogicTreeHashMap.put(
                        TectonicRegionType.SUBDUCTION_INTERFACE,
                        createGmpeLogicTree(subductionInterfaceGmpeNames,
                                subductionInterfaceGmpeWeights, component,
                                intensityMeasureType, period, damping,
                                truncType, truncLevel, stdType, vs30));
            }

            // create logic tree structure for gmpe in subduction intraslab
            if (subductionIntraSlabGmpeNames != null) {
                // add logic tree to logic tree list
                gmpeLogicTreeHashMap.put(
                        TectonicRegionType.SUBDUCTION_SLAB,
                        createGmpeLogicTree(subductionIntraSlabGmpeNames,
                                subductionIntraSlabGmpeWeights, component,
                                intensityMeasureType, period, damping,
                                truncType, truncLevel, stdType, vs30));
            }
        } catch (IOException e) {
            String msg = "ERF file not found. Program stops.";
            logger.error(msg);
            throw new IllegalArgumentException(msg, e);
        } // catch
    } // constructor

    /**
     * create logic tree from string of names and string of weights
     */
    private GemLogicTree<ScalarIntensityMeasureRelationshipAPI>
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
            // System.out.println("Number of gmpes do not corresponds to number of weights!");
            // System.out.println("Check your input!");
            // System.out.println("Execution stopped!");
            throw new IllegalArgumentException(msg);
        }

        // create logic tree
        GemLogicTree<ScalarIntensityMeasureRelationshipAPI> gmpeLogicTree =
                new GemLogicTree<ScalarIntensityMeasureRelationshipAPI>();

        // create branching level
        GemLogicTreeBranchingLevel branchingLevel =
                new GemLogicTreeBranchingLevel(1, "Gmpe Uncertainties", -1);

        // define branch
        GemLogicTreeBranch branch = null;

        // number of branches
        int numBranch = name.countTokens();

        // loop over branches
        for (int i = 0; i < numBranch; i++) {

            // gmpe name
            String gmpeName = name.nextToken();

            // gmpe weight
            double gmpeWeight = Double.parseDouble(weight.nextToken());

            branch = new GemLogicTreeBranch((i + 1), gmpeName, gmpeWeight);

            branchingLevel.addBranch(branch);

        }

        // add branching level to logic tree
        gmpeLogicTree.addBranchingLevel(branchingLevel);

        // create hashtable with gmpe
        Hashtable<String, ScalarIntensityMeasureRelationshipAPI> gmpeHashTable =
                new Hashtable<String, ScalarIntensityMeasureRelationshipAPI>();
        // loop over branches
        for (int i = 0; i < numBranch; i++) {

            // gmpe name
            String gmpeName =
                    gmpeLogicTree.getBranchingLevel(0).getBranch(i)
                            .getBranchingValue();

            // get the Gmpe Class
            Class cl = null;
            try {
                cl = Class.forName(packageName + gmpeName);
            } catch (ClassNotFoundException e) {
                String msg =
                        "Program stops!\nGMPE class not not found: \'"
                                + packageName + gmpeName;
                logger.info(msg);
                throw new IllegalArgumentException(msg, e);
            }

            // get the constructor
            Constructor cstr = null;
            try {
                cstr =
                        cl.getConstructor(new Class[] { ParameterChangeWarningListener.class });
            } catch (NoSuchMethodException e) {
                // Should never happen. If yes:
                String msg =
                        "Strange error: Method in GMPE class not found."
                                + " Program stops.";
                logger.fatal(msg);
                throw new IllegalArgumentException(msg, e);
            }

            // create an instance of the class
            AttenuationRelationship ar = null;
            try {
                ar =
                        (AttenuationRelationship) cstr
                                .newInstance(ParameterChangeWarningListener(event));
            } catch (IllegalAccessException e) {
                // Should never happen. If yes:
                String msg = "Strange error. Program stops.";
                logger.fatal(msg);
                throw new IllegalArgumentException(msg, e);
            } catch (InstantiationException e) {
                String msg =
                        "Correct this or report this error to the "
                                + "OpenGEM group. Program stops.";
                logger.fatal(msg);
                throw new IllegalArgumentException(msg, e);
            } catch (InvocationTargetException e) {
                String msg =
                        "Correct this or report this error to the "
                                + "OpenGEM group. Program stops.";
                logger.fatal(msg);
                throw new IllegalArgumentException(msg, e);
            } catch (IllegalArgumentException e) {
                String msg =
                        "Correct this or report this error to the "
                                + "OpenGEM group. Program stops.";
                logger.fatal(msg);
                throw new IllegalArgumentException(msg, e);
            }

            // set defaults parameters
            ar.setParamDefaults();

            // set component
            // first check if the chosen component is allowed
            if (ar.getParameter(ComponentParam.NAME).isAllowed(component)) {
                ar.getParameter(ComponentParam.NAME).setValue(component);
            } else {
                String msg =
                        "The chosen component: "
                                + component
                                + " is not supported by "
                                + gmpeName
                                + "\n"
                                + "The supported components are the following:\n"
                                + ar.getParameter(ComponentParam.NAME)
                                        .getConstraint() + "\n"
                                + "Check your input file!\n"
                                + "Execution stopped.";
                logger.error(msg);
                throw new IllegalArgumentException(msg);
            }

            // set intensity measure type
            if (ar.getSupportedIntensityMeasuresList().containsParameter(
                    intensityMeasureType)) {
                ar.setIntensityMeasure(intensityMeasureType);
            } else {
                String msg =
                        "The chosen intensity measure type: "
                                + intensityMeasureType
                                + " is not supported by "
                                + gmpeName
                                + "\n"
                                + "The supported types are the following:\n"
                                + ar.getSupportedIntensityMeasuresList()
                                        .toString() + "\n"
                                + "Check your input file!\n"
                                + "Execution stopped.";
                logger.error(msg);
                // System.out.println("The chosen intensity measure type: "+intensityMeasureType+" is not supported by "+gmpeName);
                // System.out.println("The supported types are the following: ");
                // System.out.println(ar.getSupportedIntensityMeasuresList().toString());
                // System.out.println("Check your input file!");
                // System.out.println("Execution stopped.");
                throw new IllegalArgumentException(msg);
            }

            // if SA set period and damping
            if (intensityMeasureType.equalsIgnoreCase(SA_Param.NAME)) {

                // period
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

                // damping
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

            // set gmpe truncation type
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
                                + "Check your input file\n"
                                + "Execution stopped.";
                logger.error(msg);
                throw new IllegalArgumentException(msg);
            }

            // set gmpe truncation level
            if (ar.getParameter(SigmaTruncLevelParam.NAME)
                    .isAllowed(truncLevel)) {
                ar.getParameter(SigmaTruncLevelParam.NAME).setValue(truncLevel);
            } else {
                String msg =
                        "The chosen truncation level: "
                                + truncLevel
                                + " is not supported.\n"
                                + "The allowed values are the following: \n"
                                + ar.getParameter(SigmaTruncLevelParam.NAME)
                                        .getConstraint() + "\n"
                                + "Check your input file\n"
                                + "Execution stopped.";
                logger.error(msg);
                throw new IllegalArgumentException(msg);
            }

            // set standard deviation type
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
                                + "Check your input file\n"
                                + "Execution stopped.";
                logger.error(msg);
                new IllegalArgumentException(msg);
            }

            // set vs30 value
            if (ar.getParameter(Vs30_Param.NAME).isAllowed(vs30)) {
                ar.getParameter(Vs30_Param.NAME).setValue(vs30);
            } else {
                String msg =
                        "The chosen vs30 value: "
                                + vs30
                                + " is not valid\n"
                                + "The allowed values are the following: \n"
                                + ar.getParameter(Vs30_Param.NAME)
                                        .getConstraint() + "\n"
                                + "Check your input file\n"
                                + "Execution stopped.";
                logger.error(msg);
                throw new IllegalArgumentException(msg);
            }

            // set end-branch mapping
            gmpeLogicTree.getEBMap().put(
                    Integer.toString(gmpeLogicTree.getBranchingLevel(0)
                            .getBranch(i).getRelativeID()), ar);
        }

        return gmpeLogicTree;
    }

    private static ParameterChangeWarningListener
            ParameterChangeWarningListener(ParameterChangeWarningEvent event) {
        return null;
    }

    public
            HashMap<TectonicRegionType, GemLogicTree<ScalarIntensityMeasureRelationshipAPI>>
            getGmpeLogicTreeHashMap() {
        return this.gmpeLogicTreeHashMap;
    }

}
