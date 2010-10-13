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

package org.opensha.commons.data;

import static org.junit.Assert.*;

import org.junit.Before;
import org.junit.Test;
import org.opensha.commons.data.DataPoint2D;
import org.opensha.commons.data.DataPoint2DTreeMap;

/**
 * <p>
 * Title: TestDataPoint2DTreeMap
 * </p>
 * <p>
 * Description: JUnit tester class that verifies the DataPoint2DTreeMap class is
 * functioning properly.
 * </p>
 * 
 * Note: Requires the JUnit classes to run
 * <p>
 * Note: This class is not needed in production, only for testing.
 * <p>
 * 
 * JUnit has gained many supporters, specifically used in ANT which is a java
 * based tool that performs the same function as the make command in unix. ANT
 * is developed under Apache.
 * <p>
 * 
 * Any function that begins with test will be executed by JUnit
 * <p>
 * 
 * @author Steven W. Rock
 * @version 1.0
 */
public class DataPoint2DTreeMapTests {

    DataPoint2DTreeMap map = new DataPoint2DTreeMap();
    double tolerance = 0.001;

    public DataPoint2DTreeMapTests() {
    }

    @Before
    public void setUp() {
        map = new DataPoint2DTreeMap();
        map.setTolerance(tolerance);
    }

    @Test
    public void testClear() {

        map.clear();
        map.put(new DataPoint2D(1.0, 2.0));
        assertTrue(map.size() > 0);
        map.clear();
        assertTrue(map.size() == 0);
    }

    @Test
    public void testPut() {
        DataPoint2D key1 = new DataPoint2D(1.0, 2.0);
        map.put(key1);
    }

    @Test
    public void testGetTolerance() {
        double doubleRet = map.getTolerance();
        assertTrue(tolerance == doubleRet);
    }

    @Test
    public void testGet() {

        map.clear();
        int i = 0, j = 0;
        for (; i < 20;) {

            DataPoint2D point = new DataPoint2D(i, j);
            map.put(point);

            i++;
            j++;

        }

        i = 0;
        for (; i < 20; i++) {

            DataPoint2D point = map.get(i);
            // System.out.println("Point: " + point.toString());
            assertTrue(point.getX() == i);
            assertTrue(point.getY() == i);

        }

    }

    @Test
    public void testGetMaxY() {
        double doubleRet = map.getMaxY();
    }

    @Test
    public void testGetMinY() {
        double doubleRet = map.getMinY();
    }

    @Test
    public void testSetTolerance() {
        double newTolerance1 = tolerance;
        try {
            map.setTolerance(newTolerance1);

        } catch (Exception e) {
            System.err.println("Exception thrown:  " + e);
        }
    }
}
