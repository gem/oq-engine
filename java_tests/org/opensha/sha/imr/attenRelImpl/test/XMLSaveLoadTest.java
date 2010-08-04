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

import java.lang.reflect.InvocationTargetException;
import java.util.ArrayList;
import java.util.Iterator;

import static org.junit.Assert.*;

import org.dom4j.Document;
import org.dom4j.Element;
import org.junit.Before;
import org.junit.Test;
import org.opensha.commons.param.ParameterAPI;
import org.opensha.commons.util.XMLUtils;
import org.opensha.sha.gui.infoTools.AttenuationRelationshipsInstance;
import org.opensha.sha.imr.IntensityMeasureRelationship;
import org.opensha.sha.imr.ScalarIntensityMeasureRelationshipAPI;

public class XMLSaveLoadTest {

	private AttenuationRelationshipsInstance attenRelInst;
	
	public XMLSaveLoadTest() {
	}

	@Before
	public void setUp() {
		attenRelInst = new AttenuationRelationshipsInstance();
	}
	
	@Test
	public void testIMRSaveLoad() throws InvocationTargetException {
		ArrayList<ScalarIntensityMeasureRelationshipAPI> imrs = attenRelInst.createIMRClassInstance(null);
		
		Document doc = XMLUtils.createDocumentWithRoot();
		Element root = doc.getRootElement();
		
		for (ScalarIntensityMeasureRelationshipAPI imr : imrs) {
			System.out.println("Handling '" + imr.getName() + "'");
			imr.setParamDefaults();
			imr.toXMLMetadata(root);
			Element imrElem = root.element(IntensityMeasureRelationship.XML_METADATA_NAME);
			ScalarIntensityMeasureRelationshipAPI fromXML = (ScalarIntensityMeasureRelationshipAPI)
						IntensityMeasureRelationship.fromXMLMetadata(imrElem, null);
			imrElem.detach();
			
			Iterator<ParameterAPI<?>> it = imr.getOtherParamsIterator();
			while (it.hasNext()) {
				ParameterAPI<?> origParam = it.next();
				Object origVal = origParam.getValue();
				ParameterAPI<?> newParam = fromXML.getParameter(origParam.getName());
				Object newVal = newParam.getValue();
				if (origVal == null) {
					assertNull(newVal);
				} else {
					assertTrue(origParam.getValue().equals(newParam.getValue()));
				}
			}
		}
	}

}
