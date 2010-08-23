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

import java.io.Serializable;
import java.util.ArrayList;
import java.util.Calendar;
import java.util.Date;
import java.util.EventObject;
import java.util.GregorianCalendar;
import java.util.Iterator;
import java.util.ListIterator;
import java.util.TimeZone;

import org.dom4j.Attribute;
import org.dom4j.Element;
import org.opensha.commons.param.DoubleConstraint;
import org.opensha.commons.param.DoubleDiscreteConstraint;
import org.opensha.commons.param.DoubleDiscreteParameter;
import org.opensha.commons.param.DoubleParameter;
import org.opensha.commons.param.IntegerConstraint;
import org.opensha.commons.param.IntegerParameter;
import org.opensha.commons.param.ParameterList;
import org.opensha.commons.param.StringConstraint;
import org.opensha.commons.param.StringParameter;
import org.opensha.commons.param.event.ParameterChangeEvent;
import org.opensha.commons.param.event.ParameterChangeListener;
import org.opensha.commons.param.event.TimeSpanChangeListener;

/**
 *  <b>Title:</b> TimeSpan<p>
 *
 *  <b>Description:</b> This object represents a start time and a duration.<p>
 *
 * The start-time is represented with a Year, Month, Day, Hour, Minute, Second,
 * and Millisecond, all of which are stored internally with IntegerParameter objects.
 * The default constraints (range of allowed values) for these parameters are:<p>
 * <UL>
 * <LI>Year - 0 to Integer.MAX_VALUE (AD or "common erra")
 * <LI>Month - 1 to 12
 * <LI>Day - 1 to 31
 * <LI>Hour - 0 to 23
 * <LI>Minute - 0 to 59
 * <LI>Second - 0 to 59
 * <LI>Millisecond - 0 to 999
 * </UL><p>
 * <p>

 * Important Notes: 1) the Month parameter constraint here (min=1, max=12) differs from the 0-11
 * range in the java.util.GregorianCalendar object.  This means that what's returned from
 * the getStartTimeMonth() method is always one greater than what's obtained using
 * getStartTimeCalendar().get(Calendar.MONTH)). Keep this in mind if you use the setStartTimeCalendar(),
 * getStartTimeCalendar(), or getEndTimeCalendar methods.  2) the Day and Hour fields here correspond
 * to the DATE and HOUR_OF_DAY fields, respecively in java.util.GregorianCalendar (the HOUR field of
 * GregorianCalendar goes from 0 to 11 rather than 0 to 23).<p>
 *
 * The above start-time parameter constraints can be overridden using the
 * setStartTimeConstraint() method.
 *
 * The startTimePrecision field specifies the level of precision.  For example, if this
 * is set as "Days", then one cannot set or get the Hours, Minute, Second, or Millisecond
 * parameter values (and the associated methods throw exceptions).  Setting the startTimePrecsion
 * as "None" indicates that only the Duration is relevant (e.g., for a Poissonian forecast).
 * Presently one can only set the startTimePrecision in the constructor, but we could relax
 * this later.  If one gets a GregorianCalendar using the getStartTimeCalendar() method, the
 * fields that are not within the specified precision are set to their minimum
 * value.  <p>
 *
 * Before a value is returned from any one of the getStartTime*() methods, it is
 * first confirmed that the start-time parameter settings correspond to an acutual
 * date.  For example, assuming the startTimePrecision is "Months", one could execute
 * the method: setStartTime(2003,2,29).  However, when they go to get one of these
 * fields (e.g., getStartYear() or getStartMonth()) an exception will be thrown
 * because there are not 29 days in Feburary (unless it's a leap year).  This check
 * is made in the get* rather than set* methods to allow users to finish their settings
 * (e.g., in a GUI) before checking values.
 *
 * The Units on the Duration field must presently be set in the constructor, (this could be
 * relaxed later). These Units are assumed when using the getDuration() and
 * setDuration(double duration) methods.  If one wishes to get or set the duration with other
 * units (e.g., to avoid having to check what the internal units are), they can use the
 * setDuration(String units, double duration) and getDuration(String units, double duration)
 * methods, but note that the internal "chosen" units will not have changed.
 * The constraints on the units can be set using the setDurationConstraint()
 * method.  NOTE: in converting between duration units it is assumed there are 365.25 days
 * per year (correct only for durations in years that are an integer when divided by four).
 * This limitation can be fixed, but will require some thought.<p>
 *
 * Finally, one can get an end-time calendar object that corresponds to the start time
 * plus the duration (getEndTimeCalendar()).  Note, that because this invoves a duration
 * unit conversion, it is assumed that there are 365.25 days per year (see discussion
 * above).<p>
 *
 * TO DO LATER:<p>
 * Make the Duration units adjustable after construction.  This could be done by
 * allowing an "Adjustable" opting for the duration units in the constructor.  For
 * this case, make the units field of the durationParameter empty, and use the
 * value set in the durationUnitsParameter for the getDuration() and setDuration()
 * methods.  Also add durationUnitsParameter to the list returned by the
 * getAdjustableParamsList().  This raises the question of how non-default constraints
 * can be applied if the user is changing the units (perhaps only default constraints
 * can be applied in this case).  Care will be required in using the getDuration() and
 * setDuration() methods if other objects can change the units (perhaps these should
 * throw and non-usable exception).<p>
 *
 * We might need a setNonEditable() method here (e.g., to prevent ouside entities from
 * changing constraints).
 *
 *
 *
 *
 * @author     Edward Field, based on an earlier version by Sid Hellman and Steven W. Rock.
 * @created    March, 2003
 * @version    1.0
 */
public class TimeSpan implements ParameterChangeListener, Serializable {
	
	

    /**
	 * 
	 */
	private static final long serialVersionUID = -1567318877618681307L;

	/** The name of this class, used for debug statements */
    protected final static String C = "TimeSpan";
    
    public final static String XML_METADATA_NAME = "TimeSpan";

    /** Static boolean whether to print out debugging statements */
    protected final static boolean D = false;

