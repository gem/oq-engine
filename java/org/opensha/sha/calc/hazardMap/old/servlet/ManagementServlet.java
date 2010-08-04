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

package org.opensha.sha.calc.hazardMap.old.servlet;

import java.io.IOException;
import java.io.ObjectInputStream;
import java.io.ObjectOutputStream;

import javax.servlet.ServletException;
import javax.servlet.http.HttpServletRequest;
import javax.servlet.http.HttpServletResponse;

import org.dom4j.Document;
import org.dom4j.Element;
import org.opensha.commons.gridComputing.XMLPresetLoader;
import org.opensha.commons.util.XMLUtils;
import org.opensha.sha.calc.hazardMap.old.HazardMapJob;
import org.opensha.sha.calc.hazardMap.old.cron.CronOperation;

public class ManagementServlet extends ConfLoadingServlet {
	
	public static final String NAME = "ManagementServlet";
	
	public static final String OP_GET_RESOURCES = "GetResources";
	public static final String OP_GET_REGIONS = "GetRegoins";
	
	public ManagementServlet() {
		super(NAME);
	}
	
	// Process the HTTP Get request
	public void doGet(HttpServletRequest request, HttpServletResponse response) throws ServletException, IOException {
		
		debug("Handling GET");
		
		// get an input stream from the applet
		ObjectInputStream in = new ObjectInputStream(request.getInputStream());
		ObjectOutputStream out = new ObjectOutputStream(response.getOutputStream());

		// get the function desired by the user
		String functionDesired = null;
		try {
			debug("Reading Operation");
			functionDesired  = (String) in.readObject();
			
			if (confLoader == null) {
				fail(out, "Failed to load server configuration file.");
				return;
			}
			
			if (functionDesired.equals(CronOperation.OP_SUBMIT)) {
				debug("Handling SUBMIT Operation");
				handleSubmit(in, out);
			} else if (functionDesired.equals(CronOperation.OP_CANCEL)) {
				debug("Handling STOP Operation");
				handleSimpleOp(in, out, CronOperation.OP_CANCEL);
			} else if (functionDesired.equals(CronOperation.OP_DELETE)) {
				debug("Handling DELETE Operation");
				handleSimpleOp(in, out, CronOperation.OP_DELETE);
			} else if (functionDesired.equals(CronOperation.OP_RESTART)) {
				debug("Handling RESTART Operation");
				handleSimpleOp(in, out, CronOperation.OP_RESTART);
			} else if (functionDesired.equals(OP_GET_RESOURCES)) {
				debug("Handling GET_RESOURCES Operation");
				handleGetResources(in, out);
			} else if (functionDesired.equals(OP_GET_REGIONS)) {
				debug("Handling GET_REGIONS Operation");
				handleGetRegions(in, out);
			} else {
				fail(out, "Unknown request: " + functionDesired);
				return;
			}
		} catch (ClassNotFoundException e) {
			e.printStackTrace(System.out);
			fail(out, "ClassNotFoundException: " + e.getMessage());
			return;
		}
	}
	
	private void success(ObjectOutputStream out) throws IOException {
		debug("Sending 'Success' message!");
		out.writeObject(new Boolean(true));
		out.close();
		debug("Request handled successfully");
	}
	
	private void handleGetResources(ObjectInputStream in, ObjectOutputStream out) throws IOException {
		XMLPresetLoader presets = this.confLoader.getPresets();
		
		try {
			out.writeObject(presets.getGridResourcesList());
			
			out.close();
		} catch (Exception e) {
			// TODO Auto-generated catch block
			e.printStackTrace();
			fail(out, e.getMessage());
		}
	}
	
	private void handleGetRegions(ObjectInputStream in, ObjectOutputStream out) throws IOException {
		try {
			out.writeObject(this.confLoader.getGeographicRegionsDocs());
			
			out.close();
		} catch (Exception e) {
			// TODO Auto-generated catch block
			e.printStackTrace();
			fail(out, e.getMessage());
		}
	}
	
	private void handleSubmit(ObjectInputStream in, ObjectOutputStream out) throws IOException {
		try {
			Document doc = (Document)in.readObject();
			
			doc = CronOperation.appendSubmitOperation(doc);
			
			Element root = doc.getRootElement();
			
			Element jobEl = root.element(HazardMapJob.XML_METADATA_NAME);
			
			HazardMapJob job = HazardMapJob.fromXMLMetadata(jobEl);
			
			checkAppendEmail(job, root, jobEl);
			
			String fileName = getJobFileName();
			
			debug("Writing job file to " + fileName);
			XMLUtils.writeDocumentToFile(fileName, doc);
			
//			debug("Logging cron start message");
//			HazardMapJobCreator.logMessage(StatusServlet.getLogFileName(job.getJobID()), HazardMapJobCreator.STATUS_CRON_IN);
			
			success(out);
		} catch (Exception e) {
			e.printStackTrace(System.out);
			fail(out, e.getMessage());
		}
	}
	
	private void checkAppendEmail(HazardMapJob job, Element root, Element jobEl) {
		debug("Starting e-mail check...");
		
		String jobEmail = job.getEmail();
		
		String notifyEmail = this.confLoader.getNotifyEmail();
		
		if (notifyEmail.length() == 0) {
			debug("No notify e-mail found...");
			return;
		}
		
		// if the e-mail's not already going to the notifier
		if (!jobEmail.toLowerCase().contains(notifyEmail.toLowerCase())) {
			debug("Appending " + notifyEmail + " to job e-mail list");
			job.setEmail(jobEmail + "," + notifyEmail);
			
			jobEl.detach();
			
			root = job.toXMLMetadata(root);
		} else {
			debug(notifyEmail + " is already being notified!");
		}
	}
	
	private String getJobFileName() {
		return confLoader.getCronConf().getInDir() + System.currentTimeMillis() + ".xml";
	}
	
	private void handleSimpleOp(ObjectInputStream in, ObjectOutputStream out, String operation) throws IOException, ClassNotFoundException {
		String id = (String)in.readObject();
		
		try {
			Document doc = CronOperation.createDocument(operation, id);
			
			String fileName = getJobFileName();
			
			XMLUtils.writeDocumentToFile(fileName, doc);
			
			success(out);
		} catch (RuntimeException e) {
			fail(out, e.getMessage());
		}
	}
}
