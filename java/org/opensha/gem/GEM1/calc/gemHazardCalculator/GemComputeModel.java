package org.opensha.gem.GEM1.calc.gemHazardCalculator;

import java.io.BufferedOutputStream;
import java.io.BufferedWriter;
import java.io.File;
import java.io.FileOutputStream;
import java.io.IOException;
import java.io.OutputStreamWriter;
import java.text.SimpleDateFormat;
import java.util.ArrayList;
import java.util.Calendar;
import java.util.Collections;
import java.util.HashMap;
import java.util.List;

// import org.opengem.application.Shaml;
// import org.opengem.shaml.HazardCurveListType;
// import org.opengem.shaml.HazardCurveType;
// import org.opengem.shaml.HazardResultListType;
// import org.opengem.shaml.HazardResultType;
// import org.opengem.shaml.SiteDataType;
import org.opensha.commons.data.Site;
import org.opensha.commons.data.TimeSpan;
import org.opensha.commons.geo.GriddedRegion;
import org.opensha.commons.geo.Location;
import org.opensha.commons.geo.LocationList;
import org.opensha.commons.geo.Region;
import org.opensha.sha.earthquake.rupForecastImpl.GEM1.SourceData.GEMSourceData;
import org.opensha.gem.GEM1.calc.gemLogicTree.GemLogicTree;
import org.opensha.gem.GEM1.calc.gemLogicTree.GemLogicTreeBranch;
import org.opensha.gem.GEM1.calc.gemLogicTree.GemLogicTreeBranchingLevel;
import org.opensha.gem.GEM1.calc.gemOutput.GEMHazardCurveRepositoryList;
import org.opensha.gem.GEM1.commons.CalculationSettings;
import org.opensha.gem.GEM1.util.SiteParams;
import org.opensha.sha.imr.ScalarIntensityMeasureRelationshipAPI;
import org.opensha.sha.imr.param.SiteParams.Vs30_Param;
import org.opensha.sha.util.TectonicRegionType;

public class GemComputeModel {

    private GemLogicTree<ArrayList<GEMSourceData>> modelLogicTree;
    private GemLogicTree<HashMap<TectonicRegionType, ScalarIntensityMeasureRelationshipAPI>> gmpeLogicTree;
    private ArrayList<Site> hazSite;
    private double[] probLevel;
    private CalculationSettings calcSet;

    private GEMHazardCurveRepositoryList endBranchHazCurveList;

    private String dirName;

