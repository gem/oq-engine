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

import org.junit.runner.RunWith;
import org.junit.runners.Suite;
import org.opensha.commons.geo.GriddedRegionTest;
import org.opensha.commons.geo.RegionTest;

@RunWith(Suite.class)
@Suite.SuiteClasses({ DataPoint2DTests.class, DataPoint2DTreeMapTests.class,
        TimeSpanTests.class, GriddedRegionTest.class, RegionTest.class })
public class DataSuite {

    public static void main(String args[]) {
        org.junit.runner.JUnitCore.runClasses(DataSuite.class);
    }
}