    protected GregorianCalendar startTimeCal;

    // Start-Time Parameters
    public final static String START_YEAR = "Start Year";
    private IntegerParameter startYearParam;
    private IntegerConstraint startYearConstraint = new IntegerConstraint(0,Integer.MAX_VALUE);
    private final static Integer START_YEAR_DEFAULT = new Integer(2003);
    public final static String START_MONTH = "Start Month";
    private IntegerParameter startMonthParam;
    private IntegerConstraint startMonthConstraint = new IntegerConstraint(1,12);
    private final static Integer START_MONTH_DEFAULT = new Integer(1);
    public final static String START_DAY = "Start Day";
    private IntegerParameter startDayParam;
    private final static Integer START_DAY_DEFAULT = new Integer(1);
    private IntegerConstraint startDayConstraint = new IntegerConstraint(1,31);
    public final static String START_HOUR = "Start Hour";
    private IntegerParameter startHourParam;
    private final static Integer START_HOUR_DEFAULT = new Integer(0);
    private IntegerConstraint startHourConstraint = new IntegerConstraint(0,59);
    public final static String START_MINUTE = "Start Minute";
    private IntegerParameter startMinuteParam;
    private final static Integer START_MINUTE_DEFAULT = new Integer(0);
    private IntegerConstraint startMinuteConstraint = new IntegerConstraint(0,59);
    public final static String START_SECOND = "Start Second";
    private IntegerParameter startSecondParam;
    private final static Integer START_SECOND_DEFAULT = new Integer(0);
    private IntegerConstraint startSecondConstraint = new IntegerConstraint(0,Integer.MAX_VALUE);
    public final static String START_MILLISECOND = "Start Second";
    private IntegerParameter startMillisecondParam;
    private IntegerConstraint startMillisecondConstraint = new IntegerConstraint(0,999);
    private final static Integer START_MILLISECOND_DEFAULT = new Integer(0);

    // Misc Strings (e.g., for setting units)
    public final static String YEARS = "Years";
    public final static String MONTHS = "Months";
    public final static String DAYS = "Days";
    public final static String HOURS = "Hours";
    public final static String MINUTES = "Minutes";
    public final static String SECONDS = "Seconds";
    public final static String MILLISECONDS = "Milliseconds";
    public final static String NONE = "None";

    private final static String START_TIME_ERR = "Start-Time Precision Violation: ";

    // For Duration Units Parameter
    private final static String DURATION_UNITS = "Duration Units";
    private final static String DURATION_UNITS_DEFAULT = YEARS;
    private StringParameter durationUnitsParam;

    // For Duration Parameter
    public final static String DURATION = "Duration";
    private final static Double DURATION_DEFAULT = new Double(50.);
    private DoubleConstraint durationConstraint = new DoubleConstraint(0.0,Double.MAX_VALUE);
    private DoubleParameter durationParam;
    private DoubleDiscreteParameter discreteDurationParam;
    private boolean isDurationDiscrete;  // default is false

   // to define the maximum precision for the start time
    public final static String START_TIME_PRECISION = "Start-Time Precision";
    private String START_TIME_PRECISION_DEFAULT = YEARS;
    private StringParameter startTimePrecisionParam;

    // this vector will hold all the listeners of this time span object
    // whenver any change is made in this timespan object, all the listeners are notified
    private transient ArrayList changeListeners;


    /**
     * Constructor
     * @param startTimePrecision
     * @param durationUnits
     */
    public TimeSpan(String startTimePrecision, String durationUnits) {
      initParams();
      setStartTimePrecision(startTimePrecision);
      setDurationUnits(durationUnits);
    }



    /**
     * Initialize Parameters
     */
    private void initParams() {

      // Start Time Parameters
      startYearParam = new IntegerParameter(START_YEAR,startYearConstraint,START_YEAR_DEFAULT);
      startMonthParam = new IntegerParameter(START_MONTH,startMonthConstraint,START_MONTH_DEFAULT);
      startDayParam = new IntegerParameter(START_DAY,startDayConstraint,START_DAY_DEFAULT);
      startHourParam = new IntegerParameter(START_HOUR,startHourConstraint,START_HOUR_DEFAULT);
      startMinuteParam = new IntegerParameter(START_MINUTE,startMinuteConstraint,START_MINUTE_DEFAULT);
      startSecondParam = new IntegerParameter(START_SECOND,startSecondConstraint,START_SECOND_DEFAULT);
      startMillisecondParam = new IntegerParameter(START_MILLISECOND,startMillisecondConstraint,START_MILLISECOND_DEFAULT);

      // Duration Units Parameter
      StringConstraint durationUnitsConstraint = new StringConstraint();
      durationUnitsConstraint.addString( YEARS );
      durationUnitsConstraint.addString( DAYS );
      durationUnitsConstraint.addString( HOURS );
      durationUnitsConstraint.addString( MINUTES );
      durationUnitsConstraint.addString( SECONDS );
      durationUnitsConstraint.addString( MILLISECONDS );
      durationUnitsConstraint.setNonEditable();
      durationUnitsParam = new StringParameter(this.DURATION_UNITS,durationUnitsConstraint,DURATION_UNITS_DEFAULT);

      // Duration Parameters (continuous versus discrete; only one used at any one time)
      durationParam = new DoubleParameter(DURATION,durationConstraint,DURATION_UNITS_DEFAULT,DURATION_DEFAULT);
      discreteDurationParam = new DoubleDiscreteParameter(DURATION,DURATION_UNITS_DEFAULT,DURATION_DEFAULT);
      isDurationDiscrete = false;    // continuous is the default

      // Start Time Precision Parameter
      StringConstraint precisionConstraint = new StringConstraint();
      precisionConstraint.addString( YEARS );
      precisionConstraint.addString( MONTHS );
      precisionConstraint.addString( DAYS );
      precisionConstraint.addString( HOURS );
      precisionConstraint.addString( MINUTES );
      precisionConstraint.addString( SECONDS );
      precisionConstraint.addString( MILLISECONDS );
      precisionConstraint.addString( NONE );    // this one is for start-time independent models (e.g., Poissonian)
      precisionConstraint.setNonEditable();
      startTimePrecisionParam = new StringParameter(START_TIME_PRECISION,precisionConstraint,
                                                    START_TIME_PRECISION_DEFAULT);

      // add a listener to each of these parameter
      // various other objects like ERFs can listen to Timespan
      // whenever any parameter changes, it will notify to all the listeners
      startYearParam.addParameterChangeListener(this);
      startMonthParam.addParameterChangeListener(this);
      startDayParam.addParameterChangeListener(this);
      startHourParam.addParameterChangeListener(this);
      startMinuteParam.addParameterChangeListener(this);
      startSecondParam.addParameterChangeListener(this);
      startMillisecondParam.addParameterChangeListener(this);
      durationParam.addParameterChangeListener(this);
      discreteDurationParam.addParameterChangeListener(this);
      startTimePrecisionParam.addParameterChangeListener(this);
    }

