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

package org.opensha.sha.calc.hazardMap.old.cron;

import java.io.File;
import java.net.MalformedURLException;

import org.apache.log4j.Logger;
import org.dom4j.Document;
import org.dom4j.DocumentException;
import org.dom4j.Element;
import org.dom4j.io.SAXReader;
import org.opensha.commons.util.XMLUtils;

public class CronOperation {
	
	// *************
	// OPERATIONS
	// *************
	public static final String OP_SUBMIT = "submit";
	public static final String OP_CANCEL = "cancel";
	public static final String OP_DELETE = "delete";
	public static final String OP_RESTART = "restart";
	
	public static final String XML_ELEMENT_NAME = "CronOperation";
	public static final String XML_OPERATION_ATTRIBUTE_NAME = "operation";
	public static final String XML_ID_ATTRIBUTE_NAME = "id";
	
	Logger logger = HazardMapCronJob.logger;
	
	private String fileName;
	private Document document;
	
	private String operation;
	private String id = null;
	
	public CronOperation(String fileName) throws MalformedURLException, DocumentException {
		this.fileName = fileName;
		
		logger.info("Loading " + fileName);
		
		SAXReader reader = new SAXReader();
		document = reader.read(new File(fileName));
		
		// get the root element
		Element root = document.getRootElement();
		
		Element cronEl = root.element(XML_ELEMENT_NAME);
		
		operation = cronEl.attributeValue(XML_OPERATION_ATTRIBUTE_NAME);
		operation = operation.trim();
		
		if (!operation.equals(OP_SUBMIT)) {
			// if it's not the submit option, then they needed to supply an id
			id = cronEl.attributeValue(XML_ID_ATTRIBUTE_NAME);
		}
	}
	
	public String getFileName() {
		return fileName;
	}

	public Document getDocument() {
		return document;
	}

	public String getOperation() {
		return operation;
	}

	public String getID() {
		return id;
	}
	
	public static Document createDocument(String operation, String id) {
		Document doc = XMLUtils.createDocumentWithRoot();
		
		Element root = doc.getRootElement();
		
		Element cronEl = root.addElement(XML_ELEMENT_NAME);
		
		cronEl.addAttribute(XML_OPERATION_ATTRIBUTE_NAME, operation);
		cronEl.addAttribute(XML_ID_ATTRIBUTE_NAME, id);
		
		return doc;
	}
	
	public static Document appendSubmitOperation(Document doc) {
		Element root = doc.getRootElement();
		
		Element cronEl = root.addElement(XML_ELEMENT_NAME);
		
		cronEl.addAttribute(XML_OPERATION_ATTRIBUTE_NAME, OP_SUBMIT);
		
		return doc;
	}

}
