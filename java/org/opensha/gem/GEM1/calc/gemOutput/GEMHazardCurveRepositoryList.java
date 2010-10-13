package org.opensha.gem.GEM1.calc.gemOutput;

import java.util.ArrayList;
import java.util.Collections;
import java.util.HashMap;
import java.util.List;
import java.util.Map;
import java.util.Set;
import java.util.StringTokenizer;

import org.gem.engine.hazard.memcached.Cache;
import org.opensha.commons.calc.ProbabilityMassFunctionCalc;
import org.opensha.commons.data.DataPoint2D;
import org.opensha.commons.data.Site;
import org.opensha.commons.data.function.ArbitrarilyDiscretizedFunc;
import org.opensha.gem.GEM1.calc.gemLogicTree.GemLogicTree;
import org.opensha.gem.GEM1.commons.UnoptimizedDeepCopy;
import org.opensha.sha.earthquake.rupForecastImpl.GEM1.SourceData.GEMSourceData;
import org.opensha.sha.imr.ScalarIntensityMeasureRelationshipAPI;
import org.opensha.sha.util.TectonicRegionType;

import com.google.gson.Gson;

public class GEMHazardCurveRepositoryList {

    private String modelName;
    private ArrayList<GEMHazardCurveRepository> hcRepList;
    private ArrayList<String> endBranchLabels;

    /**
     * Constructor
     */
    public GEMHazardCurveRepositoryList() {
        this.modelName = "";
        this.endBranchLabels = new ArrayList<String>();
        this.hcRepList = new ArrayList<GEMHazardCurveRepository>();
    }

    public void setModelName(String str) {
        this.modelName = str;
    }

    public String getModelName() {
        return this.modelName;
    }

    /**
     * Add a GEMHazardCurveRepository to the GEMHazardCurveRepositoryList
     * 
     * @param hcRep
     */
    public void add(GEMHazardCurveRepository hcRep, String lab) {
        this.hcRepList.add(hcRep);
        this.endBranchLabels.add(lab);
    }

    /**
     * This method compute mean hazard curves generated from a set of hazard
     * curves assumed generated through a Monte Carlo process.
     */
    public GEMHazardCurveRepository getMeanHazardCurves() {
        // define GEMHazardCurveRepository for storing mean hazard curves
        // the initialization is done considering the first
        // HazardCurveRepository in the HazardCurveRepositoryList
        UnoptimizedDeepCopy udp = new UnoptimizedDeepCopy();
        GEMHazardCurveRepository meanHC =
                new GEMHazardCurveRepository(
                        (ArrayList<Site>) udp.copy(hcRepList.get(0)
                                .getGridNode()),
                        (ArrayList<Double>) udp.copy(hcRepList.get(0)
                                .getGmLevels()),
                        (ArrayList<Double[]>) udp.copy(hcRepList.get(0)
                                .getProbList()), hcRepList.get(0)
                                .getUnitsMeas());
        // loop over sites
        int indexSite = 0;
        for (Site site : meanHC.getGridNode()) {
            // hazard curve (probabilities of exceedance)
            Double[] probEx = new Double[meanHC.getGmLevels().size()];
            // loop over ground motion values
            int indexGMV = 0;
            for (Double gml : meanHC.getGmLevels()) {
                // array list containing probability of exceedance values
                // for the current ground motion values
                ArrayList<Double> probExValList = new ArrayList<Double>();
                // loop over hazard curves realizations
                for (int i = 0; i < hcRepList.size(); i++) {
                    // get corresponding ground motion value
                    probExValList.add(hcRepList.get(i).getProbExceedanceList(
                            indexSite)[indexGMV]);
                }
                // calculate mean value
                double mean = 0.0;
                for (int j = 0; j < probExValList.size(); j++)
                    mean = mean + probExValList.get(j);
                mean = mean / probExValList.size();
                probEx[indexGMV] = mean;
                indexGMV = indexGMV + 1;
            }// end loop over ground motion values

            meanHC.setHazardCurveGridNode(indexSite, site.getLocation()
                    .getLatitude(), site.getLocation().getLongitude(), probEx);

            indexSite = indexSite + 1;
        }// end loop over site
        return meanHC;
    }

