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

package org.opensha.sha.imr.attenRelImpl.test;

import org.junit.runner.RunWith;
import org.junit.runners.Suite;;

@RunWith(Suite.class)
@Suite.SuiteClasses({
	Spudich_1999_test.class,
	Shakemap_2003_test.class,
	Abrahamson_2000_test.class,
	Abrahamson_Silva_1997_test.class,
	BJF_1997_test.class,
	CB_2003_test.class,
	SCEMY_1997_test.class,
	Campbell_1997_test.class,
	Field_2000_test.class,
	AS_2008_test.class,
	BA_2008_test.class,
	CB_2008_test.class,
	CY_2008_test.class,
	NGA08_Site_EqkRup_Tests.class
})


/**
 * <p>Title: </p>
 * <p>Description: </p>
 * <p>Copyright: Copyright (c) 2002</p>
 * <p>Company: </p>
 * @author unascribed
 * @version 1.0
 */

public class AttenRelTestsSuite {

	public static void main(String args[])
	{
		org.junit.runner.JUnitCore.runClasses(AttenRelTestsSuite.class);
	}
}