    /**
     * This method allows one to override the default constraints for any of the
     * start-time parameters.  The name options (start-time parameter names) are:
     * "Start Year", "Start Month", "Start Day", "Start Hour", "Start Minute",
     * "Start Second", or "Start Millisecond".  Note that you cannot set the min
     * and max outside the default bounds (e.g., min and max for "Start Hour" must
     * be between 0 and 23).  Note also that this method ignores the start-time precision
     * (e.g., you can set new constraints on "Start Minute" even if the start-time
     * precision has been set as "Years").
     * @param name - the name of the start-time parameter
     * @param min - the new minimum
     * @param max - the new maximum
     */
    public void setStartTimeConstraint(String name, int min, int max) {
      // make the new constraint
      IntegerConstraint constraint = new IntegerConstraint(min,max);

      if (name.equals(START_YEAR)) {
        //check that min and max are within the originally defined constraint (absolute constraint)
        if (startYearConstraint.isAllowed(min) && startYearConstraint.isAllowed(max))
          startYearParam.setConstraint(constraint);
        else
          throw new RuntimeException("TimeSpan.setStartTimeConstraint(): max or min is outside absolute bounds for \""+
                                     name+"\"");
      }
      else if (name.equals(START_MONTH)) {
        //check that min and max are within the originally defined constraint (absolute constraint)
        if (startMonthConstraint.isAllowed(min) && startYearConstraint.isAllowed(max))
          startMonthParam.setConstraint(constraint);
        else
          throw new RuntimeException("TimeSpan.setStartTimeConstraint(): max or min is outside absolute bounds for \""+
                                     name+"\"");
      }
      else if (name.equals(START_DAY)) {
        //check that min and max are within the originally defined constraint (absolute constraint)
        if (startDayConstraint.isAllowed(min) && startYearConstraint.isAllowed(max))
          startDayParam.setConstraint(constraint);
        else
          throw new RuntimeException("TimeSpan.setStartTimeConstraint(): max or min is outside absolute bounds for \""+
                                     name+"\"");
      }
      else if (name.equals(START_HOUR)) {
        //check that min and max are within the originally defined constraint (absolute constraint)
        if (startHourConstraint.isAllowed(min) && startYearConstraint.isAllowed(max))
          startHourParam.setConstraint(constraint);
        else
          throw new RuntimeException("TimeSpan.setStartTimeConstraint(): max or min is outside absolute bounds for \""+
                                     name+"\"");
      }
      else if (name.equals(START_MINUTE)) {
        //check that min and max are within the originally defined constraint (absolute constraint)
        if (startMinuteConstraint.isAllowed(min) && startYearConstraint.isAllowed(max))
          startMinuteParam.setConstraint(constraint);
        else
          throw new RuntimeException("TimeSpan.setStartTimeConstraint(): max or min is outside absolute bounds for \""+
                                     name+"\"");
      }
      else if (name.equals(START_SECOND)) {
        //check that min and max are within the originally defined constraint (absolute constraint)
        if (startSecondConstraint.isAllowed(min) && startYearConstraint.isAllowed(max))
          startSecondParam.setConstraint(constraint);
        else
          throw new RuntimeException("TimeSpan.setStartTimeConstraint(): max or min is outside absolute bounds for \""+
                                     name+"\"");
      }
      else if (name.equals(START_MILLISECOND)) {
        //check that min and max are within the originally defined constraint (absolute constraint)
        if (startMillisecondConstraint.isAllowed(min) && startYearConstraint.isAllowed(max))
          startMillisecondParam.setConstraint(constraint);
        else
          throw new RuntimeException("TimeSpan.setStartTimeConstraint(): max or min is outside absolute bounds for \""+
                                     name+"\"");
      }
      else
        throw new RuntimeException ("TimeSpan.setStartTimeConstraint(): invalid name");
    }


    /**
     * Sets the Start-Time Precision.  Options are "Years", "Months", "Days",
     * "Hours", "Minutes", "Seconds" and "Milliseconds".  "None" can also be
     * set if the start-time is not needed (e.g., for Poissonian models).
     * @param startTimePrecision
     */
    private void setStartTimePrecision(String startTimePrecision) {
      startTimePrecisionParam.setValue(startTimePrecision);
    }

    /**
     * This returns the start-time precision's integer equivalent (0 for NONE,
     * 1 for YEARS, 2 for MONTHS, 3 for DAYS, 4 for HOURS, 5 for MINUTES, 6 for
     * SECONDS, and 7 for MILLISECONDS).
     * @return precision integer
     */
    private int getStartTimePrecInt() {
      String precisionUnitString = (String) startTimePrecisionParam.getValue();
      if(precisionUnitString.equalsIgnoreCase(NONE)) return 0;
      else if(precisionUnitString.equalsIgnoreCase(YEARS)) return 1;
      else if(precisionUnitString.equalsIgnoreCase(MONTHS)) return 2;
      else if(precisionUnitString.equalsIgnoreCase(DAYS)) return 3;
      else if(precisionUnitString.equalsIgnoreCase(HOURS)) return 4;
      else if(precisionUnitString.equalsIgnoreCase(MINUTES)) return 5;
      else if(precisionUnitString.equalsIgnoreCase(SECONDS)) return 6;
      else return 7; // milliseconds    }
    }


