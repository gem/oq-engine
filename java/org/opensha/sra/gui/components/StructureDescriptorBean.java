package org.opensha.sra.gui.components;

import java.util.EventListener;

import javax.swing.JOptionPane;

import org.opensha.commons.param.DoubleParameter;
import org.opensha.commons.param.ParameterList;
import org.opensha.commons.param.editor.ParameterListEditor;
import org.opensha.commons.param.event.ParameterChangeEvent;
import org.opensha.commons.param.event.ParameterChangeFailEvent;
import org.opensha.commons.param.event.ParameterChangeFailListener;
import org.opensha.commons.param.event.ParameterChangeListener;

import org.opensha.sra.vulnerability.AbstractVulnerability;
/**
 * <strong>Title:</strong> StructureDescriptorBean<br />
 * <strong>Description:</strong> A bean to gather and store information about a structure.
 * While this can be expanding upon to include more specific information about a structure,
 * its current implementation holds only the information for the purposes of the BenefitCostRatio
 * application.
 * 
 * @see BRC_Application
 * @author <a href="mailto:emartinez@usgs.gov">Eric Martinez</a>
 */
public class StructureDescriptorBean implements GuiBeanAPI {
	private ParameterListEditor applicationEditor = null;
	private DoubleParameter replaceCost = null;
	private VulnerabilityBean vulnBean = null;
	private String descriptorName = "";
	
	private double replaceVal = 0.0;
	
	private EventListener listener = null;
	private static final String REPLACE_PARAM = "Replacement Cost";
	
	////////////////////////////////////////////////////////////////////////////////
	//                              Public Functions                              //
	////////////////////////////////////////////////////////////////////////////////
	
	/**
	 * Creates an unnamed StructureDescriptorBean
	 */
	public StructureDescriptorBean() {
		this("");
	}
	
	/**
	 * Creates a new StructureDescriptorBean with the given name.  The name is used for display purposes
	 * within the application.
	 * @param name The title of this bean.
	 */
	public StructureDescriptorBean(String name) {
		descriptorName = name;
		vulnBean = new VulnerabilityBean();
		listener = new StructureDescriptorParameterListener();
		
		replaceCost = new DoubleParameter(REPLACE_PARAM, 0, 10E+10, "$$$");
		replaceCost.setInfo("The cost to replace the facility excluding land and demolition");
		replaceCost.addParameterChangeListener((ParameterChangeListener) listener);
		replaceCost.addParameterChangeFailListener((ParameterChangeFailListener) listener);
	}
	
	/** @return The vulnerability bean used by this bean */
	public VulnerabilityBean getVulnerabilityBean() { return vulnBean; }
	/** @return The current vulnerability model selected within the vulnerability bean */
	public AbstractVulnerability getVulnerabilityModel() { return vulnBean.getCurrentModel(); }
	/** @return The current cost to replace the structre describe by this bean */
	public double getReplaceCost() { return replaceVal; }

	////////////////////////////////////////////////////////////////////////////////
	//                Minimum Functions to Implement GuiBeanAPI                   //
	////////////////////////////////////////////////////////////////////////////////

	/**
	 * See the general contract in GuiBeanAPI.
	 */
	public Object getVisualization(int type) {
		if(!isVisualizationSupported(type))
			throw new IllegalArgumentException("Only the Application type is supported at this time.");
		if(type == GuiBeanAPI.APPLICATION) {
			return getApplicationVisualization();
		}
		return null;
	}

	/**
	 * See the general contract in GuiBeanAPI.
	 */
	public String getVisualizationClassName(int type) {
		String cname = null;
		if(type == GuiBeanAPI.APPLICATION) {
			cname = "org.opensha.commons.param.editor.ParameterListEditor";
		}
		
		return cname;
	}
	/**
	 * See the general contract in GuiBeanAPI.
	 */
	public boolean isVisualizationSupported(int type) {
		return type == GuiBeanAPI.APPLICATION;
	}

	////////////////////////////////////////////////////////////////////////////////
	//                             Private Functions                              //
	////////////////////////////////////////////////////////////////////////////////
	
	private ParameterListEditor getApplicationVisualization() {
		if(applicationEditor == null) {
			ParameterList plist = new ParameterList();
			plist.addParameter(vulnBean.getParameter());
			plist.addParameter(replaceCost);
			applicationEditor = new ParameterListEditor(plist);
			applicationEditor.setTitle(descriptorName);
		}
		return applicationEditor;
	}

	private void handleReplaceCostChange(ParameterChangeEvent event) {
		replaceVal = (Double) event.getNewValue();
	}
	private class StructureDescriptorParameterListener implements ParameterChangeListener, ParameterChangeFailListener {

		public void parameterChange(ParameterChangeEvent event) {
			if(REPLACE_PARAM.equals(event.getParameterName()))
				handleReplaceCostChange(event);
		}
		
		public void parameterChangeFailed(ParameterChangeFailEvent event) {
			JOptionPane.showMessageDialog(null, "The given value of " + event.getBadValue() +
					" is out of range.", "Failed to Change Value", JOptionPane.ERROR_MESSAGE);
		}
	}
}
