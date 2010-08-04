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

package org.opensha.commons.data.siteData.impl;

import java.io.IOException;
import java.util.ArrayList;

import org.opensha.commons.data.function.ArbitrarilyDiscretizedFunc;
import org.opensha.commons.data.siteData.AbstractSiteData;
import org.opensha.commons.data.siteData.SiteDataAPI;
import org.opensha.commons.exceptions.RegionConstraintException;
import org.opensha.commons.geo.GeoTools;
import org.opensha.commons.geo.GriddedRegion;
import org.opensha.commons.geo.Location;
import org.opensha.commons.geo.LocationList;
import org.opensha.commons.geo.Region;
import org.opensha.commons.param.ArbitrarilyDiscretizedFuncParameter;
import org.opensha.commons.param.BooleanParameter;
import org.opensha.commons.param.StringParameter;
import org.opensha.commons.param.editor.ArbitrarilyDiscretizedFuncTableModel;
import org.opensha.commons.param.editor.ParameterEditor;
import org.opensha.commons.param.event.ParameterChangeEvent;
import org.opensha.commons.param.event.ParameterChangeListener;

public class WaldAllenGlobalVs30 extends AbstractSiteData<Double> implements ParameterChangeListener {
	
	private static final boolean D = false;
	
	public static final String NAME = "Global Vs30 from Topographic Slope (Wald & Allen 2008)";
	public static final String SHORT_NAME = "GlobalTopoSlopeVs30";
	
	public static final double arcSecondSpacing = 30.0;
	// for 30 arc seconds this is 0.008333333333333333
	public static final double spacing = GeoTools.secondsToDeg(arcSecondSpacing);
	
	private StringParameter coeffPresetParam;
	public static final String COEFF_SELECT_PARAM_NAME = "Region Type";
	public static final String COEFF_ACTIVE_NAME = "Active Tectonic";
	public static final String COEFF_STABLE_NAME = "Stable Continent";
	public static final String COEFF_CUSTOM_NAME = "Custom Coefficients";
	
	private ArbitrarilyDiscretizedFuncParameter coeffFuncParam;
	public static final String COEFF_FUNC_PARAM_NAME = "Topographic Slope Translation Coefficients";
	
	private final ArbitrarilyDiscretizedFunc activeFunc = createActiveCoefficients();
	private final ArbitrarilyDiscretizedFunc stableFunc = createStableCoefficients();
	private ArbitrarilyDiscretizedFunc customFunc = null;
	
	private SRTM30TopoSlope srtm30_Slope = null;
	private SRTM30PlusTopoSlope srtm30plus_Slope = null;
	
	private SiteDataAPI<Double> slopeProvider;
	
	private ArbitrarilyDiscretizedFunc coeffFunc;
	
	private BooleanParameter interpolateParam;
	public static final String INTERPOLATE_PARAM_NAME = "Interpolate Between Slope Values (Linear)";
	public static final Boolean INTERPOLATE_PARAM_DEFAULT = true;
	
	private StringParameter demParam;
	public static final String DEM_SELECT_PARAM_NAME = "Digital Elevation Model";
	public static final String DEM_SRTM30 = "SRTM30 Version 2";
	public static final String DEM_SRTM30_PLUS = "SRTM30 Plus Version 5 (NOTE: contains bathymetry)";
	public static final String DEM_SELECT_DEFAULT = DEM_SRTM30;
	
	private boolean interpolate = true;
	
	/**
	 * Creates function for active tectonic regions from Allen & Wald 2008
	 * @return
	 */
	public static ArbitrarilyDiscretizedFunc createActiveCoefficients() {
		ArbitrarilyDiscretizedFunc func = new ArbitrarilyDiscretizedFunc();
		
		func.set(3e-4,		180);
		func.set(3.5e-3,	240);
		func.set(0.010,		300);
		func.set(0.018,		360);
		func.set(0.050,		490);
		func.set(0.10,		620);
		func.set(0.14,		760);
		
		return func;
	}
	
	/**
	 * Creates function for stable tectonic regions from Wald & Allen 2007
	 * @return
	 */
	public static ArbitrarilyDiscretizedFunc createStableCoefficients() {
		ArbitrarilyDiscretizedFunc func = new ArbitrarilyDiscretizedFunc();
		
		func.set(2.0e-5,	180);
		func.set(2.0e-3,	240);
		func.set(4.0e-3,	300);
		func.set(7.2e-3,	360);
		func.set(0.013,		490);
		func.set(0.018,		620);
		func.set(0.025,		760);
		
		return func;
	}
	
