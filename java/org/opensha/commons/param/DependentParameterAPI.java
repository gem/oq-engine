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

package org.opensha.commons.param;

import java.util.ListIterator;

import org.opensha.commons.exceptions.ParameterException;

/**
 * <b>Title:</b> DependentParameterAPI<p>
 *
 * <b>Description:</b> Implementation classes of this interface are
 * known as dependent parameters, i.e. it's values and/or constraints
 * depend on other independent parametes. The basic functionality is to
 * just maintain the list of parameters this depends on. There is no
 * other logic between these parameters. An implementation class will
 * maintain a list of parameters that it depends on. <p>
 *
 * This interface simply states the functions for list accessors
 * to maintain this list of independent parameters. Standard list functions
 * are implemented (paraphrasing) such as get() , set(), remove() iterator(),
 * etc. <p>
 *
 * @author Steven W. Rock
 * @version 1.0
 */
public interface DependentParameterAPI<E> extends ParameterAPI<E> {
	
	public static final String XML_INDEPENDENT_PARAMS_NAME = "IndependentParameters";

    /**
     * Returns an iterator of all indepenedent parameters this parameter
     * depends upon. Returns the parametes in the order they were added.
     */
    public ListIterator getIndependentParametersIterator();

    /**
     * Locates and returns an independent parameter from the list if it
     * exists. Throws a parameter excpetion if the requested parameter
     * is not one of the independent parameters.
     *
     * @param name  Parameter name to lookup.
     * @return      The found independent Parameter.
     * @throws ParameterException   Thrown if not one of the independent parameters.
     */
    public ParameterAPI getIndependentParameter(String name)throws ParameterException;

    /** Set's a complete list of independent parameters this parameter requires */
    public void setIndependentParameters(ParameterList list);

    /** Adds the parameter if it doesn't exist, else throws exception */
    public void addIndependentParameter(ParameterAPI parameter) throws ParameterException;

    /** Returns true if this parameter is one of the independent ones */
    public boolean containsIndependentParameter(String name);

    /** Removes the parameter if it exist, else throws exception */
    public void removeIndependentParameter(String name) throws ParameterException;

    /** Returns all the names of the independent parameters concatenated */
    public String getIndependentParametersKey();

    /** see implementation in the DependentParameter class for information */
    public String getDependentParamMetadataString();
    
    /** see implementation in the DependentParameter class for information */
    public int getNumIndependentParameters();

}