    /**
     * This returns the Start-Time Precision String
     * @return
     */
    public String getStartTimePrecision() {
      return (String) startTimePrecisionParam.getValue();
    }
    
    public int getStartTimeFromType(String type) {
    	if (type.equals(START_DAY))
    		return getStartTimeDay();
    	else if (type.equals(START_HOUR))
			return getStartTimeHour();
    	else if (type.equals(START_MILLISECOND))
			return getStartTimeMillisecond();
    	else if (type.equals(START_MINUTE))
			return getStartTimeMinute();
    	else if (type.equals(START_MONTH))
			return getStartTimeMonth();
    	else if (type.equals(START_SECOND))
			return getStartTimeSecond();
    	else if (type.equals(START_YEAR))
			return getStartTimeYear();
    	else
    		throw new RuntimeException("Type '" + type + "' is not a valid start time precision!");
    }


    /**
     * @return Start-time year
     * @throws RuntimeException if year is not within the start-time precision.
     */
    public int getStartTimeYear() throws RuntimeException {
      if(getStartTimePrecInt() >= 1) {
        // check the start-time parameter settings (e.g., to make sure day exists in chosen month)
        checkStartTimeValues();
        return ((Integer)startYearParam.getValue()).intValue();
      }
      else {
        String str = "cannot use the getStartTimeYear() method because start-time precision is \"";
        String prec = getStartTimePrecision();
        throw new RuntimeException(START_TIME_ERR+str+prec+"\"");
      }
    }


    /** Note that our indexing on Month goes from 1 to 12, whereas that for the
     * GregorianCalendar.MONTH goes from 0 to 11.
     * @return Start-time month
     * @throws RuntimeException if month is not within the start-time precision.
     */
    public int getStartTimeMonth() throws RuntimeException {
      if(getStartTimePrecInt() >= 2) {
        // check the start-time parameter settings (e.g., to make sure day exists in chosen month)
        checkStartTimeValues();
        return ((Integer)startMonthParam.getValue()).intValue();
      }
      else {
        String str = "cannot use the getStartTimeMonth() method because start-time precision is \"";
        String prec = getStartTimePrecision();
        throw new RuntimeException(START_TIME_ERR+str+prec+"\"");
      }
    }


    /**
     * @return Start-time day
     * @throws RuntimeException if day is not within the start-time precision.
     */
    public int getStartTimeDay() throws RuntimeException {
      if(getStartTimePrecInt() >= 3) {
        // check the start-time parameter settings (e.g., to make sure day exists in chosen month)
        checkStartTimeValues();
        return ((Integer)startDayParam.getValue()).intValue();
      }
      else {
        String str = "cannot use the getStartTimeDay() method because start-time precision is \"";
        String prec = getStartTimePrecision();
        throw new RuntimeException(START_TIME_ERR+str+prec+"\"");
      }
    }


    /**
     * @return Start-time hour
     * @throws RuntimeException if hour is not within the start-time precision.
     */
    public int getStartTimeHour() throws RuntimeException {
      if(getStartTimePrecInt() >= 4) {
        // check the start-time parameter settings (e.g., to make sure day exists in chosen month)
        checkStartTimeValues();
        return ((Integer)startHourParam.getValue()).intValue();
      }
      else {
        String str = "cannot use the getStartTimeHour() method because start-time precision is \"";
        String prec = getStartTimePrecision();
        throw new RuntimeException(START_TIME_ERR+str+prec+"\"");
      }
    }

    /**
     * @return Start-time minute
     * @throws RuntimeException if minute is not within the start-time precision.
     */
    public int getStartTimeMinute() throws RuntimeException {
      if(getStartTimePrecInt() >= 5) {
        // check the start-time parameter settings (e.g., to make sure day exists in chosen month)
        checkStartTimeValues();
        return ((Integer)startMinuteParam.getValue()).intValue();
      }
      else {
        String str = "cannot use the getStartTimeMinute() method because start-time precision is \"";
        String prec = getStartTimePrecision();
        throw new RuntimeException(START_TIME_ERR+str+prec+"\"");
      }
    }

    /**
     * @return Start-time second
     * @throws RuntimeException if second is not within the start-time precision.
     */
    public int getStartTimeSecond() throws RuntimeException {
      if(getStartTimePrecInt() >= 6) {
        // check the start-time parameter settings (e.g., to make sure day exists in chosen month)
        checkStartTimeValues();
        return ((Integer)startSecondParam.getValue()).intValue();
      }
      else {
        String str = "cannot use the getStartTimeSecond() method because start-time precision is \"";
        String prec = getStartTimePrecision();
        throw new RuntimeException(START_TIME_ERR+str+prec+"\"");
      }
    }

    /**
     * @return Start-time millisecond
     * @throws RuntimeException if millisecond is not within the start-time precision.
     */
    public int getStartTimeMillisecond() throws RuntimeException {
      if(getStartTimePrecInt() >= 7) {
        // check the start-time parameter settings (e.g., to make sure day exists in chosen month)
        checkStartTimeValues();
        return ((Integer)startMillisecondParam.getValue()).intValue();
      }
      else {
        String str = "cannot use the getStartTimeMillisecond() method because start-time precision is \"";
        String prec = getStartTimePrecision();
        throw new RuntimeException(START_TIME_ERR+str+prec+"\"");
      }
    }

    /**
     * Sets the units for the duration; presently private until we know how to
     * handle changes after instantiation.  Options are "Years", "Days", "Hours",
     * "Minutes", "Seconds", and "Milliseconds".
     * @param durationUnits
     */
    private void setDurationUnits(String durationUnits) {
      durationUnitsParam.setValue(durationUnits);
      durationParam.setUnits(durationUnits);
      discreteDurationParam.setUnits(durationUnits);
    }