	public WaldAllenGlobalVs30() throws IOException {
		srtm30_Slope = new SRTM30TopoSlope();
		srtm30plus_Slope = new SRTM30PlusTopoSlope();
		
		ArrayList<String> coeffNames = new ArrayList<String>();
		
		coeffNames.add(COEFF_ACTIVE_NAME);
		coeffNames.add(COEFF_STABLE_NAME);
		coeffNames.add(COEFF_CUSTOM_NAME);
		
		coeffPresetParam = new StringParameter(COEFF_SELECT_PARAM_NAME, coeffNames, COEFF_ACTIVE_NAME);
		
		coeffFuncParam = new ArbitrarilyDiscretizedFuncParameter(COEFF_FUNC_PARAM_NAME, activeFunc.deepClone());
		coeffFuncParam.setNonEditable();
		
		coeffPresetParam.addParameterChangeListener(this);
		coeffFuncParam.addParameterChangeListener(this);
		
		coeffFunc = (ArbitrarilyDiscretizedFunc) coeffFuncParam.getValue();
		
		interpolateParam = new BooleanParameter(INTERPOLATE_PARAM_NAME, INTERPOLATE_PARAM_DEFAULT);
		interpolateParam.addParameterChangeListener(this);
		
		ArrayList<String> demNames = new ArrayList<String>();
		
		demNames.add(DEM_SRTM30);
		demNames.add(DEM_SRTM30_PLUS);
		
		demParam = new StringParameter(DEM_SELECT_PARAM_NAME, demNames, DEM_SELECT_DEFAULT);
		demParam.addParameterChangeListener(this);
		slopeProvider = srtm30_Slope;
		
		initDefaultVS30Params();
		this.paramList.addParameter(demParam);
		this.paramList.addParameter(interpolateParam);
		this.paramList.addParameter(coeffPresetParam);
		this.paramList.addParameter(coeffFuncParam);
		this.paramList.addParameter(minVs30Param);
		this.paramList.addParameter(maxVs30Param);
	}

	public Region getApplicableRegion() {
		return slopeProvider.getApplicableRegion();
	}

	public Location getClosestDataLocation(Location loc) throws IOException {
		return srtm30_Slope.getClosestDataLocation(loc);
	}

	public String getMetadata() {
		return 	"Vs30 estimations from topographic slope, as described in:\n" +
				"\n" +
				"Topographic Slope as a Proxy for Seismic Site Conditions and Amplification\n" +
				"By David J. Wald and Trevor I. Allen\n" +
				"Bulletin of the Seismological Society of America, Vol. 97, No. 5, pp. 1379–1395, October 2007, doi: 10.1785/0120060267\n" +
				"\n" +
				"And updated in:\n" +
				"\n" +
				"On the use of high­resolution topographic data as a proxy for seismic site conditions (Vs30)\n" +
				"By Trevor I. Allen and David J. Wald\n" +
				"\n" +
				"Digital Elevation model in use is '" + slopeProvider.getName() + "', 30 arc second resolution";
	}

	public String getName() {
		return NAME;
	}

	public double getResolution() {
		return spacing;
	}

	public String getShortName() {
		return SHORT_NAME;
	}

	public String getDataType() {
		return TYPE_VS30;
	}

	public String getDataMeasurementType() {
		return TYPE_FLAG_INFERRED;
	}
	
	private double getVs30(double slope) {
//		System.out.println("old: " + slope);
//		slope = slope / 100d;
//		System.out.println("new: " + slope);
		double vs;
		if (slope <= coeffFunc.getMinX())
			vs = coeffFunc.getY(0);
		else if (slope >= coeffFunc.getMaxX())
			vs = coeffFunc.getY(coeffFunc.getNum()-1);
		else {
			if (interpolate)
				vs = coeffFunc.getInterpolatedY(slope);
			else {
				vs = coeffFunc.getClosestY(slope);
			}
		}
		
		if (D) System.out.println("Translated slope of " + slope + " to Vs30 of " + vs);
		return vs;
	}

