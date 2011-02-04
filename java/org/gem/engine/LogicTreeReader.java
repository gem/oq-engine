package org.gem.engine;

import java.io.BufferedInputStream;
import java.io.BufferedReader;
import java.io.ByteArrayInputStream;
import java.io.File;
import java.io.FileInputStream;
import java.io.InputStream;
import java.io.InputStreamReader;
import java.util.HashMap;
import java.util.Iterator;
import java.util.Map;

import org.dom4j.Document;
import org.dom4j.Element;
import org.dom4j.io.SAXReader;
import org.gem.engine.hazard.redis.Cache;
import org.gem.engine.logictree.LogicTree;
import org.gem.engine.logictree.LogicTreeBranch;
import org.gem.engine.logictree.LogicTreeBranchingLevel;
import org.gem.engine.logictree.LogicTreeRule;
import org.gem.engine.logictree.LogicTreeRuleParam;

/**
 * Class for reading logic tree data in a nrML format file.
 * 
 */
public class LogicTreeReader {

    private final BufferedReader bufferedReader;

    private final Map<String, LogicTree> logicTreeHashMap;

    private static final String BRANCHING_LEVEL = "branchingLevel";
    private static final String TECTONIC_REGION = "tectonicRegion";
    private static final String UNCERTAINTY_TYPE = "uncertaintyType";
    private static final String UNCERTAINTY_MODEL = "uncertaintyModel";
    private static final String UNCERTAINTY_WEIGHT = "uncertaintyWeight";
    private static final String SOURCE_MODEL = "sourceModel";
    private static final String MAX_MAGNITUDE_GUTENBERG_RICHTER_RELATIVE =
            "maxMagnitudeGutenbergRichterRelative";
    private static final String B_VALUE_GUTENBERG_RICHTER_RELATIVE =
            "bValueGutenbergRichterRelative";

    /**
     * Creates a new LogicTreeReader given the path of the file to read from.
     */
    public LogicTreeReader(String path) {
        File xml = new File(path);
        FileInputStream fileInputStream;
        try {
            fileInputStream = new FileInputStream(xml.getPath());
        } catch (Exception e) {
            throw new RuntimeException(e);
        }
        BufferedInputStream bufferedInputStream =
                new BufferedInputStream(fileInputStream);
        this.bufferedReader =
                new BufferedReader(new InputStreamReader(bufferedInputStream));
        logicTreeHashMap = new HashMap<String, LogicTree>();
    }

    /**
     * Creates a new LogicTreeReader given cache and key to read from
     */
    public LogicTreeReader(Cache cache, String key) {
        String source = (String) cache.get(key);
        byte[] bytevals = source.getBytes();
        InputStream byteis = new ByteArrayInputStream(bytevals);
        BufferedInputStream bufferedInputStream =
                new BufferedInputStream(byteis);
        this.bufferedReader =
                new BufferedReader(new InputStreamReader(bufferedInputStream));
        logicTreeHashMap = new HashMap<String, LogicTree>();
    }

    /**
     * Creates a new LogicTreeReader given BufferedReader to read from
     */
    public LogicTreeReader(BufferedReader bufferedReader) {
        this.bufferedReader = bufferedReader;
        logicTreeHashMap = new HashMap<String, LogicTree>();
    }

    /**
     * Reads file and returns logic tree data. The method loops over the
     * possible logic trees defined in the file. For each logic tree definition,
     * it creates a corresponding {@link LogicTree} object and stores it in a
     * map with a key that is the logic tree number or the tectonic region type
     * (if defined in the file).
     */
    public Map<String, LogicTree> read() {

        SAXReader reader = new SAXReader();
        Document doc = null;
        try {
            doc = reader.read(this.bufferedReader);
        } catch (Exception e) {
            throw new RuntimeException(e);
        }
        Element root = doc.getRootElement(); // <nrml> tag

        /**
         * Makes a loop over the possible logic trees defined in the file. In
         * case of the GMPE logic tree file, multiple logic trees are defined,
         * one for each tectonic region implied by the source model. For the
         * source model logic tree file, currently only one logic tree is
         * defined. For each logic tree definition, creates a logic tree object.
         * Depending on the uncertainty type, additional attributed of the
         * branch class must be edited. In case of source model uncertainties, a
         * source model file must be specified. In case of parameter
         * uncertainties, a logic tree rule must be defined.
         */
        int indexLogicTree = 1;
        Iterator i = root.elements().iterator();
        while (i.hasNext()) {
            Element logicTreeSetElem = (Element) i.next();

            Map<String, LogicTree> logicTrees =
                    parseLogicTreeSet(logicTreeSetElem, indexLogicTree);

            for (String key : logicTrees.keySet()) {
                logicTreeHashMap.put(key, logicTrees.get(key));
            }

            indexLogicTree++;
        }
        return logicTreeHashMap;
    }