    /**
     * 
     * @param inputToErf
     *            : GemLogicTree for input model
     * @param gmpeLT
     *            : GemLogicTree for gmpes
     * @param hazSite
     *            : list of sites where to compute hazard
     * @param probLevel
     *            : probability level for hazard map
     * @param outDir
     * @param outputHazCurve
     * @param calcSet
     * @throws IOException
     */
    public GemComputeModel(
            GemLogicTree<ArrayList<GEMSourceData>> modelLogicTree,
            GemLogicTree<HashMap<TectonicRegionType, ScalarIntensityMeasureRelationshipAPI>> gmpeLogicTree,
            ArrayList<Site> hazSite, double[] probLevel, String outDir,
            boolean outputHazCurve, CalculationSettings calcSet)
            throws IOException {

        this.modelLogicTree = modelLogicTree;
        this.gmpeLogicTree = gmpeLogicTree;
        this.hazSite = hazSite;
        this.probLevel = probLevel;
        this.calcSet = calcSet;

        // today's date and time (used to define output folder)
        String DATE_FORMAT_NOW = "yyyy-MM-dd_HH:mm:ss";
        Calendar cal = Calendar.getInstance();
        SimpleDateFormat sdf = new SimpleDateFormat(DATE_FORMAT_NOW);
        String DateTime;
        DateTime = sdf.format(cal.getTime());

        // create a directory where to store results; all ancestor directories
        // must exist
        String modelName = modelLogicTree.getModelName();

        this.dirName = outDir + "results_" + modelName + "_" + DateTime + "/";
        boolean success = (new File(dirName).mkdirs());
        if (!success) {
            // Directory creation failed
            System.out.println("Creation of the directory failed!!");
            System.out.println("Execution stopped!");
            System.exit(0);
        }

        // shuffle list of sites in order to balance load among threads
        System.out.println("Randominzing hazard sites...");
        Collections.shuffle(hazSite);

        // initialize array of sites in calculation settings object
        calcSet.getOut().put(SiteParams.SITE_LIST.toString(), hazSite);

        // create GemComputeHazardLogicTree object
        GemComputeHazardLogicTree compHaz =
                new GemComputeHazardLogicTree(this.modelLogicTree,
                        this.gmpeLogicTree, this.calcSet);

        // compute hazard curves
        long startTimeMs = System.currentTimeMillis();
        this.endBranchHazCurveList = compHaz.calculateHaz();
        long taskTimeMs = System.currentTimeMillis() - startTimeMs;

        System.out
                .println("Wall clock time (excluding time for saving output files)");
        // 1h = 60*60*10^3 ms
        System.out.printf("hours  : %6.3f\n",
                taskTimeMs / (60 * 60 * Math.pow(10, 3)));
        // 1 min = 60*10^3 ms
        System.out.printf("minutes: %6.3f\n",
                taskTimeMs / (60 * Math.pow(10, 3)));

        if (outputHazCurve) {
            this.saveHazardCurves();
            // this.saveHazardCurvesToXML(this.dirName+"HazardCurves.xml");
        }

        // calculate and save mean hazard map
        this.saveMeanHazardMap();

    }

    /**
     * 
     * @param gemLogicTreeFile
     *            : file containing GemLogicTree object representing input model
     * @param gmpeLT
     *            : GemLogicTree object for gmpes
     * @param latmin
     *            : minimum latitude of rectangular region
     * @param latmax
     *            : maximum latitude of rectangular region
     * @param lonmin
     *            : minimum longitude of rectangular region
     * @param lonmax
     *            : maximum longitude of rectangular region
     * @param delta
     *            : discretization of rectangular region
     * @param probLevel
     *            : probability level for hazard map
     * @param outDir
     *            : output directory where store results
     * @param outputHazCurve
     *            : true if you want to print also hazard curves
     * @param calculation
     *            settings
     * @throws ClassNotFoundException
     * @throws IOException
     */
    public GemComputeModel(
            String gemLogicTreeFile,
            GemLogicTree<HashMap<TectonicRegionType, ScalarIntensityMeasureRelationshipAPI>> gmpeLogicTree,
            double latmin, double latmax, double lonmin, double lonmax,
            double delta, double[] probLevel, String outDir,
            boolean outputHazCurve, CalculationSettings calcSet)
            throws IOException, ClassNotFoundException {

        // initialize logic tree for input model
        GemLogicTree<ArrayList<GEMSourceData>> inputToErf =
                new GemLogicTree<ArrayList<GEMSourceData>>(gemLogicTreeFile);

        // define array list of sites
        ArrayList<Site> hazSite =
                createListOfSitesFromRectangularRegion(latmin, latmax, lonmin,
                        lonmax, delta);

        // use first constructor
        new GemComputeModel(inputToErf, gmpeLogicTree, hazSite, probLevel,
                outDir, outputHazCurve, calcSet);

    }