	public Double getValue(Location loc) throws IOException {
		Double slope = slopeProvider.getValue(loc);
		
		if (!srtm30_Slope.isValueValid(slope))
			return Double.NaN;
		
		double vs30 = getVs30(slope);
		
		return certifyMinMaxVs30(vs30);
	}
	
	@Override
	public ArrayList<Double> getValues(LocationList locs) throws IOException {
		// it more efficient to get all of the slopes, and then translate them
		ArrayList<Double> slopes = slopeProvider.getValues(locs);
		ArrayList<Double> vs30 = new ArrayList<Double>();
		
		for (int i=0; i<slopes.size(); i++) {
			vs30.add(certifyMinMaxVs30(getVs30(slopes.get(i))));
		}
		
		return vs30;
	}
	
	/**
	 * Helper method for setting interpolation.
	 * 
	 * @param interpolate - if true, linearly interpolate vs30 values
	 */
	public void setInterpolateValues(boolean interpolate) {
		this.interpolateParam.setValue(interpolate);
	}
	
	/**
	 * Helper method for setting active coefficients
	 */
	public void setActiveCoefficients() {
		this.coeffPresetParam.setValue(COEFF_ACTIVE_NAME);
	}
	
	/**
	 * Helper method for setting stable coefficients
	 */
	public void setStableCoefficients() {
		this.coeffPresetParam.setValue(COEFF_STABLE_NAME);
	}

	public boolean isValueValid(Double el) {
		return el > 0 && !el.isNaN();
	}

	public void parameterChange(ParameterChangeEvent event) {
		String paramName = event.getParameterName();
		if (D) System.out.println("WaldparameterChange start...");
		if (paramName == COEFF_SELECT_PARAM_NAME) {
			if (D) System.out.println("Coeff select changed...");
			String val = (String)coeffPresetParam.getValue();
			
			// if we're switching away from a custom function, we want to store that
			ArbitrarilyDiscretizedFunc oldFunc = (ArbitrarilyDiscretizedFunc)coeffFuncParam.getValue();
			if (!ArbitrarilyDiscretizedFuncTableModel.areFunctionPointsEqual(oldFunc, activeFunc)
					&& !ArbitrarilyDiscretizedFuncTableModel.areFunctionPointsEqual(oldFunc, stableFunc)) {
				// the function has been edited...store it
				customFunc = oldFunc;
			}
				
			if (val == COEFF_ACTIVE_NAME) {
				coeffFuncParam.setValue(activeFunc.deepClone());
			} else if (val == COEFF_STABLE_NAME) {
				coeffFuncParam.setValue(stableFunc.deepClone());
			} else if (val == COEFF_CUSTOM_NAME) {
				if (customFunc == null) {
					customFunc = activeFunc.deepClone();
				}
				coeffFuncParam.setValue(customFunc);
			}
			refreshParams();
		} else if (paramName == COEFF_FUNC_PARAM_NAME) {
			if (D) System.out.println("Coeff func changed...");
			coeffFunc = (ArbitrarilyDiscretizedFunc)coeffFuncParam.getValue();
			double prevX = 0;
			double prevY = 0;
			for (int i=0; i<coeffFunc.getNum(); i++) {
				double x = coeffFunc.getX(i);
				double y = coeffFunc.getY(i);
				if (x < prevX || y < prevY)
					System.err.println("WARNING: portion of coefficient function has negative slope!");
				prevX = x;
				prevY = y;
				if (D) System.out.println("x: " + coeffFunc.getX(i) + ", y: " + coeffFunc.getY(i));
			}
		} else if (paramName == INTERPOLATE_PARAM_NAME) {
			interpolate = (Boolean)interpolateParam.getValue();
			if (D) System.out.println("Interpolate changed: " + interpolate);
		} else if (paramName == DEM_SELECT_PARAM_NAME) {
			String newDem = (String)demParam.getValue();
			if (newDem == DEM_SRTM30) {
				slopeProvider = srtm30_Slope;
			} else if (newDem == DEM_SRTM30_PLUS) {
				slopeProvider = srtm30plus_Slope;
			}
			if (D) System.out.println("DEM changed: " + slopeProvider.getName());
		}
		if (D) System.out.println("WaldparameterChange DONE");
	}
	
