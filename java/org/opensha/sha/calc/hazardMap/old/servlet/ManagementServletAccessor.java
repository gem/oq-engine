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
import java.net.Authenticator;
import java.net.URLConnection;
import java.util.ArrayList;

import org.dom4j.Document;
import org.dom4j.Element;
import org.opensha.commons.geo.Region;
import org.opensha.commons.gridComputing.GridResourcesList;
import org.opensha.commons.util.http.HTTPAuthenticator;
import org.opensha.sha.calc.hazardMap.old.cron.CronOperation;

public class ManagementServletAccessor extends ServletAccessor {
	
	public static final String SERVLET_URL = "http://opensha.usc.edu:8080/HazardMaps/restricted/HazardMapManagement";
	public static final String SERVLET_URL_SSL = "https://opensha.usc.edu:443/HazardMaps/restricted/HazardMapManagement";
	
	public static final String SUCCESS = "Success";
	
	boolean ssl;
	
	public ManagementServletAccessor(String url, boolean ssl) {
		super(url);
		this.ssl = ssl;
		
		Authenticator.setDefault(new HTTPAuthenticator());
	}
	
	public GridResourcesList getGridResourcesList() throws IOException, ClassNotFoundException {
		URLConnection servletConnection = this.openServletConnection(ssl);
		
		ObjectOutputStream outputToServlet = new
		ObjectOutputStream(servletConnection.getOutputStream());

		// send the operation to servlet
		System.out.println("Sending Operation...");
		outputToServlet.writeObject(ManagementServlet.OP_GET_RESOURCES);
		
		System.out.println("Closing Output...");
		outputToServlet.flush();
		outputToServlet.close();
		
		ObjectInputStream inputFromServlet = new
		ObjectInputStream(servletConnection.getInputStream());
		
		Object obj = inputFromServlet.readObject();
		
		checkHandleError("Resource List Request Failed: ", obj, inputFromServlet);
		
		GridResourcesList list = (GridResourcesList)obj;
		
		return list;
	}
	
	public ArrayList<Region> getGeographicRegiongs() throws IOException, ClassNotFoundException {
		URLConnection servletConnection = this.openServletConnection(ssl);
		
		ObjectOutputStream outputToServlet = new
		ObjectOutputStream(servletConnection.getOutputStream());

		// send the operation to servlet
		System.out.println("Sending Operation...");
		outputToServlet.writeObject(ManagementServlet.OP_GET_REGIONS);
		
		System.out.println("Closing Output...");
		outputToServlet.flush();
		outputToServlet.close();
		
		ObjectInputStream inputFromServlet = new
		ObjectInputStream(servletConnection.getInputStream());
		
		Object obj = inputFromServlet.readObject();
		
		if (obj instanceof Boolean) {
			String message = (String)inputFromServlet.readObject();
			
			throw new RuntimeException("Region List Request Failed: " + message);
		}
		
		ArrayList<Document> docs = (ArrayList<Document>)obj;
		
		ArrayList<Region> regions = new ArrayList<Region>();
		
		for (Document doc : docs) {
			Element el = doc.getRootElement().element(Region.XML_METADATA_NAME);
			Region region = Region.fromXMLMetadata(el);
			System.out.println("Loaded region: " + region.getName());
			regions.add(region);
		}
		
		return regions;
	}
	
	public String submit(Document doc) throws IOException, ClassNotFoundException {
		URLConnection servletConnection = this.openServletConnection(ssl);
		
		ObjectOutputStream outputToServlet = new
		ObjectOutputStream(servletConnection.getOutputStream());

		// send the operation to servlet
		System.out.println("Sending Operation...");
		outputToServlet.writeObject(CronOperation.OP_SUBMIT);
		
		// send the XML document
		System.out.println("Sending XML Document...");
		outputToServlet.writeObject(doc);
		
		System.out.println("Closing Output...");
		outputToServlet.flush();
		outputToServlet.close();
		
		// Receive the "destroy" from the servlet after it has received all the data
		System.out.println("Getting Input...");
		ObjectInputStream inputFromServlet = new
		ObjectInputStream(servletConnection.getInputStream());
		
		boolean success = (Boolean)inputFromServlet.readObject();
		
		String message;
		if (success) {
			message = SUCCESS;
		} else {
			message = (String)inputFromServlet.readObject();
		}

		System.out.println("Closing Input...");
		inputFromServlet.close();
		
		return message;
	}

}
