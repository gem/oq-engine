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

package org.opensha.sha.imr.attenRelImpl.SA_InterpolatedWrapperAttenRel;

import org.opensha.commons.param.event.ParameterChangeWarningListener;
import org.opensha.sha.imr.attenRelImpl.BA_2008_AttenRel;

/**
 * <b>Title:</b> InterpolatedBA_2008_AttenRel<p>
 *
 * <b>Description:</b> 
 * 
 * @author     Edward H. Field
 * @created    June, 2010
 * @version    1.0
 */


public class InterpolatedBA_2008_AttenRel
    extends InterpolatedSA_AttenRelWrapper {

  // Debugging stuff
  public final static String SHORT_NAME = "Interp"+BA_2008_AttenRel.SHORT_NAME;
  private static final long serialVersionUID = 1234567890987654353L;
  public final static String NAME = "Interpolated "+BA_2008_AttenRel.NAME;

  /**
   *  This initializes several ParameterList objects.
   */
  public InterpolatedBA_2008_AttenRel(ParameterChangeWarningListener warningListener) {
    super(warningListener,new BA_2008_AttenRel(warningListener));
  }
  
  /**
   * get the name of this IMR
   *
   * @returns the name of this IMR
   */
  public String getName() {
    return NAME;
  }

  /**
   * Returns the Short Name of each AttenuationRelationship
   * @return String
   */
  public String getShortName() {
    return SHORT_NAME;
  }


}
