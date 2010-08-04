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

package org.opensha.refFaultParamDb.gui.infotools;

import java.io.ObjectInputStream;
import java.io.ObjectOutputStream;
import java.net.URL;
import java.net.URLConnection;

import org.opensha.refFaultParamDb.servlets.RefFaultDB_UpdateEmailServlet;

/**
 * <p>Title: ConnectToEmailServlet.java </p>
 * <p>Description: Connect to email servlet to email whenever an addition/deletion/update
 * is done to the database. </p>
 * <p>Copyright: Copyright (c) 2002</p>
 * <p>Company: </p>
 * @author not attributable
 * @version 1.0
 */

public class ConnectToEmailServlet {

  /**
   * Send email to database curator whenever a data is addded/removed/updated
   * from the database.
   *
   * @param message
   */
  public final static void sendEmail(String message) {
    try {
      URL emailServlet = new URL(RefFaultDB_UpdateEmailServlet.SERVLET_ADDRESS);

      URLConnection servletConnection = emailServlet.openConnection();

      // inform the connection that we will send output and accept input
      servletConnection.setDoInput(true);
      servletConnection.setDoOutput(true);
      // Don't use a cached version of URL connection.
      servletConnection.setUseCaches(false);
      servletConnection.setDefaultUseCaches(false);
      // Specify the content type that we will send binary data
      servletConnection.setRequestProperty("Content-Type",
                                           "application/octet-stream");
      ObjectOutputStream toServlet = new
          ObjectOutputStream(servletConnection.getOutputStream());
      //sending the email message
      toServlet.writeObject(message);
      toServlet.flush();
      toServlet.close();

      ObjectInputStream fromServlet = new
          ObjectInputStream(servletConnection.getInputStream());

      String outputFromServlet = (String) fromServlet.readObject();
      fromServlet.close();
    }catch(Exception e) {
      e.printStackTrace();
    }
  }
}
