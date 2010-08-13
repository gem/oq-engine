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

package org.opensha.sha.imr.param.PropagationEffectParams;

import java.util.ListIterator;

import org.dom4j.Element;
import org.opensha.commons.exceptions.ConstraintException;
import org.opensha.commons.geo.Location;
import org.opensha.commons.geo.LocationUtils;
import org.opensha.commons.param.DoubleConstraint;
import org.opensha.commons.param.ParameterConstraintAPI;
import org.opensha.commons.param.WarningParameterAPI;
import org.opensha.sha.faultSurface.EvenlyGriddedSurfaceAPI;


/**
 * <b>Title:</b> DistanceRupParameter<p>
 *
 * <b>Description:</b> Special subclass of PropagationEffectParameter.
 * This finds the shortest distance to the fault surface. <p>
 *
 * @see DistanceJBParameter
 * @see DistanceSeisParameter
 * @author Steven W. Rock
 * @version 1.0
 */
public class DistRupMinusJB_OverRupParameter
     extends WarningDoublePropagationEffectParameter
     implements WarningParameterAPI
{


    /** Class name used in debug strings */
    protected final static String C = "DistanceRupMinusJB_Parameter";
    /** If true debug statements are printed out */
    protected final static boolean D = false;


    /** Hardcoded name */
    public final static String NAME = "(distRup-distJB)/distRup";
    /** Hardcoded info string */
    public final static String INFO = "(DistanceRup - DistanceJB)/DistanceRup";
    /** Hardcoded min allowed value */
    private final static Double MIN = new Double(0.0);
    /** Hardcoded max allowed value */
    private final static Double MAX = new Double(1.0);


    /** No-Arg constructor that calls init(). No constraint so all values are allowed.  */
    public DistRupMinusJB_OverRupParameter() { init(); }
    
	/** This constructor sets the default value.  */
	public DistRupMinusJB_OverRupParameter(double defaultValue) { 
		init(); 
		this.setDefaultValue(defaultValue);
	}



    /** Constructor that sets up constraints. This is a constrained parameter. */
    public DistRupMinusJB_OverRupParameter(ParameterConstraintAPI warningConstraint)
        throws ConstraintException
    {
        if( ( warningConstraint != null ) && !( warningConstraint instanceof DoubleConstraint) ){
            throw new ConstraintException(
                C + " : Constructor(): " +
                "Input constraint must be a DoubleConstraint"
            );
        }
        init( (DoubleConstraint)warningConstraint );
    }
    
    /** Constructor that sets up constraints & the default value. This is a constrained parameter. */
    public DistRupMinusJB_OverRupParameter(ParameterConstraintAPI warningConstraint, double defaultValue)
        throws ConstraintException
    {
        if( ( warningConstraint != null ) && !( warningConstraint instanceof DoubleConstraint) ){
            throw new ConstraintException(
                C + " : Constructor(): " +
                "Input constraint must be a DoubleConstraint"
            );
        }
        init( (DoubleConstraint)warningConstraint );
        setDefaultValue(defaultValue);
    }


    /** Sets default fields on the Constraint,  such as info and units. */
    protected void init( DoubleConstraint warningConstraint){
        this.warningConstraint = warningConstraint;
        this.constraint = new DoubleConstraint(MIN, MAX );
        this.constraint.setNullAllowed(false);
        this.name = NAME;
        this.constraint.setName( this.name );
        this.info = INFO;
        //setNonEditable();
    }

    /** Sets the warning constraint to null, then initializes the absolute constraint */
    protected void init(){ init( null ); }


    /**
     * Note that this doesn not throw a warning
     */
    protected void calcValueFromSiteAndEqkRup(){
        if( ( this.site != null ) && ( this.eqkRupture != null ) ){

            Location loc1 = site.getLocation();
            double minRupDistance = Double.MAX_VALUE;
            double minHorzDistance = Double.MAX_VALUE;
            double horzDist, vertDist, totalDist;

            EvenlyGriddedSurfaceAPI rupSurf = eqkRupture.getRuptureSurface();
            
			// get locations to iterate over depending on dip
			ListIterator it;
			if(rupSurf.getAveDip() > 89)
				it = rupSurf.getColumnIterator(0);
			else
				it = rupSurf.getLocationsIterator();
			

            while( it.hasNext() ){

                Location loc2 = (Location) it.next();

                horzDist = LocationUtils.horzDistance(loc1, loc2);
                vertDist = LocationUtils.vertDistance(loc1, loc2);

                totalDist = horzDist * horzDist + vertDist * vertDist;
                if( totalDist < minRupDistance ) minRupDistance = totalDist;
                if( horzDist < minHorzDistance ) minHorzDistance = horzDist;

            }
            totalDist = Math.sqrt( minRupDistance );
            if(totalDist == 0)
              this.setValueIgnoreWarning( new Double( 0 ));
            else{
              double fract = (totalDist - minHorzDistance) / totalDist;
              this.setValueIgnoreWarning(new Double(fract));
            }
        }
        else this.value = null;


    }

    /** This is used to determine what widget editor to use in GUI Applets.  */
    public String getType() {
        String type = "DoubleParameter";
        // Modify if constrained
        ParameterConstraintAPI constraint = this.constraint;
        if (constraint != null) type = "Constrained" + type;
        return type;
    }


    /**
     *  Returns a copy so you can't edit or damage the origial.<P>
     *
     * Note: this is not a true clone. I did not clone Site or ProbEqkRupture.
     * PE could potentially have a million points, way to expensive to clone. Should
     * not be a problem though because once the PE and Site are set, they can not
     * be modified by this class. The clone has null Site and PE parameters.<p>
     *
     * This will probably have to be changed in the future once the use of a clone is
     * needed and we see the best way to implement this.
     *
     * @return    Exact copy of this object's state
     */
    public Object clone() {

        DoubleConstraint c1 = null;
        DoubleConstraint c2 = null;

        if( constraint != null ) c1 = ( DoubleConstraint ) constraint.clone();
        if( warningConstraint != null ) c2 = ( DoubleConstraint ) warningConstraint.clone();

        Double val = null, val2 = null;
        if( value != null ) {
            val = ( Double ) this.value;
            val2 = new Double( val.doubleValue() );
        }

        DistRupMinusJB_OverRupParameter param = new DistRupMinusJB_OverRupParameter(  );
        param.value = val2;
        param.constraint =  c1;
        param.warningConstraint = c2;
        param.name = name;
        param.info = info;
        param.site = site;
        param.eqkRupture = eqkRupture;
        if( !this.editable ) param.setNonEditable();
        return param;
    }


	public boolean setIndividualParamValueFromXML(Element el) {
		// TODO Auto-generated method stub
		return false;
	}

}
