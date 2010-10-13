package org.opensha.gem.GEM1.calc.gemHazardCalculator;

import java.rmi.RemoteException;
import java.util.ArrayList;
import java.util.HashMap;
import java.util.Hashtable;
import java.util.Iterator;
import java.util.ListIterator;
import java.util.Set;

import org.opensha.commons.data.Site;
import org.opensha.commons.data.function.ArbitrarilyDiscretizedFunc;
import org.opensha.commons.param.ParameterAPI;
import org.opensha.commons.param.event.ParameterChangeWarningEvent;
import org.opensha.commons.param.event.ParameterChangeWarningListener;
// import org.opensha.sha.calc.HazardCurveCalculator;
import org.opensha.sha.earthquake.EqkRupForecast;
import org.opensha.sha.earthquake.rupForecastImpl.GEM1.SourceData.GEMSourceData;
import org.opensha.gem.GEM1.calc.gemOutput.GEMHazardCurveRepository;
import org.opensha.gem.GEM1.commons.UnoptimizedDeepCopy;
import org.opensha.gem.GEM1.scratch.HazardCurveCalculator;
import org.opensha.sha.imr.ScalarIntensityMeasureRelationshipAPI;
import org.opensha.sha.util.TectonicRegionType;

/**
 * <p>
 * title: GEMch: Gem Hazard Curves Calculator
 * </p>
 * 
 * <p>
 * This is the "final" GEM1 calculator. It accepts a logic tree on GMPEs and an
 * Hazard Calculator that accepts ERF with sources defined in terms of a
 * Tectonic Environment
 * </p>
 * 
 * @author damianom & marcop
 * @version 1.0
 * 
 */
public class GemComputeHazard implements Runnable {

    private class computeHazardRange {
        public int start, end;
    }

    // hazard curve repository
    private GEMHazardCurveRepository hcRep;

    // list of sites where to compute hazard curves
    public ArrayList<Site> siteList;

    // earthquake rupture forecast
    public EqkRupForecast ERF;

    // input sources
    ArrayList<GEMSourceData> sourceList;

    // attenuation relationship vs. tectonic region map
    public HashMap<TectonicRegionType, ScalarIntensityMeasureRelationshipAPI> gmpeMap;

    // intensity measure level list
    private ArbitrarilyDiscretizedFunc imlList;

    // maximum distance to source
    private double maxSourceDist;

    // number of threads
    private Thread pgaThreads[];
    private int startLoop, endLoop, curLoop, numThreads;

    /**
     * 
     * @param nproc
     * @param siteList
     * @param ERF
     * @param AttenRel
     */
    public GemComputeHazard(
            int nproc,
            ArrayList<Site> siteList,
            EqkRupForecast ERF,
            HashMap<TectonicRegionType, ScalarIntensityMeasureRelationshipAPI> gmpeMap,
            ArbitrarilyDiscretizedFunc imlList, double maxSourceDist) {

        // GMPE units (extracted from the first GMPE)
        Set<TectonicRegionType> gmpeLabels = gmpeMap.keySet();
        Iterator<TectonicRegionType> iterGmpeLabel = gmpeLabels.iterator();
        TectonicRegionType trt = iterGmpeLabel.next();
        String units = gmpeMap.get(trt).getIntensityMeasure().getUnits();
        String intensityMeasType =
                gmpeMap.get(trt).getIntensityMeasure().getName();

        // Y values of the hazard curves
        ArrayList<Double[]> probExList = new ArrayList<Double[]>();
        for (int i = 0; i < siteList.size(); i++)
            probExList.add(new Double[imlList.getNum()]);
        // for(int i=0;i<siteList.size();i++) probExList.add(new
        // Double[iml.getArrayLnIML().size()]);

        // array of ground motion values
        ArrayList<Double> gmv = new ArrayList<Double>();
        for (int i = 0; i < imlList.getNum(); i++)
            gmv.add(i, imlList.getX(i));

        // this.hcRep = new
        // GEMHazardCurveRepository(siteList,iml.getArrayLnIML(),probExList,units);
        this.hcRep =
                new GEMHazardCurveRepository(siteList, gmv, probExList, units);
        hcRep.setIntensityMeasureType(intensityMeasType);
        this.ERF = ERF;
        this.gmpeMap = gmpeMap;
        this.siteList = siteList;
        this.pgaThreads = new Thread[nproc];
        this.startLoop = this.curLoop = 0;
        this.endLoop = siteList.size();
        this.numThreads = nproc;
        this.imlList = imlList;
        this.maxSourceDist = maxSourceDist;
    }