    /**
     * 
     * @param srcList
     * @param modelName
     * @param gmpeLogicTree
     * @param latmin
     * @param latmax
     * @param lonmin
     * @param lonmax
     * @param delta
     * @param probLevel
     * @param outDir
     * @param outputHazCurve
     * @param calcSet
     * @throws IOException
     */
    public GemComputeModel(
            ArrayList<GEMSourceData> srcList,
            String modelName,
            GemLogicTree<HashMap<TectonicRegionType, ScalarIntensityMeasureRelationshipAPI>> gmpeLogicTree,
            double latmin, double latmax, double lonmin, double lonmax,
            double delta, double[] probLevel, String outDir,
            boolean outputHazCurve, CalculationSettings calcSet)
            throws IOException {

        // define logic tree for input model
        GemLogicTree<ArrayList<GEMSourceData>> modelLogicTree =
                new GemLogicTree<ArrayList<GEMSourceData>>();

        // instantiate logic tree branches
        GemLogicTreeBranch bra1 = null;

        // 1st branching level
        GemLogicTreeBranchingLevel braLev1 =
                new GemLogicTreeBranchingLevel(1, "Model", -1);

        // 1st branching level-1st branch
        bra1 = new GemLogicTreeBranch(1, "MeanModel", 1.0);

        // add branches to 1st branching level
        braLev1.addBranch(bra1);

        // add branching levels to logic tree
        modelLogicTree.addBranchingLevel(braLev1);

        modelLogicTree.addEBMapping("1", srcList);

        modelLogicTree.setModelName(modelName);

        // define array list of sites
        ArrayList<Site> hazSite =
                createListOfSitesFromRectangularRegion(latmin, latmax, lonmin,
                        lonmax, delta);

        // use first constructor
        new GemComputeModel(modelLogicTree, gmpeLogicTree, hazSite, probLevel,
                outDir, outputHazCurve, calcSet);

    }

    /**
     * 
     * @param srcList
     * @param modelName
     * @param gmpeLogicTree
     * @param hazSite
     * @param probLevel
     * @param outDir
     * @param outputHazCurve
     * @param calcSet
     * @throws IOException
     */
    public GemComputeModel(
            ArrayList<GEMSourceData> srcList,
            String modelName,
            GemLogicTree<HashMap<TectonicRegionType, ScalarIntensityMeasureRelationshipAPI>> gmpeLogicTree,
            ArrayList<Site> hazSite, double[] probLevel, String outDir,
            boolean outputHazCurve, CalculationSettings calcSet)
            throws IOException {

        // define logic tree for input model
        GemLogicTree<ArrayList<GEMSourceData>> modelLogicTree =
                new GemLogicTree<ArrayList<GEMSourceData>>();

        // instantiate logic tree branches
        GemLogicTreeBranch bra1 = null;

        // 1st branching level
        GemLogicTreeBranchingLevel braLev1 =
                new GemLogicTreeBranchingLevel(1, "Model", -1);

        // 1st branching level-1st branch
        bra1 = new GemLogicTreeBranch(1, "MeanModel", 1.0);

        // add branches to 1st branching level
        braLev1.addBranch(bra1);

        // add branching levels to logic tree
        modelLogicTree.addBranchingLevel(braLev1);

        modelLogicTree.addEBMapping("1", srcList);

        modelLogicTree.setModelName(modelName);

        // define array list of sites
        // ArrayList<Site> hazSite =
        // createListOfSitesFromRectangularRegion(latmin,latmax,lonmin,lonmax,delta);

        // use first constructor
        new GemComputeModel(modelLogicTree, gmpeLogicTree, hazSite, probLevel,
                outDir, outputHazCurve, calcSet);

    }

    /**
     * 
     * @param latmin
     * @param latmax
     * @param lonmin
     * @param lonmax
     * @param delta
     * @return
     */
    private ArrayList<Site>
            createListOfSitesFromRegion(Region reg, double delta) {

        // Create a gridded region
        GriddedRegion grdReg = new GriddedRegion(reg, delta, null);

        // list of sites where to compute hazard
        ArrayList<Site> hazSite = new ArrayList<Site>();

        // LocationList
        List<LocationList> locLst = grdReg.getInteriors();

        // Create the list of sites
        int ii = 0;
        for (int i = 0; i < locLst.size(); i++) {
            for (int j = 0; i < locLst.get(i).size(); j++) {
                double lon = locLst.get(i).get(j).getLongitude();
                double lat = locLst.get(i).get(j).getLatitude();
                hazSite.add(ii, new Site(new Location(lat, lon)));
                ii += 1;
            }
        }

        // Returns the list of sites
        return hazSite;
    }

