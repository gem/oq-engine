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

package org.opensha.sha.cybershake.openshaAPIs;

import java.lang.reflect.InvocationTargetException;
import java.net.MalformedURLException;
import java.util.ArrayList;

import org.dom4j.Document;
import org.dom4j.DocumentException;
import org.dom4j.Element;
import org.opensha.commons.util.XMLUtils;
import org.opensha.sha.earthquake.EqkRupForecast;
import org.opensha.sha.earthquake.ProbEqkSource;

public class CyberShakeUCERFWrapper_ERF extends EqkRupForecast {
	
	public static final String NAME = "CyberShake UCERF 2 Wrapper";
	
	public static final String ERF_XML_FILE = "org/opensha/sha/cybershake/conf/MeanUCERF.xml";
	
	public static final int ERF_ID = 35;
	
	private EqkRupForecast erf = null;
	
	public CyberShakeUCERFWrapper_ERF() {
		super();
	}
	
	private EqkRupForecast getERF() {
		if (erf == null) {
			try {
				Document doc = XMLUtils.loadDocument(ERF_XML_FILE);
				Element root = doc.getRootElement();
				Element erfEl = root.element(XML_METADATA_NAME);
				erf = EqkRupForecast.fromXMLMetadata(erfEl);
			} catch (MalformedURLException e) {
				// TODO Auto-generated catch block
				e.printStackTrace();
			} catch (DocumentException e) {
				// TODO Auto-generated catch block
				e.printStackTrace();
			} catch (InvocationTargetException e) {
				// TODO Auto-generated catch block
				e.printStackTrace();
			}
		}
		return erf;
	}

	public int getNumSources() {
		// TODO Auto-generated method stub
		return getERF().getNumSources();
	}

	public ProbEqkSource getSource(int sourceID) {
		ProbEqkSource source = getERF().getSource(sourceID);
		
		CyberShakeProbEqkSource csSource = new CyberShakeProbEqkSource(source, sourceID, ERF_ID);
		
		return csSource;
	}

	public ArrayList getSourceList() {
		// TODO Auto-generated method stub
		return getERF().getSourceList();
	}

	public String getName() {
		// TODO Auto-generated method stub
		return NAME;
	}

	public void updateForecast() {
		getERF().updateForecast();
	}

}
