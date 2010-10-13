package org.gem.engine.hazard.models.nshmp.us;

import java.io.FileNotFoundException;
import java.io.Serializable;
import java.util.ArrayList;
import java.util.Hashtable;
import java.util.Iterator;
import java.util.Set;

import org.gem.engine.hazard.parsers.GemFileParser;
import org.gem.engine.hazard.parsers.nshmp.NshmpGrid2GemSourceData;
import org.opensha.sha.earthquake.rupForecastImpl.GEM1.SourceData.GEMSourceData;
import org.opensha.sha.util.TectonicRegionType;

public class NewNshmpCeusGridData extends GemFileParser {

    // directory for grid seismicity files
    public static String inDir = "nshmp/ceus_grids/";

    public NewNshmpCeusGridData(double latmin, double latmax, double lonmin,
            double lonmax) throws FileNotFoundException {

        srcDataList = new ArrayList<GEMSourceData>();

        NshmpGrid2GemSourceData gm = null;

        ArrayList<String> inputGridFile = null;

        ArrayList<Double> inputGridFileWeight = null;

        // // CEUSABhigh.pga.out
        // // 0.0333
        // gridFile.put(inDir+"CEUS.2007.AB4.in",0.0333);
        // //// CEUSABstd.pga.out
        // //// 0.08333
        // gridFile.put(inDir+"CEUS.2007.AB3.in",0.08333);
        // //// CEUSABmid.pga.out
        // //// 0.0333
        // gridFile.put(inDir+"CEUS.2007.AB2.in",0.0333);
        // //// CEUSABlow.pga.out
        // //// 0.01667
        // gridFile.put(inDir+"CEUS.2007.AB1.in",0.01667);
        inputGridFile = new ArrayList<String>();
        inputGridFileWeight = new ArrayList<Double>();
        inputGridFile.add(inDir + "CEUS.2007.AB4.in");
        inputGridFileWeight.add(0.0333);
        inputGridFile.add(inDir + "CEUS.2007.AB3.in");
        inputGridFileWeight.add(0.08333);
        inputGridFile.add(inDir + "CEUS.2007.AB2.in");
        inputGridFileWeight.add(0.0333);
        inputGridFile.add(inDir + "CEUS.2007.AB1.in");
        inputGridFileWeight.add(0.01667);

        // ////// CEUSJhigh.pga.out
        // ////// 0.0333
        // gridFile.put(inDir+"CEUS.2007.J4.in",0.0333);
        // ////// CEUSJstd.pga.out
        // ////// 0.083333
        // gridFile.put(inDir+"CEUS.2007.J3.in",0.083333);
        // ////// CEUSJmid.pga.out
        // ////// 0.0333
        // gridFile.put(inDir+"CEUS.2007.J2.in",0.0333);
        // ////// CEUSJlow.pga.out
        // ////// 0.01667
        // gridFile.put(inDir+"CEUS.2007.J1.in",0.01667);
        inputGridFile.add(inDir + "CEUS.2007.J4.in");
        inputGridFileWeight.add(0.0333);
        inputGridFile.add(inDir + "CEUS.2007.J3.in");
        inputGridFileWeight.add(0.083333);
        inputGridFile.add(inDir + "CEUS.2007.J2.in");
        inputGridFileWeight.add(0.0333);
        inputGridFile.add(inDir + "CEUS.2007.J1.in");
        inputGridFileWeight.add(0.01667);

        // ////// CEUSABhigh.pga.nmc
        // ////// 0.0667
        // gridFile.put(inDir+"CEUS.2007a.AB4.in",0.0667);
        // ////// CEUSABstd.pga.nmc
        // ////// 0.16666
        // gridFile.put(inDir+"CEUS.2007a.AB3.in",0.16666);
        // ////// CEUSABmid.pga.nmc
        // ////// 0.0667
        // gridFile.put(inDir+"CEUS.2007a.AB2.in",0.0667);
        // ////// CEUSABlow.pga.nmc
        // ////// 0.0333
        // gridFile.put(inDir+"CEUS.2007a.AB1.in",0.0333);
        inputGridFile.add(inDir + "CEUS.2007a.AB4.in");
        inputGridFileWeight.add(0.0667);
        inputGridFile.add(inDir + "CEUS.2007a.AB3.in");
        inputGridFileWeight.add(0.16666);
        inputGridFile.add(inDir + "CEUS.2007a.AB2.in");
        inputGridFileWeight.add(0.0667);
        inputGridFile.add(inDir + "CEUS.2007a.AB1.in");
        inputGridFileWeight.add(0.0333);

        // ////// CEUSJhigh.pga.nmc
        // ////// 0.06667
        // gridFile.put(inDir+"CEUS.2007a.J4.in",0.06667);
        // ////// CEUSJstd.pga.nmc
        // ////// 0.16667
        // gridFile.put(inDir+"CEUS.2007a.J3.in",0.16667);
        // ////// CEUSJmid.pga.nmc
        // ////// 0.06667
        // gridFile.put(inDir+"CEUS.2007a.J2.in",0.06667);
        // ////// CEUSJlow.pga.nmc
        // ////// 0.0333
        // gridFile.put(inDir+"CEUS.2007a.J1.in",0.0333);
        inputGridFile.add(inDir + "CEUS.2007a.J4.in");
        inputGridFileWeight.add(0.0667);
        inputGridFile.add(inDir + "CEUS.2007a.J3.in");
        inputGridFileWeight.add(0.16667);
        inputGridFile.add(inDir + "CEUS.2007a.J2.in");
        inputGridFileWeight.add(0.06667);
        inputGridFile.add(inDir + "CEUS.2007a.J1.in");
        inputGridFileWeight.add(0.0333);
        gm =
                new NshmpGrid2GemSourceData(inputGridFile,
                        TectonicRegionType.STABLE_SHALLOW, inputGridFileWeight,
                        latmin, latmax, lonmin, lonmax, true);
        srcDataList.addAll(gm.getList());

        // ////// CEUSchar.broad.pga
        // ////// 0.225 ! Broad charleston zone extending further offshore
        // gridFile.put(inDir+"CEUSchar.broad.in",0.225);
        // ////// CEUScharA.broad.pga
        // ////// 0.1
        // gridFile.put(inDir+"CEUScharA.broad.in",0.1);
        // ////// CEUScharB.broad.pga
        // ////// 0.075
        // gridFile.put(inDir+"CEUScharB.broad.in",0.075);
        // ////// CEUScharC.broad.pga
        // ////// 0.1
        // gridFile.put(inDir+"CEUScharC.broad.in",0.1);
        inputGridFile = new ArrayList<String>();
        inputGridFileWeight = new ArrayList<Double>();
        inputGridFile.add(inDir + "CEUSchar.broad.in");
        inputGridFileWeight.add(0.225);
        inputGridFile.add(inDir + "CEUScharA.broad.in");
        inputGridFileWeight.add(0.1);
        inputGridFile.add(inDir + "CEUScharB.broad.in");
        inputGridFileWeight.add(0.075);
        inputGridFile.add(inDir + "CEUScharC.broad.in");
        inputGridFileWeight.add(0.1);
        gm =
                new NshmpGrid2GemSourceData(inputGridFile,
                        TectonicRegionType.STABLE_SHALLOW, inputGridFileWeight,
                        latmin, latmax, lonmin, lonmax, true);
        srcDataList.addAll(gm.getList());

        // ////// CEUScharna.2007.pga
        // ////// 0.225
        // gridFile.put(inDir+"CEUScharn.in",0.225);
        // ////// CEUScharnA.2007.pga
        // ////// 0.1
        // gridFile.put(inDir+"CEUScharnA.in",0.1);
        // ////// CEUScharnB.2007.pga
        // ////// 0.075
        // gridFile.put(inDir+"CEUScharnB.in",0.075);
        // ////// CEUScharnC.2007.pga
        // ////// 0.1
        // gridFile.put(inDir+"CEUScharnC.in",0.1);
        inputGridFile = new ArrayList<String>();
        inputGridFileWeight = new ArrayList<Double>();
        inputGridFile.add(inDir + "CEUScharn.in");
        inputGridFileWeight.add(0.225);
        inputGridFile.add(inDir + "CEUScharnA.in");
        inputGridFileWeight.add(0.1);
        inputGridFile.add(inDir + "CEUScharnB.in");
        inputGridFileWeight.add(0.075);
        inputGridFile.add(inDir + "CEUScharnC.in");
        inputGridFileWeight.add(0.1);
        gm =
                new NshmpGrid2GemSourceData(inputGridFile,
                        TectonicRegionType.STABLE_SHALLOW, inputGridFileWeight,
                        latmin, latmax, lonmin, lonmax, true);
        srcDataList.addAll(gm.getList());

        // // iterator over files
        // Set<String> fileName = gridFile.keySet();
        // Iterator<String> iterFileName = fileName.iterator();
        // int indexFile = 1;
        // while(iterFileName.hasNext()){
        // String key = iterFileName.next();
        // System.out.println("Processing file: "+key+", weight: "+gridFile.get(key));
        // NshmpGrid2GemSourceData gm = null;
        // gm = new
        // NshmpGrid2GemSourceData(key,TectonicRegionType.STABLE_SHALLOW,gridFile.get(key),
        // latmin, latmax, lonmin, lonmax,true);
        // for(int i=0;i<gm.getList().size();i++)
        // srcDataList.add(gm.getList().get(i));
        // // if(indexFile>1){
        // // gridList = trimGridList(gridList);
        // // }
        // // indexFile = indexFile+1;
        //
        // }

    }

}