    /**
     * This method compute mean hazard curves given a logic tree on the ERF and
     * an hash map of tectonic regions/logic tree for gmpes
     * 
     */
    public
            GEMHazardCurveRepository
            getMeanHazardCurves(
                    GemLogicTree<ArrayList<GEMSourceData>> erfLogicTree,
                    HashMap<TectonicRegionType, GemLogicTree<ScalarIntensityMeasureRelationshipAPI>> gmpeLogicTreeHashMap) {
        // define GEMHazardCurveRepository for storing mean hazard curves
        // the initialization is done considering the first
        // HazardCurveRepository in the HazardCurveRepositoryList
        UnoptimizedDeepCopy udp = new UnoptimizedDeepCopy();
        GEMHazardCurveRepository meanhc =
                new GEMHazardCurveRepository(
                        (ArrayList<Site>) udp.copy(hcRepList.get(0)
                                .getGridNode()),
                        (ArrayList<Double>) udp.copy(hcRepList.get(0)
                                .getGmLevels()),
                        (ArrayList<Double[]>) udp.copy(hcRepList.get(0)
                                .getProbList()), hcRepList.get(0)
                                .getUnitsMeas());
        // initialize ProbExList to 0 for all nodes
        // loop over grid nodes
        for (int i = 0; i < meanhc.getGridNode().size(); i++) {
            // loop over probability values
            for (int j = 0; j < meanhc.getProbExceedanceList(i).length; j++) {
                meanhc.getProbExceedanceList(i)[j] = 0.0;
            }
        }
        // loop over end-branches
        for (int i = 0; i < hcRepList.size(); i++) {
            // take the i-th end-branch
            GEMHazardCurveRepository hcTmp = hcRepList.get(i);
            // get the i-th end branch label
            String lab = endBranchLabels.get(i);
            // get the label corresponding to the ERF and the GMPE logic trees
            StringTokenizer labTokens = new StringTokenizer(lab, "-");
            // erf label
            String erfLab = labTokens.nextToken();
            // gmpe labels
            ArrayList<String> gmpeLab = new ArrayList<String>();
            ArrayList<TectonicRegionType> gmpeTectRegType =
                    new ArrayList<TectonicRegionType>();
            while (labTokens.hasMoreTokens()) {
                StringTokenizer st =
                        new StringTokenizer(labTokens.nextToken(), "_");
                // tectonic region type
                String trtName = st.nextToken();
                // label
                String label = st.nextToken();
                gmpeTectRegType.add(TectonicRegionType.getTypeForName(trtName));
                // label
                gmpeLab.add(label);
            }
            // Find the weight
            // given by the product of the total weight of the InputToERF logic
            // tree end branch
            // and the total weight of the GMPE logic tree end branch
            double wei = erfLogicTree.getTotWeight(erfLab);
            // loop over tectonic region types
            int indexTrt = 0;
            for (TectonicRegionType trt : gmpeTectRegType) {
                wei =
                        wei
                                * gmpeLogicTreeHashMap.get(trt).getTotWeight(
                                        gmpeLab.get(indexTrt));
                indexTrt = indexTrt + 1;
            }
            // loop over nodes
            for (int j = 0; j < hcTmp.getNodesNumber(); j++) {
                // loop over prob values
                for (int k = 0; k < hcTmp.getProbExceedanceList(j).length; k++) {
                    meanhc.getProbList().get(j)[k] =
                            meanhc.getProbExceedanceList(j)[k]
                                    + hcTmp.getProbExceedanceList(j)[k] * wei;
                }
            }
        }

        return meanhc;
    }