	private void refreshParams() {
		if (this.paramEdit == null)
			return;
		if (D) System.out.println("WaldRefreshParams start...");
		String val = (String)coeffPresetParam.getValue();
		ParameterEditor funcEditor = this.paramEdit.getParameterEditor(COEFF_FUNC_PARAM_NAME);
		funcEditor.setEnabled(val == COEFF_CUSTOM_NAME);
		if (D) System.out.println("WaldRefreshParams refreshing params...");
//		funcEditor.refreshParamEditor();
		paramEdit.refreshParamEditor();
		funcEditor.validate();
		paramEdit.validate();
//		paramEdit.refreshParamEditor();
		if (D) System.out.println("WaldRefreshParams DONE");
	}
	
	public void setCoeffFunction(ArbitrarilyDiscretizedFunc func) {
		String selected = (String)coeffPresetParam.getValue();
		if (!selected.equals(COEFF_CUSTOM_NAME)) {
			coeffPresetParam.setValue(COEFF_CUSTOM_NAME);
		}
		this.coeffFuncParam.setValue(func);
	}
	
	public ArbitrarilyDiscretizedFunc getCoeffFunctionClone() {
		return coeffFunc.deepClone();
	}
	
	public static void printMapping(ArbitrarilyDiscretizedFunc func) {
		for (int i=0; i<func.getNum(); i++) {
			System.out.println(func.getX(i) + "\t=>\t" + func.getY(i));
		}
	}

	@Override
	protected void initParamListEditor() {
		super.initParamListEditor();
		refreshParams();
	}
	
	public static void main(String args[]) throws IOException, RegionConstraintException {
		WaldAllenGlobalVs30 data = new WaldAllenGlobalVs30();
		data.setActiveCoefficients();
//		data.setStableCoefficients();
		double vs30 = data.getValue(new Location(34, -118));
		LocationList locs = new LocationList();
		locs.add(new Location(34.1, -118));
		locs.add(new Location(34.2, -118));
		locs.add(new Location(34.3, -118));
		ArrayList<Double> vs30Vals = data.getValues(locs);
		SRTM30TopoSlope sdata = new SRTM30TopoSlope();
		SRTM30PlusTopoSlope spdata = new SRTM30PlusTopoSlope();
		SRTM30Topography tdata = new SRTM30Topography();
		SRTM30PlusTopography tpdata = new SRTM30PlusTopography();
		
		System.out.println(data.getValue(new Location(34, -118)));
		System.out.println(data.getValue(new Location(34, -10)));
		
		GriddedRegion region = 
			new GriddedRegion(
					new Location(32, -121),
					new Location(35, -117),
					0.01, new Location(0,0));
//		EvenlyGriddedRectangularGeographicRegion region = new EvenlyGriddedRectangularGeographicRegion(-60, 60, -180, 180, 1);
		
		ArbitrarilyDiscretizedFunc func = new ArbitrarilyDiscretizedFunc();
		func.set(0.000032,	180);
		func.set(0.0022,	240);
		func.set(0.0063,	300);
		func.set(0.018,		360);
		func.set(0.05,		490);
		func.set(0.1,		620);
		func.set(0.138,		760);
		data.setCoeffFunction(func);
//		
//		SiteDataToXYZ.writeXYZ(data, region, "/tmp/topo_vs30.txt");
		
		System.out.println(data.getCoeffFunctionClone());
		
		System.out.println("Active Tectonic:");
		printMapping(createActiveCoefficients());
		System.out.println("Stable Continent:");
		printMapping(createStableCoefficients());
		
		Location loc = new Location(34.5, -117.51);
		System.out.println("Slope: " + sdata.getValue(loc));
		System.out.println("Elevation: " + tdata.getValue(loc));
		System.out.println("Plus Slope: " + spdata.getValue(loc));
		System.out.println("Plus Elevation: " + tpdata.getValue(loc));
		System.out.println("Vs30: " + data.getValue(loc));
	}
	
//	@Override
//	protected Element addXMLParameters(Element paramsEl) {
//		paramsEl.addAttribute("useServlet", this.useServlet + "");
//		paramsEl.addAttribute("fileName", this.fileName);
//		paramsEl.addAttribute("type", this.type);
//		return super.addXMLParameters(paramsEl);
//	}
	
	public static WaldAllenGlobalVs30 fromXMLParams(org.dom4j.Element paramsElem) throws IOException {
		return new WaldAllenGlobalVs30();
	}
}
