package org.opensha.gem.GEM1.calc.gemCommandLineCalculator;

import java.io.BufferedInputStream;
import java.io.BufferedReader;
import java.io.File;
import java.io.FileInputStream;
import java.io.IOException;
import java.io.InputStreamReader;
import java.util.ArrayList;
import java.util.StringTokenizer;

import org.apache.commons.logging.Log;
import org.apache.commons.logging.LogFactory;
import org.opensha.gem.GEM1.calc.gemLogicTree.GemLogicTree;
import org.opensha.gem.GEM1.calc.gemLogicTree.GemLogicTreeBranch;
import org.opensha.gem.GEM1.calc.gemLogicTree.GemLogicTreeBranchingLevel;
import org.opensha.gem.GEM1.calc.gemLogicTree.GemLogicTreeRule;
import org.opensha.gem.GEM1.calc.gemLogicTree.GemLogicTreeRuleParam;
import org.opensha.sha.earthquake.rupForecastImpl.GEM1.SourceData.GEMSourceData;

/**
 * This class instantiate the GEMLogicTree for the ERF
 * 
 * @author damianomonelli
 * 
 */
public class ErfLogicTreeData {
    //
    // Apache commons logging, not log4j specifically
    // declaring the logger static here is more efficient as one Log object is
    // created per class
    // (This is not safe for a class which may be deployed via a "shared"
    // classloader in a servlet or j2ee container or similar environment.
    private static Log logger = LogFactory.getLog(ErfLogicTreeData.class);

    // ERF logic tree
    private GemLogicTree<ArrayList<GEMSourceData>> erfLogicTree;

    // comment line identifier
    private static String comment = "#";

    // keyword
    private static String BRANCHING_LEVEL = "BranchingLevel";
    private static String BRANCH_SET = "BranchSet";

    // for debugging
    // TODO:
    // Refactor this all over OpenSha: Connect this debug flag to the debug
    // level of the logger.
    // -> D = logger.isDebugEnabled()
    // Then, to avoid the calculation time to construct unnecessary debug
    // messages, construct it only after the check of the flag D:
    // if(D) {
    // logger.debug("Entry number: " + i + " is " + String.valueOf(entry[i]));
    // }
    private static Boolean D = false;

