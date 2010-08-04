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

package org.opensha.sha.earthquake.rupForecastImpl.step;

import static org.junit.Assert.*;

import org.junit.Test;
import org.opensha.commons.geo.Location;
import org.opensha.sha.earthquake.ProbEqkRupture;
import org.opensha.sha.earthquake.rupForecastImpl.PointEqkSource;
import org.opensha.sha.earthquake.rupForecastImpl.step.STEP_EqkRupForecast;


/**
 * <b>Title:</b> STEPTests<p>
 *
 * <b>Description:>/b> JUnit tester for the STEP EqkRupObjects. Tests every
 * piece of functionality, included expected fail conditions. If any
 * part of the test fails, the error code is indicated. Useful to ensure
 * the accuracy and weither the class is functioning as expect. Any
 * time in the future if the internal code is changed, this class will
 * verify that the class still works as prescribed. This is called
 * unit testing in software engineering. <p>
 *
 * Note: Requires the JUnit classes to run<p>
 * Note: This class is not needed in production, only for testing.<p>
 *
 * JUnit has gained many supporters, specifically used in ANT which is a java
 * based tool that performs the same function as the make command in unix. ANT
 * is developed under Apache.<p>
 *
 * Any function that begins with test will be executed by JUnit<p>
 *
 * @author Steven W. Rock
 * @version 1.0
 */

public class TestSTEP_EqkRupForecast
{
	public TestSTEP_EqkRupForecast() {

	}

	@Test
	public void testEqualsLocation()
	{

		// make the forecast
		STEP_EqkRupForecast forecast=null;
		try{
			forecast = new STEP_EqkRupForecast();
		}catch(Exception e){
			System.out.println("No internet connection available");
		}
		String result = "java.util.GregorianCalendar[time=?,areFieldsSet=false,areAllFieldsSet=true,lenient=false,zone=sun.util.calendar.ZoneInfo[id=\"America/Los_Angeles\",offset=-28800000,dstSavings=3600000,useDaylight=true,transitions=185,lastRule=java.util.SimpleTimeZone[id=America/Los_Angeles,offset=-28800000,dstSavings=3600000,useDaylight=true,startYear=0,startMode=3,startMonth=3,startDay=1,startDayOfWeek=1,startTime=7200000,startTimeMode=0,endMode=2,endMonth=9,endDay=-1,endDayOfWeek=1,endTime=7200000,endTimeMode=0]],firstDayOfWeek=1,minimalDaysInFirstWeek=1,ERA=1,YEAR=2003,MONTH=4,WEEK_OF_YEAR=19,WEEK_OF_MONTH=2,DAY_OF_MONTH=5,DAY_OF_YEAR=125,DAY_OF_WEEK=2,DAY_OF_WEEK_IN_MONTH=1,AM_PM=1,HOUR=4,HOUR_OF_DAY=16,MINUTE=2,SECOND=58,MILLISECOND=0,ZONE_OFFSET=-28800000,DST_OFFSET=3600000]";
		//
		// Return value includes a current time value. Substring prior to that to test the non-changing portion of the result,
		// arbitrarily identified as the first 100 characters.
		assertEquals("Time doesn't match:",result.substring(0,100),forecast.getTimeSpan().getStartTimeCalendar().toString().substring(0,100));
		assertTrue("Duration in Forecast:" + forecast.getTimeSpan().getDuration(),1.0==forecast.getTimeSpan().getDuration());
		assertEquals("TimeSpan in Forecast:","Days",forecast.getTimeSpan().getDurationUnits());
		assertEquals("Number of Sources:",398,forecast.getNumSources());

		ProbEqkRupture rup;
		double rate;

		// check first one
		int index = 0;
		PointEqkSource qkSrc = (PointEqkSource) forecast.getSource(index);
		assertEquals("Number of Ruptures",41,qkSrc.getNumRuptures());

		double duration = qkSrc.getDuration();

		for(int i=0;i<qkSrc.getNumRuptures();i++)
		{
			rup = qkSrc.getRupture(i);
			Location loc = (Location) rup.getRuptureSurface().get(0,0);
			if(i==0)
			{
				assertTrue("First Rupture Lat/Long Check:" + loc.getLongitude() + " " +
						loc.getLatitude() ,(-116.325==loc.getLongitude()) && (36.525 == loc.getLatitude()));
			}
			rate = -Math.log(1-rup.getProbability())/duration;
			assertTrue("Rate must be larger than 0",rate>0.0);
			//
			// Based on knowledge of Step Rupture Models, we require a map > 0.0, although mag < 0.0 are valid seismologically
			assertTrue("Mag greater than 1.0",(float)rup.getMag() > 0);
		}
		// check last one
		index = forecast.getNumSources()-1;
		qkSrc = (PointEqkSource) forecast.getSource(index);
		assertEquals("Known number of ruptures:",41,qkSrc.getNumRuptures());
		duration = qkSrc.getDuration();
		assertTrue("Know duration:" + duration,1.0==duration);
		for(int i=0;i<qkSrc.getNumRuptures();i++)
		{
			rup = qkSrc.getRupture(i);
			Location loc = (Location) rup.getRuptureSurface().get(0,0);
			if(i==0)
			{
				assertTrue("Last Source:\n" + loc.getLongitude()+"  "+loc.getLatitude(),((-116.825==loc.getLongitude()) && (34.275==loc.getLatitude())));
			}
			rate = -Math.log(1-rup.getProbability())/duration;
			assertTrue("Rate must be larger than 0",rate>0.0);
			//
			// Based on knowledge of Step Rupture Models, we require a map > 0.0, although mag < 0.0 are valid seismologically
			assertTrue("Mag greater than 1.0",(float)rup.getMag() > 0);
		}
	}


	public static void main(String args[])
	{
		org.junit.runner.JUnitCore.runClasses(TestSTEP_EqkRupForecast.class);
	}
}