    /**
     * Gets the units for the duration
     * @return
     */
    public String getDurationUnits() {
      return (String) durationUnitsParam.getValue();
    }


    /**
     * This sets the duration assuming the previously set units.
     * @param duration
     */
    public void setDuration( double duration ) {
      if(isDurationDiscrete)
        discreteDurationParam.setValue(new Double(duration));
      else
        durationParam.setValue(duration);
    }


    /**
     * This sets the duration from the units specified.  Duration-unit options
     * are "Years", "Days","Hours", "Minutes", "Seconds", or "Milliseconds".  This
     * does not change the "chosen" units held internally.
     * @param duration - in the units supplied
     * @param units - the units of the passed in duration
     */
    public void setDuration( double duration, String units ) {
      String desiredUnits = (String) durationUnitsParam.getValue();
      double newValue = convertDurationUnits(duration,units,desiredUnits);
      if(isDurationDiscrete)
         discreteDurationParam.setValue(new Double(newValue));
       else
         durationParam.setValue(newValue);
    }

    /**
     * This puts a new constraint on the duration parameter, although the new
     * min and max must be within the default values (0 and Double.MAX_VALUE,
     * respectively).
     * @param min - new minimum
     * @param max - new maximum
     */
    public void setDuractionConstraint(double min, double max) {

      // make sure new values are within the originals
      if(durationConstraint.isAllowed(min) && durationConstraint.isAllowed(min)) {
        DoubleConstraint constraint = new DoubleConstraint(min, max);
        durationParam.setConstraint(constraint);
        isDurationDiscrete = false;
      }
      else throw new RuntimeException(C+"setDuractionConstraint - negative values not allowed");

    }


    /**
     * This puts a new discrete constraint (list of doubles) on the duration
     * parameter. All the new values must be within the default values
     * (0 and Double.MAX_VALUE, respectively).
     * @param doubles - a vector of doubles
     */
    public void setDurationConstraint(ArrayList doubles) {

      // make sure new values are all positive (within the originals)
      Iterator it = doubles.iterator();
      while(it.hasNext()) {
        if( ((Double)it.next()).doubleValue() < 0  )
          throw new RuntimeException(C+"setDuractionConstraint - negative values not allowed");
      }

      DoubleDiscreteConstraint constraint = new DoubleDiscreteConstraint(doubles);
      discreteDurationParam.setConstraint(constraint);
      isDurationDiscrete = true;

    }



    /**
     * This converts the input duration in it's present units into the desired units.
     * Duration-unit options are "Years", "Days","Hours", "Minutes", "Seconds", or
     * "Milliseconds".  This assumes that there are 365.25 days per year (correct only
     * when the duration in years is an integer when divided by 4).
     * @param duration - the duration after units conversion
     * @param presentUnits - units of the input
     * @param desiredUnits - units of the output
     * @return
     */
    private double convertDurationUnits(double duration, String presentUnits, String desiredUnits ) {
      // convert the duration to milliseconds
      double msecs;
      if(presentUnits.equals(YEARS))
         msecs = duration*365.25*24*60*60*1000;
      else if(presentUnits.equals(DAYS))
         msecs = duration*24*60*60*1000;
      else if(presentUnits.equals(HOURS))
         msecs = duration*60*60*1000;
      else if(presentUnits.equals(MINUTES))
         msecs = duration*60*1000;
      else if(presentUnits.equals(SECONDS))
         msecs = duration*1000;
      else // must be milliseconds
         msecs = duration;

      // now convert to the units desired for output
      double outDur;
      if(desiredUnits.equals(YEARS))
        outDur = msecs/(365.25*24*60*60*1000);
      else if(desiredUnits.equals(DAYS))
        outDur = msecs/(24*60*60*1000);
      else if(desiredUnits.equals(HOURS))
        outDur = msecs/(60*60*1000);
      else if(desiredUnits.equals(MINUTES))
        outDur = msecs/(60*1000);
      else if(desiredUnits.equals(SECONDS))
        outDur = msecs/1000;
      else // must be milliseconds
        outDur = msecs;

      return outDur;

    }


    /**
     * Gets the duration in the default (internally specified) units
     * @return
     */
    public double getDuration() {
      if(isDurationDiscrete)
        return ((Double)discreteDurationParam.getValue()).doubleValue();
      else
        return ((Double)durationParam.getValue()).doubleValue();
    }

    /**
     * This returns the duration in the units specified (it leaves the units
     * specified internally unchanged).  Duration-unit options are "Years",
     * "Days","Hours", "Minutes", "Seconds", or "Milliseconds".
     * @param units - the desired units
     * @return
     */
    public double getDuration( String units ) {
      String presentUnits = (String) durationUnitsParam.getValue();
      double duration;
      if(isDurationDiscrete)
        duration = ((Double) discreteDurationParam.getValue()).doubleValue();
      else
        duration = ((Double) durationParam.getValue()).doubleValue();
      return convertDurationUnits(duration,presentUnits,units);
    }


    /**
     * Sets the start time if start-time precision = "Years".
     * @param year
     * @throws RuntimeException if start-time precision is not "Years"
     */
    public void setStartTime(int year) throws RuntimeException {

      if(getStartTimePrecInt() == 1)
        startYearParam.setValue(new Integer(year));
      else {
        String prec = (String) startTimePrecisionParam.getValue();
        String method = "setStartTime(int year)";
        throw new RuntimeException(START_TIME_ERR+
                                   "can't use the "+method+" method because start-time precision is \""+
                                   prec+"\"");
      }
    }

    /**
     * Sets the start time if start-time precision = "Months".
     * @params year, month
     * @throws RuntimeException if start-time precision is not "Months"
     */
    public void setStartTime(int year, int month) throws RuntimeException {

      if(getStartTimePrecInt() == 2) {
        startYearParam.setValue(new Integer(year));
        startMonthParam.setValue(new Integer(month));
      }
      else {
        String prec = (String) startTimePrecisionParam.getValue();
        String method = "setStartTime(int year, int month)";
        throw new RuntimeException(START_TIME_ERR+
                                   "can't use the "+method+" method because start-time precision is \""+
                                   prec+"\"");
      }
    }

