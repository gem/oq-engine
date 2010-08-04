package org.opensha.sha.gui.beans;

import java.util.ArrayList;
import java.util.Collection;
import java.util.Collections;
import java.util.HashMap;
import java.util.ListIterator;

import org.opensha.commons.param.DependentParameterAPI;
import org.opensha.commons.param.DoubleDiscreteConstraint;
import org.opensha.commons.param.ParameterAPI;
import org.opensha.commons.param.ParameterList;
import org.opensha.commons.param.StringParameter;
import org.opensha.commons.param.editor.ParameterListEditor;
import org.opensha.commons.param.event.ParameterChangeEvent;
import org.opensha.commons.param.event.ParameterChangeListener;
import org.opensha.sha.gui.beans.event.IMTChangeEvent;
import org.opensha.sha.gui.beans.event.IMTChangeListener;
import org.opensha.sha.imr.ScalarIntensityMeasureRelationshipAPI;
import org.opensha.sha.imr.event.ScalarIMRChangeEvent;
import org.opensha.sha.imr.event.ScalarIMRChangeListener;
import org.opensha.sha.imr.param.IntensityMeasureParams.PeriodParam;
import org.opensha.sha.imr.param.IntensityMeasureParams.SA_Param;
import org.opensha.sha.util.TectonicRegionType;

/**
 * This is a GUI bean for selecting IMTs with an IMT-First approach. It takes a list
 * of IMRs and lists every IMT supported by at least one IMR.
 * 
 * @author kevin
 *
 */