    /**
     * Constructor taking as input the file describing the ERF logic tree
     * 
     * @param erfInputFile
     * @throws IOException
     */
    public ErfLogicTreeData(String erfInputFile) {
        D = logger.isDebugEnabled();
        try {
            // instantiate logic tree
            erfLogicTree = new GemLogicTree<ArrayList<GEMSourceData>>();

            // define branching level
            GemLogicTreeBranchingLevel branchingLevel = null;
            // define branch
            GemLogicTreeBranch branch = null;

            String sRecord = null;

            // open file
            File file = new File(erfInputFile);
            FileInputStream oFIS = new FileInputStream(file.getPath());
            BufferedInputStream oBIS = new BufferedInputStream(oFIS);
            BufferedReader oReader =
                    new BufferedReader(new InputStreamReader(oBIS));

            sRecord = oReader.readLine();
            // start reading the file
            while (sRecord != null) {

                // skip comments or empty lines
                while (sRecord.trim().startsWith(comment)
                        || sRecord.replaceAll(" ", "").isEmpty()) {
                    sRecord = oReader.readLine();
                    continue;
                }

                // if the keyword BranchingLevel is found
                // define branching level
                if (sRecord.trim().equalsIgnoreCase("BranchingLevel")) {

                    // read branching level number
                    sRecord = oReader.readLine();
                    while (sRecord.trim().startsWith(comment)
                            || sRecord.replaceAll(" ", "").isEmpty()) {
                        sRecord = oReader.readLine();
                        continue;
                    }
                    int branchingLevelNumber = Integer.parseInt(sRecord.trim());

                    // read branching label
                    sRecord = oReader.readLine();
                    while (sRecord.trim().startsWith(comment)
                            || sRecord.replaceAll(" ", "").isEmpty()) {
                        sRecord = oReader.readLine();
                        continue;
                    }
                    String branchingLabel = sRecord.trim();

                    // read applies to
                    sRecord = oReader.readLine();
                    while (sRecord.trim().startsWith(comment)
                            || sRecord.replaceAll(" ", "").isEmpty()) {
                        sRecord = oReader.readLine();
                        continue;
                    }
                    String appliesTo = sRecord.trim();
                    if (D) {
                        logger.debug("\n\n"
                                + "//----------------------------------------------------------------------------------------//\n"
                                + "Branching level: " + branchingLevelNumber
                                + ", label: " + branchingLabel
                                + ", applies to: " + appliesTo + "\n");
                    }
                    // if(D) System.out.println("\n\n");
                    // if(D)
                    // System.out.println("//----------------------------------------------------------------------------------------//");
                    // if(D)
                    // System.out.println("Branching level: "+branchingLevelNumber+", label: "+branchingLabel+", applies to: "+appliesTo);

                    // instantiate branching level
                    if (appliesTo.equalsIgnoreCase("ALL")) {
                        // I assume 0 meaning apply to all previous branches
                        branchingLevel =
                                new GemLogicTreeBranchingLevel(
                                        branchingLevelNumber, branchingLabel, 0);
                    } else if (appliesTo.equalsIgnoreCase("NONE")) {
                        // I assume -1 meaning do not apply to anything
                        branchingLevel =
                                new GemLogicTreeBranchingLevel(
                                        branchingLevelNumber, branchingLabel,
                                        -1);
                    } else {
                        logger.info("At the moment a branching level can be applied to NONE or ALL. No other options are available!\n"
                                + "Execution stopped!\n");
                        // System.out.println("At the moment a branching level can be applied to NONE or ALL. No other options are available!");
                        // System.out.println("Execution stopped!");
                        System.exit(0);
                    }

                } // end if BranchLevel

                // if keyword BranchSet is found
                // define branches to be added to the
                // previously created branching level
                if (sRecord.trim().equalsIgnoreCase("BranchSet")) {

                    // read branch uncertainty model
                    sRecord = oReader.readLine();
                    while (sRecord.trim().startsWith(comment)
                            || sRecord.replaceAll(" ", "").isEmpty()) {
                        sRecord = oReader.readLine();
                        continue;
                    }
                    String branchModel = sRecord.trim();

                    if (branchModel.equalsIgnoreCase("inputfile")) {

                        // read input file names
                        sRecord = oReader.readLine();
                        while (sRecord.trim().startsWith(comment)
                                || sRecord.replaceAll(" ", "").isEmpty()) {
                            sRecord = oReader.readLine();
                            continue;
                        }
                        String fileNames = sRecord;
                        StringTokenizer fileNameToken =
                                new StringTokenizer(fileNames);

                        // read labels
                        sRecord = oReader.readLine();
                        while (sRecord.trim().startsWith(comment)
                                || sRecord.replaceAll(" ", "").isEmpty()) {
                            sRecord = oReader.readLine();
                            continue;
                        }
                        String fileLabels = sRecord;
                        StringTokenizer fileLabelsToken =
                                new StringTokenizer(fileLabels);

                        // read weights
                        sRecord = oReader.readLine();
                        while (sRecord.trim().startsWith(comment)
                                || sRecord.replaceAll(" ", "").isEmpty()) {
                            sRecord = oReader.readLine();
                            continue;
                        }
                        String fileWeights = sRecord;
                        StringTokenizer fileWeightsToken =
                                new StringTokenizer(fileWeights);

                        if (D) {
                            logger.debug("BranchSet. Definition through: "
                                    + branchModel + "\n" + "Input files: "
                                    + fileNames + "\n" + "Input files labels: "
                                    + fileLabels + "\n" + "File weights: "
                                    + fileWeights + "\n");
                        }
                        // if(D)
                        // System.out.println("BranchSet. Definition through: "+branchModel);
                        // if(D) System.out.println("Input files: "+fileNames);
                        // if(D)
                        // System.out.println("Input files labels: "+fileLabels);
                        // if(D)
                        // System.out.println("File weights: "+fileWeights);
                        // instantiate branches
                        // number of branches
                        int numBra = fileNameToken.countTokens();
                        for (int i = 0; i < numBra; i++) {
                            // define branch
                            branch =
                                    new GemLogicTreeBranch((i + 1),
                                            fileLabelsToken.nextToken(),
                                            Double.parseDouble(fileWeightsToken
                                                    .nextToken()));
                            // set input file name
                            branch.setNameInputFile(fileNameToken.nextToken());
                            // add to branching level
                            branchingLevel.addBranch(branch);
                        }

                        // add the previously created branching level to the
                        // logic tree
                        erfLogicTree.addBranchingLevel(branchingLevel);

                    } // end if inputfile
                    else if (branchModel.equalsIgnoreCase("rule")) {

                        // read rule name
                        sRecord = oReader.readLine();
                        while (sRecord.trim().startsWith(comment)
                                || sRecord.replaceAll(" ", "").isEmpty()) {
                            sRecord = oReader.readLine();
                            continue;
                        }
                        String ruleName = sRecord.trim();

                        // read uncertainty values
                        sRecord = oReader.readLine();
                        while (sRecord.trim().startsWith(comment)
                                || sRecord.replaceAll(" ", "").isEmpty()) {
                            sRecord = oReader.readLine();
                            continue;
                        }
                        String uncertaintyValues = sRecord;
                        StringTokenizer uncertaintyValuesToken =
                                new StringTokenizer(uncertaintyValues);

                        // read uncertainty weights
                        sRecord = oReader.readLine();
                        while (sRecord.trim().startsWith(comment)
                                || sRecord.replaceAll(" ", "").isEmpty()) {
                            sRecord = oReader.readLine();
                            continue;
                        }
                        String uncertaintyWeights = sRecord;
                        StringTokenizer uncertaintyWeightsToken =
                                new StringTokenizer(uncertaintyWeights);

                        if (D) {
                            System.out
                                    .println("BranchSet. Definition through: "
                                            + branchModel + "\n" + "Rule: "
                                            + ruleName + "\n"
                                            + "Uncertainty values: "
                                            + uncertaintyValues + "\n"
                                            + "Uncertainty weights: "
                                            + uncertaintyWeights + "\n");
                        }
                        // if(D)
                        // System.out.println("BranchSet. Definition through: "+branchModel);
                        // if(D) System.out.println("Rule: "+ruleName);
                        // if(D)
                        // System.out.println("Uncertainty values: "+uncertaintyValues);
                        // if(D)
                        // System.out.println("Uncertainty weights: "+uncertaintyWeights);

                        // instantiate branches
                        // number of branches
                        int numBra = uncertaintyValuesToken.countTokens();
                        for (int i = 0; i < numBra; i++) {

                            // uncertainty value
                            double uncertVal =
                                    Double.parseDouble(uncertaintyValuesToken
                                            .nextToken());

                            // weight
                            double uncertWeight =
                                    Double.parseDouble(uncertaintyWeightsToken
                                            .nextToken());

                            // define branch
                            branch =
                                    new GemLogicTreeBranch((i + 1), ruleName,
                                            uncertWeight);
                            // set input file name
                            branch.setRule(new GemLogicTreeRule(
                                    GemLogicTreeRuleParam
                                            .getTypeForName(ruleName),
                                    uncertVal));
                            // add to branching level
                            branchingLevel.addBranch(branch);
                        }

                        // add the previously created branching level to the
                        // logic tree
                        erfLogicTree.addBranchingLevel(branchingLevel);

                    }// end if rule

                } // end if BranchSet

                // continue reading until next keyword is found or end of file
                // skip comments or empty lines
                while ((sRecord = oReader.readLine()) != null) {
                    if (sRecord.trim().startsWith(comment)
                            || sRecord.replaceAll(" ", "").isEmpty())
                        continue;
                    else if (sRecord.trim().equalsIgnoreCase(BRANCHING_LEVEL)
                            || sRecord.trim().equalsIgnoreCase(BRANCH_SET))
                        break;
                }

            } // end sRecord is null
        } catch (IOException e) {
            IOException ioe =
                    new IOException("ERF file not found. Program stops.", e);
            e.printStackTrace();
            System.exit(-1);
        } // catch
    } // constructor

    public GemLogicTree<ArrayList<GEMSourceData>> getErfLogicTree() {
        return erfLogicTree;
    }

} // class ErfLogicTreeData
