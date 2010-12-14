package org.gem.engine;

import java.io.File;
import java.net.MalformedURLException;
import java.util.HashMap;
import java.util.Iterator;
import java.util.Map;

import org.dom4j.Document;
import org.dom4j.DocumentException;
import org.dom4j.Element;
import org.dom4j.io.SAXReader;
import org.gem.engine.logictree.LogicTree;
import org.gem.engine.logictree.LogicTreeBranch;
import org.gem.engine.logictree.LogicTreeBranchingLevel;
import org.gem.engine.logictree.LogicTreeRule;
import org.gem.engine.logictree.LogicTreeRuleParam;

public class LogicTreeReader {

    private static Map<String, LogicTree> logicTreeHashMap;

    private static String TECTONIC_REGION = "tectonicRegion";
    private static String UNCERTAINTY_TYPE = "uncertaintyType";
    private static String UNCERTAINTY_MODEL = "uncertaintyModel";
    private static String UNCERTAINTY_WEIGHT = "uncertaintyWeight";
    private static String SOURCE_MODEL = "sourceModel";
    private static String MAX_MAGNITUDE_GUTENBERG_RICHTER_RELATIVE =
            "maxMagnitudeGutenbergRichterRelative";
    private static String B_VALUE_GUTENBERG_RICHTER_RELATIVE =
            "bValueGutenbergRichterRelative";

    public LogicTreeReader(String gmpeLogicTreeFile) {

        logicTreeHashMap = new HashMap<String, LogicTree>();

        File xml = new File(gmpeLogicTreeFile);
        SAXReader reader = new SAXReader();
        Document doc = null;
        try {
            doc = reader.read(xml);
        } catch (MalformedURLException e) {
            e.printStackTrace();
        } catch (DocumentException e) {
            e.printStackTrace();
        }
        Element root = doc.getRootElement();
        Iterator i = root.elements().iterator();
        int indexLogicTree = 1;
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
    }

    public Map<String, LogicTree> getLogicTreeHashMap() {
        return this.logicTreeHashMap;
    }

}
