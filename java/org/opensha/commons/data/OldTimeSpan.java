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

package org.opensha.commons.data;

import java.util.Calendar;
import java.util.Date;
import java.util.GregorianCalendar;
import java.util.Locale;
import java.util.TimeZone;

import org.opensha.commons.exceptions.InvalidRangeException;

/**
 *  <b>Title:</b> TimeSpan<p>
 *
 *  <b>Description:</b> Represents a start time and a duration, from which you
 *  can calculate the end time of an event. This object has been created to
 *  represent a duration of some event. <p>
 *
 * @author     Sid Hellman, Steven W. Rock, and Ned Field
 * @created    February 20, 2002
 * @version    1.0
 */
@Deprecated
public class OldTimeSpan extends GregorianCalendar {

    /** The name of this class, used for debug statements */
    protected final static String C = "OldTimeSpan";
    /** Static boolean whether to print out debugging statements */
    protected final static boolean D = false;

    /** Elapsed time of the event since it's start time, in seconds. */
    protected double duration;

    /** End time of the event in milliseconds. */
    protected long endTime;

    /**
     *  No-Argument constructor. Defaults to right now as the start time, and 1
     *  second as the duration.
     */
    public OldTimeSpan() {
        super();
        duration = 1;
        endTime =  this.getTimeInMillis() + (long)(duration * 1000)  ;
    }


    /**
     *  Create a TimeSpan with a duration (seconds). Defaults to right
     *  now as the start time.
     *
     * @param  interval  duration  of the event
     */
    public OldTimeSpan( double interval ) {
        super();
        this.duration = interval;
        endTime =  this.getTimeInMillis() + (long)(duration * 1000)  ;
    }


    /**
     * Create a TimeSpan with a start date and a  duration (seconds).
     *
     * @param  cal       Start time
     * @param  interval  Interval of the event
     */
    public OldTimeSpan( GregorianCalendar cal, double duration ) {

        super(TimeZone.getDefault(), Locale.getDefault());
        this.set(ERA, AD);
        this.set(YEAR, cal.get(Calendar.YEAR));
        this.set(MONTH, cal.get(Calendar.MONTH));
        this.set(DATE, cal.get(Calendar.DATE));
        this.set(HOUR_OF_DAY, cal.get(Calendar.HOUR_OF_DAY));
        this.set(MINUTE, cal.get(Calendar.MINUTE));
        this.set(SECOND, cal.get(Calendar.SECOND));
        this.set(MILLISECOND, cal.get(Calendar.MILLISECOND));

        this.duration = duration;
        endTime =  this.getTimeInMillis() + (long)(duration * 1000)  ;

    }


    /** Sets the elapsed time of this event in seconds. */
    public void setDuration( double duration ) {
        this.duration = duration;
        endTime =  this.getTimeInMillis() + (long)(duration * 1000)  ;
    }

    /** Sets the elapsed time of this event in seconds. */
    public void setStartTime( GregorianCalendar cal ) {

        this.set(YEAR, cal.get(Calendar.YEAR));
        this.set(MONTH, cal.get(Calendar.MONTH));
        this.set(DATE, cal.get(Calendar.DATE));
        this.set(HOUR_OF_DAY, cal.get(Calendar.HOUR_OF_DAY));
        this.set(MINUTE, cal.get(Calendar.MINUTE));
        this.set(SECOND, cal.get(Calendar.SECOND));
        this.set(MILLISECOND, cal.get(Calendar.MILLISECOND));

        endTime =  this.getTimeInMillis() + (long)(duration * 1000)  ;
    }

    /** Sets the end time of this event in seconds. */
    public void setEndTime( GregorianCalendar cal ) throws InvalidRangeException{

        String S = C + ": setEndTime():";

        long start = this.getTime().getTime();  //1st getTime returns a Date object, second (long) milliseconds
        long end = cal.getTime().getTime();

        if( end <= start ) throw new InvalidRangeException(S + "End time cannot be before or equal to the start time");

        endTime = end;
        this.duration =  Math.round( (double) ( ( end - start ) / 1000 ) );
    }

    /** Returns the elapsed time of this event in seconds. */
    public double getDuration() { return duration; }


    /**
     *  create a TimeSpan with a date and a time length (num seconds).
     *
     * @param  cal       Start time
     * @param  interval  Interval of the event
     */
    public GregorianCalendar getEndTime(  ) {
        GregorianCalendar cal = new GregorianCalendar();
        cal.setTime( new Date( endTime ) );
        return cal;
    }

    /** Returns the start time of this event */
    public GregorianCalendar getStartTime(  ) { return (GregorianCalendar)this; }


    // this is temporary for testing purposes
    public static void main(String[] args) {
      GregorianCalendar cal = new GregorianCalendar(2000,1,1,1,1,1);
      double dur = 3600;
      OldTimeSpan tspan = new OldTimeSpan(cal,dur);
      GregorianCalendar calEnd = tspan.getEndTime();
      System.out.println(cal.toString());
      System.out.print("Start: Year: "+cal.get(Calendar.YEAR)+"; ");
      System.out.print("Month: "+cal.get(Calendar.MONTH)+"; ");
      System.out.print("Day: "+cal.get(Calendar.DATE)+"; ");
      System.out.print("Hour: "+cal.get(Calendar.HOUR_OF_DAY)+"; ");
      System.out.print("Min: "+cal.get(Calendar.MINUTE)+"; ");
      System.out.print("Sec: "+cal.get(Calendar.SECOND)+"; \n");

      System.out.print("End:   Year: "+calEnd.get(Calendar.YEAR)+"; ");
      System.out.print("Month: "+calEnd.get(Calendar.MONTH)+"; ");
      System.out.print("Day: "+calEnd.get(Calendar.DATE)+"; ");
      System.out.print("Hour: "+calEnd.get(Calendar.HOUR_OF_DAY)+"; ");
      System.out.print("Min: "+calEnd.get(Calendar.MINUTE)+"; ");
      System.out.print("Sec: "+calEnd.get(Calendar.SECOND)+"; \n");
    }
}