    /**
     * Sets the start time if start-time precision = "Days".
     * @params year, month, day
     * @throws RuntimeException if start-time precision is not "Days"
     */
    public void setStartTime(int year, int month, int day) throws RuntimeException {

      if(getStartTimePrecInt() == 3) {
        startYearParam.setValue(new Integer(year));
        startMonthParam.setValue(new Integer(month));
        startDayParam.setValue(new Integer(day));
      }
      else {
        String prec = (String) startTimePrecisionParam.getValue();
        String method = "setStartTime(int year, int month, int day)";
        throw new RuntimeException(START_TIME_ERR+
                                   "can't use the "+method+" method because start-time precision is \""+
                                   prec+"\"");
      }
    }

    /**
     * Sets the start time if start-time precision = "Hours".
     * @params year, month, day, hour
     * @throws RuntimeException if start-time precision is not "Hours"
     */
    public void setStartTime(int year, int month, int day, int hour) throws RuntimeException {

      if(getStartTimePrecInt() == 4) {
        startYearParam.setValue(new Integer(year));
        startMonthParam.setValue(new Integer(month));
        startDayParam.setValue(new Integer(day));
        startHourParam.setValue(new Integer(hour));
      }
      else {
        String prec = (String) startTimePrecisionParam.getValue();
        String method = "setStartTime(int year, int month, int day, int hour)";
        throw new RuntimeException(START_TIME_ERR+
                                   "can't use the "+method+" method because start-time precision is \""+
                                   prec+"\"");
      }
    }


    /**
     * Sets the start time if start-time precision = "Minutes".
     * @params year, month, day, hour, minute
     * @throws RuntimeException if start-time precision is not "Minutes"
     */
    public void setStartTime(int year, int month, int day, int hour, int minute) throws RuntimeException {

      if(getStartTimePrecInt() == 5) {
        startYearParam.setValue(new Integer(year));
        startMonthParam.setValue(new Integer(month));
        startDayParam.setValue(new Integer(day));
        startHourParam.setValue(new Integer(hour));
        startMinuteParam.setValue(new Integer(minute));
      }
      else {
        String prec = (String) startTimePrecisionParam.getValue();
        String method = "setStartTime(int year, int month, int day, int hour, int minute)";
        throw new RuntimeException(START_TIME_ERR+
                                   "can't use the "+method+" method because start-time precision is \""+
                                   prec+"\"");
      }
    }

    /**
     * Sets the start time if start-time precision = "Seconds".
     * @params year, month, day, hour, minute, second
     * @throws RuntimeException if start-time precision is not "Seconds"
     */
    public void setStartTime(int year, int month, int day, int hour, int minute, int second) throws RuntimeException {

      if(getStartTimePrecInt() == 6) {
        startYearParam.setValue(new Integer(year));
        startMonthParam.setValue(new Integer(month));
        startDayParam.setValue(new Integer(day));
        startHourParam.setValue(new Integer(hour));
        startMinuteParam.setValue(new Integer(minute));
        startSecondParam.setValue(new Integer(second));
      }
      else {
        String prec = (String) startTimePrecisionParam.getValue();
        String method = "setStartTime(int year, int month, int day, int hour, int minute, int second)";
        throw new RuntimeException(START_TIME_ERR+
                                   "can't use the "+method+" method because start-time precision is \""+
                                   prec+"\"");
      }
    }

    /**
     * Sets the start time if start-time precision = "Milliseconds".
     * @params year, month, day, hour, minute, second, millisecond
     * @throws RuntimeException if start-time precision is not "Milliseconds"
     */
    public void setStartTime(int year, int month, int day, int hour,
                             int minute, int second, int millisecond)
                             throws RuntimeException {

      if(getStartTimePrecInt() == 7) {
        startYearParam.setValue(new Integer(year));
        startMonthParam.setValue(new Integer(month));
        startDayParam.setValue(new Integer(day));
        startHourParam.setValue(new Integer(hour));
        startMinuteParam.setValue(new Integer(minute));
        startSecondParam.setValue(new Integer(second));
        startMillisecondParam.setValue(new Integer(millisecond));
      }
      else {
        String prec = (String) startTimePrecisionParam.getValue();
        String method = "setStartTime(int year, int month, int day, int hour, int minute, int second, int millisecond)";
        throw new RuntimeException(START_TIME_ERR+
                                   "can't use the "+method+" method because start-time precision is \""+
                                   prec+"\"");
      }
    }

    /**
     * This checks whether the start-time parameter values correspond to an actaul
     * date (e.g., can't have day=29 if month=2, unless it's a leap year).
     * Currently this is done by simply rebuilding the startTimeCalendar
     * (which will throw and exception if there is a problem), but a
     * more efficient approach could be implemented later.
     * @return
     */
    private void checkStartTimeValues() {
        // for efficiency there should be an if statement here to check whether any parameters have changed
        buildStartTimeCalendar();
    }

