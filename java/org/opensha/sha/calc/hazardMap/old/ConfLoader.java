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

package org.opensha.sha.calc.hazardMap.old;

import java.io.File;
import java.net.MalformedURLException;
import java.util.ArrayList;
import java.util.Arrays;

import org.dom4j.Document;
import org.dom4j.DocumentException;
import org.dom4j.Element;
import org.dom4j.io.SAXReader;
import org.opensha.commons.gridComputing.XMLPresetLoader;
import org.opensha.commons.util.FileNameComparator;
import org.opensha.commons.util.XMLUtils;
import org.opensha.sha.calc.hazardMap.old.cron.CronConfLoader;

public class ConfLoader {
	
	public static final String CONF_NOTIFY_ELEMENT = "Notify";
	public static final String CONF_REGIONS_PATH_ELEMENT = "GeographicRegionsPath";
	public static final String CONF_EMAIL = "email";
	
	XMLPresetLoader presets;
	String notifyEmail = "";
	CronConfLoader cronConf;
	String regionsPath;
	
	ArrayList<Document> regions = null;
	
	public ConfLoader(String confFile) throws MalformedURLException, DocumentException {
		SAXReader reader = new SAXReader();
		Document document = reader.read(new File(confFile));
		
		// get the root element
		Element root = document.getRootElement();
		
		// get the main conf element
		Element cronConfEl = root.element(CronConfLoader.CONF_MAIN_ELEMENT);
		
		Element notifyEl = root.element(CONF_NOTIFY_ELEMENT);
		if (notifyEl != null) {
			notifyEmail = notifyEl.attributeValue(CONF_EMAIL);
		}
		
		Element gridDefaultsEl = root.element(XMLPresetLoader.XML_METADATA_NAME);
		
		presets = XMLPresetLoader.fromXMLMetadata(gridDefaultsEl);
		cronConf = new CronConfLoader(cronConfEl);
		
		Element regionsEl = root.element(CONF_REGIONS_PATH_ELEMENT);
		regionsPath = regionsEl.attributeValue("value");
	}

	public XMLPresetLoader getPresets() {
		return presets;
	}

	public String getNotifyEmail() {
		return notifyEmail;
	}

	public CronConfLoader getCronConf() {
		return cronConf;
	}
	
	public ArrayList<Document> getGeographicRegionsDocs() {
		if (regions == null) {
			regions = new ArrayList<Document>();
			
			File dir = new File(regionsPath);
			
			if (dir.exists()) {
				File files[] = dir.listFiles();
				
				Arrays.sort(files, new FileNameComparator());
				
				for (File file : files) {
					if (!file.getName().toLowerCase().endsWith(".xml"))
						continue;
					try {
						Document doc = XMLUtils.loadDocument(file.getAbsolutePath());
						regions.add(doc);
						System.out.println("Loaded " + file.getName());
					} catch (Exception e) {
						// TODO Auto-generated catch block
						e.printStackTrace();
						System.out.println("Error loading " + file.getName());
					}
				}
			}
		}
		
		return regions;
	}

}
