package org.gem.engine.hazard.parsers.nshmp;

import java.io.BufferedReader;
import java.io.FileNotFoundException;
import java.io.FileReader;
import java.io.FileWriter;
import java.io.IOException;
import java.io.InputStreamReader;
import java.net.URL;
import java.util.ArrayList;
import java.util.StringTokenizer;

import org.gem.engine.hazard.parsers.GemFileParser;
import org.opensha.commons.data.function.ArbitrarilyDiscretizedFunc;
import org.opensha.commons.geo.Location;
import org.opensha.sha.earthquake.FocalMechanism;
import org.opensha.sha.earthquake.griddedForecast.HypoMagFreqDistAtLoc;
import org.opensha.sha.earthquake.rupForecastImpl.GEM1.SourceData.GEMPointSourceData;
import org.opensha.sha.earthquake.rupForecastImpl.GEM1.SourceData.GEMSourceData;
import org.opensha.sha.magdist.GutenbergRichterMagFreqDist;
import org.opensha.sha.magdist.IncrementalMagFreqDist;
import org.opensha.sha.magdist.SummedMagFreqDist;
import org.opensha.sha.util.TectonicRegionType;

/**
 * This class reads a NSHMP grid seismicity input file and returns a list of
 * GEMGridSourceData object. The user must specify the tectonic region
 * associated with the input model and also the file weight (as derived by the
 * logic tree)
 * 
 * @author damianomonelli
 * 
 */

public class NshmpGrid2GemSourceData extends GemFileParser {

    // variable containing the source data
    // private ArrayList<GEMPointSourceData> srcDataList;

    // cut off magnitude to distinguish between point
    // and finite sources. If I well understood this
    // value is not specified in the input file but is
    // reported in the documentation. See page 5
    // Paragraph: Seismicity-Derived Hazard Component
    private static double cutOffMag = 6.0;

    // magnitude interval for average top of rupture
    // distribution
    private static double dM = 0.1;

    private static double borderThickness = 2.0;