    /**
     * 
     * @param latmin
     * @param latmax
     * @param lonmin
     * @param lonmax
     * @param delta
     * @return
     */
    private ArrayList<Site> createListOfSitesFromRectangularRegion(
            double latmin, double latmax, double lonmin, double lonmax,
            double delta) {

        // total number of nodes in latitude and longitude direction
        int npgaLat = (int) ((latmax - latmin) / delta) + 1;
        int npgaLon = (int) ((lonmax - lonmin) / delta) + 1;

        // list of sites where to compute hazard
        ArrayList<Site> hazSite = new ArrayList<Site>();
        int ii = 0;
        for (int i = 0; i < npgaLat; i++) {
            for (int j = 0; j < npgaLon; j++) {
                hazSite.add(ii, new Site(new Location(latmin + delta * i,
                        lonmin + delta * j)));
                ii = ii + 1;
            }
        }

        return hazSite;
    }

    private void saveMeanHazardMap() {

        // loop over probability levels
        for (int ip = 0; ip < probLevel.length; ip++) {

            // calculate mean ground motion hazard map
            ArrayList<Double> meanHazMap =
                    endBranchHazCurveList.getMeanGroundMotionMap(probLevel[ip],
                            modelLogicTree, gmpeLogicTree);

            String duration =
                    calcSet.getOut().get(TimeSpan.DURATION).toString();
            String intensityMeasureType =
                    endBranchHazCurveList.getHcRepList().get(0)
                            .getIntensityMeasureType();
            String modelName = modelLogicTree.getModelName();

            // print mean hazard map
            try {
                String outfile =
                        dirName + modelName + "_hazardMap_"
                                + intensityMeasureType + "_"
                                + (probLevel[ip] * 100) + "pe" + duration
                                + "yr_mean" + ".dat";

                FileOutputStream oOutFIS = new FileOutputStream(outfile);
                BufferedOutputStream oOutBIS =
                        new BufferedOutputStream(oOutFIS);
                BufferedWriter oWriter =
                        new BufferedWriter(new OutputStreamWriter(oOutBIS));
                for (int i = 0; i < hazSite.size(); i++) {
                    oWriter.write(String.format("%+8.3f %+7.3f %7.4e\n",
                            hazSite.get(i).getLocation().getLongitude(),
                            hazSite.get(i).getLocation().getLatitude(),
                            meanHazMap.get(i)));
                }
                oWriter.close();
                oOutBIS.close();
                oOutFIS.close();
            } catch (Exception ex) {
                System.err.println("Trouble generating mean hazard map!");
                ex.printStackTrace();
                System.exit(-1);
            }

        }
    }