public class IMT_NewGuiBean extends ParameterListEditor
implements ParameterChangeListener, ScalarIMRChangeListener {
	
	/**
	 * 
	 */
	private static final long serialVersionUID = 1L;
	
	private static double default_period = 1.0;
	
	public final static String IMT_PARAM_NAME =  "IMT";
	
	public final static String TITLE =  "Set IMT";
	
	private boolean commonParamsOnly = false;
	
	private ParameterList imtParams;
	
	private StringParameter imtParameter;
	
	private ArrayList<ScalarIntensityMeasureRelationshipAPI> imrs;
	
	private ArrayList<IMTChangeListener> listeners = new ArrayList<IMTChangeListener>();
	
	private ArrayList<Double> allPeriods;
	private ArrayList<Double> currentSupportedPeriods;

	/**
	 * Init with single IMR
	 * 
	 * @param imr
	 */
	public IMT_NewGuiBean(ScalarIntensityMeasureRelationshipAPI imr) {
		this(wrapInList(imr));
	}
	
	/**
	 * Init with an IMR gui bean. Listeners will be set up so that the IMT GUI will be updated
	 * when the IMRs change, and visa-versa.
	 * 
	 * @param imrGuiBean
	 */
	public IMT_NewGuiBean(IMR_MultiGuiBean imrGuiBean) {
		this(imrGuiBean.getIMRs());
		this.addIMTChangeListener(imrGuiBean);
		imrGuiBean.addIMRChangeListener(this);
		fireIMTChangeEvent();
	}
	
	/**
	 * Init with a list of IMRs
	 * 
	 * @param imrs
	 */
	public IMT_NewGuiBean(ArrayList<ScalarIntensityMeasureRelationshipAPI> imrs) {
		this.setTitle(TITLE);
		setIMRs(imrs);
	}
	
	private static ArrayList<ScalarIntensityMeasureRelationshipAPI> wrapInList(
			ScalarIntensityMeasureRelationshipAPI imr) {
		ArrayList<ScalarIntensityMeasureRelationshipAPI> imrs =
			new ArrayList<ScalarIntensityMeasureRelationshipAPI>();
		imrs.add(imr);
		return imrs;
	}
	
	/**
	 * Setup IMT GUI for single IMR
	 * 
	 * @param imr
	 */
	public void setIMR(ScalarIntensityMeasureRelationshipAPI imr) {
		this.setIMRs(wrapInList(imr));
	}
	
	/**
	 * Set IMT GUI for multiple IMRs. All IMTs supported by at least one IMR will be displayed.
	 * 
	 * @param imrs
	 */
	public void setIMRs(ArrayList<ScalarIntensityMeasureRelationshipAPI> imrs) {
		this.imrs = imrs;
		
		// first get a master list of all of the supported Params
		// this is hardcoded to allow for checking of common SA period
		ArrayList<Double> saPeriods;
		ParameterList paramList = new ParameterList();
		for (ScalarIntensityMeasureRelationshipAPI imr : imrs) {
			for (ParameterAPI<?> param : imr.getSupportedIntensityMeasuresList()) {
				if (paramList.containsParameter(param.getName())) {
					// it's already in there, do nothing
				} else {
					paramList.addParameter(param);
				}
			}
		}
		
		SA_Param oldSAParam = null;
		if (commonParamsOnly) {
			// now we weed out the ones that aren't supported by everyone
			ParameterList toBeRemoved = new ParameterList();
			for (ParameterAPI param : paramList) {
				boolean remove = false;
				for (ScalarIntensityMeasureRelationshipAPI imr : imrs) {
					if (!imr.getSupportedIntensityMeasuresList().containsParameter(param.getName())) {
						remove = true;
						break;
					}
				}
				if (remove) {
					if (!toBeRemoved.containsParameter(param.getName())) {
						toBeRemoved.addParameter(param);
					}
					// if SA isn't supported, we can skip the below logic
					continue;
				}
				ArrayList<Double> badPeriods = new ArrayList<Double>();
				if (param.getName().equals(SA_Param.NAME)) {
					oldSAParam = (SA_Param)param;
				}
			}
			// now we remove them
			for (ParameterAPI badParam : toBeRemoved) {
				paramList.removeParameter(badParam.getName());
			}
			saPeriods = getCommonPeriods(imrs);
		} else {
			for (ParameterAPI<?> param : paramList) {
				if (param.getName().equals(SA_Param.NAME)) {
					oldSAParam = (SA_Param) param;
					break;
				}
			}
			saPeriods = getAllSupportedPeriods(imrs);
		}
		if (oldSAParam != null && paramList.containsParameter(oldSAParam.getName())) {
			Collections.sort(saPeriods);
			allPeriods = saPeriods;
			DoubleDiscreteConstraint pConst = new DoubleDiscreteConstraint(saPeriods);
			double defaultPeriod = default_period;
			if (!pConst.isAllowed(defaultPeriod))
				defaultPeriod = saPeriods.get(0);
			PeriodParam periodParam = new PeriodParam(pConst, defaultPeriod, true);
			periodParam.addParameterChangeListener(this);
//			System.out.println("new period param with " + saPeriods.size() + " periods");
			SA_Param replaceSA = new SA_Param(periodParam, oldSAParam.getDampingParam());
			replaceSA.setValue(defaultPeriod);
			paramList.replaceParameter(replaceSA.getName(), replaceSA);
		}
		
		this.imtParams = paramList;
		
		ParameterList finalParamList = new ParameterList();
		
		ArrayList<String> imtNames = new ArrayList<String>();
		for (ParameterAPI<?> param : paramList) {
			imtNames.add(param.getName());
		}
		
		// add the IMT paramter
		imtParameter = new StringParameter (IMT_PARAM_NAME,imtNames,
				(String)imtNames.get(0));
		imtParameter.addParameterChangeListener(this);
		finalParamList.addParameter(imtParameter);
		for (ParameterAPI<?> param : paramList) {
			finalParamList.addParameter(param);
		}
		updateGUI();
		fireIMTChangeEvent();
	}
	
	private void updateGUI() {
		ParameterList params = new ParameterList();
		params.addParameter(imtParameter);
		
		// now add the independent params for the selected IMT
		String imtName = imtParameter.getValue();
//		System.out.println("Updating GUI for: " + imtName);
		DependentParameterAPI<?> imtParam = (DependentParameterAPI<?>) imtParams.getParameter(imtName);
		ListIterator<ParameterAPI<?>> paramIt = imtParam.getIndependentParametersIterator();
		while (paramIt.hasNext()) {
			ParameterAPI<?> param = paramIt.next();
			if (param.getName().equals(PeriodParam.NAME)) {
				PeriodParam periodParam = (PeriodParam) param;
				ArrayList<Double> periods = currentSupportedPeriods;
				if (periods == null)
					periods = allPeriods;
				DoubleDiscreteConstraint pConst = new DoubleDiscreteConstraint(periods);
				periodParam.setConstraint(pConst);
				if (periodParam.getValue() == null) {
					if (periodParam.isAllowed(default_period))
						periodParam.setValue(default_period);
					else
						periodParam.setValue(periods.get(0));
				}
				periodParam.getEditor().setParameter(periodParam);
			}
			params.addParameter(param);
		}
		
		this.setParameterList(params);
		this.refreshParamEditor();
		this.revalidate();
		this.repaint();
	}
	
	/**
	 * Returns the name of the selected Intensity Measure
	 * 
	 * @return
	 */
	public String getSelectedIMT() {
		return imtParameter.getValue();
	}
	
	/**
	 * Set the selected Intensity Measure by name
	 * 
	 * @param imtName
	 */
	public void setSelectedIMT(String imtName) {
		if (!imtName.equals(getSelectedIMT())) {
			imtParameter.setValue(imtName);
		}
	}
	
	public ArrayList<String> getSupportedIMTs() {
		return imtParameter.getAllowedStrings();
	}
	
	/**
	 * 
	 * @return The selected intensity measure parameter
	 */
	@SuppressWarnings("unchecked")
	public DependentParameterAPI<Double> getSelectedIM() {
		return (DependentParameterAPI<Double>) imtParams.getParameter(getSelectedIMT());
	}

	@Override
	public void parameterChange(ParameterChangeEvent event) {
		String paramName = event.getParameterName();
		
		if (paramName.equals(IMT_PARAM_NAME)) {
			fireIMTChangeEvent();
			updateGUI();
		} else if (paramName.equals(PeriodParam.NAME)) {
			if (getSelectedIMT().equals(SA_Param.NAME))
				fireIMTChangeEvent();
		}
			
	}
	
	public void addIMTChangeListener(IMTChangeListener listener) {
		listeners.add(listener);
	}
	
	public void removeIMTChangeListener(IMTChangeListener listener) {
		listeners.remove(listener);
	}
	
	public void clearIMTChangeListeners(IMTChangeListener listener) {
		listeners.clear();
	}
	
	private void fireIMTChangeEvent() {
//		System.out.println("firing change event!");
		IMTChangeEvent event = new IMTChangeEvent(this, getSelectedIM());
		
		for (IMTChangeListener listener : listeners) {
			listener.imtChange(event);
		}
	}
	
	/**
	 * Sets the current IM in the given IMR
	 * 
	 * @param imr
	 */
	public void setIMTinIMR(ScalarIntensityMeasureRelationshipAPI imr) {
		setIMTinIMR(getSelectedIM(), imr);
	}
	
	/**
	 * Sets the current IM in each IMR in the given IMR map
	 * 
	 * @param imrMap
	 */
	public void setIMTinIMRs(HashMap<TectonicRegionType, ScalarIntensityMeasureRelationshipAPI> imrMap) {
		setIMTinIMRs(getSelectedIM(), imrMap);
	}
	
	/**
	 * This will set the IMT (and it's independent params) in the given IMR. If you simply called
	 * <code>setIntensityMeasure</code> for the IMR, it might throw an error because the IMT could
	 * have been cloned or could be from another IMR. This gets around that problem by setting
	 * the IMR by name, then setting the value of each independent parameter.
	 * 
	 * @param imt
	 * @param imr
	 */
	@SuppressWarnings("unchecked")
	public static void setIMTinIMR(
			DependentParameterAPI<Double> imt,
			ScalarIntensityMeasureRelationshipAPI imr) {
		imr.setIntensityMeasure(imt.getName());
		DependentParameterAPI<Double> newIMT = (DependentParameterAPI<Double>) imr.getIntensityMeasure();
		
		ListIterator<ParameterAPI<?>> paramIt = newIMT.getIndependentParametersIterator();
		while (paramIt.hasNext()) {
			ParameterAPI toBeSet = paramIt.next();
			ParameterAPI newVal = imt.getIndependentParameter(toBeSet.getName());
			
			toBeSet.setValue(newVal.getValue());
		}
	}
	
	/**
	 * Set the IMT in each IMR contained in the IMR map
	 * 
	 * @param imt
	 * @param imrMap
	 */
	public static void setIMTinIMRs(
			DependentParameterAPI<Double> imt,
			HashMap<TectonicRegionType, ScalarIntensityMeasureRelationshipAPI> imrMap) {
		for (TectonicRegionType trt : imrMap.keySet()) {
			ScalarIntensityMeasureRelationshipAPI imr = imrMap.get(trt);
			setIMTinIMR(imt, imr);
		}
	}
	
	/**
	 * Sets the periods that should be displayed...by default all periods will be displayed,
	 * even those only supported by a single IMR.
	 * 
	 * @param supportedPeriods
	 */
	public void setSupportedPeriods(ArrayList<Double> supportedPeriods) {
		this.currentSupportedPeriods = supportedPeriods;
		Collections.sort(currentSupportedPeriods);
		updateGUI();
	}
	
	/**
	 * Creates a list of periods common to all of the given IMRs
	 * 
	 * @param imrs
	 * @return
	 */
	public static ArrayList<Double> getCommonPeriods(Collection<ScalarIntensityMeasureRelationshipAPI> imrs) {
		ArrayList<Double> allPeriods = getAllSupportedPeriods(imrs);
		
		ArrayList<Double> commonPeriods = new ArrayList<Double>();
		for (Double period : allPeriods) {
			boolean include = true;
			for (ScalarIntensityMeasureRelationshipAPI imr : imrs) {
				imr.setIntensityMeasure(SA_Param.NAME);
				SA_Param saParam = (SA_Param)imr.getIntensityMeasure();
				PeriodParam periodParam = saParam.getPeriodParam();
				if (!periodParam.isAllowed(period)) {
					include = false;
					break;
				}
			}
			
			if (include)
				commonPeriods.add(period);
		}
		
		return commonPeriods;
	}
	
	/**
	 * Creates a list of all periods found in any of the given IMRs
	 * 
	 * @param imrs
	 * @return
	 */
	public static ArrayList<Double> getAllSupportedPeriods(Collection<ScalarIntensityMeasureRelationshipAPI> imrs) {
		ArrayList<Double> periods = new ArrayList<Double>();
		for (ScalarIntensityMeasureRelationshipAPI imr : imrs) {
			if (imr.isIntensityMeasureSupported(SA_Param.NAME)) {
				imr.setIntensityMeasure(SA_Param.NAME);
				SA_Param saParam = (SA_Param)imr.getIntensityMeasure();
				PeriodParam periodParam = saParam.getPeriodParam();
				for (double period : periodParam.getAllowedDoubles()) {
					if (!periods.contains(period))
						periods.add(period);
				}
			}
		}
		return periods;
	}

	@Override
	public void imrChange(ScalarIMRChangeEvent event) {
		this.setSupportedPeriods(getCommonPeriods(event.getNewIMRs().values()));
	}

}
