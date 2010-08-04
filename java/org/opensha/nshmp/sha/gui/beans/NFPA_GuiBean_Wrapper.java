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

package org.opensha.nshmp.sha.gui.beans;

import java.util.ArrayList;

import org.opensha.commons.exceptions.RegionConstraintException;
import org.opensha.commons.geo.Region;
import org.opensha.nshmp.sha.gui.api.ProbabilisticHazardApplicationAPI;
import org.opensha.nshmp.util.GlobalConstants;
import org.opensha.nshmp.util.RegionUtil;

/**
 * <p>Title NFPA_GuiBean_Wrapper</p>
 *
 *<p>Description</p>
 *<p>This is a simple wrapper class that only overrides one function from
 *   the ASCE_7 gui bean.  The desired effect is that NFPA behaves just like
 *   ASCE_7.
 *@author Eric Martinez
 *@version 1.0
 */
public class NFPA_GuiBean_Wrapper extends ASCE7_GuiBean {
  public NFPA_GuiBean_Wrapper(ProbabilisticHazardApplicationAPI api) {
	  super(api);
  }

  /**
	 * Creates the Parameter that allows user to select the Editions based
	 * on the selected Analysis and chosen Geographic region.
	 */
	 protected void createEditionSelectionParameter() {
	   ArrayList supportedEditionList = new ArrayList();

		 supportedEditionList.add(GlobalConstants.NFPA_2006);
		 supportedEditionList.add(GlobalConstants.NFPA_2003);

	   datasetGui.createEditionSelectionParameter(supportedEditionList);
		 datasetGui.getEditionSelectionParameter().addParameterChangeListener(this);
		 selectedEdition = datasetGui.getSelectedDataSetEdition();
	}

	/**
	*
	* @return RectangularGeographicRegion
	*/
	protected Region getRegionConstraint() throws
		RegionConstraintException {

		if (selectedRegion.equals(GlobalConstants.CONTER_48_STATES) ||
			selectedRegion.equals(GlobalConstants.ALASKA) ||
			selectedRegion.equals(GlobalConstants.HAWAII) ||
			selectedEdition.equals(GlobalConstants.NFPA_2006)) {
			return RegionUtil.getRegionConstraint(selectedRegion);
		}

		return null;
	}
}