    // constructor
    public NshmpGrid2GemSourceData(String inputFile,
            TectonicRegionType tectReg, double fileWeight, double latmin,
            double latmax, double lonmin, double lonmax,
            boolean bigEndian2LittleEndian) throws FileNotFoundException {

        srcDataList = new ArrayList<GEMSourceData>();

        BufferedReader oReader = new BufferedReader(new FileReader(inputFile));

        String sRecord = null;
        StringTokenizer st = null;

        // start reading
        try {

            // Integer value indicating where to compute hazard.
            // 0 = grid of sites; 1-31 = list of sites
            sRecord = oReader.readLine();
            st = new StringTokenizer(sRecord);
            int site = Integer.valueOf(st.nextToken()).intValue();
            if (site == 0) {
                // site grid definition
                // minimum latitude, maximum latitude, delta latitude
                sRecord = oReader.readLine();
                st = new StringTokenizer(sRecord);
                double minLatSites =
                        Double.valueOf(st.nextToken()).doubleValue();
                double maxLatSites =
                        Double.valueOf(st.nextToken()).doubleValue();
                double deltaLatSites =
                        Double.valueOf(st.nextToken()).doubleValue();
                //

                // minimum longitude, maximum longitude, delta longitude
                sRecord = oReader.readLine();
                st = new StringTokenizer(sRecord);
                double minLonSites =
                        Double.valueOf(st.nextToken()).doubleValue();
                double maxLonSites =
                        Double.valueOf(st.nextToken()).doubleValue();
                double deltaLonSites =
                        Double.valueOf(st.nextToken()).doubleValue();
                //

            } else if (site != 0) {
                double[] staLat = new double[site];
                double[] staLon = new double[site];
                String[] staName = new String[site];
                // loop over stations
                for (int is = 0; is < site; is++) {
                    sRecord = oReader.readLine();
                    st = new StringTokenizer(sRecord);
                    staLat[is] = Double.valueOf(st.nextToken()).doubleValue();
                    staLon[is] = Double.valueOf(st.nextToken()).doubleValue();
                    staName[is] = st.nextToken();
                }
            }

            // Vs30 (m/s), depth to 2.5 km/sec shear wave speed (Campbell basin
            // depth)
            sRecord = oReader.readLine();
            st = new StringTokenizer(sRecord);
            double vs30 = Double.valueOf(st.nextToken()).doubleValue();
            double campbellBasinDepth =
                    Double.valueOf(st.nextToken()).doubleValue();

            // depth(s) to top of rupture (number of depths to top of rupture,
            // for each depth: depth (km), weight (M<=6.5), weight (M>6.5))
            sRecord = oReader.readLine();
            st = new StringTokenizer(sRecord);
            // number of depths to top of rupture
            int nDepthTopRupture = Integer.valueOf(st.nextToken()).intValue();
            double[] depthTopRupture = new double[nDepthTopRupture];
            double[] weightLess65 = new double[nDepthTopRupture];
            double[] weightGreater65 = new double[nDepthTopRupture];
            for (int i = 0; i < nDepthTopRupture; i++) {
                depthTopRupture[i] =
                        Double.valueOf(st.nextToken()).doubleValue();
                weightLess65[i] = Double.valueOf(st.nextToken()).doubleValue();
                weightGreater65[i] =
                        Double.valueOf(st.nextToken()).doubleValue();
            }

            // weights for strike-slip, reverse, normal
            double[] weightFaultStyle = new double[3];
            sRecord = oReader.readLine();
            st = new StringTokenizer(sRecord);
            weightFaultStyle[0] = Double.valueOf(st.nextToken()).doubleValue();
            weightFaultStyle[1] = Double.valueOf(st.nextToken()).doubleValue();
            weightFaultStyle[2] = Double.valueOf(st.nextToken()).doubleValue();

            // distance increment (its meaning is not clear yet), maximum
            // distance
            // (from a given site I consider only those sources that are within
            // the maximum distance))
            sRecord = oReader.readLine();
            st = new StringTokenizer(sRecord);
            double distIncr = Double.valueOf(st.nextToken()).doubleValue();
            double maxDist = Double.valueOf(st.nextToken()).doubleValue();

            // source grid definition
            // minimum latitude, maximum latitude, delta latitude
            sRecord = oReader.readLine();
            st = new StringTokenizer(sRecord);
            double minLatSources = Double.valueOf(st.nextToken()).doubleValue();
            double maxLatSources = Double.valueOf(st.nextToken()).doubleValue();
            double deltaLatSources =
                    Double.valueOf(st.nextToken()).doubleValue();
            // minimum longitude, maximum longitude, delta longitude
            sRecord = oReader.readLine();
            st = new StringTokenizer(sRecord);
            double minLonSources = Double.valueOf(st.nextToken()).doubleValue();
            double maxLonSources = Double.valueOf(st.nextToken()).doubleValue();
            double deltaLonSources =
                    Double.valueOf(st.nextToken()).doubleValue();

            // number of sources along latitude
            int nSrcLat =
                    (int) ((maxLatSources - minLatSources) / deltaLatSources) + 1;
            // number of sources along longitude
            int nSrcLon =
                    (int) ((maxLonSources - minLonSources) / deltaLonSources) + 1;
            // total number of sources
            int nSrc = nSrcLat * nSrcLon;

            // b value, minimum magnitude, maximum magnitude,
            // delta magnitude, magRef (? its meaning not clear yet, maybe no
            // longer used))
            sRecord = oReader.readLine();
            st = new StringTokenizer(sRecord);
            double bVal = Double.valueOf(st.nextToken()).doubleValue();
            double minMag = Double.valueOf(st.nextToken()).doubleValue();
            double maxMag = Double.valueOf(st.nextToken()).doubleValue();
            double deltaMag = Double.valueOf(st.nextToken()).doubleValue();
            double magRef = Double.valueOf(st.nextToken()).doubleValue();

            // iflt, ibmat, maxMat, Mtaper
            // iflt = 0 -> no finite faults
            // iflt = 1 -> apply finite fault corrections for M>6 assuming
            // random strike
            // iflt = 2 -> use finite line faults for M>6 and fix strike
            // iflt = 3 -> use finite faults with Johston mblg to Mw converter
            // iflt = 4 -> use finite faults with Boore and Atkinson mblg to Mw
            // converter
            // ibmax = 0 -> use specified b value
            // ibmax = 1 -> use b value matrix (provided in a file)
            // maxMat = 0 -> use specified maximum magnitude
            // maxMat = 1 -> use maximum magnitude matrix (provided in a file)
            // maxMat = -1 -> use as maximum magnitude the minimum between the
            // default and grid value
            // No longer needed? (throws an exception for now)
            // Mtaper (for M>Mtaper reduce occurance rates by the factor
            // specified in
            // the weight file right below)
            sRecord = oReader.readLine();
            st = new StringTokenizer(sRecord);
            int iflt = Integer.valueOf(st.nextToken()).intValue();
            int ibmax = Integer.valueOf(st.nextToken()).intValue();
            int imaxMat = Integer.valueOf(st.nextToken()).intValue();
            // the mTaper variable is defined only for input files that work
            // with
            // hazgridXnga3.f but not those that work with hazgridXnga2.f
            // (like SHEAR1.in, SHEAR2.in, etc.)
            double mTaper = Double.NaN;
            if (st.hasMoreTokens()) {
                mTaper = Double.valueOf(st.nextToken()).doubleValue();
            }

            if (iflt > 2) {
                System.out
                        .println("iflt>2. Magnitude conversion equation is applied!");
            }

            // Depending on the previous record read b value file and/or maximum
            // magnitude file.
            String bValFileName = null;
            ReadBinaryInputMatrix bValMat = null;
            if (ibmax == 1) {
                sRecord = oReader.readLine();
                st = new StringTokenizer(sRecord);
                // read b file name
                bValFileName = relativePath(inputFile, st.nextToken());
                System.out.println("b value matrix: " + bValFileName);
                // read b value matrix
                bValMat =
                        new ReadBinaryInputMatrix(bValFileName,
                                bigEndian2LittleEndian);
            }
            String maxMagFileName = null;
            ReadBinaryInputMatrix maxMagMat = null;
            if (imaxMat == 1 || imaxMat == -1) {
                sRecord = oReader.readLine();
                st = new StringTokenizer(sRecord);
                // read maximum magnitude file name
                maxMagFileName = relativePath(inputFile, st.nextToken());
                System.out.println("Maximum magnitude matrix: "
                        + maxMagFileName);
                // read maximum magnitude matrix
                maxMagMat =
                        new ReadBinaryInputMatrix(maxMagFileName,
                                bigEndian2LittleEndian);
            }

            // weight file (to be used to decrease rates of events for M>Mtaper)
            String weightMTaperFileName = null;
            ReadBinaryInputMatrix weightMTaperMat = null;
            if (mTaper > 5.0 && mTaper < 8.0) {
                sRecord = oReader.readLine();
                st = new StringTokenizer(sRecord);
                // read maximum magnitude file name
                weightMTaperFileName = relativePath(inputFile, st.nextToken());
                System.out.println("Tapering magnitude weights matrix: "
                        + weightMTaperFileName);
                // read weights file
                weightMTaperMat =
                        new ReadBinaryInputMatrix(weightMTaperFileName,
                                bigEndian2LittleEndian);
            } else {
                // line 620 in hazgridXnga3.f
                mTaper = 10.0;
            }

            // a value file (actually rates! that is 10^a)
            String aValFileName = null;
            sRecord = oReader.readLine();
            st = new StringTokenizer(sRecord);
            // read a value file name
            aValFileName = relativePath(inputFile, st.nextToken());

            System.out.println("a value file name: " + aValFileName);

            // read a value file
            ReadBinaryInputMatrix aValMat =
                    new ReadBinaryInputMatrix(aValFileName,
                            bigEndian2LittleEndian);
            // make the source number(source points) equal to the a-value grid
            // points
            if (aValMat.getVal().size() != nSrc) {
                // System.out.println();
                nSrc = aValMat.getVal().size();
            }

            // System.out.println("avalue matrix: " +aValMat.getVal());
            // for(int iv=0;iv<aValMat.getVal().size();iv++)
            // System.out.println(aValMat.getVal().get(iv));

            // year for a value file (that is rates are referred to this number
            // of years
            // , if 1 a value is cumulative (never used?)
            sRecord = oReader.readLine();
            st = new StringTokenizer(sRecord);
            double aValYear = Double.valueOf(st.nextToken()).doubleValue();
            int aValConvert = Integer.valueOf(st.nextToken()).intValue();

            // if iflt = 2 read strike angle
            double strike = Double.NaN;
            if (iflt == 2) {
                sRecord = oReader.readLine();
                st = new StringTokenizer(sRecord);
                strike = Double.valueOf(st.nextToken()).doubleValue();
            }

            // later version (hazgridXnga5.f) includes a file that specify
            // the magnitude-distance correction

            if (aValConvert == 1) {
                // convert a value from cumulative to incremental
                for (int iav = 0; iav < aValMat.getVal().size(); iav++) {
                    double a = aValMat.getVal().get(iav);
                    if (a != 0) {
                        // line 643/644
                        // a(j)= alog10(a(j))+fac
                        // a(j)= 10.**a(j)
                        // line 602
                        // fac= alog10(10.**(bval*dmag2)-10.**(-bval*dmag2))
                        double val =
                                Math.log10(a)
                                        + Math.log10(Math.pow(10, bVal
                                                * deltaMag / 2)
                                                - Math.pow(10, -bVal * deltaMag
                                                        / 2));
                        aValMat.getVal().set(iav, Math.pow(10.0, val));
                    }
                }
            }

            // average top of rupture-magnitude distribution
            ArbitrarilyDiscretizedFunc aveRupTopVsMag =
                    new ArbitrarilyDiscretizedFunc();
            // average top of rupture depth for events with M<6.5 and M>6.5
            double aveTopRupLess65 = 0.0;
            double aveTopRupGreater65 = 0.0;
            // loop over depths
            for (int idepth = 0; idepth < depthTopRupture.length; idepth++) {
                aveTopRupLess65 =
                        aveTopRupLess65 + weightLess65[idepth]
                                * depthTopRupture[idepth];
                aveTopRupGreater65 =
                        aveTopRupGreater65 + weightGreater65[idepth]
                                * depthTopRupture[idepth];
            }
            // number of magnitude values in the top of rupture-magnitude
            // distribution
            // the magnitude axis start from the cutOffMag because below this
            // value the source is
            // treated as a point
            int nMag = (int) ((10.0 - cutOffMag) / dM + 1);
            for (int imag = 0; imag < nMag; imag++) {
                // magnitude value
                double mag = cutOffMag + imag * deltaMag;
                if (mag < 6.5) {
                    aveRupTopVsMag.set(mag, aveTopRupLess65);
                } else if (mag >= 6.5) {
                    aveRupTopVsMag.set(mag, aveTopRupGreater65);
                }
            }
            // average hypocentral depth (used when the source is treated as a
            // point)
            // I do not think this parameter is given by the USGS model.
            // I assume it to be equal to the average top of rupture depth for
            // M<6.5
            double aveHypoDepth = aveTopRupLess65;

            // loop over sources
            int indexSrc = 0;
            for (int is = 0; is < nSrc; is++) {

                // System.out.println(is+" "+aValMat.getVal().get(is));
                // source rate
                double rate = aValMat.getVal().get(is);

                if (rate == 0.0) {
                    continue;
                } else {

                    // compute source cell coordinates
                    // line 1205->1210
                    // do 101 j=1,nsrc 
                    // isy= (j-1)/nsx
                    // isx= j-1-isy*nsx
                    // sx= xsmin+float(isx)*dsx
                    // sy= ysmax-float(isy)*dsy 
                    int isy = is / nSrcLon;
                    int isx = is - isy * nSrcLon;
                    double lonSrc = minLonSources + isx * deltaLonSources;
                    double latSrc = maxLatSources - isy * deltaLatSources;

                    // System.out.println("latitude: "+latSrc+", longitude: "+lonSrc);

                    // line 659
                    // if((ibmat.eq.1).and.(b(j).eq.0.)) b(j)=bval
                    if (ibmax == 1 && bValMat.getVal().get(is) == 0)
                        bValMat.getVal().set(is, bVal);
                    // line 664/665
                    // if((abs(maxmat) .eq.1).and.(mmax(j).lt.0.)) a(j)=1.e-10
                    // if((abs(maxmat) .eq.1).and.(mmax(j).le.0.))
                    // mmax(j)=magmax
                    if (Math.abs(imaxMat) == 1
                            && maxMagMat.getVal().get(is) < 0.0)
                        aValMat.getVal().set(is, 1e-10);
                    if (Math.abs(imaxMat) == 1
                            && maxMagMat.getVal().get(is) <= 0.0)
                        maxMagMat.getVal().set(is, maxMag);

                    // incremental a value
                    double aValue =
                            Math.log10(aValMat.getVal().get(is) / aValYear);

                    // b value
                    double bValue = Double.NaN;
                    if (ibmax == 1) {
                        bValue = bValMat.getVal().get(is);
                    } else if (ibmax == 0) {
                        bValue = bVal;
                    }

                    // maximum magnitude
                    double maximumMag = Double.NaN;
                    if (imaxMat == 1) {
                        maximumMag = maxMagMat.getVal().get(is);
                    } else if (imaxMat == -1) {
                        if (maxMag < maxMagMat.getVal().get(is)) {
                            maximumMag = maxMag;
                        } else {
                            maximumMag = maxMagMat.getVal().get(is);
                        }
                    } else if (imaxMat == 0) {
                        maximumMag = maxMag;
                    }

                    // minimum magnitude
                    // and number of magnitude values in the mfd
                    double minimumMag = minMag;
                    int nmag = 0;
                    if (minimumMag != maximumMag) {
                        minimumMag = minimumMag + deltaMag / 2;
                        maximumMag = maximumMag - deltaMag / 2;
                        nmag =
                                (int) ((maximumMag - minimumMag) / deltaMag + 1.4);
                    } else if (minimumMag == maximumMag) {
                        nmag = 1;
                    }

                    // total moment rate
                    double tmr =
                            totMoRate(minimumMag, nmag, deltaMag, aValue,
                                    bValue);

                    // count how many weights are non-zero
                    int nWeight = 0;
                    for (int ifs = 0; ifs < weightFaultStyle.length; ifs++) {
                        if (weightFaultStyle[ifs] > 0)
                            nWeight = nWeight + 1;
                    }

                    // array of focal mechanisms
                    FocalMechanism[] fmList = new FocalMechanism[nWeight];

                    // array of mfd
                    IncrementalMagFreqDist[] mfdList =
                            new IncrementalMagFreqDist[nWeight];

                    // loop over fault mechanisms
                    int ifm = 0;
                    for (int ifs = 0; ifs < weightFaultStyle.length; ifs++) {

                        // if the corresponding weight is non-zero
                        if (weightFaultStyle[ifs] != 0.0) {

                            // define mfd
                            GutenbergRichterMagFreqDist mfd =
                                    new GutenbergRichterMagFreqDist(minimumMag,
                                            nmag, deltaMag);
                            // set total moment rate
                            mfd.setAllButTotCumRate(minimumMag, minimumMag
                                    + (nmag - 1) * deltaMag, fileWeight
                                    * weightFaultStyle[ifs] * tmr, bValue);
                            // System.out.println("Source: "+is);
                            // for(int imv=0;imv<mfd.getNum();imv++){
                            // System.out.println("Rate, magnitude: "+mfd.getX(imv)+" "+mfd.getY(imv));
                            // }
                            if (mTaper > 5.0 && mTaper < 8.0) {
                                // scale the rates, by the specified weight, for
                                // magnitudes greater than the taper magnitude
                                for (int im = 0; im < mfd.getNum(); im++) {
                                    if (mfd.getX(im) >= mTaper) {
                                        double val =
                                                mfd.getY(im)
                                                        * weightMTaperMat
                                                                .getVal().get(
                                                                        is);
                                        mfd.set(im, val);
                                    }
                                }
                            }

                            // System.out.println(mfd);

                            if (iflt > 2) { // apply magnitude conversion
                                            // equation

                                // compute new values of minimum and maximum
                                // magnitude
                                double minMagnitude = mfd.getMinX();
                                double maxMagnitude = mfd.getMaxX();
                                if (iflt == 3) {// Johnston equation line 1124
                                    // if(iflt.eq.3) xmag= 1.14 +
                                    // 0.24*xmag+0.0933*xmag*xmag
                                    minMagnitude =
                                            1.14 + 0.24 * minMagnitude + 0.0933
                                                    * minMagnitude
                                                    * minMagnitude;
                                    maxMagnitude =
                                            1.14 + 0.24 * maxMagnitude + 0.0933
                                                    * maxMagnitude
                                                    * maxMagnitude;
                                } else if (iflt == 4) {// Boore Atkinson line
                                                       // 1126
                                    // if(iflt.eq.4) xmag= 2.715 -
                                    // 0.277*xmag+0.127*xmag*xmag
                                    minMagnitude =
                                            2.715 - 0.277 * minMagnitude
                                                    + 0.127 * minMagnitude
                                                    * minMagnitude;
                                    maxMagnitude =
                                            2.715 - 0.277 * maxMagnitude
                                                    + 0.127 * maxMagnitude
                                                    * maxMagnitude;
                                }

                                // compute mean magnitude
                                double meanMagnitude = 0.0;
                                for (int im = 0; im < mfd.getNum(); im++) {
                                    double mag = mfd.getX(im);
                                    if (iflt == 3) {
                                        meanMagnitude =
                                                meanMagnitude
                                                        + (1.14 + 0.24 * mag + 0.0933
                                                                * mag * mag)
                                                        * mfd.getIncrRate(im);
                                    } else if (iflt == 4) {
                                        meanMagnitude =
                                                meanMagnitude
                                                        + (2.715 - 0.277 * mag + 0.127
                                                                * mag * mag)
                                                        * mfd.getIncrRate(im);
                                    }
                                }
                                meanMagnitude =
                                        meanMagnitude / mfd.getTotCumRate();
                                // recompute b value by using Aki's formula
                                bValue =
                                        Math.log10(Math.E)
                                                / (meanMagnitude - minMagnitude);

                                // number of magnitude values
                                int numMag = mfd.getNum();

                                // redefine the magnitude frequency distribution
                                // conserving the total rate
                                // and using the new b value
                                double totCumRate = mfd.getTotCumRate();
                                mfd =
                                        new GutenbergRichterMagFreqDist(bValue,
                                                totCumRate, minMagnitude,
                                                maxMagnitude, numMag);
                            }

                            // if tapering has been applied convert mfd from GR
                            // to IncrementalMagFreqDist
                            // because in this way in the xml the rates are
                            // explicitly saved. Because after
                            // applying the tapering the mfd is not anymore pure
                            // GR
                            if (mTaper > 5.0 && mTaper < 8.0) {
                                IncrementalMagFreqDist MFD =
                                        new IncrementalMagFreqDist(
                                                mfd.getMinX(), mfd.getNum(),
                                                mfd.getDelta());
                                // loop over values
                                for (int iv = 0; iv < mfd.getNum(); iv++) {
                                    MFD.set(iv, mfd.getY(iv));
                                }
                                mfdList[ifm] = MFD;

                            } else {
                                mfdList[ifm] = mfd;
                            }

                            // define focal mechanism
                            FocalMechanism fm = new FocalMechanism();
                            // dip and rake
                            // from appendix D of the USGS documentation I
                            // understood that
                            // strike-slip faults (rake=0) have dip=90,
                            // whereas normal (rake=-90) or reverse (rake=90)
                            // faults have
                            // fixed dip = 50.
                            if (ifs == 0) { // strike-slip
                                fm.setStrike(strike);
                                fm.setRake(0.0);
                                fm.setDip(90.0);
                            } else if (ifs == 1) { // reverse
                                fm.setStrike(strike);
                                fm.setRake(90.0);
                                fm.setDip(50.0);
                            } else if (ifs == 2) { // normal
                                fm.setStrike(strike);
                                fm.setRake(-90.0);
                                fm.setDip(90.0);
                            }

                            fmList[ifm] = fm;

                            ifm = ifm + 1;

                        }

                    } // end loop over focal mechanism

                    boolean includeSrc = false;
                    // if the source is inside the region of interest take it
                    if (latSrc >= latmin - borderThickness
                            && latSrc <= latmax + borderThickness
                            && lonSrc >= lonmin - borderThickness
                            && lonSrc <= lonmax + borderThickness) {
                        includeSrc = true;
                    }

                    if (includeSrc) {

                        // define GEMGridSourceData
                        // id
                        String id = Integer.toString(indexSrc);

                        // name
                        String name = "";

                        // define HypoMagFreqDistAtLoc object for the is-th grid
                        // cell
                        HypoMagFreqDistAtLoc hmfd =
                                new HypoMagFreqDistAtLoc(mfdList, new Location(
                                        latSrc, lonSrc), fmList);

                        srcDataList.add(new GEMPointSourceData(id, name,
                                tectReg, hmfd, aveRupTopVsMag, aveHypoDepth));

                        indexSrc = indexSrc + 1;

                    }
                } // end if rate !=0

            } // end loop over sources

        } catch (IOException e) {
            e.printStackTrace();
        }

    }

