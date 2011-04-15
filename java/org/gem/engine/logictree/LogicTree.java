package org.gem.engine.logictree;

import java.io.File;
import java.io.FileInputStream;
import java.io.FileNotFoundException;
import java.io.ObjectInputStream;
import java.io.Serializable;
import java.net.URL;
import java.util.ArrayList;
import java.util.HashMap;
import java.util.Iterator;
import java.util.List;
import java.util.Map;
import java.util.Random;

import org.apache.commons.logging.Log;
import org.apache.commons.logging.LogFactory;
import org.gem.engine.LogicTreeProcessor;
import org.gem.engine.hazard.GemComputeHazardLogicTree;

/**
 * Class for logic tree definition.
 * <p>
 * A logic tree is defined in terms of a list of {@link LogicTreeBranchingLevel} objects (each containing one or more
 * {@link LogicTreeBranch} objects (each defining an uncertainty model)) plus a map storing end-branch models
 * (HashMap<String, Element>). A name can be also provided.
 */
public class LogicTree<Element> implements Iterable<Element>, Serializable
{

    private static final long serialVersionUID = -2656457282143245160L;
    private static final Log logger = LogFactory.getLog(LogicTreeProcessor.class);

    private String name;
    private Map<String, Element> ebMap;
    private final List<LogicTreeBranchingLevel> branchingLevels;

    public LogicTree()
    {
        this.name = "";
        this.ebMap = new HashMap<String, Element>();
        this.branchingLevels = new ArrayList<LogicTreeBranchingLevel>();
    }

    public LogicTree(String name)
    {
        this.name = name;
        this.ebMap = new HashMap<String, Element>();
        this.branchingLevels = new ArrayList<LogicTreeBranchingLevel>();
    }

    @SuppressWarnings("unchecked")
    public static LogicTree fromFile(String fileName)
    {
        URL data = GemComputeHazardLogicTree.class.getResource(fileName);

        FileInputStream inputStream = null;
        File file = new File(data.getFile());

        try
        {
            inputStream = new FileInputStream(file.getPath());
        }
        catch (FileNotFoundException e)
        {
            String msg = file.getPath() + " not found!!";

            logger.error(msg);
            throw new RuntimeException(msg);
        }

        ObjectInputStream objectInputStream;

        try
        {
            objectInputStream = new ObjectInputStream(inputStream);
            Object obj = objectInputStream.readObject();

            return (LogicTree) obj;
        }
        catch (Exception e)
        {
            throw new RuntimeException(e);
        }
    }

    public void appendBranchingLevel(LogicTreeBranchingLevel branchingLevel)
    {
        this.branchingLevels.add(branchingLevel);
    }

    public void addEBMapping(String label, Element obj)
    {
        this.ebMap.put(label, obj);
    }

    public List<LogicTreeBranchingLevel> getBranchingLevels()
    {
        return this.branchingLevels;
    }

    public LogicTreeBranchingLevel getBranchingLevelAt(int index)
    {
        return this.branchingLevels.get(index);
    }

    public String getModelName()
    {
        return this.name;
    }

    /**
     * Returns weight for end-branch model specified by string lab.
     */
    public double getWeight(String lab)
    {
        String[] strarr = lab.split("_");
        LogicTreeBranchingLevel brl = this.branchingLevels.get(strarr.length - 1);
        return brl.getBranch(Integer.valueOf(strarr[strarr.length - 1]).intValue()).getWeight();
    }

    /**
     * Returns total weight (product of weights) for end-branch model specified by string lab.
     */
    public double getTotWeight(String lab)
    {
        double weight = 1.0;
        String[] strarr = lab.split("_");

        for (int i = 0; i < strarr.length; i++)
        {
            LogicTreeBranchingLevel brl = this.branchingLevels.get(i);
            LogicTreeBranch br = brl.getBranch(Integer.valueOf(strarr[i]).intValue() - 1);
            weight = weight * br.getWeight();
        }

        return weight;
    }

    /**
     * Returns the end-branch models map.
     */
    public Map<String, Element> getEBMap()
    {
        return ebMap;
    }

    /**
     * Iterator over the end-branch models.
     */
    @Override
    public Iterator<Element> iterator()
    {
        return ebMap.values().iterator();
    }

    @Override
    public String toString()
    {
        StringBuilder asString = new StringBuilder();

        asString.append("Logic tree name: " + this.name + "\n");
        asString.append("Total number of branching levels in the logic tree: " + this.branchingLevels.size() + "\n");

        for (int i = 0; i < this.branchingLevels.size(); i++)
        {
            LogicTreeBranchingLevel branchingLevel = getBranchingLevelAt(i);

            asString.append("> Branching level: " + branchingLevel.getLevel());
            asString.append(", label: " + branchingLevel.getBranchingLabel());
            asString.append(", appliesTo: " + branchingLevel.getAppliesTo() + "\n");

            int numBranches = branchingLevel.getBranchList().size();

            // TODO: We should call toString() on the logicTreeBranch
            for (int j = 0; j < numBranches; j++)
            {
                LogicTreeBranch branch = branchingLevel.getBranch(j);

                asString.append(">> Branch number: " + branch.getRelativeID());
                asString.append(", label: " + branch.getBranchingValue());
                asString.append(", weight: " + branch.getWeight() + "\n");

                asString.append(">>> Associated file: " + branch.getNameInputFile() + "\n");
                asString.append(">>> Associated rule: " + branch.getRule().getRuleName() + "\n");
                asString.append(">>> Associated uncertainty value: " + branch.getRule().getVal() + "\n");
            }
        }

        return asString.toString();
    }

    /**
     * This method samples a branching level and return the index of a branch.
     * <p>
     * The sampling is done using the inverse transform method. (For the algorithm description see
     * "Computational Statistics Handbook with Matlab", Martinez & Martinez, Champman & all, pag.83).
     */
    public int sampleBranchingLevel(int branchingLevelIndex, Random rn)
    {

        int sample = -Integer.MIN_VALUE;

        // get the corresponding branching level
        LogicTreeBranchingLevel bl = this.branchingLevels.get(branchingLevelIndex);

        // x values
        int[] x = new int[bl.getBranchList().size()];
        // p (probability values)

        double[] p = new double[bl.getBranchList().size()];

        // loop over branches
        int i = 0;

        for (LogicTreeBranch b : bl.getBranchList())
        {
            x[i] = b.getRelativeID();
            p[i] = b.getWeight();

            logger.debug("label, prob: " + x[i] + " " + p[i]);

            i = i + 1;
        }

        // compute cumulative distribution
        double[] cdf = new double[p.length];

        // initialize to zero
        for (i = 0; i < cdf.length; i++)
        {
            cdf[i] = 0.0;
        }

        for (i = 0; i < cdf.length; i++)
        {
            for (int j = 0; j <= i; j++)
            {
                cdf[i] = cdf[i] + p[j];
            }
        }

        logger.debug("Cumulative distribution:");

        for (i = 0; i < cdf.length; i++)
        {
            logger.debug(cdf[i]);
        }

        // generate uniform random number between 0 and 1
        double rand = rn.nextDouble();

        logger.debug("Random number: " + rand);

        // loop over probabilities
        for (int j = 0; j < p.length; j++)
        {
            if (rand <= cdf[j])
            {
                sample = x[j];
                break;
            }
        }

        return sample;
    }

    @Override
    @SuppressWarnings("unchecked")
    public boolean equals(Object obj)
    {
        if (!(obj instanceof LogicTree))
        {
            return false;
        }

        LogicTree other = (LogicTree) obj;
        return branchingLevels.equals(other.branchingLevels);
    }

}