    /**
     * This sets the Start-Time Calendar, making any fields greater than the
     * Start-Time Precision equal to defaults (usually the lowest allowed value).
     * This throws an exception if the Day is incompatable with the chosen Month
     * (and perhaps if any other problems are encountered, although I can't think
     * of any give our constraints on each parameter).
     * @throws Exception
     */
    private void buildStartTimeCalendar() throws RuntimeException {

      int year, month, day, hour, minute, second, millisecond;

      // get the precision integer
      int precisionInt = getStartTimePrecInt();

      // get a primitave for each field according to the precision

      // set the year
      if(precisionInt>0)
        year = ((Integer) startYearParam.getValue()).intValue();
      else
        year = this.START_YEAR_DEFAULT.intValue();

      // set the month (subtract one to make compatible with GregorianCalendar indexing)
      if(precisionInt>1)
        month = ((Integer) startMonthParam.getValue()).intValue()-1;
      else
        month = this.START_MONTH_DEFAULT.intValue()-1;

      // set the day
      if(precisionInt>2)
        day = ((Integer) startDayParam.getValue()).intValue();
      else
        day = this.START_DAY_DEFAULT.intValue();

      // set the hour
      if(precisionInt>3)
        hour = ((Integer) startHourParam.getValue()).intValue();
      else
        hour = this.START_HOUR_DEFAULT.intValue();

      // set the minute
      if(precisionInt>4)
        minute = ((Integer) startMinuteParam.getValue()).intValue();
      else
        minute = this.START_MINUTE_DEFAULT.intValue();

      // set the second
      if(precisionInt>5)
        second = ((Integer) startSecondParam.getValue()).intValue();
      else
        second = this.START_SECOND_DEFAULT.intValue();

      // set the millisecond
      if(precisionInt>6)
        millisecond = ((Integer) startMillisecondParam.getValue()).intValue();
      else
        millisecond = START_MILLISECOND_DEFAULT.intValue();

      // now make the calendar
      startTimeCal = new GregorianCalendar();//
      startTimeCal.setTimeZone(TimeZone.getTimeZone("GMT"));//TODO pls check, set to use same time zone
      // make this throw exceptions for bogus values (rather than fixing them  )
      startTimeCal.setLenient(false);
      startTimeCal.set(Calendar.ERA, GregorianCalendar.AD);
      startTimeCal.set(Calendar.YEAR,year);
      startTimeCal.set(Calendar.MONTH,month);
      // make sure day is valid for the chosen month
      try {
        startTimeCal.set(Calendar.DATE,day);
      } catch (Exception e) {
        throw new RuntimeException("Calendar Error: Invalid Day for the chosen Month");
      }
      startTimeCal.set(Calendar.HOUR_OF_DAY,hour);
      startTimeCal.set(Calendar.MINUTE,minute);
      startTimeCal.set(Calendar.SECOND,second);
      startTimeCal.set(Calendar.MILLISECOND,millisecond);
    }



    /**
     * This sets the start-time fields (year, month, day, hour, minute, second,
     * and millisecond) from the inpute GregorianCalendar.  Fields above
     * the start-time precision are igored.  For example, if the start-
     * time precision equals "Hour", then the year, month, day, and hour are
     * set, but the minute, second, and millisecond fields are not.  If start-
     * time precision equals "None", then none of the fields are filled in.
     * @param cal
     */
    public void setStartTime( GregorianCalendar cal ) {
      int year = cal.get(Calendar.YEAR);
      int month = cal.get(Calendar.MONTH) + 1; // our indexing starts from 1
      int day = cal.get(Calendar.DATE);
      int hour = cal.get(Calendar.HOUR_OF_DAY);
      int minute = cal.get(Calendar.MINUTE);
      int second = cal.get(Calendar.SECOND);
      int millisecond = cal.get(Calendar.MILLISECOND);
      if(getStartTimePrecInt() == 7)
        setStartTime(year,month,day,hour,minute,second,millisecond);
      else if(getStartTimePrecInt() == 6)
        setStartTime(year,month,day,hour,minute,second);
      else if(getStartTimePrecInt() == 5)
        setStartTime(year,month,day,hour,minute);
      else if(getStartTimePrecInt() == 4)
        setStartTime(year,month,day,hour);
      else if(getStartTimePrecInt() == 3)
        setStartTime(year,month,day);
      else if(getStartTimePrecInt() == 2)
        setStartTime(year,month);
      else if(getStartTimePrecInt() == 1)
        setStartTime(year);
      else {} // do nothing if getStartTimePrecInt() == 0

    }


    /**
     *  This returns an end-time GregorianCalendar representing the start time
     *  plus the duration.  Note that this correctly accounts for leap years
     * (and leap seconds?) thanks to the sophistication of the
     * java.util.GregorianCalendar object.  Note also the indexing
     * difference for the Month field (our parameter goes from 1 to 12, whereas
     * GregorianCalendar.MONTH goes from 0 to 11).
     */
    public GregorianCalendar getEndTimeCalendar() {
      if(getStartTimePrecInt() > 0) {
        // build the startTime Calendar
        buildStartTimeCalendar();
        // compute duration in mSec from the duration parameter
        Double durMsec = new Double(getDuration(MILLISECONDS));
        long endTime_mSec =  startTimeCal.getTime().getTime() + durMsec.longValue();
        GregorianCalendar cal = new GregorianCalendar();
        cal.setTime( new Date( endTime_mSec ) );
        return cal;
      }
      else {
        String str = "Can't use getEndTime() method because start-time precision = \"";
        String prec = (String) startTimePrecisionParam.getValue();
        throw new RuntimeException(START_TIME_ERR+str+prec+"\"");
      }
    }

    /**
     * This returns a ParameterList Iterator(e.g., to put in a GUI so users can set values).
     * This only includes start-time parameters that are within the chosen precision.
     * @return
     */
    public ListIterator getAdjustableParamsIterator() {
      return this.getAdjustableParams().getParametersIterator();
    }

    /**
     * This returns a ParameterList (e.g., to put in a GUI so users can set values).
     * This only includes start-time parameters that are within the chosen precision.
     * @return
     */
    public ParameterList getAdjustableParams() {
      ParameterList list = new ParameterList();

      // always add duration
      if(isDurationDiscrete)
        list.addParameter(discreteDurationParam);
      else
        list.addParameter(durationParam);

      if(getStartTimePrecInt() > 0)
        list.addParameter(startYearParam);
      if(getStartTimePrecInt() > 1)
        list.addParameter(startMonthParam);
      if(getStartTimePrecInt() > 2)
        list.addParameter(startDayParam);
      if(getStartTimePrecInt() > 3)
        list.addParameter(startHourParam);
      if(getStartTimePrecInt() > 4)
        list.addParameter(startMinuteParam);
      if(getStartTimePrecInt() > 5)
        list.addParameter(startSecondParam);
      if(getStartTimePrecInt() > 6)
        list.addParameter(startMillisecondParam);

      return list;
    }


