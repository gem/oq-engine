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

package org.opensha.nshmp.sha.calc.servlet;

import java.io.IOException;
import java.io.ObjectInputStream;
import java.io.ObjectOutputStream;
import java.util.ArrayList;

import javax.servlet.ServletException;
import javax.servlet.http.HttpServlet;
import javax.servlet.http.HttpServletRequest;
import javax.servlet.http.HttpServletResponse;

/**
 * <p>Title: HazardDataCalcServlet.java </p>
 * <p>Description: this class is called from the application. This servlet calls
 * the HazardDataCalcServletHelper which in turn calls the HazardDataCalc to
 * return the results to the application on user machine </p>
 * <p>Copyright: Copyright (c) 2002</p>
 * <p>Company: </p>
 * @author not attributable
 * @version 1.0
 */

public class HazardDataCalcServlet extends HttpServlet{
   private HazardDataCalcServletHelper hazardDataCalcServletHelper = new HazardDataCalcServletHelper();
   //Process the HTTP Get request
   public void doGet(HttpServletRequest request, HttpServletResponse response) throws
   ServletException, IOException {

     try {
       // get an input stream from the applet
       ObjectInputStream inputFromApplet = new ObjectInputStream(request.
           getInputStream());
       //get method name and method parameters
       String mathodName = (String) inputFromApplet.readObject();
       ArrayList parameters = (ArrayList) inputFromApplet.readObject();
       //  get result based on method call
       Object result = hazardDataCalcServletHelper.getResult(mathodName, parameters);
       // return the result to the applet
       ObjectOutputStream outputToApplet = new ObjectOutputStream(response.
           getOutputStream());
       outputToApplet.writeObject(result);
       outputToApplet.close();
     }catch (Exception e) {
       // report to the user whether the operation was successful or not
       e.printStackTrace();
     }
   }



   //Process the HTTP Post request
   public void doPost(HttpServletRequest request, HttpServletResponse response) throws
       ServletException, IOException {
     // call the doPost method
     doGet(request, response);
   }


}