    // constructor that takes multiple input grid models and merge them. This
    // constructor can be used
    // only when the different input models differ only for the MFD
    // the constructor checks only that the sources are located in the same
    // point. The user must make sure
    // that the two sources differ only for the MFD, but have the same focal
    // mechanism and top of rupture
    // depth distribution.
    public NshmpGrid2GemSourceData(ArrayList<String> inputFile,
            TectonicRegionType tectReg, ArrayList<Double> fileWeight,
            double latmin, double latmax, double lonmin, double lonmax,
            boolean bigEndian2LittleEndian) throws FileNotFoundException {

        srcDataList = new ArrayList<GEMSourceData>();

        // number of models
        int numModels = inputFile.size();

        // read first model
        NshmpGrid2GemSourceData model =
                new NshmpGrid2GemSourceData(inputFile.get(0), tectReg,
                        fileWeight.get(0), latmin, latmax, lonmin, lonmax,
                        bigEndian2LittleEndian);

        // number of sources in the first model
        int numSources = model.getList().size();

        // loop over the remaining models
        for (int i = 1; i < numModels; i++) {

            // read model
            NshmpGrid2GemSourceData currentModel =
                    new NshmpGrid2GemSourceData(inputFile.get(i), tectReg,
                            fileWeight.get(i), latmin, latmax, lonmin, lonmax,
                            bigEndian2LittleEndian);

            // loop over sources
            for (int is = 0; is < numSources; is++) {

                double lat =
                        ((GEMPointSourceData) model.getList().get(is))
                                .getHypoMagFreqDistAtLoc().getLocation()
                                .getLatitude();
                double lon =
                        ((GEMPointSourceData) model.getList().get(is))
                                .getHypoMagFreqDistAtLoc().getLocation()
                                .getLongitude();
                double currLat =
                        ((GEMPointSourceData) currentModel.getList().get(is))
                                .getHypoMagFreqDistAtLoc().getLocation()
                                .getLatitude();
                double currLon =
                        ((GEMPointSourceData) currentModel.getList().get(is))
                                .getHypoMagFreqDistAtLoc().getLocation()
                                .getLongitude();

                // check at least that the two sources are located in the same
                // place
                if (lat != currLat || lon != currLon) {
                    System.out
                            .println("ERROR!! Sources to be merged are not in the same position!");
                    System.exit(0);
                }

                // loop over focal mechanisms
                for (int ifm = 0; ifm < ((GEMPointSourceData) model.getList()
                        .get(is)).getHypoMagFreqDistAtLoc().getNumFocalMechs(); ifm++) {

                    // array list storing mfds for each magnitude model
                    ArrayList<IncrementalMagFreqDist> mfds =
                            new ArrayList<IncrementalMagFreqDist>();

                    mfds.add(((GEMPointSourceData) model.getList().get(is))
                            .getHypoMagFreqDistAtLoc().getMagFreqDist(ifm));
                    mfds.add(((GEMPointSourceData) currentModel.getList().get(
                            is)).getHypoMagFreqDistAtLoc().getMagFreqDist(ifm));

                    // find lowest and highest mag from mfds
                    // find also the lowest dmag
                    double lowestMag = Double.MAX_VALUE;
                    double highestMag = 0;
                    double lowestDeltaM = Double.MAX_VALUE;
                    for (int imfd = 0; imfd < mfds.size(); imfd++) {
                        IncrementalMagFreqDist mfd = mfds.get(imfd);
                        if (mfd.getMaxX() > highestMag)
                            highestMag = mfd.getMaxX();
                        if (mfd.getMinX() < lowestMag)
                            lowestMag = mfd.getMinX();
                        if (mfd.getDelta() < lowestDeltaM)
                            lowestDeltaM = mfd.getDelta();
                    }

                    // calculate number of magnitude values
                    int num = 0;
                    if (lowestDeltaM != 0) {
                        num =
                                (int) Math.round((highestMag - lowestMag)
                                        / lowestDeltaM) + 1;
                    } else {
                        lowestDeltaM = dM;
                        num =
                                (int) Math.round((highestMag - lowestMag)
                                        / lowestDeltaM) + 1;
                    }

                    SummedMagFreqDist finalMFD =
                            new SummedMagFreqDist(lowestMag, num, lowestDeltaM);
                    for (int iv = 0; iv < mfds.size(); iv++) {
                        // add mfds conserving total moment rate
                        finalMFD.addResampledMagFreqDist(mfds.get(iv), false);
                    }

                    // replace
                    ((GEMPointSourceData) model.getList().get(is))
                            .getHypoMagFreqDistAtLoc().getMagFreqDistList()[ifm] =
                            finalMFD;

                } // end loop over focal mechanisms

            } // end loop over sources

        } // end loop over models

        srcDataList.addAll(model.getList());

    }

