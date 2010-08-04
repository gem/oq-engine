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

package org.opensha.commons.data.function;

import java.util.Comparator;
import java.util.Iterator;

import org.opensha.commons.data.DataPoint2D;
import org.opensha.commons.data.DataPoint2DComparatorAPI;
import org.opensha.commons.param.ParameterList;



/**
 * <b>Title:</b> ArbDiscrFuncWithParams<p>
 *
 * <b>Description:</b> Subclass of the ArbitrarlyDiscretizedFunc that
 * also includes a ParameterList of paramters associated with the
 * function. Not much different that parent class but provides methods
 * for dealing with the parameter list and overides such methods as
 * toString(), equals(), etc. These extra methods are put in an interface
 * FuncWithParamsAPI. Therefore this class implements that
 * interface as well as the DiscretizedFuncAPI.<p>
 *
 * This function implements FuncWithParamsAPI so it maintains a
 * ParameterList internally. These parameters are the values of
 * the input variables that went into calculating this function.<p>
 *
 * @see DiscretizedFunction2D
 * @see XYDiscretizedFunction2DAPI
 * @see DiscretizedFunction2DAPI
 * @see ParameterList
 * @author Steven W. Rock
 * @version 1.0
 */
public class ArbDiscrFuncWithParams
    extends ArbitrarilyDiscretizedFunc
    implements FuncWithParamsAPI
{


    /**
     * This parameter list is the set of parameters that went into
     * calculation this DiscretizedFunction. Useful for determining if two
     * data sets are the same, i.e. have the same x/y axis and the same
     * set of independent parameters. Bypasses the more numerically intensive
     * task of comparing each DataPoint2D of two DiscretizedFunction2D.
     */
    protected ParameterList list = new ParameterList();


    /**
     * The passed in comparator must be an implementor of DataPoint2DComparatorAPI.
     * These comparators know they are dealing with a DataPoint2D and usually
     * only compare the x-values for sorting. Special comparators may wish to
     * sort on both the x and y values, i.e. the data points are geographical
     * locations.
     */
    public ArbDiscrFuncWithParams(Comparator comparator) { super(comparator); }

    /**
     * The passed in comparator must be an implementor of DataPoint2DComparatorAPI.
     * These comparators know they are dealing with a DataPoint2D and usually
     * only compare the x-values for sorting. Special comparators may wish to
     * sort on both the x and y values, i.e. the data points are geographical
     * locations.
     */
    public ArbDiscrFuncWithParams(DataPoint2DComparatorAPI comparator) { super(comparator); }

    /**
     *  Easiest one to use, uses the default DataPoint2DToleranceComparator comparator.
     */
    public ArbDiscrFuncWithParams(double tolerance) { super(tolerance); }


    /**
     *  basic No-Arg constructor
     */
    public ArbDiscrFuncWithParams() { super(); }

    /**
     * Sets all values for this special type of DiscretizedFunction
     */
    public ArbDiscrFuncWithParams( ParameterList list ) {
        super();
        this.list = list;
    }





    // **********************************
    /** @todo  Data Accessors / Setters */
    // **********************************

    /**
     * Returns the info of this function. This subclass proxys this method to the
     * lsit by returning list.toString(). THis is useful for plot legends,
     * comparisions, etc.
     *
     * These field getters and setters provide the basic information to describe
     * a function. All functions have a name, information string,
     * and a tolerance level that specifies how close two points
     * have to be along the x axis to be considered equal.
     */
    public String getInfo(){ return list.toString(); }

    /**
     * This parameter list is the set of parameters that went into
     * calculation this DiscretizedFunction. Useful for determining if two
     * data sets are the same, i.e. have the same x/y axis and the same
     * set of independent parameters. Bypasses the more numerically intensive
     * task of comparing each DataPoint2D of two DiscretizedFunction2D.
     */
    public ParameterList getParameterList(){ return list; }

    /** Set the parameter list from an external source */
    public void setParameterList(ParameterList list){ this.list = list; }

    /** Returns name/value pairs, separated with commas, as one string, usefule for legends, etc. */
    public String getParametersString(){ return list.toString(); }

    /** Returns true if the second function has the same named parameter values. One
     * current use is to determine if two XYDiscretizedFunction2DAPIs are the same.
     */
    public boolean equalParameterNamesAndValues(FuncWithParamsAPI function){
        if( function.getParametersString().equals( getParametersString() ) ) return true;
        else return false;
    }

    /**
     * Returns true if the second function has the same named parameters in
     * it's list, values may be different
     */
    public boolean equalParameterNames(FuncWithParamsAPI function){
        return function.getParameterList().equalNames( this.getParameterList() );
    }




    /**
     * This function returns a new copy of this list, including copies
     * of all the points. Paramters are also cloned. <p>
     *
     * A shallow clone would only create a new DiscretizedFunc
     * instance, but would maintain a reference to the original points. <p>
     *
     * Since this is a clone, you can modify it without changing the original.
     * @return
     */
    public ArbDiscrFuncWithParams deepClone(){

        ArbDiscrFuncWithParams function = new ArbDiscrFuncWithParams();
        function.setTolerance( this.getTolerance() );
        function.setInfo(getInfo());
        function.setParameterList( (ParameterList)this.getParameterList().clone() );

        Iterator it = this.getPointsIterator();
        if( it != null ) {
            while(it.hasNext()) {
                function.set( (DataPoint2D)((DataPoint2D)it.next()).clone() );
            }
        }

        return function;

    }

    /**
     * Determines if two functions are the same with respect to the parameters that
     * were used to calculate the function, NOT THAT EACH POINT IS THE SAME. This is used
     * by the DiscretizedFunction2DAPIList to determine if it should add a new function
     * to the list.
     */
    public boolean equalParameters(FuncWithParamsAPI function){
        String S = C + ": equalParameters():";
        return function.getParameterList().equals( this.list );
    }

}
