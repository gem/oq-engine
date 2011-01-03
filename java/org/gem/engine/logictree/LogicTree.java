package org.gem.engine.logictree;

import java.io.File;
import java.io.FileInputStream;
import java.io.FileNotFoundException;
import java.io.FileOutputStream;
import java.io.IOException;
import java.io.ObjectInputStream;
import java.io.ObjectOutputStream;
import java.io.Serializable;
import java.net.URL;
import java.util.ArrayList;
import java.util.HashMap;
import java.util.Iterator;
import java.util.Random;

import org.apache.commons.logging.Log;
import org.apache.commons.logging.LogFactory;
import org.gem.engine.CommandLineCalculator;
import org.gem.engine.hazard.GemComputeHazardLogicTree;

/**
 * Class for logic tree definition. A logic tree is defined in terms of a list
 * of {@link LogicTreeBranchingLevel} objects (each containing one or more
 * {@link LogicTreeBranch} objects (each defining an uncertainty model)) plus a
 * map storing end-branch models (HashMap<String, Element>). A name can be also
 * provided.
 */
public class LogicTree<Element> implements LogicTreeAPI<Element>, Serializable {

    private static Log logger = LogFactory.getLog(CommandLineCalculator.class);

    private final ArrayList<LogicTreeBranchingLevel> branLevLst;
    protected HashMap<String, Element> ebMap;
    private String modelName;

    /**
     * Creates and empty logic tree
     */
    public LogicTree() {
        this.branLevLst = new ArrayList<LogicTreeBranchingLevel>();
        this.ebMap = new HashMap<String, Element>();
        this.modelName = "";
    }

    /**
     * Creates logic tree from file
     */
    public LogicTree(String fileName) throws IOException,
            ClassNotFoundException {

        URL data = GemComputeHazardLogicTree.class.getResource(fileName);
        File file = new File(data.getFile());
        FileInputStream f_in = null;
        try {
            // f_in = new FileInputStream(fileName);
            f_in = new FileInputStream(file.getPath());
        } catch (FileNotFoundException e) {
            String msg = file.getPath() + " not found!!";
            logger.info(msg);
            throw new RuntimeException(msg);
        }

        // Read object using ObjectInputStream.
        ObjectInputStream obj_in = new ObjectInputStream(f_in);

        // Read an object.
        Object obj = obj_in.readObject();

        LogicTree<Element> gemLogicTree = (LogicTree<Element>) obj;

        this.branLevLst = gemLogicTree.getBranchingLevelsList();
        this.ebMap = gemLogicTree.getEBMap();
        this.modelName = gemLogicTree.getModelName();

    }

    /**
     * Adds branching level
     */
    @Override
    public void addBranchingLevel(LogicTreeBranchingLevel branLev) {
        this.branLevLst.add(branLev);
    }

    /**
     * Adds end branch model
     */
    @Override
    public void addEBMapping(String str, Element obj) {
        this.ebMap.put(str, obj);
    }

    /**
     * Gets list of branching levels
     */
    @Override
    public ArrayList<LogicTreeBranchingLevel> getBranchingLevelsList() {
        return this.branLevLst;
    }

    /**
     * Gets branching level of index idx
     */
    @Override
    public LogicTreeBranchingLevel getBranchingLevel(int idx) {
        return this.branLevLst.get(idx);
    }

    /**
     * Sets logic tree name
     */
    @Override
    public void setModelName(String str) {
        this.modelName = str;
    }

    /**
     * Gets logic tree name
     */
    @Override
    public String getModelName() {
        return this.modelName;
    }

    /**
     * Gets weight for end-branch model specified by string lab
     */
    @Override
    public double getWeight(String lab) {
        String[] strarr = lab.split("_");
        LogicTreeBranchingLevel brl = this.branLevLst.get(strarr.length - 1);
        return brl.getBranch(
                Integer.valueOf(strarr[strarr.length - 1]).intValue())
                .getWeight();
    }

    /**
     * Gets total weight (product of weights) for end-branch model specified by
     * string lab
     */
    @Override
    public double getTotWeight(String lab) {
        double weight = 1.0;
        String[] strarr = lab.split("_");
        for (int i = 0; i < strarr.length; i++) {
            LogicTreeBranchingLevel brl = this.branLevLst.get(i);
            LogicTreeBranch br =
                    brl.getBranch(Integer.valueOf(strarr[i]).intValue() - 1);
            weight = weight * br.getWeight();
        }
        return weight;
    }