    private String relativePath(String inputFile, String relatedFile) {
        System.out.println("Processing file: " + relatedFile);
        return inputFile.substring(0, inputFile.lastIndexOf("/") + 1)
                + relatedFile;
    }

    /**
     * compute total moment rate as done by NSHMP code
     * 
     * @param minMag
     *            : minimum magnitude (rounded to multiple of deltaMag and moved
     *            to bin center)
     * @param numMag
     *            : number of magnitudes
     * @param deltaMag
     *            : magnitude bin width
     * @param aVal
     *            : incremental a value (defined with respect to deltaMag)
     * @param bVal
     *            : b value
     * @return
     */

    private double totMoRate(double minMag, int numMag, double deltaMag,
            double aVal, double bVal) {
        double moRate = 0;
        double mag;
        for (int imag = 0; imag < numMag; imag++) {
            mag = minMag + imag * deltaMag;
            moRate += Math.pow(10, aVal - bVal * mag + 1.5 * mag + 9.05);
        }
        return moRate;
    }

    // for testing
    public static void main(String[] args) throws IOException {

        // directory for grid seismicity files
        String inDir = "../../data/nshmp/wus_grids/";
        inDir = "../../data/nshmp/south_east_asia/grid/";

        String inFile = "CAmapC_21.in";
        inFile = "suma-java.shallow.highQ.in";

        NshmpGrid2GemSourceData model =
                new NshmpGrid2GemSourceData(inDir + inFile,
                        TectonicRegionType.STABLE_SHALLOW, 1.0, -90.0, 90.0,
                        -180.0, 180.0, false);

        model.writeGridSources2KMLfile(new FileWriter(
                "/Users/damianomonelli/Desktop/SumatraGrid.kml"), 0.1);

    }
}