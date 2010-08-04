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

package org.opensha.commons.metadata;

import java.io.File;
import java.lang.reflect.Constructor;
import java.lang.reflect.InvocationTargetException;
import java.net.MalformedURLException;
import java.util.ArrayList;

import org.dom4j.Document;
import org.dom4j.DocumentException;
import org.dom4j.io.SAXReader;
import org.opensha.commons.param.event.ParameterChangeWarningEvent;
import org.opensha.commons.param.event.ParameterChangeWarningListener;
import org.opensha.sha.calc.hazardMap.old.HazardMapJob;
import org.opensha.sha.earthquake.EqkRupForecast;
import org.opensha.sha.imr.IntensityMeasureRelationship;
import org.opensha.sha.imr.param.IntensityMeasureParams.PeriodParam;

public class MetadataLoader implements ParameterChangeWarningListener {

	public MetadataLoader() {
	}

	/**
	 * Creates a class instance from a string of the full class name including packages.
	 * This is how you dynamically make objects at runtime if you don't know which\
	 * class beforehand.
	 *
	 */
	public static Object createClassInstance(String className) throws InvocationTargetException{
		return createClassInstance(className, null, null);
	}
	
	/**
	 * Creates a class instance from a string of the full class name including packages.
	 * This is how you dynamically make objects at runtime if you don't know which\
	 * class beforehand.
	 *
	 */
	public static Object createClassInstance(String className, ArrayList<Object> args) throws InvocationTargetException{
		return createClassInstance(className, null, null);
	}
	
	/**
	 * Creates a class instance from a string of the full class name including packages.
	 * This is how you dynamically make objects at runtime if you don't know which\
	 * class beforehand.
	 *
	 */
	public static Object createClassInstance(String className, ArrayList<Object> args, ArrayList<String> argNames) throws InvocationTargetException{
		try {
			Object[] paramObjects;;
			Class[] params;
			if (args == null) {
				paramObjects = new Object[]{};
				params = new Class[]{};
			} else {
				paramObjects = new Object[args.size()];
				params = new Class[args.size()];
				for (int i=0; i<args.size(); i++) {
					Object obj = args.get(i);
					paramObjects[i] = obj;
					if (argNames == null) {
						params[i] = obj.getClass();
					} else {
						String name = argNames.get(i);
						params[i] = Class.forName(name);
					}
				}
			}
			
			Class newClass = Class.forName( className );
			Constructor con = newClass.getConstructor(params);
			Object obj = con.newInstance( paramObjects );
			return obj;
		} catch (InvocationTargetException e) {
			throw e;
		} catch (Exception e ) {
			throw new RuntimeException(e);
		}
	}


	public static void main(String args[]) {
		try {
			SAXReader reader = new SAXReader();
	        Document document = reader.read(new File("output.xml"));
	        IntensityMeasureRelationship imr = IntensityMeasureRelationship.fromXMLMetadata(document.getRootElement().element(IntensityMeasureRelationship.XML_METADATA_NAME), new MetadataLoader());
	        System.out.println("Name: " + imr.getName());
	        System.out.println("IMT: " + imr.getIntensityMeasure().getName());
	        System.out.println("Period: " + imr.getParameter(PeriodParam.NAME).getValue());
	        EqkRupForecast erf = EqkRupForecast.fromXMLMetadata(document.getRootElement().element(EqkRupForecast.XML_METADATA_NAME));
	        System.out.println("Name: " + erf.getName());
//	        System.out.println("Background: " + erf.getAdjustableParameterList().getParameter(UCERF2.BACK_SEIS_NAME).getValue());
//	        System.out.println("TimeSpan: " + erf.getTimeSpan().getStartTimeYear() + ", " + erf.getTimeSpan().getDuration());
	        HazardMapJob job = HazardMapJob.fromXMLMetadata(document.getRootElement().element(HazardMapJob.XML_METADATA_NAME));
	        System.out.println(job.toString());
		} catch (InvocationTargetException e) {
			e.printStackTrace();
		} catch (MalformedURLException e) {
			// TODO Auto-generated catch block
			e.printStackTrace();
		} catch (DocumentException e) {
			// TODO Auto-generated catch block
			e.printStackTrace();
		}
	}

	public void parameterChangeWarning(ParameterChangeWarningEvent event) {
		// TODO Auto-generated method stub
		
	}
}
