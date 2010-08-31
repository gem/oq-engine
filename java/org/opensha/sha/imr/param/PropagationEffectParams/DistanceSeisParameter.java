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
 * <b>Title:</b> DistanceSeisParameter<p>
 *
 * <b>Description:</b> Special subclass of PropagationEffectParameter.
 * This computes the closest distance to the seimogenic part of the fault;
 * that is, the closest distance to the part of the fault that is below the seimogenic
 * thickness (seisDepth); this depth is currently hardwired at 3 km, but we can add
 * setSeisDepth() and getSeisDepth() methods if desired (the setter will have to create
 * a new constraint with seisDepth as the lower bound, which can be done even if the
 * parameter has been set as non editable).  Note that if the earthquake rupture is a
 * line or point source where the depths are less than seisDepth, then the depths are
 * treated as seisDepth (e.g., for grid based forecast where all sources are put at
 * zero depth) <p>
 *
 * @see DistanceRupParameter
 * @see DistanceJBParameter
 * @author Steven W. Rock
 * @version 1.0
 */
public class DistanceSeisParameter
extends WarningDoublePropagationEffectParameter
implements WarningParameterAPI
{


	/** Class name used in debug strings */
	protected final static String C = "DistanceSeisParameter";
	/** If true debug statements are printed out */
	protected final static boolean D = false;


	/** Hardcoded name */
	public final static String NAME = "DistanceSeis";
	/** Hardcoded units string */
	private final static String UNITS = "km";
	/** Hardcoded info string */
	private final static String INFO = "Seismogenic Distance (closest distance to seismogenic part of fault surface)";

	/** Hardcoded max allowed value */
	private final static Double MAX = new Double(Double.MAX_VALUE);

	/** set default seismogenic depth. actually hard-wired for now. */
	public final static double seisDepth = 3.0;


	/**
	 * No-Arg constructor that just calls init() with null constraints.
	 * All value are allowed.
	 */
	public DistanceSeisParameter() { init(); }

	/** This constructor sets the default value.  */
	public DistanceSeisParameter(double defaultValue) { 
		init(); 
		this.setDefaultValue(defaultValue);
	}


	/** Constructor that sets up constraints. This is a constrained parameter. */
	public DistanceSeisParameter(ParameterConstraintAPI warningConstraint)
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
	public DistanceSeisParameter(ParameterConstraintAPI warningConstraint, double defaultValue)
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



	/** Initializes the constraints, name, etc. for this parameter */
	protected void init( DoubleConstraint warningConstraint){
		this.warningConstraint = warningConstraint;
		this.constraint = new DoubleConstraint(seisDepth, Double.MAX_VALUE );
		this.name = NAME;
		this.constraint.setName( this.name );
		this.constraint.setNullAllowed(false);
		this.units = UNITS;
		this.info = INFO;
		//setNonEditable();
	}

	/** Initializes the constraints, name, etc. for this parameter */
	protected void init(){ init( null ); }

	/**
	 * Note that this does not throw a warning
	 */
	protected void calcValueFromSiteAndEqkRup(){
		if( ( this.site != null ) && ( this.eqkRupture != null ) ){

			Location loc1 = site.getLocation();
			double minDistance = Double.MAX_VALUE;
			double totalDist, horzDist, vertDist;

			EvenlyGriddedSurfaceAPI rupSurf = eqkRupture.getRuptureSurface();

			// flag to project to seisDepth if only one row and depth is below seisDepth
			boolean projectToDepth = false;
			if (rupSurf.getNumRows() == 1 && rupSurf.getLocation(0,0).getDepth() < seisDepth)
				projectToDepth = true;

			// get locations to iterate over depending on dip
			ListIterator it;
			if(rupSurf.getAveDip() > 89) {
				it = rupSurf.getColumnIterator(0);
				if (rupSurf.getLocation(0,0).getDepth() < seisDepth)
					projectToDepth = true;
			}
			else
				it = rupSurf.getLocationsIterator();

			while( it.hasNext() ){

				Location loc2 = (Location)it.next();
				// ignore locations with depth less than siesDepth (unless projectToDepth=true):
				if (loc2.getDepth() >= seisDepth) {
					horzDist = LocationUtils.horzDistance(loc1, loc2);
					vertDist = LocationUtils.vertDistance(loc1, loc2);
					totalDist = horzDist * horzDist + vertDist * vertDist;
					if( totalDist < minDistance )  minDistance = totalDist;
				}
				// put a zero-depth point source at the seisDepth
				else if (projectToDepth) {
					horzDist = LocationUtils.horzDistance(loc1, loc2);
					totalDist = horzDist * horzDist + seisDepth * seisDepth;
					if( totalDist < minDistance )  minDistance = totalDist;
				}

			}
			// take square root before returning
			// Steve- is this effiecient?
			this.setValueIgnoreWarning( new Double( Math.pow ( minDistance , 0.5 ) ));

		}
		else this.setValue(null);

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

			DistanceSeisParameter param = new DistanceSeisParameter(  );
			param.info = info;
			param.value = val2;
			param.constraint = c1;
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
