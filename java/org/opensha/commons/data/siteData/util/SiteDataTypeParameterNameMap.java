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

package org.opensha.commons.data.siteData.util;

import java.util.Collection;
import java.util.HashMap;
import java.util.ListIterator;

import org.opensha.commons.data.siteData.SiteDataAPI;
import org.opensha.commons.data.siteData.SiteDataValue;
import org.opensha.commons.param.ParameterAPI;
import org.opensha.commons.util.NtoNMap;
import org.opensha.sha.imr.ScalarIntensityMeasureRelationshipAPI;
import org.opensha.sha.imr.attenRelImpl.Campbell_1997_AttenRel;
import org.opensha.sha.imr.param.SiteParams.Vs30_Param;
import org.opensha.sha.util.SiteTranslator;
import org.opensha.sha.util.TectonicRegionType;

/**
 * This class represents an N to N mapping between site data types and parameter names. If
 * a mapping exists, then the given parameter can be set by the given site data type. 
 * 
 * @author Kevin Milner
 *
 */
public class SiteDataTypeParameterNameMap extends NtoNMap<String, String> {
	
	public SiteDataTypeParameterNameMap() {
		super();
	}
	
	/**
	 * Add a mapping
	 * 
	 * @param type
	 * @param paramName
	 */
	public void addMapping(String type, String paramName) {
		this.put(type, paramName);
	}
	
	/**
	 * Returns a list of all site data types that can set this parameter
	 * 
	 * @param paramName
	 * @return
	 */
	public Collection<String> getTypesForParameterName(String paramName) {
		return this.getLefts(paramName);
	}
	
	/**
	 * Returns a list of all of the parameter names that can be set from this
	 * site data type
	 * 
	 * @param type
	 * @return
	 */
	public Collection<String> getParameterNamesForType(String type) {
		return this.getRights(type);
	}
	
	/**
	 * Returns true if the specified mapping exists
	 * 
	 * @param type
	 * @param paramName
	 * @return
	 */
	public boolean isValidMapping(String type, String paramName) {
		return this.containsMapping(type, paramName);
	}
	
	/**
	 * Returns true if the specified mapping exists
	 * 
	 * @param type
	 * @param paramName
	 * @return
	 */
	public boolean isValidMapping(SiteDataValue<?> value, String paramName) {
		return this.containsMapping(value.getDataType(), paramName);
	}
	
	/**
	 * Returns true if the given attenuation relationship has a parameter that can be set by
	 * this type.
	 * 
	 * @param type
	 * @param attenRel
	 * @return
	 */
	public boolean isTypeApplicable(String type, ScalarIntensityMeasureRelationshipAPI attenRel) {
		ListIterator<ParameterAPI<?>> it = attenRel.getSiteParamsIterator();
		while (it.hasNext()) {
			ParameterAPI param = it.next();
			if (isValidMapping(type, param.getName()))
				return true;
		}
		return false;
	}
	
	/**
	 * Returns true if the given IMR/Tectonic Region mapping has a parameter that can be set by
	 * this type.
	 * 
	 * @param type
	 * @param imrMap
	 * @return
	 */
	public boolean isTypeApplicable(String type,
			HashMap<TectonicRegionType, ScalarIntensityMeasureRelationshipAPI> imrMap) {
		for (TectonicRegionType trt : imrMap.keySet()) {
			ScalarIntensityMeasureRelationshipAPI imr = imrMap.get(trt);
			if (isTypeApplicable(type, imr))
				return true;
		}
		return false;
	}
	
	/**
	 * Returns true if the given attenuation relationship has a parameter that can be set by
	 * this type.
	 * 
	 * @param type
	 * @param attenRel
	 * @return
	 */
	public boolean isTypeApplicable(SiteDataValue<?> value, ScalarIntensityMeasureRelationshipAPI attenRel) {
		return isTypeApplicable(value.getDataType(), attenRel);
	}
	
	/**
	 * Returns true if the given IMR/Tectonic Region mapping has a parameter that can be set by
	 * this type.
	 * 
	 * @param type
	 * @param imrMap
	 * @return
	 */
	public boolean isTypeApplicable(SiteDataValue<?> value,
			HashMap<TectonicRegionType, ScalarIntensityMeasureRelationshipAPI> imrMap) {
		return isTypeApplicable(value.getDataType(), imrMap);
	}
	
	private void printParamsForType(String type) {
		System.out.println("***** Type: " + type);
		Collection<String> names = this.getParameterNamesForType(type);
		if (names == null) {
			System.out.println("- <NONE>");
		} else {
			for (String name : names) {
				System.out.println("- " + name);
			}
		}
	}
	
	private void printTypesForParams(String paramName) {
		System.out.println("***** Param Name: " + paramName);
		Collection<String> types = this.getTypesForParameterName(paramName);
		if (types == null) {
			System.out.println("- <NONE>");
		} else {
			for (String name : types) {
				System.out.println("- " + name);
			}
		}
	}
	
	private void printValidTest(String type, String paramName) {
		System.out.println(type + " : " + paramName + " ? " + this.isValidMapping(type, paramName));
	}
	
	public static void main(String args[]) {
		SiteDataTypeParameterNameMap map = SiteTranslator.DATA_TYPE_PARAM_NAME_MAP;
		
		map.printParamsForType(SiteDataAPI.TYPE_VS30);
		map.printParamsForType(SiteDataAPI.TYPE_WILLS_CLASS);
		map.printParamsForType(SiteDataAPI.TYPE_DEPTH_TO_2_5);
		map.printParamsForType(SiteDataAPI.TYPE_DEPTH_TO_1_0);
		
		map.printTypesForParams(Vs30_Param.NAME);
		
		map.printValidTest(SiteDataAPI.TYPE_VS30, Vs30_Param.NAME);
		map.printValidTest(SiteDataAPI.TYPE_WILLS_CLASS, Campbell_1997_AttenRel.SITE_TYPE_NAME);
		map.printValidTest(SiteDataAPI.TYPE_VS30, Campbell_1997_AttenRel.SITE_TYPE_NAME);
		map.printValidTest(SiteDataAPI.TYPE_DEPTH_TO_2_5, Vs30_Param.NAME);
		
		System.out.println("Size: " + map.size());
	}

}
