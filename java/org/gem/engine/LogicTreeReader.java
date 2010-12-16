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
 * Class for reading logic tree data in a nrML format file. The constructor of
 * this class takes the path of the file to read from.
 * 
 */
public class LogicTreeReader {

    private final BufferedReader bufferedReader;

    private final Map<String, LogicTree> logicTreeHashMap;

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
        Element root = doc.getRootElement();

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
            Element logicTreeElem = (Element) i.next();
            String key = Integer.toString(indexLogicTree);
            LogicTree logicTree = new LogicTree();
            if (logicTreeElem.attributeValue(TECTONIC_REGION) != null)
                key = logicTreeElem.attributeValue(TECTONIC_REGION);

            int indexBranchingLevel = 1;
            Iterator j = logicTreeElem.elementIterator();
            while (j.hasNext()) {
                Element branchSetElem = (Element) j.next();
                String uncertaintyType =
                        branchSetElem.attributeValue(UNCERTAINTY_TYPE);
                LogicTreeBranchingLevel branchingLevel =
                        new LogicTreeBranchingLevel(indexBranchingLevel, "", 0);

                int indexBranch = 1;
                Iterator k = branchSetElem.elementIterator();
                while (k.hasNext()) {
                    Element branchElem = (Element) k.next();
                    String uncertaintyModel =
                            (String) branchElem.element(UNCERTAINTY_MODEL)
                                    .getData();
                    Double uncertaintyWeight =
                            Double.valueOf((String) branchElem.element(
                                    UNCERTAINTY_WEIGHT).getData());
                    LogicTreeBranch branch =
                            new LogicTreeBranch(indexBranch, uncertaintyModel,
                                    uncertaintyWeight);
                    if (uncertaintyType.equalsIgnoreCase(SOURCE_MODEL))
                        branch.setNameInputFile(uncertaintyModel);
                    else if (uncertaintyType
                            .equalsIgnoreCase(MAX_MAGNITUDE_GUTENBERG_RICHTER_RELATIVE))
                        branch.setRule(new LogicTreeRule(
                                LogicTreeRuleParam.mMaxGRRelative, Double
                                        .valueOf(uncertaintyModel)));
                    else if (uncertaintyType
                            .equalsIgnoreCase(B_VALUE_GUTENBERG_RICHTER_RELATIVE))
                        branch.setRule(new LogicTreeRule(
                                LogicTreeRuleParam.bGRRelative, Double
                                        .valueOf(uncertaintyModel)));
                    branchingLevel.addBranch(branch);
                    indexBranch = indexBranch + 1;
                }
                logicTree.addBranchingLevel(branchingLevel);
                indexBranchingLevel = indexBranchingLevel + 1;
            }
            logicTreeHashMap.put(key, logicTree);
            indexLogicTree = indexLogicTree + 1;
        }
        return logicTreeHashMap;
    }

}
