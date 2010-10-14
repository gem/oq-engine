/*******************************************************************************
 * Copyright 2009 OpenSHA.org in partnership with the Southern California
 * Earthquake Center (SCEC, http://www.scec.org) at the University of Southern
 * California and the UnitedStates Geological Survey (USGS; http://www.usgs.gov)
 * 
 * Licensed under the Apache License, Version 2.0 (the "License"); you may not
 * use this file except in compliance with the License. You may obtain a copy of
 * the License at
 * 
 * http://www.apache.org/licenses/LICENSE-2.0
 * 
 * Unless required by applicable law or agreed to in writing, software
 * distributed under the License is distributed on an "AS IS" BASIS, WITHOUT
 * WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied. See the
 * License for the specific language governing permissions and limitations under
 * the License.
 ******************************************************************************/

package org.opensha.sha.earthquake;

import org.opensha.commons.exceptions.InvalidRangeException;
import org.opensha.commons.geo.Location;
import org.opensha.sha.faultSurface.EvenlyGriddedSurfaceAPI;

/**
 * <p>
 * Title:ProbEqkRupture
 * </p>
 * <p>
 * Description: Probabilistic Earthquake Rupture
 * </p>
 * 
 * @author Nitin Gupta & Vipin Gupta
 * @date aug 27, 2002
 * @version 1.0
 */

public class ProbEqkRupture extends EqkRupture {

    protected double probability;

    // index of rupture for a given source as defined by a ERF
    private int rupIndex, srcIndex;
    // name of the source of which this rupture is a part.
    private String srcName;

    /* ********************* */
    /** @todo Constructors */
    /* ********************* */

    public ProbEqkRupture() {
        super();
    }

    public ProbEqkRupture(double mag, double aveRake, double probability,
            EvenlyGriddedSurfaceAPI ruptureSurface, Location hypocenterLocation)
            throws InvalidRangeException {

        super(mag, aveRake, ruptureSurface, hypocenterLocation);
        this.probability = probability;

    }

    public double getProbability() {
        return probability;
    }

    public void setProbability(double p) {
        probability = p;
    }

    /**
     * This is a function of probability and duration
     */
    public double getMeanAnnualRate(double duration) {
        return -Math.log(1 - probability) / duration;
    }

    public String getInfo() {
        String info1, info2;
        info1 =
                new String("\tMag. = " + (float) mag + "\n" + "\tAve. Rake = "
                        + (float) aveRake + "\n" + "\tProb. = "
                        + (float) probability + "\n" + "\tAve. Dip = "
                        + (float) ruptureSurface.getAveDip() + "\n"
                        + "\tHypocenter = " + hypocenterLocation + "\n");

        // write our rupture surface information
        if (ruptureSurface.getNumCols() == 1
                && ruptureSurface.getNumRows() == 1) {
            Location loc = ruptureSurface.getLocation(0, 0);
            info2 =
                    new String(
                            "\tPoint-Surface Location (lat, lon, depth (km):"
                                    + "\n\n" + "\t\t"
                                    + (float) loc.getLatitude() + ", "
                                    + (float) loc.getLongitude() + ", "
                                    + (float) loc.getDepth());
        } else {
            Location loc1 = ruptureSurface.getLocation(0, 0);
            Location loc2 =
                    ruptureSurface.getLocation(0,
                            ruptureSurface.getNumCols() - 1);
            Location loc3 =
                    ruptureSurface.getLocation(ruptureSurface.getNumRows() - 1,
                            0);
            Location loc4 =
                    ruptureSurface.getLocation(ruptureSurface.getNumRows() - 1,
                            ruptureSurface.getNumCols() - 1);
            info2 =
                    new String(
                            "\tRup. Surf. Corner Locations (lat, lon, depth (km):"
                                    + "\n\n" + "\t\t"
                                    + (float) loc1.getLatitude()
                                    + ", "
                                    + (float) loc1.getLongitude()
                                    + ", "
                                    + (float) loc1.getDepth()
                                    + "\n"
                                    + "\t\t"
                                    + (float) loc2.getLatitude()
                                    + ", "
                                    + (float) loc2.getLongitude()
                                    + ", "
                                    + (float) loc2.getDepth()
                                    + "\n"
                                    + "\t\t"
                                    + (float) loc3.getLatitude()
                                    + ", "
                                    + (float) loc3.getLongitude()
                                    + ", "
                                    + (float) loc3.getDepth()
                                    + "\n"
                                    + "\t\t"
                                    + (float) loc4.getLatitude()
                                    + ", "
                                    + (float) loc4.getLongitude()
                                    + ", "
                                    + (float) loc4.getDepth() + "\n");
        }
        return info1 + info2;
    }

    /**
     * Sets the rupture index from given source.
     * 
     * @param sourceIndex
     *            int source of the rupture
     * @param sourceName
     *            String Name of the Source
     * @param ruptureIndex
     *            int rupture index of the given source
     * 
     */
    public void setRuptureIndexAndSourceInfo(int sourceIndex,
            String sourceName, int ruptureIndex) {
        srcIndex = sourceIndex;
        srcName = sourceName;
        rupIndex = ruptureIndex;
    }

    /**
     * Returns the rupture index as defined by the Source
     * 
     * @return int
     */
    public int getRuptureIndex() {
        return rupIndex;
    }

    /**
     * Returns the Metadata for the rupture of a given source. Following
     * information is represented as a single line for the rupture.
     * <ul>
     * <li>Source Index
     * <li>Rupture Index
     * <li>Magnitude
     * <li>Probablity
     * <li>Ave. Rake
     * <p>
     * If rupture surface is a point surface then point surface locations are
     * included in it.So the next 3 elements are :
     * </p>
     * <li>Point Surface Latitude
     * <li>Point Surface Longitude
     * <li>Point Surface Depth
     * <li>Source Name
     * </ul>
     * 
     * Each element in the single line is seperated by a tab ("\t").
     * 
     * @return String
     */
    public String getRuptureMetadata() {
        // rupture Metadata
        String ruptureMetadata;
        ruptureMetadata = srcIndex + "\t";
        ruptureMetadata += rupIndex + "\t";
        ruptureMetadata += (float) mag + "\t";
        ruptureMetadata += (float) probability + "\t";
        ruptureMetadata += (float) aveRake + "\t";
        ruptureMetadata += (float) ruptureSurface.getAveDip() + "\t";
        ruptureMetadata += "\"" + srcName + "\"";
        return ruptureMetadata;

    }

    /**
     * Clones the eqk rupture and returns the new cloned object
     * 
     * @return
     */
    public Object clone() {
        ProbEqkRupture eqkRuptureClone = new ProbEqkRupture();
        eqkRuptureClone.setAveRake(this.aveRake);
        eqkRuptureClone.setMag(this.mag);
        eqkRuptureClone.setRuptureSurface(this.ruptureSurface);
        eqkRuptureClone.setHypocenterLocation(this.hypocenterLocation);
        eqkRuptureClone.setProbability(this.probability);
        return eqkRuptureClone;
    }

}