    public GemComputeHazard(
            int nproc,
            ArrayList<Site> siteList,
            ArrayList<GEMSourceData> sourceList,
            HashMap<TectonicRegionType, ScalarIntensityMeasureRelationshipAPI> gmpeMap,
            ArbitrarilyDiscretizedFunc imlList, double maxSourceDist) {

        // GMPE units (extracted from the first GMPE)
        Set<TectonicRegionType> gmpeLabels = gmpeMap.keySet();
        Iterator<TectonicRegionType> iterGmpeLabel = gmpeLabels.iterator();
        TectonicRegionType trt = iterGmpeLabel.next();
        String units = gmpeMap.get(trt).getIntensityMeasure().getUnits();
        String intensityMeasType =
                gmpeMap.get(trt).getIntensityMeasure().getName();

        // Y values of the hazard curves
        ArrayList<Double[]> probExList = new ArrayList<Double[]>();
        for (int i = 0; i < siteList.size(); i++)
            probExList.add(new Double[imlList.getNum()]);
        // for(int i=0;i<siteList.size();i++) probExList.add(new
        // Double[iml.getArrayLnIML().size()]);

        // array of ground motion values
        ArrayList<Double> gmv = new ArrayList<Double>();
        for (int i = 0; i < imlList.getNum(); i++)
            gmv.add(i, imlList.getX(i));

        // this.hcRep = new
        // GEMHazardCurveRepository(siteList,iml.getArrayLnIML(),probExList,units);
        this.hcRep =
                new GEMHazardCurveRepository(siteList, gmv, probExList, units);
        hcRep.setIntensityMeasureType(intensityMeasType);
        this.sourceList = sourceList;
        this.gmpeMap = gmpeMap;
        this.siteList = siteList;
        this.pgaThreads = new Thread[nproc];
        this.startLoop = this.curLoop = 0;
        this.endLoop = siteList.size();
        this.numThreads = nproc;
        this.imlList = imlList;
        this.maxSourceDist = maxSourceDist;
    }

    /**
     * 
     * @return
     */
    private synchronized computeHazardRange loopGetRange() {
        if (curLoop >= endLoop)
            return null;

        computeHazardRange r = new computeHazardRange();
        r.start = curLoop;

        // distribute hazard calculation to the different threads
        curLoop += (endLoop - startLoop) / numThreads + 1;
        r.end = (curLoop < endLoop) ? curLoop : endLoop;
        return r;

    }