    /**
     * This method computes the mean hazard curve on each node of the grid given
     * the GemLogicTreeInputToERF and the GemLogicTreeGMPE
     * 
     * @return meanhc - Mean hazard curve on each node of the grid
     */
    public
            GEMHazardCurveRepository
            getMeanHazardCurve(
                    GemLogicTree<ArrayList<GEMSourceData>> ilTree,
                    GemLogicTree<HashMap<TectonicRegionType, ScalarIntensityMeasureRelationshipAPI>> gmpeLT) {

        // define GEMHazardCurveRepository for storing the mean hazard map
        // the initialization is done considering the first
        // HazardCurveRepository in the HazardCurveRepositoryList
        UnoptimizedDeepCopy udp = new UnoptimizedDeepCopy();
        GEMHazardCurveRepository meanhc =
                new GEMHazardCurveRepository(
                        (ArrayList<Site>) udp.copy(hcRepList.get(0)
                                .getGridNode()),
                        (ArrayList<Double>) udp.copy(hcRepList.get(0)
                                .getGmLevels()),
                        (ArrayList<Double[]>) udp.copy(hcRepList.get(0)
                                .getProbList()), hcRepList.get(0)
                                .getUnitsMeas());

        // initialize ProbExList to 0 for all nodes
        // loop over grid nodes
        for (int i = 0; i < meanhc.getGridNode().size(); i++) {
            // loop over probability values
            for (int j = 0; j < meanhc.getProbExceedanceList(i).length; j++) {
                meanhc.getProbExceedanceList(i)[j] = 0.0;
            }
        }

        // loop over end-branches
        for (int i = 0; i < hcRepList.size(); i++) {

            // take the i-th end-branch
            GEMHazardCurveRepository hcTmp = hcRepList.get(i);
            // get the i-th end branch label
            String lab = endBranchLabels.get(i);

            // separate the end branch label in the part which belongs
            // to the GemLogicTreeInputToERF and that belonging to
            // GemLogicTreeGMPE
            String[] strarr = lab.split("_");

            // GemLogicTreeInputToERF end branch label
            String erfLab = strarr[0];
            for (int ii = 1; ii < ilTree.getBranchingLevelsList().size(); ii++)
                erfLab = erfLab + "_" + strarr[ii];

            // GemLogicTreeGMPE end branch label
            String gmpeLab = strarr[ilTree.getBranchingLevelsList().size()];
            for (int ii = ilTree.getBranchingLevelsList().size() + 1; ii < strarr.length; ii++)
                gmpeLab = gmpeLab + "_" + strarr[ii];

            // Find the weight
            // given by the product of the total weight of the InputToERF logic
            // tree end branch
            // and the total weight of the GMPE logic tree end branch
            double wei =
                    ilTree.getTotWeight(erfLab) * gmpeLT.getTotWeight(gmpeLab);

            // loop over nodes
            for (int j = 0; j < hcTmp.getNodesNumber(); j++) {

                // loop over prob values
                for (int k = 0; k < hcTmp.getProbExceedanceList(j).length; k++) {
                    meanhc.getProbList().get(j)[k] =
                            meanhc.getProbExceedanceList(j)[k]
                                    + hcTmp.getProbExceedanceList(j)[k] * wei;
                }

            }
        }
        return meanhc;
    }

    public GEMHazardCurveRepository getQuantiles(double probLevel) {

        // define GEMHazardCurveRepository for storing quantile hazard curve
        // corresponding to the given
        // probability level
        // the initialization is done considering the first
        // HazardCurveRepository in the HazardCurveRepositoryList
        UnoptimizedDeepCopy udp = new UnoptimizedDeepCopy();
        GEMHazardCurveRepository hcRep =
                new GEMHazardCurveRepository(
                        (ArrayList<Site>) udp.copy(hcRepList.get(0)
                                .getGridNode()),
                        (ArrayList<Double>) udp.copy(hcRepList.get(0)
                                .getGmLevels()),
                        (ArrayList<Double[]>) udp.copy(hcRepList.get(0)
                                .getProbList()), hcRepList.get(0)
                                .getUnitsMeas());

        // loop over sites
        int indexSite = 0;
        for (Site site : hcRep.getGridNode()) {

            // hazard curve (probabilities of exceedance)
            Double[] probEx = new Double[hcRep.getGmLevels().size()];

            int indexGMV = 0;
            // loop over ground motion values
            for (Double gml : hcRep.getGmLevels()) {

                // array list containing probability of exceedance values
                // for the current ground motion values
                ArrayList<Double> probExValList = new ArrayList<Double>();

                // loop over hazard curves realizations
                for (int i = 0; i < hcRepList.size(); i++) {

                    // get corresponding ground motion value
                    probExValList.add(hcRepList.get(i).getProbExceedanceList(
                            indexSite)[indexGMV]);

                }

                // System.out.println("prob values before sorting: ");
                // for(int iv=0;iv<probExValList.size();iv++)
                // System.out.println(probExValList.get(iv));

                // sort values from smallest to largest (that is ascending
                // order)
                Collections.sort(probExValList);

                // System.out.println("prob values after sorting: ");
                // for(int iv=0;iv<probExValList.size();iv++)
                // System.out.println(probExValList.get(iv));

                // loop over sorted values and find the one corresponding to
                // the specified quantile
                for (int iv = 0; iv < probExValList.size(); iv++) {
                    double index = new Double(iv);
                    double size = new Double(probExValList.size());
                    double lev1 = index / size;
                    double lev2 = (index + 1) / size;
                    if (probLevel > lev1 && probLevel <= lev2) {
                        probEx[indexGMV] = probExValList.get(iv);
                        break;
                    }
                }

                indexGMV = indexGMV + 1;
            }// end loop over ground motion values

            hcRep.setHazardCurveGridNode(indexSite, site.getLocation()
                    .getLatitude(), site.getLocation().getLongitude(), probEx);

            indexSite = indexSite + 1;
        }// end loop over site

        return hcRep;
    }