    /**
     * Parse child elements of a &lt;logicTreeSet&gt; element.
     * 
     * @param logicTreeSet
     * @param indexLogicTree
     * @return Map of LogicTrees, keyed by tectonicRegion. If no tectonicRegion
     *         is defined for a logicTree, keys will be "1" through "N", where N
     *         is the total number of logicTree elements in the logicTreeSet.
     */
    private Map<String, LogicTree> parseLogicTreeSet(Element logicTreeSet,
            int indexLogicTree) {

        String key = Integer.toString(indexLogicTree);
        Map<String, LogicTree> logicTrees = new HashMap<String, LogicTree>();
        Iterator i = logicTreeSet.elementIterator();
        while (i.hasNext()) {
            Element elem = (Element) i.next();
            LogicTree logicTree = new LogicTree();

            // skip config for now
            // TODO(LB): we might care about the <config> elem later
            // at the time this was written, the example files did not
            // include any config items
            if (elem.getName().equals("config")) {
                continue;
            }

            String tectonicRegion = parseLogicTree(elem, logicTree);
            if (tectonicRegion != null) {
                key = tectonicRegion;
            }
            logicTrees.put(key, logicTree);
        }
        return logicTrees;
    }

    /**
     * Parse attributes and children of a &lt;logicTree&gt; element.
     * 
     * @param logicTreeElem
     * @param logicTree
     * @return tectonicRegion of the logic tree (or null if none is defined)
     */
    private String parseLogicTree(Element logicTreeElem, LogicTree logicTree) {

        String tectonicRegion = logicTreeElem.attributeValue(TECTONIC_REGION);

        Iterator i = logicTreeElem.elementIterator();
        while (i.hasNext()) {
            Element branchSet = (Element) i.next(); // <logicTreeBranchSet>

            parseLogicTreeBranchSet(branchSet, logicTree);

        }
        return tectonicRegion;
    }

    /**
     * Parse attributes and children of a &lt;logicTreeBranchSet&gt; element.
     * 
     * @param branchSet
     * @param logicTree
     */
    private void parseLogicTreeBranchSet(Element branchSet, LogicTree logicTree) {

        int indexBranchingLevel =
                Integer.parseInt(branchSet.attributeValue(BRANCHING_LEVEL));

        String uncertaintyType = branchSet.attributeValue(UNCERTAINTY_TYPE);
        LogicTreeBranchingLevel branchingLevel =
                new LogicTreeBranchingLevel(indexBranchingLevel, "", 0);

        int indexBranch = 1;
        Iterator i = branchSet.elementIterator();
        while (i.hasNext()) { // <logicTreeBranch> items
            Element logicTreeBranch = (Element) i.next();

            parseLogicTreeBranch(logicTreeBranch, branchingLevel,
                    uncertaintyType, indexBranch);

            indexBranch++;
        }
        logicTree.addBranchingLevel(branchingLevel);
    }

    /**
     * Parse child elements of &lt;logicTreeBranch&gt; element.
     * 
     * @param logicTreeBranch
     * @param branchingLevel
     * @param uncertaintyType
     * @param indexBranch
     */
    private void parseLogicTreeBranch(Element logicTreeBranch,
            LogicTreeBranchingLevel branchingLevel, String uncertaintyType,
            int indexBranch) {

        String uncertaintyModel =
                (String) logicTreeBranch.element(UNCERTAINTY_MODEL).getData();
        Double uncertaintyWeight =
                Double.valueOf((String) logicTreeBranch.element(
                        UNCERTAINTY_WEIGHT).getData());
        LogicTreeBranch branch =
                new LogicTreeBranch(indexBranch, uncertaintyModel,
                        uncertaintyWeight);
        if (uncertaintyType.equalsIgnoreCase(SOURCE_MODEL))
            branch.setNameInputFile(uncertaintyModel);
        else if (uncertaintyType
                .equalsIgnoreCase(MAX_MAGNITUDE_GUTENBERG_RICHTER_RELATIVE))
            branch.setRule(new LogicTreeRule(LogicTreeRuleParam.mMaxGRRelative,
                    Double.valueOf(uncertaintyModel)));
        else if (uncertaintyType
                .equalsIgnoreCase(B_VALUE_GUTENBERG_RICHTER_RELATIVE))
            branch.setRule(new LogicTreeRule(LogicTreeRuleParam.bGRRelative,
                    Double.valueOf(uncertaintyModel)));
        branchingLevel.addBranch(branch);
    }
}