    /**
     * 
     * @param start
     * @param end
     */
    private void loopDoRange(int start, int end) {

        UnoptimizedDeepCopy udp = new UnoptimizedDeepCopy();

        // ********** intensity measure level **********//
        // ArbitrarilyDiscretizedFunc hcThread = iml.getLnIML();
        ArbitrarilyDiscretizedFunc hcThread =
                (ArbitrarilyDiscretizedFunc) UnoptimizedDeepCopy.copy(imlList);

        // ********* hazard curve calculator ************//
        HazardCurveCalculator hcc;

        // Each thread has its own copy of the ERF and GMPEs

        // ********* ERF for NSHMP fault model ************//
        EqkRupForecast ERFThread = ERF;

        // ***************** GMPE *****************//
        // GMPEs needs a deep copy
        HashMap<TectonicRegionType, ScalarIntensityMeasureRelationshipAPI> gmpeMapThread;
        gmpeMapThread =
                (HashMap<TectonicRegionType, ScalarIntensityMeasureRelationshipAPI>) UnoptimizedDeepCopy
                        .copy(gmpeMap);

        // loop over sites where to compute hazard
        for (int i = start; i < end; i += 1) {

            Set<TectonicRegionType> gmpeLabels = gmpeMapThread.keySet();
            Iterator<TectonicRegionType> iterGmpeLabel = gmpeLabels.iterator();
            // initialize site parameters for each attenuation relation
            while (iterGmpeLabel.hasNext()) {
                ListIterator<ParameterAPI<?>> it =
                        gmpeMapThread.get(iterGmpeLabel.next())
                                .getSiteParamsIterator();
                while (it.hasNext()) {
                    ParameterAPI param = it.next();
                    if (!siteList.get(i).containsParameter(param))
                        siteList.get(i).addParameter(param);
                }
            }

            // temporary: we convert the HashMap into a Hashtable to accomodate
            // what has been done
            // in the OpenSHA hazard curve calculator
            Hashtable<TectonicRegionType, ScalarIntensityMeasureRelationshipAPI> gmpeTmp =
                    new Hashtable<TectonicRegionType, ScalarIntensityMeasureRelationshipAPI>();
            iterGmpeLabel = gmpeLabels.iterator();
            while (iterGmpeLabel.hasNext()) {
                TectonicRegionType trt = iterGmpeLabel.next();
                gmpeTmp.put(trt, gmpeMapThread.get(trt));
            }

            // perform hazard calculation
            try {

                // define hazard curve calculator
                hcc = new HazardCurveCalculator();

                // set maximum source distance
                hcc.setMaxSourceDistance(maxSourceDist);

                // compute hazard curve
                // if(sourceListThread.){
                // hcc.getHazardCurve(hcThread,siteList.get(i),gmpeTmp,sourceList);
                // }
                // else{
                hcc.getHazardCurve(hcThread, siteList.get(i), gmpeTmp,
                        ERFThread);
                // }

                Double[] tmp = new Double[hcThread.getNum()];
                for (int j = 0; j < hcThread.getNum(); j++) {
                    tmp[j] = hcThread.getY(j);
                }

                // Store the hazard curve
                hcRep.setHazardCurveGridNode(i, siteList.get(i).getLocation()
                        .getLatitude(), siteList.get(i).getLocation()
                        .getLongitude(), tmp);

                // Info
                System.out.printf("thrd: %3d node: %5d/%d site (%.2f,%.2f)\n",
                        (start - startLoop) / (end - start), (i - start),
                        (end - start), siteList.get(i).getLocation()
                                .getLatitude(), siteList.get(i).getLocation()
                                .getLongitude());
                // System.out.printf("thrd: %3d node: %5d/%d site (%.2f,%.2f) - pex(0.1) %8.6e\n",
                // (start-startLoop)/(end-start),(i-start),(end-start),siteList.get(i).getLocation().getLatitude(),
                // siteList.get(i).getLocation().getLongitude(),Math.exp(hcThread.getFirstInterpolatedX(0.1)));

            } catch (RemoteException e) {
                e.printStackTrace();
            }

        }
    }

    /**
	 * 
	 */
    public void run() {
        computeHazardRange range;

        while ((range = loopGetRange()) != null) {
            loopDoRange(range.start, range.end);
        }

    }

    /**
     * 
     * @return
     */
    public GEMHazardCurveRepository getValues() {
        for (int i = 0; i < numThreads; i++) {
            pgaThreads[i] = new Thread(this);
            pgaThreads[i].start();
        }
        for (int i = 0; i < numThreads; i++) {
            try {
                pgaThreads[i].join();
            } catch (InterruptedException iex) {
            }
        }
        return hcRep;
    }

    /**
     * 
     * @param event
     * @return
     */
    private static ParameterChangeWarningListener
            ParameterChangeWarningListener(ParameterChangeWarningEvent event) {
        return null;
    }

}
