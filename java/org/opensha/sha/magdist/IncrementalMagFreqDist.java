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

package org.opensha.sha.magdist;

import org.opensha.commons.calc.MomentMagCalc;
import org.opensha.commons.data.function.EvenlyDiscretizedFunc;
import org.opensha.commons.exceptions.DataPoint2DException;
import org.opensha.commons.exceptions.DiscretizedFuncException;
import org.opensha.commons.exceptions.InvalidRangeException;

/**
 * <p>
 * Title:IncrementalMagFreqDist
 * </p>
 * <p>
 * Description:This class give the rate of earthquakes (number per year) in
 * succesion
 * </p>
 * 
 * @author : Nitin Gupta Date:July 26,2002
 * @version 1.0
 */

public class IncrementalMagFreqDist extends EvenlyDiscretizedFunc implements
        IncrementalMagFreqDistAPI, java.io.Serializable {

    // for Debug purposes
    private boolean D = false;

    protected String defaultInfo;
    protected String defaultName;

    /**
     * todo constructors
     * 
     * @param min
     * @param num
     * @param delta
     *            using the parameters we call the parent class constructors to
     *            initialise the parent class variables
     */
    public IncrementalMagFreqDist(double min, int num, double delta)
            throws InvalidRangeException {
        super(min, num, delta);
        setTolerance(delta / 1000000);
    }

    /**
     * todo constructors
     * 
     * @param min
     * @param max
     * @param num
     *            using the min, max and num we calculate the delta
     */
    public IncrementalMagFreqDist(double min, double max, int num)
            throws DiscretizedFuncException, InvalidRangeException {
        super(min, max, num);
        setTolerance(delta / 1000000);
    }

    /**
     * This function finds IncrRate for the given magnitude
     * 
     * @param mag
     * @return
     */
    public double getIncrRate(double mag) throws DataPoint2DException {
        int xIndex = getXIndex(mag);
        return getIncrRate(xIndex);
    }

    /**
     * This function finds the IncrRate at the given index
     * 
     * @param index
     * @return
     */
    public double getIncrRate(int index) {
        return getY(index);
    }

    /**
     * This function finds the cumulative Rate at a specified magnitude (the
     * rate greater than and equal to that mag)
     * 
     * @param mag
     * @return
     */
    public double getCumRate(double mag) throws DataPoint2DException {
        return getCumRate(getXIndex(mag));
    }

    /**
     * This function finds the cumulative Rate at a specified index (the rate
     * greater than and equal to that index)
     * 
     * @param index
     * @return
     */

    public double getCumRate(int index) {
        double sum = 0.0;
        for (int i = index; i < num; ++i)
            sum += getIncrRate(i);
        return sum;
    }

    /**
     * This function finds the moment Rate at a specified magnitude
     * 
     * @param mag
     * @return
     */

    public double getMomentRate(double mag) throws DataPoint2DException {
        return getIncrRate(mag) * MomentMagCalc.getMoment(mag);
    }

    /**
     * This function finds the moment Rate at a specified index
     * 
     * @param index
     * @return
     */

    public double getMomentRate(int index) {
        return getIncrRate(index) * MomentMagCalc.getMoment(getX(index));
    }

    /**
     * This function return the sum of all the moment rates as a double variable
     * 
     * @return
     */

    public double getTotalMomentRate() {
        double sum = 0.0;
        for (int i = 0; i < num; ++i)
            sum += getMomentRate(i);
        return sum;
    }

    /**
     * This function returns the sum of all the incremental rate as the double
     * varibale
     * 
     * @return
     */

    public double getTotalIncrRate() {
        double sum = 0.0;
        for (int i = 0; i < num; ++i)
            sum += getIncrRate(i);
        return sum;
    }

    /**
     * This function normalises the values of all the Incremental rate at each
     * point, by dividing each one by the totalIncrRate, so that after
     * normalization the sum addition of all incremental rate at each point
     * comes to be 1.
     */

    public void normalizeByTotalRate() throws DataPoint2DException {
        double totalIncrRate = getTotalIncrRate();
        for (int i = 0; i < num; ++i) {
            double newRate = getIncrRate(i) / totalIncrRate;
            super.set(i, newRate);
        }
    }

    /**
     * This returns the object of the class EvenlyDiscretizedFunc which contains
     * all the points with Cum Rate Distribution (the rate greater than and
     * equal to each magnitude)
     * 
     * @return
     */

    public EvenlyDiscretizedFunc getCumRateDist() throws DataPoint2DException {
        EvenlyDiscretizedFunc cumRateDist =
                new EvenlyDiscretizedFunc(minX, num, delta);
        double sum = 0.0;
        for (int i = num - 1; i >= 0; --i) {
            sum += getIncrRate(i);
            cumRateDist.set(i, sum);
        }
        cumRateDist.setInfo(this.getInfo());
        cumRateDist.setName(this.getName());
        return cumRateDist;
    }

    /**
     * This returns the object of the class EvenlyDiscretizedFunc which contains
     * all the points with Cum Rate Distribution (the rate greater than and
     * equal to each magnitude). It differs from getCumRateDist() in the X
     * Values because the values are offset by delta/2 in the CumDist returned
     * by this method.
     * 
     * @return
     */

    public EvenlyDiscretizedFunc getCumRateDistWithOffset()
            throws DataPoint2DException {
        EvenlyDiscretizedFunc cumRateDist =
                new EvenlyDiscretizedFunc(minX - delta / 2, num, delta);
        double sum = 0.0;
        for (int i = num - 1; i >= 0; --i) {
            sum += getIncrRate(i);
            cumRateDist.set(i, sum);
        }
        cumRateDist.setInfo(this.getInfo());
        cumRateDist.setName(this.getName());
        return cumRateDist;
    }

    /**
     * This returns the object of the class EvenlyDiscretizedFunc which contains
     * all the points with Moment Rate Distribution
     * 
     * @return
     */

    public EvenlyDiscretizedFunc getMomentRateDist()
            throws DataPoint2DException {
        EvenlyDiscretizedFunc momentRateDist =
                new EvenlyDiscretizedFunc(minX, num, delta);
        for (int i = num - 1; i >= 0; --i) {
            momentRateDist.set(i, getMomentRate(i));
        }
        momentRateDist.setInfo(this.getInfo());
        momentRateDist.setName(this.getName());
        return momentRateDist;
    }

    /**
     * Using this function each data point is scaled to ratio of specified
     * newTotalMomentRate and oldTotalMomentRate.
     * 
     * @param newTotMoRate
     */

    public void scaleToTotalMomentRate(double newTotMoRate)
            throws DataPoint2DException {
        double oldTotMoRate = getTotalMomentRate();
        if (D)
            System.out.println("old Mo. Rate = " + oldTotMoRate);
        if (D)
            System.out.println("target Mo. Rate = " + newTotMoRate);
        double scaleRate = newTotMoRate / oldTotMoRate;
        for (int i = 0; i < num; ++i) {
            super.set(i, scaleRate * getIncrRate(i));
        }
        if (D)
            System.out.println("actual Mo. Rate = " + getTotalMomentRate());

    }

    /**
     * Using this function each data point is scaled to the ratio of the CumRate
     * at a given magnitude and the specified rate.
     * 
     * @param mag
     * @param rate
     */

    public void scaleToCumRate(double mag, double rate)
            throws DataPoint2DException {
        int index = getXIndex(mag);
        scaleToCumRate(index, rate);
    }

    /**
     * Using this function each data point is scaled to the ratio of the CumRate
     * at a given index and the specified rate
     * 
     * @param index
     * @param rate
     */

    public void scaleToCumRate(int index, double rate)
            throws DataPoint2DException {
        double temp = getCumRate(index);
        double scaleCumRate = rate / temp;
        for (int i = 0; i < num; ++i)
            super.set(i, scaleCumRate * getIncrRate(i));
    }

    /**
     * Using this function each data point is scaled to the ratio of the
     * IncrRate at a given magnitude and the specified newRate
     * 
     * @param mag
     * @param newRate
     */

    public void scaleToIncrRate(double mag, double newRate)
            throws DataPoint2DException {
        int index = getXIndex(mag);
        scaleToIncrRate(index, newRate);
    }

    /**
     * Using this function each data point is scaled to the ratio of the
     * IncrRate at a given index and the specified newRate
     * 
     * @param index
     * @param newRate
     */

    public void scaleToIncrRate(int index, double newRate)
            throws DataPoint2DException {
        double temp = getIncrRate(index);
        double scaleIncrRate = newRate / temp;
        for (int i = 0; i < num; ++i)
            super.set(i, scaleIncrRate * getIncrRate(i));
    }

    /**
     * Returns the default Info String for the Distribution
     * 
     * @return String
     */
    public String getDefaultInfo() {
        return defaultInfo;
    }

    /**
     * Returns the default Name for the Distribution
     * 
     * @return String
     */
    public String getDefaultName() {
        defaultName = "Incremental Mag Freq Dist";
        return defaultName;
    }

    /**
     * Returns the Name of the Distribution that user has set from outside, if
     * it is null then it returns the default Name from the distribution. Makes
     * the call to the parent "getName()" method to get the metadata set outside
     * the application.
     * 
     * @return String
     */
    public String getName() {
        if (name != null && !(name.trim().equals("")))
            return super.getName();
        return getDefaultName();
    }

    /**
     * Returns the info of the distribution that user has set from outside, if
     * it is null then it returns the default info from the distribution. Makes
     * the call to the parent "getInfo()" method to get the metadata set outside
     * the application.
     * 
     * @return String
     */
    public String getInfo() {
        if (info != null && !(info.trim().equals("")))
            return super.getInfo();
        return getDefaultInfo();
    }

    /** Returns a copy of this and all points in this DiscretizedFunction */
    public IncrementalMagFreqDist deepClone() throws DataPoint2DException {

        IncrementalMagFreqDist f = new IncrementalMagFreqDist(minX, num, delta);

        f.tolerance = tolerance;
        f.setInfo(this.getInfo());
        f.setName(this.getName());
        for (int i = 0; i < num; i++)
            f.set(i, points[i]);

        return f;
    }

    /**
     * This returns the maximum magnitude with a non-zero rate
     * 
     * @return
     */
    public double getMaxMagWithNonZeroRate() {
        for (int i = num - 1; i >= 0; i--) {
            if (getY(i) > 0)
                return getX(i);
        }
        return -1;
    }

}
