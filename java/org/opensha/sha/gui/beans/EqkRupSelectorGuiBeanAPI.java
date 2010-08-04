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

package org.opensha.sha.gui.beans;

import org.opensha.commons.geo.Location;
import org.opensha.commons.param.ParameterAPI;
import org.opensha.commons.param.ParameterList;
import org.opensha.commons.param.editor.ParameterEditor;
import org.opensha.commons.param.editor.ParameterListEditor;
import org.opensha.sha.earthquake.EqkRupture;

/**
 * <p>Title: EqkRupSelectorGuiBeanAPI</p>
 * <p>Description: This class defines methods that any class providing the
 * user the functionality of getting EqkRupture to EqkRupSelectorGuiBean.</p>
 * @author : Ned Field, Nitin Gupta and Vipin Gupta
 * @since Dec 03,2004
 * @version 1.0
 */

public interface EqkRupSelectorGuiBeanAPI {

    /**
     *
     * @returns the Hypocenter Location if selected else return null
     */
    public Location getHypocenterLocation();


    /**
     *
     * @returns the panel which allows user to select Eqk rupture from existing
     * ERF models
     */
    public EqkRupSelectorGuiBeanAPI getEqkRuptureSelectorPanel();



    /**
     *
     * @returns the Metadata String of parameters that constitute the making of this
     * ERF_RupSelectorGUI  bean.
     */
    public String getParameterListMetadataString();

    /**
     *
     * @returns the timespan Metadata for the selected Rupture.
     * If no timespan exists for the rupture then it returns the Message:
     * "No Timespan exists for the selected Rupture".
     */
    public String getTimespanMetadataString();

    /**
     *
     * @returns the EqkRupture Object
     */
    public EqkRupture getRupture();

    /**
     *
     * @param paramName
     * @returns the parameter from the parameterList with paramName.
     */
    public ParameterAPI getParameter(String paramName);

    /**
     *
     * @param paramName
     * @returns the ParameterEditor associated with paramName
     */
    public ParameterEditor getParameterEditor(String paramName);

    /**
     *
     * @returns the visible parameters in the list
     */
    public ParameterList getVisibleParameterList();

    /**
     *
     * @returns the parameterlist editor
     */
    public ParameterListEditor getParameterListEditor();


  }
