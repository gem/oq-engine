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

package org.opensha.refFaultParamDb.gui.view;

import org.opensha.refFaultParamDb.vo.CombinedEventsInfo;
import org.opensha.refFaultParamDb.vo.PaleoSite;

/**
 * <p>Title: SiteSelectionAPI.java </p>
 * <p>Description: this API is implemented by any class which needs to listen
 * to site selection events. </p>
 * <p>Copyright: Copyright (c) 2002</p>
 * <p>Company: </p>
 * @author not attributable
 * @version 1.0
 */

public interface SiteSelectionAPI {
  /**
   * Whenever a user selects a site, this function is called in the listener class
   * @param siteId
   */
  public void siteSelected(PaleoSite paleoSite, int referenceId);

  /**
   * Get the CombinedInfo which is currently displayed/selected by the user
   * @return
   */
  public CombinedEventsInfo getSelectedCombinedInfo();
}