    /**
     * 
     * @param probEx
     *            - Probability of exceedance
     * @param inputToERFLT
     *            -
     * @return meanHM
     */
    public
            ArrayList<Double>
            getMeanHazardMap(
                    double probEx,
                    GemLogicTree<ArrayList<GEMSourceData>> inputToERFLT,
                    GemLogicTree<HashMap<TectonicRegionType, ScalarIntensityMeasureRelationshipAPI>> gmpeLT) {
        GEMHazardCurveRepository meanHC =
                getMeanHazardCurve(inputToERFLT, gmpeLT);
        ArrayList<Double> meanHM = meanHC.getHazardMap(probEx);
        return meanHM;
    }

    public
            ArrayList<Double>
            getMeanGroundMotionMap(
                    double probEx,
                    GemLogicTree<ArrayList<GEMSourceData>> ilTree,
                    GemLogicTree<HashMap<TectonicRegionType, ScalarIntensityMeasureRelationshipAPI>> gmpeLT) {

        // instantiate mean hazard map
        ArrayList<Double> meanHM = hcRepList.get(0).getHazardMap(probEx);
        // initialize to zero
        for (int i = 0; i < meanHM.size(); i++)
            meanHM.set(i, 0.0);

        // loop over end-branches
        for (int i = 0; i < hcRepList.size(); i++) {

            // get the current hazard map
            ArrayList<Double> HM = hcRepList.get(i).getHazardMap(probEx);

            // get the i-th end branch label
            String lab = endBranchLabels.get(i);

            // separate the end branch label in the part which belongs
            // to the GemLogicTreeInputToERF and that belonging to
            // GemLogicTreeGMPE
            String[] strarr = lab.split("_");
            // GemLogicTreeInputToERF end branch label
            String erfLab = strarr[0];
            for (int ii = 1; ii < ilTree.getBranchingLevelsList().size(); ii++)
                erfLab = erfLab + "_" + strarr[ii];
            // GemLogicTreeGMPE end branch label
            String gmpeLab = strarr[ilTree.getBranchingLevelsList().size()];
            for (int ii = ilTree.getBranchingLevelsList().size() + 1; ii < strarr.length; ii++)
                gmpeLab = gmpeLab + "_" + strarr[ii];

            // Find the weight
            // given by the product of the total weight of the InputToERF logic
            // tree end branch
            // and the total weight of the GMPE logic tree end branch
            double wei =
                    ilTree.getTotWeight(erfLab) * gmpeLT.getTotWeight(gmpeLab);

            // loop over grid nodes
            for (int ii = 0; ii < meanHM.size(); ii++) {
                double val = meanHM.get(ii) + HM.get(ii) * wei;
                meanHM.set(ii, val);
            }

        }

        return meanHM;
    }