    /**
     * Returns end-branch models map
     */
    @Override
    public HashMap<String, Element> getEBMap() {
        return ebMap;
    }

    /**
     * Iterator over end-branch models
     */
    @Override
    public Iterator<Element> iterator() {
        return ebMap.values().iterator();
    }

    /**
     * Serialize Logic Tree to file
     */
    @Override
    public void saveGemLogicTreeModel(String fileName) throws Exception {

        // Use a FileOutputStream to send data to a file
        FileOutputStream f_out = new FileOutputStream(fileName);

        // Use an ObjectOutputStream to send object data to the
        // FileOutputStream for writing to disk.
        ObjectOutputStream obj_out = new ObjectOutputStream(f_out);

        // Pass our object to the ObjectOutputStream's
        // writeObject() method to cause it to be written out
        // to disk.
        obj_out.writeObject(this);
    }

    /**
     * print logic tree structure on standard output
     * 
     */
    public void printGemLogicTreeStructure() {

        // total number of branching levels
        int numBranchingLevels = this.branLevLst.size();

        logger.info("Total number of branching levels in the logic tree: "
                + numBranchingLevels + "\n");
        // loop over branching levels
        for (int i = 0; i < numBranchingLevels; i++) {

            LogicTreeBranchingLevel braLev = this.branLevLst.get(i);
            logger.info("Branching level: " + braLev.getLevel() + ", label: "
                    + braLev.getBranchingLabel() + ", appliesTo: "
                    + braLev.getAppliesTo());

            // number of branches
            int numBranches = braLev.getBranchList().size();
            // loop over branches
            for (int j = 0; j < numBranches; j++) {

                LogicTreeBranch bra = braLev.getBranch(j);

                logger.info("Branch number: " + bra.getRelativeID()
                        + ", label: " + bra.getBranchingValue() + ", weight: "
                        + bra.getWeight());
                if (bra.getNameInputFile() != null)
                    logger.info("Associated file: " + bra.getNameInputFile());
                if (bra.getRule() != null) {
                    logger.info("Associated rule: "
                            + bra.getRule().getRuleName());
                    logger.info("Associated uncertainty value: "
                            + bra.getRule().getVal());
                }

            }
            logger.info("\n\n");

        }
    }

    /**
     * This method samples a branching level and return the index of a branch.
     * The sampling is done using the inverse transform method. (For the
     * algorithm description see "Computational Statistics Handbook with
     * Matlab", Martinez & Martinez, Champman & all, pag.83)
     */
    @Override
    public int sampleBranchingLevel(int branchingLevelIndex, Random rn) {

        int sample = -Integer.MIN_VALUE;

        // get the corresponding branching level
        LogicTreeBranchingLevel bl = this.branLevLst.get(branchingLevelIndex);

        // x values
        int[] x = new int[bl.getBranchList().size()];
        // p (probability values)
        double[] p = new double[bl.getBranchList().size()];

        // loop over branches
        int i = 0;
        for (LogicTreeBranch b : bl.getBranchList()) {

            x[i] = b.getRelativeID();
            p[i] = b.getWeight();
            logger.debug("label, prob: " + x[i] + " " + p[i]);

            i = i + 1;

        }

        // compute cumulative distribution
        double[] cdf = new double[p.length];
        // initialize to zero
        for (i = 0; i < cdf.length; i++)
            cdf[i] = 0.0;
        for (i = 0; i < cdf.length; i++) {
            for (int j = 0; j <= i; j++)
                cdf[i] = cdf[i] + p[j];
        }
        logger.debug("Cumulative distribution:");
        for (i = 0; i < cdf.length; i++)
            logger.debug(cdf[i]);

        // generate uniform random number between 0 and 1
        double rand = rn.nextDouble();
        logger.debug("Random number: " + rand);

        // loop over probabilities
        for (int j = 0; j < p.length; j++) {

            if (rand <= cdf[j]) {
                sample = x[j];
                break;
            }

        }// end loop over probabilities

        return sample;
    }

    @Override
    public boolean equals(Object obj) {

        if (!(obj instanceof LogicTree)) {
            return false;
        }

        LogicTree other = (LogicTree) obj;

        return branLevLst.equals(other.branLevLst);
    }

}