    // print hazard curves
    private void saveHazardCurves() throws IOException {

        // number of ground motion values
        int nGMV =
                endBranchHazCurveList.getHcRepList().get(0).getGmLevels()
                        .size();

        String duration = calcSet.getOut().get(TimeSpan.DURATION).toString();
        String intensityMeasureType =
                endBranchHazCurveList.getHcRepList().get(0)
                        .getIntensityMeasureType();
        String modelName = modelLogicTree.getModelName();

        // loop over end-branches
        for (int iebr = 0; iebr < endBranchHazCurveList.getHcRepList().size(); iebr++) {

            // open new file for each end-branch
            // String outfile =
            // dirName+endBranchHazCurveList.getEndBranchLabels().get(iebr)+".dat";//"-"+Double.toString(lat)+"_"+Double.toString(lon)+".dat";
            String branching =
                    endBranchHazCurveList.getEndBranchLabels().get(iebr)
                            + ".dat";
            String outfile =
                    dirName + modelName + "_hazardCurves_"
                            + intensityMeasureType + "_" + duration + "yr"
                            + "_" + branching.replaceAll("_", "-");

            FileOutputStream oOutFIS = new FileOutputStream(outfile);
            BufferedOutputStream oOutBIS = new BufferedOutputStream(oOutFIS);
            BufferedWriter oWriter =
                    new BufferedWriter(new OutputStreamWriter(oOutBIS));

            // first line contains ground motion values
            // loop over ground motion values
            oWriter.write(String.format("%8s %8s ", " ", " "));
            for (int igmv = 0; igmv < nGMV; igmv++) {
                double gmv =
                        endBranchHazCurveList.getHcRepList().get(iebr)
                                .getGmLevels().get(igmv);
                gmv = Math.exp(gmv);
                oWriter.write(String.format("%7.4e ", gmv));
            }
            oWriter.write("\n");

            // loop over grid points
            for (int igp = 0; igp < endBranchHazCurveList.getHcRepList()
                    .get(iebr).getNodesNumber(); igp++) {

                double lat =
                        endBranchHazCurveList.getHcRepList().get(iebr)
                                .getGridNode().get(igp).getLocation()
                                .getLatitude();
                double lon =
                        endBranchHazCurveList.getHcRepList().get(iebr)
                                .getGridNode().get(igp).getLocation()
                                .getLongitude();
                oWriter.write(String.format("%+8.4f %+7.4f ", lon, lat));

                // loop over ground motion values
                for (int igmv = 0; igmv < nGMV; igmv++) {
                    double rateEx = 0.0;
                    double probEx =
                            endBranchHazCurveList.getHcRepList().get(iebr)
                                    .getProbExceedanceList(igp)[igmv];
                    // if (probEx < 0.99){
                    // rateEx = (-1.0/50.0)*Math.log(1-probEx);
                    // } else {
                    // rateEx = probEx;
                    // }
                    // oWriter.write(String.format("%7.4e ",rateEx));
                    oWriter.write(String.format("%7.4e ", probEx));
                }
                oWriter.write("\n");
            }
            oWriter.close();
            oOutBIS.close();
            oOutFIS.close();
        } // end loop over end-branches

        // // print mean hazard curve for each grid point
        // // String outfile = dirName+modelName+"_MeanHazardCurves.dat";
        // String outfile =
        // dirName+modelName+"_hazardCurves_"+intensityMeasureType+"_"+duration+"yr"+"_mean.dat";
        //
        // FileOutputStream oOutFIS = new FileOutputStream(outfile);
        // BufferedOutputStream oOutBIS = new BufferedOutputStream(oOutFIS);
        // BufferedWriter oWriter = new BufferedWriter(new
        // OutputStreamWriter(oOutBIS));
        //
        // // write ground motion values - loop over ground motion values
        // oWriter.write(String.format("%8s %8s "," "," "));
        // for (int igmv=0;igmv<nGMV;igmv++) {
        // double gmv =
        // endBranchHazCurveList.getHcRepList().get(0).getGmLevels().get(igmv);
        // gmv = Math.exp(gmv);
        // oWriter.write(String.format("%7.4e ",gmv));
        // }
        // oWriter.write("\n");
        //
        // // loop over grid points
        // for(int
        // igp=0;igp<endBranchHazCurveList.getHcRepList().get(0).getNodesNumber();igp++){
        // double lat =
        // endBranchHazCurveList.getHcRepList().get(0).getGridNode().get(igp).getLocation().getLatitude();
        // double lon =
        // endBranchHazCurveList.getHcRepList().get(0).getGridNode().get(igp).getLocation().getLongitude();
        // // oWriter.write(lon+" "+lat+" ");
        // oWriter.write(String.format("%+8.4f %+7.4f ",lon,lat));
        //
        // // loop over ground motion values
        // for(int igmv=0;igmv<nGMV;igmv++){
        // double probEx =
        // endBranchHazCurveList.getMeanHazardCurve(modelLogicTree,gmpeLogicTree).getProbExceedanceList(igp)[igmv];
        // // double rateEx = (-1.0/50.0)*Math.log(1-probEx);
        // // oWriter.write(rateEx+" ");
        // oWriter.write(String.format("%7.4e ",probEx));
        // }
        // oWriter.write("\n");
        // } // end loop over grid points
        //
        // System.out.println("Created output file:"+outfile);
        // oWriter.close();
        // oOutBIS.close();
        // oOutFIS.close();
    }

