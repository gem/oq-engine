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

/**
 * <b>Title:</b> DataPoint2DTestCase
 * <p>
 * 
 * <b>Description:</b> Class used by the JUnit testing harness to test the
 * DataPoint2D. This class was used to test using JUnit. For some reason
 * testEquals() fails in JUnit, but the main() test (hand coded testing) shows
 * that the DataPoint2D passes the tests. Need more exploring of JUnit.
 * <P>
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
 * @created February 20, 2002
 * @version 1.0
 */

public class DataPoint2DTests {

    /** First test DataPoint2D */
    public DataPoint2D d1;

    /** Second test DataPoint2D */
    public DataPoint2D d2;

    /** Third test DataPoint2D */
    public DataPoint2D d3;

    /** Fourth test DataPoint2D */
    public DataPoint2D d4 = null;

    /**
     * Constructor for the DataPoint2DTestCase object.
     */
    public DataPoint2DTests() {
    }

    /**
     * The JUnit setup method
     */
    @Before
    public void setUp() {
        d1 = new DataPoint2D(12.2, 11.3);
        d3 = new DataPoint2D(120.2, 111.3);
        d2 = new DataPoint2D(12.2, 11.3);

    }

    /**
     * A unit test for JUnit
     */
    @Test
    public void testEquals() {
        assertNotNull(d1);
        assertNull(d4);
        assertEquals(d1, d1);
        assertEquals(d1, d2);
        assertTrue(!(d1.equals(d3)));
        assertTrue(d1.equals(d2));
    }

}