    /**
     * This method returns the mean ground motion map (for a given probability
     * of exceedance) from a set of hazard curves generated through Monte Carlo
     * approach. The mean ground motion value at each grid point is calculated
     * as the mean value of the ground motion values (corresponding to the
     * selected probability of exceedance) resulting from the different
     * calculated hazard curves.
     * 
     * @return
     */
    public ArrayList<Double> getMeanGrounMotionMap(double probEx) {

        // instantiate mean hazard map
        ArrayList<Double> meanHM = hcRepList.get(0).getHazardMap(probEx);
        // initialize to zero
        for (int i = 0; i < meanHM.size(); i++)
            meanHM.set(i, 0.0);

        // loop over end-branches (that is hazard curve realizations per grid
        // point)
        for (int i = 0; i < hcRepList.size(); i++) {

            // get the current hazard map
            ArrayList<Double> HM = hcRepList.get(i).getHazardMap(probEx);

            // loop over grid nodes
            for (int ii = 0; ii < meanHM.size(); ii++) {
                double val = meanHM.get(ii) + HM.get(ii);
                meanHM.set(ii, val);
            }

        }// end loop over end-branches

        // divide by the total number of hazard curve realizations
        // loop over grid nodes
        for (int ii = 0; ii < meanHM.size(); ii++) {
            double val = meanHM.get(ii) / hcRepList.size();
            meanHM.set(ii, val);
        }

        return meanHM;
    }

    public
            ArrayList<Double>
            getMeanGroundMotionMap(
                    double probEx,
                    GemLogicTree<ArrayList<GEMSourceData>> erfLogicTree,
                    HashMap<TectonicRegionType, GemLogicTree<ScalarIntensityMeasureRelationshipAPI>> gmpeLogicTreeHashMap) {

        // instantiate mean hazard map
        ArrayList<Double> meanHM = hcRepList.get(0).getHazardMap(probEx);
        // initialize to zero
        for (int i = 0; i < meanHM.size(); i++)
            meanHM.set(i, 0.0);

        // loop over end-branches
        for (int i = 0; i < hcRepList.size(); i++) {

            // get the current hazard map
            ArrayList<Double> HM = hcRepList.get(i).getHazardMap(probEx);

            // get the i-th end branch label
            String lab = endBranchLabels.get(i);

            // get the label corresponding to the ERF and the GMPE logic trees
            StringTokenizer labTokens = new StringTokenizer(lab, "-");

            // erf label
            String erfLab = labTokens.nextToken();

            ArrayList<String> gmpeLab = new ArrayList<String>();
            ArrayList<TectonicRegionType> gmpeTectRegType =
                    new ArrayList<TectonicRegionType>();
            while (labTokens.hasMoreTokens()) {
                StringTokenizer st =
                        new StringTokenizer(labTokens.nextToken(), "_");
                // tectonic region type
                String trtName = st.nextToken();
                // label
                String label = st.nextToken();
                gmpeTectRegType.add(TectonicRegionType.getTypeForName(trtName));
                // label
                gmpeLab.add(label);
            }

            // Find the weight
            // given by the product of the total weight of the InputToERF logic
            // tree end branch
            // and the total weight of the GMPE logic tree end branch
            double wei = erfLogicTree.getTotWeight(erfLab);
            // loop over tectonic region types
            int indexTrt = 0;
            for (TectonicRegionType trt : gmpeTectRegType) {
                wei =
                        wei
                                * gmpeLogicTreeHashMap.get(trt).getTotWeight(
                                        gmpeLab.get(indexTrt));
                indexTrt = indexTrt + 1;
            }

            // loop over grid nodes
            for (int ii = 0; ii < meanHM.size(); ii++) {
                double val = meanHM.get(ii) + HM.get(ii) * wei;
                meanHM.set(ii, val);
            }

        }

        return meanHM;
    }

    /**
     * 
     * @return
     */
    public ArrayList<GEMHazardCurveRepository> getHcRepList() {
        return hcRepList;
    }

    public void setHcRepList(ArrayList<GEMHazardCurveRepository> hcRepList) {
        this.hcRepList = hcRepList;
    }

    public ArrayList<String> getEndBranchLabels() {
        return endBranchLabels;
    }

    public void setEndBranchLabels(ArrayList<String> endBranchLabels) {
        this.endBranchLabels = endBranchLabels;
    }

    /**
     * Serializes this model in cache.
     * 
     * @param cache
     *            the cache used to store the serialized version of this model
     * @return the key used as index in cache
     */
    public String serialize(Cache cache) {
        // TODO Change with the model ID later on!
        // the hashCode method defined by class Object
        // does return distinct integers for distinct objects
        String key = new Integer(this.hashCode()).toString();
        cache.set(key, new Gson().toJson(this));

        return key;
    }

    /**
     * Computes the PMFs and updates the current model.
     */
    public void computePMFs() {
        for (GEMHazardCurveRepository curves : hcRepList) {
            curves.computePMFs();
        }
    }
}
