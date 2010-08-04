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
import java.net.URL;
import java.net.URLConnection;

public abstract class ServletAccessor {

	String url;
	
	public ServletAccessor(String url) {
		this.url = url;
	}
	
	protected URLConnection openServletConnection(boolean ssl) throws IOException {
		if (ssl) {
			throw new RuntimeException("SSL not implemented yet!");
		}
		URL servlet = new URL(url);
		System.out.println("Connecting to: " + url + " ...");
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
	
	public void checkHandleError(String message, Object obj, ObjectInputStream inputFromServlet) throws IOException, ClassNotFoundException {
		if (obj instanceof Boolean) {
			Object errorObj = inputFromServlet.readObject();
			if (errorObj instanceof Exception) {
				Exception e = (Exception)errorObj;
				
				throw new RuntimeException(e);
			} else {
				String error = (String)errorObj;
				
				throw new RuntimeException(message + error);
			}
		}
	}
}
