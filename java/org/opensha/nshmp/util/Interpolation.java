/*******************************************************************************
 * Copyright 2009 OpenSHA.org in partnership with
 * the Southern California Earthquake Center (SCEC, http://www.scec.org)
 * at the University of Southern California and the UnitedStates Geological
 * Survey (USGS; http://www.usgs.gov)
 * 
 * Licensed under the Apache License, Version 2.0 (the "License");
 * you may not use this file except in compliance with the License.
 * You may obtain a copy of the License at
 * 
 *   http://www.apache.org/licenses/LICENSE-2.0
 * 
 * Unless required by applicable law or agreed to in writing, software
 * distributed under the License is distributed on an "AS IS" BASIS,
 * WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
 * See the License for the specific language governing permissions and
 * limitations under the License.
 ******************************************************************************/

package org.opensha.nshmp.util;

import org.opensha.nshmp.exceptions.InterpolationException;


/**
 * <p>Title: Interpolation</p>
 *
 * <p>Description: This class provides the generic capability of Log and Linear
 * Interpolation.</p>
 * @author Ned Field, Nitin Gupta and E.V.Leyendecker
 * @version 1.0
 */
public final class Interpolation {

  /**
   * Returns the Interpolated X Value in Linear space
   * @param x1 double
   * @param x2 double
   * @param y1 double
   * @param y2 double
   * @param y double
   * @return double
   */
  public static double getInterpolatedX(double x1, double x2, double y1,
                                        double y2, double y) {
    return (x2 - x1) / (y2 - y1) * (y - y1) + x1;
  }

  /**
   * Returns the Interpolated Y Value in Linear space
   * @param x1 double
   * @param y1 double
   * @param x2 double
   * @param y2 double
   * @param x double
   * @return double
   */
  public static double getInterpolatedY(double x1, double x2, double y1,
                                        double y2,
                                        double x) {
    return (y2 - y1) / (x2 - x1) * (x - x1) + y1;
  }

  /**
   *
   * @param x1 double
   * @param x2 double
   * @param y1 double
   * @param y2 double
   * @param y double
   * @return double
   */
  public static double getLogInterpolatedX(double x1, double x2, double y1,
                                           double y2, double y) {

    y1 = Math.log(y1);
    y2 = Math.log(y2);
    x1 = Math.log(x1);
    x2 = Math.log(x2);
    y = Math.log(y);

    double x = getInterpolatedX(x1, x2, y1, y2, y);
    return Math.exp(x);
  }

  /**
   *
   * @param x1 double
   * @param x2 double
   * @param y1 double
   * @param y2 double
   * @param y double
   * @return double
   */
  public static double getLogInterpolatedY(double x1, double x2, double y1,
                                           double y2, double x) {

    y1 = Math.log(y1);
    y2 = Math.log(y2);
    x1 = Math.log(x1);
    x2 = Math.log(x2);
    x = Math.log(x);

    double y = getInterpolatedY(x1, x2, y1, y2, x);
    return Math.exp(y);
  }

  /**
   * Returns the interpolated value at a given point.
   * It can do bi-linear interpolation only for the rectangular region.
   * x1y1 is considered the SW point of the region
   * x1y2 is considered the NW point of the region
   * x2y1 is considered the SE point of the region
   * x2y2 is considered the NE point of the region
   * Values for these 4 corner points should be in same order
   * xy is the point in the region where we have to find the interpolated z value.
   * @param x1 double
   * @param y1 double
   * @param x2 double
   * @param y2 double
   * @param z1 double[] : Values at each of the 4 points in the region
   * @param x double
   * @param y double
   * @return double
   * @throws InterpolationException
   */
  public static double getBilinearInterpolatedY(double x1, double y1, double x2,
                                                double y2, double[] z1,
                                                double x, double y) throws
      InterpolationException {

    int zLength = z1.length;

    if (zLength != 4) {
      throw new InterpolationException(
          "Must provide correct inputs for Z for Bilinear interpolation.\n" +
          "It takes 4 elements");
    }

    double interpolatedX = (x - x1) / (x2 - x1);
    double interpolatedY = (y - y1) / (y2 - y1);

    double interpolatedZ1 = getValForBilinearInterpolation(z1[0], z1[1],
        interpolatedY);
    double interpolatedZ2 = getValForBilinearInterpolation(z1[2], z1[3],
        interpolatedY);

    double interpolatedZ = getValForBilinearInterpolation(interpolatedZ1,
        interpolatedZ2, interpolatedX);
    return interpolatedZ;
  }

  /*
   *
   * @param z1 double
   * @param z2 double
   * @param y double
   * @return double
   */
  private static double getValForBilinearInterpolation(double z1, double z2,
      double y) {
    return z1 + y * (z2 - z1);
  }

}