    /**
     * This returns a GregorianCalendar representation of the start-time fields.
     * Those fields above the start-time precision are set to their defaults
     * (generally the lowest possible value).  For example, if start-time precision
     * equals "Day", then the HOUR_OF_DAY, MINUTE, SECOND, and MILLISECOND fields
     * of the returned GregorianCalendar are all set to 0.  Note also the indexing
     * difference for the Month field (our parameter goes from 1 to 12, whereas
     * GregorianCalendar.MONTH goes from 0 to 11).
     * @return
     * @throws Exception
     */
    public GregorianCalendar getStartTimeCalendar() throws RuntimeException{

      // check that requesting a calendar is valie
      if(getStartTimePrecInt() == 0) {
        String str = "cannot use the getStartTimeCalendar() method when start-time precision equals \"";
        String prec = (String) this.startTimePrecisionParam.getValue();
        throw new RuntimeException(START_TIME_ERR+str+prec+"\"");
      }

      buildStartTimeCalendar();
      return startTimeCal;
    }



    /**
     * This method will be used by ERFs to listen for changes in Timespan object
     * @param listener : Object that wants to listen to changes in Timespan object
     * listener must implement the TimeSpanChangeListener interface
     */
    public void addParameterChangeListener(TimeSpanChangeListener listener) {
      if ( changeListeners == null ) changeListeners = new ArrayList();
      if ( !changeListeners.contains( listener ) ) changeListeners.add( listener );
    }


    /**
     * this function is called whenenver any parameter changes in the params list
     * This function then notifies all the listeners about this change
     *
     * @param e
     */
    public void parameterChange(ParameterChangeEvent e) {
      // construct the new Event object
      EventObject event = new EventObject(this);
      if(changeListeners == null) return;
      int numListeners = changeListeners.size();
      // dispatch the time span change event to all the listeners
      for ( int i = 0; i < numListeners; i++ ) {
        TimeSpanChangeListener listener =
                    ( TimeSpanChangeListener ) changeListeners.get( i );
        listener.timeSpanChange( event );
      }
    }
    
    public Element toXMLMetadata(Element root) {
    	Element xml = root.addElement(TimeSpan.XML_METADATA_NAME);
    	String precision = this.getStartTimePrecision();
    	xml.addAttribute("startTimePrecision", precision);
    	
    	ArrayList<String> timeTypes = new ArrayList<String>();
    	timeTypes.add(TimeSpan.START_DAY);
    	timeTypes.add(TimeSpan.START_HOUR);
    	timeTypes.add(TimeSpan.START_MILLISECOND);
    	timeTypes.add(TimeSpan.START_MINUTE);
    	timeTypes.add(TimeSpan.START_MONTH);
    	timeTypes.add(TimeSpan.START_SECOND);
    	timeTypes.add(TimeSpan.START_YEAR);
    	
    	Element startTimes = xml.addElement("startTimes");
    	int time = 0;
    	// set day
    	for (String type : timeTypes) {
    		try {
    			time = this.getStartTimeFromType(type);
    			startTimes.addAttribute(type.replaceAll(" ", ""), time + "");
    		} catch (RuntimeException e) {
    		}
    	}
    	
    	
    	xml.addAttribute("duration", this.getDuration() + "");
    	xml.addAttribute("durationUnits", this.getDurationUnits());
    	return root;
      }
    
    public static TimeSpan fromXMLMetadata(Element el) {
    	String precision = el.attribute("startTimePrecision").getValue();
    	String units = el.attribute("durationUnits").getValue();
    	double duration = Double.parseDouble(el.attribute("duration").getValue());
    	
    	TimeSpan span = new TimeSpan(precision, units);
    	span.setDuration(duration, units);
    	Element startTimes = el.element("startTimes");
    	
    	int count = startTimes.attributeCount();
    	
    	int num = 0;
    	int year = -1;
    	int month = -1;
    	int day = -1;
    	int hour = -1;
    	int minute = -1;
    	int second = -1;
    	int millisecond = -1;
    	
    	for (int i=0; i<count; i++) {
    		Attribute att = startTimes.attribute(i);
    		if (att.getName().equals(TimeSpan.START_DAY.replaceAll(" ", ""))) {
    			day = Integer.parseInt(att.getValue());
    			num++;
    		} else if (att.getName().equals(TimeSpan.START_HOUR.replaceAll(" ", ""))) {
    			hour = Integer.parseInt(att.getValue());
    			num++;
    		} else if (att.getName().equals(TimeSpan.START_MILLISECOND.replaceAll(" ", ""))) {
    			millisecond = Integer.parseInt(att.getValue());
    			num++;
    		} else if (att.getName().equals(TimeSpan.START_MINUTE.replaceAll(" ", ""))) {
    			minute = Integer.parseInt(att.getValue());
    			num++;
    		} else if (att.getName().equals(TimeSpan.START_MONTH.replaceAll(" ", ""))) {
    			month = Integer.parseInt(att.getValue());
    			num++;
    		} else if (att.getName().equals(TimeSpan.START_SECOND.replaceAll(" ", ""))) {
    			second = Integer.parseInt(att.getValue());
    			num++;
    		} else if (att.getName().equals(TimeSpan.START_YEAR.replaceAll(" ", ""))) {
    			year = Integer.parseInt(att.getValue());
    			num++;
    		}
    	}
    	
    	if (num == 1)
    		span.setStartTime(year);
    	else if (num == 2)
    		span.setStartTime(year, month);
    	else if (num == 3)
    		span.setStartTime(year, month, day);
    	else if (num == 4)
    		span.setStartTime(year, month, day, hour);
    	else if (num == 5)
    		span.setStartTime(year, month, day, hour, minute);
    	else if (num == 6)
    		span.setStartTime(year, month, day, hour, minute, second);
    	else if (num == 7)
    		span.setStartTime(year, month, day, hour, minute, second, millisecond);
    	
    	return span;
    }
}