    // private void saveHazardCurvesToXML(String fileName){
    //
    // File f = new File(fileName);
    //
    // HazardResultListType hrlt = Shaml.Output.getHazardResultListType();
    //
    // // loop over end-branches (each end-branch has its own hazard curve
    // repository)
    // for(int endBranchIndex = 0; endBranchIndex <
    // endBranchHazCurveList.getEndBranchLabels().size(); ++endBranchIndex) {
    //
    // // the hazard curves for the end branch
    // GEMHazardCurveRepository ghcr =
    // endBranchHazCurveList.getHcRepList().get(endBranchIndex);
    //
    // // the endBranchLabel
    // String endBranchLabel =
    // endBranchHazCurveList.getEndBranchLabels().get(endBranchIndex);
    //
    // // important: Append one SHAML "Result" element (of HazardResultType) per
    // end branch / GemHazardCurveRepository
    // HazardResultType hrt = Shaml.Output.appendHazardResultType(hrlt);
    //
    // // time span
    // double timeSpan = (Double) calcSet.getOut().get(TimeSpan.DURATION);
    // hrt.setTimeSpanDuration(timeSpan);
    //
    // // modelID
    // String IDmodel = modelLogicTree.getModelName();
    // hrt.setIDmodel(IDmodel);
    //
    // // intensity measure type
    // String imt =
    // endBranchHazCurveList.getHcRepList().get(0).getIntensityMeasureType();
    // hrt.setIMT(imt);
    //
    // // result descriptor
    // hrt.getDescriptor().setEndBranchLabel(endBranchLabel);
    //
    // HazardCurveListType hclt =
    // Shaml.Output.appendHazardCurveListType(hrt.getValues());
    //
    // // ground motion values
    // ArrayList<Double> iml = ghcr.getGmLevels();
    // // loop over ground motion values and calculate exp value
    // for(int iv=0;iv<iml.size();iv++){
    // double val = Math.exp(iml.get(iv));
    // iml.set(iv, val);
    // }
    // hclt.getIML().addAll(iml);
    //
    // // loop over grid points
    // for(int gridPointIndex = 0; gridPointIndex < ghcr.getNodesNumber()
    // ;++gridPointIndex) {
    // double lat =
    // ghcr.getGridNode().get(gridPointIndex).getLocation().getLatitude();
    // double lon =
    // ghcr.getGridNode().get(gridPointIndex).getLocation().getLongitude();
    // HazardCurveType hct = Shaml.Output.appendHazardCurveType(hclt.getList(),
    // new Double(lon), new Double(lat));
    // hct.setMinProb(ghcr.getProbExceedanceList(gridPointIndex)[ghcr.getProbExceedanceList(0).length-1]);
    // hct.setMaxProb(ghcr.getProbExceedanceList(gridPointIndex)[0]);
    // SiteDataType sdt = Shaml.Output.getSiteDataType(hct);
    // sdt.setVs30((Double)ghcr.getGridNode().get(gridPointIndex).getParameter(Vs30_Param.NAME).getValue());
    // Double[] val = ghcr.getProbExceedanceList(gridPointIndex);
    // // loop over probability values
    // for(int ip=0;ip<val.length;ip++) { sdt.getValues().add(val[ip]); }
    // } // end loop over grid points
    // } // end loop over end-branch labels
    //
    // Shaml.marshalOutput(hrlt, f);
    //
    // }

}
