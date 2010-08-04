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

package org.opensha.commons.data.siteData.servlet;

import java.io.IOException;
import java.io.ObjectInputStream;
import java.io.ObjectOutputStream;
import java.net.URL;
import java.net.URLConnection;
import java.util.ArrayList;

import org.opensha.commons.geo.Location;
import org.opensha.commons.geo.LocationList;

public class SiteDataServletAccessor<Element> {
	
	private String url;
	
	private int maxLocsPerRequest = 10000;
	
	public SiteDataServletAccessor(String servletURL) {
		this.url = servletURL;
	}
	
	public int getMaxLocsPerRequest() {
		return maxLocsPerRequest;
	}

	public void setMaxLocsPerRequest(int maxLocsPerRequest) {
		this.maxLocsPerRequest = maxLocsPerRequest;
	}

	public Element getValue(Location loc) throws IOException {
		return (Element)getResult(loc);
	}
	
	public Location getClosestLocation(Location loc) throws IOException {
		return (Location)getResult(loc, AbstractSiteDataServlet.OP_GET_CLOSEST);
	}
	
	public ArrayList<Element> getValues(LocationList locs) throws IOException {
		ArrayList<Element> result = null;
		
		if (maxLocsPerRequest > 0 && locs.size() > maxLocsPerRequest) {
			result = new ArrayList<Element>();
			
			int done = 0;
			int tot = locs.size();
			for (LocationList partialLocs : locs.split(maxLocsPerRequest)) {
				float frac = (float)done / (float)tot * 100f;
//				System.out.println("Requesting " + partialLocs.size() + " values (" + frac + " % done)");
				result.addAll((ArrayList<Element>)getResult(partialLocs));
				done += partialLocs.size();
			}
		} else {
//			System.out.println("Requesting " + locs.size() + " values");
			result = (ArrayList<Element>)getResult(locs);
		}
		
		return result;
	}
	
	private Object getResult(Object request) throws IOException {
		return getResult(request, null);
	}
	
	private Object getResult(Object request, String operation) throws IOException {
		URLConnection servletConnection = this.openServletConnection();
		
		ObjectOutputStream outputToServlet = new
				ObjectOutputStream(servletConnection.getOutputStream());
		
		// we have an operation to specify
		if (operation != null && operation.length() > 0) {
			outputToServlet.writeObject(operation);
		}
		
		outputToServlet.writeObject(request);
		
		ObjectInputStream inputFromServlet = new
		ObjectInputStream(servletConnection.getInputStream());
		
		try {
			Object result = inputFromServlet.readObject();
			
			checkForError(result, inputFromServlet);
			
			inputFromServlet.close();
			
			return result;
		} catch (ClassNotFoundException e) {
			throw new RuntimeException(e);
		}
	}
	
	private void checkForError(Object obj, ObjectInputStream inputFromServlet) throws IOException, ClassNotFoundException {
		if (obj instanceof Boolean) {
			String message = (String)inputFromServlet.readObject();
			
			throw new RuntimeException("Status Request Failed: " + message);
		}
	}
	
	protected URLConnection openServletConnection() throws IOException {
		URL servlet = new URL(url);
//		System.out.println("Connecting to: " + url + " ...");
		URLConnection servletConnection = servlet.openConnection();
		
		// inform the connection that we will send output and accept input
		servletConnection.setDoInput(true);
		servletConnection.setDoOutput(true);

		// Don't use a cached version of URL connection.
		servletConnection.setUseCaches (false);
		servletConnection.setDefaultUseCaches (false);
		// Specify the content type that we will send binary data
		servletConnection.setRequestProperty ("Content-Type","application/octet-stream");
		
		return servletConnection;
	}
}
