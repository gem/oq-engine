package org.opensha.sra.gui.components;

import java.awt.Dimension;
import java.awt.GridBagConstraints;
import java.awt.GridBagLayout;
import java.awt.Insets;
import java.util.EventListener;

import javax.swing.JComponent;
import javax.swing.JOptionPane;
import javax.swing.JPanel;
import javax.swing.JSplitPane;

import org.opensha.commons.data.function.DiscretizedFuncAPI;
import org.opensha.commons.param.DoubleParameter;
import org.opensha.commons.param.ParameterAPI;
import org.opensha.commons.param.StringParameter;
import org.opensha.commons.param.editor.DoubleParameterEditor;
import org.opensha.commons.param.editor.StringParameterEditor;
import org.opensha.commons.param.event.ParameterChangeEvent;
import org.opensha.commons.param.event.ParameterChangeFailEvent;
import org.opensha.commons.param.event.ParameterChangeFailListener;
import org.opensha.commons.param.event.ParameterChangeListener;

import org.opensha.sra.vulnerability.AbstractVulnerability;

/**
 * <strong>Title:</strong> BenefitCostBean<br />
 * <strong>Description</strong> Gathers and stores all the information required to calculate
 * a Benefit Cost Ratio.  Use in conjunction with a EALCalculator and BenefitCostCalculator 
 * to get meaningful data output.
 * 
 * @see scratch.martinez.BenefitCostCalculator
 * @see scratch.martinez.EALCalculator
 * @author <a href="mailto:emartinez@usgs.gov">Eric Martinez</a>
 *
 */
public class BenefitCostBean implements GuiBeanAPI {
	/** Request the Current structure conditions **/
	public static final int CURRENT = 0;
	/** Request the "What-If" structure conditions **/
	public static final int RETRO = 1;
	
	private String description = "";
	private double discountRate = 0.0;
	private double designLife = 0.0;
	private double retroCost = 0.0;

	private static final String DESC_PARAM = "BCR Description";
	private static final String DISCOUNT_PARAM = "Discount Rate";
	private static final String DESIGN_PARAM = "Design Life";
	private static final String RC_PARAM = "Added Cost to Retrofit";
	
	private StructureDescriptorBean structNow = null;
	private StructureDescriptorBean structRetro = null;
	private EventListener listener =  null;
	private StringParameter descParam = null;
	private DoubleParameter discRateParam = null;
	private DoubleParameter dsgnLifeParam = null;
	private DoubleParameter retroCostParam = null;
	
	////////////////////////////////////////////////////////////////////////////////
	//                              Public Functions                              //
	////////////////////////////////////////////////////////////////////////////////
	
	/**
	 * Constructs a BenefitCostBean ready to be used in an application.  To visualize the
	 * bean, one must make a call to the <code>getVisualization()</code> method as defined
	 * in the <code>GuiBeanAPI</code>.  This bean currently supports the <code>GuiBeanAPI.APPLICATION</code>
	 * visualization method, which returns a <code>JPanel</code> that can be embedded into
	 * a parent container.  The bean listens to itself and updates all its parameters accordingly.
	 * Use the public getter methods to retrieve information captured by this bean.
	 */
	public BenefitCostBean() {
		structNow = new StructureDescriptorBean("Current Construction Conditions");
		structRetro = new StructureDescriptorBean("What-If Construction Conditions");
		listener = new BenefitCostParameterListener();
		
		descParam = new StringParameter(DESC_PARAM, "Describe this BCR Action");
		descParam.addParameterChangeListener((ParameterChangeListener) listener);
		descParam.addParameterChangeFailListener((ParameterChangeFailListener) listener);
		descParam.setInfo("Describe the benefit-cost analysis being considered");
		
		discRateParam = new DoubleParameter(DISCOUNT_PARAM, 0.0, 200.0, "%");
		discRateParam.addParameterChangeListener((ParameterChangeListener) listener);
		discRateParam.addParameterChangeFailListener((ParameterChangeFailListener) listener);
		discRateParam.setInfo("The after-inflation annual rate at which future money is discounted to present value");
		
		dsgnLifeParam = new DoubleParameter(DESIGN_PARAM, 0.0, 10E+5, "Years");
		dsgnLifeParam.addParameterChangeListener((ParameterChangeListener) listener);
		dsgnLifeParam.addParameterChangeFailListener((ParameterChangeFailListener) listener);
		dsgnLifeParam.setInfo("The number of years into the future during which reduced future losses "+
				"are recognized as a benefit");
		
		retroCostParam = new DoubleParameter(RC_PARAM, 0.0, 10E+10, "$$$");
		retroCostParam.setInfo("The marginal cost to build the what-if facility relative to as-is");
		retroCostParam.addParameterChangeListener((ParameterChangeListener) listener);
		retroCostParam.addParameterChangeFailListener((ParameterChangeFailListener) listener);
	}

	/** Gets the bean's current description */
	public String getDescription() { return description; }
	/** Gets the bean's current discount rate */
	public double getDiscountRate() { return discountRate; }
	/** Gets the bean's current design life */
	public double getDesignLife() { return designLife; }
	/** Gets the bean's current retrofit cost */
	public double getRetroCost() { return retroCost; }
	
	/** Gets the bean's current vulnerability model */
	public AbstractVulnerability getCurrentVulnModel() { return getVulnModel(CURRENT); }
	/** Gets the bean's current vulnerability parameter */
	public ParameterAPI getCurrentVulnParam() { return getVulnerabilityParameter(CURRENT); }
	/** Gets the bean's current replacement cost */
	public double getCurrentReplaceCost() { return getReplaceCost(CURRENT); }
	
	/** Gets the bean's retrofitted vulnerability model */
	public AbstractVulnerability getRetroVulnModel() { return getVulnModel(RETRO); }
	/** Gets the bean's retrofitted vulnerability parameter */
	public ParameterAPI getRetroVulnParam() { return getVulnerabilityParameter(RETRO); }
	/** Gets the bean's retrofitted replacement cost */
	public double getRetroReplaceCost() { return getReplaceCost(RETRO); }
	
	/**
	 * @param design One of CURRENT or RETRO depending on which Vulnerability Model
	 * is of interest.
	 * @return The Vulnerability Model for the structure either under
	 * current construction conditions, or that of the "what-if" retrofitted conditions
	 * depending on the value of <code>design</code>.
	 * @throws IllegalArgumentException if the given <code>design</code> is not supported.
	 */
	public AbstractVulnerability getVulnModel(int design) {
		if(design == CURRENT)
			return structNow.getVulnerabilityModel();
		else if (design == RETRO)
			return structRetro.getVulnerabilityModel();
		else
			throw new IllegalArgumentException("The given design is not currently supported.");
	}
	
	/**
	 * @param design One of CURRENT or RETRO depending on which replacement cost
	 * is of interest.
	 * @return The expected replacement cost of the structure either under
	 * current construction conditions, or that of the "what-if" retrofitted conditions
	 * depending on the value of <code>design</code>.
	 * @throws IllegalArgumentException if the given <code>design</code> is not supported.
	 */
	public double getReplaceCost(int design) {
		if(design == CURRENT)
			return structNow.getReplaceCost();
		else if (design == RETRO)
			return structRetro.getReplaceCost();
		else
			throw new IllegalArgumentException("The given design is not currently supported.");
	}

	/**
	 * Only used when <code>getIntensityMeasure(design)</code> returns Spectral Acceleration (SA).
	 * @param design One of CURRENT or RETRO depending on which IMT period is of interest.
	 * @return The Vulnerability Model's IMT period for the structure either under
	 * current construction conditions, or that of the "what-if" retrofitted conditions
	 * depending on the value of <code>design</code>.
	 * @throws IllegalArgumentException if the given <code>design</code> is not supported.
	 */
	public double getIntensityMeasurePeriod(int design) {
		if(design == CURRENT) {
			return structNow.getVulnerabilityModel().getPeriod();
		} else if (design == RETRO) {
			return structRetro.getVulnerabilityModel().getPeriod();
		} else {
			throw new IllegalArgumentException("The given design is not currently supported");
		}
	}
	
	/**
	 * @param design One of CURRENT or RETRO depending on which Vulnerability Model
	 * is of interest.
	 * @return A template Hazard Curve (IML values) for the structure either under
	 * current construction conditions, or that of the "what-if" retrofitted conditions
	 * depending on the value of <code>design</code>.
	 * @throws IllegalArgumentException If the given <code>design</code> is not supported.
	 */
	public DiscretizedFuncAPI getSupportedIMLevels(int design) throws IllegalArgumentException {
		if(design == CURRENT)
			return structNow.getVulnerabilityModel().getHazardTemplate();
		else if (design == RETRO)
			return structRetro.getVulnerabilityModel().getHazardTemplate();
		else
			throw new IllegalArgumentException("The given design is not currently supported");
	}
	
	/**
	 * @param design One of CURRENT or RETOR depending on which Vulnerability Parameter
	 * is of interest.
	 * @return The underlying <code>ParameterAPI</code> that is used by the VulnerabilityBean.
	 * @throws IllegalArgumentException If the given <code>design</code> is not supported.
	 */
	public ParameterAPI getVulnerabilityParameter(int design) throws IllegalArgumentException {
		if(design == CURRENT) {
			return structNow.getVulnerabilityBean().getParameter();
		} else if (design == RETRO) {
			return structNow.getVulnerabilityBean().getParameter();
		} else {
			throw new IllegalArgumentException("The given design is not currently supported");
		}
	}
	////////////////////////////////////////////////////////////////////////////////
	//                   Minimum Functions to Implement GuiBeanAPI                //
	////////////////////////////////////////////////////////////////////////////////
	
	/**
	 * See the general contract specified in GuiBeanAPI.
	 */
	public Object getVisualization(int type) {
		if(!isVisualizationSupported(type))
			throw new IllegalArgumentException("That type of visualization is not yet supported.");
		if(type == GuiBeanAPI.APPLICATION)
			return getApplicationVisualization();
		return null;
	}

	/**
	 * See the general contract specified in GuiBeanAPI.
	 */
	public String getVisualizationClassName(int type) {
		if(type == GuiBeanAPI.APPLICATION)
			return "javax.swing.JPanel";
		else
			return null;
	}

	/**
	 * See the general contract specified in GuiBeanAPI.
	 */
	public boolean isVisualizationSupported(int type) {
		return type == GuiBeanAPI.APPLICATION;
	}
	
	////////////////////////////////////////////////////////////////////////////////
	//                             Private Functions                              //
	////////////////////////////////////////////////////////////////////////////////
	private JPanel getApplicationVisualization() {
		
		JPanel ret = new JPanel(new GridBagLayout());
		JPanel panel = new JPanel(new GridBagLayout());
		JSplitPane structSplit = new JSplitPane(JSplitPane.HORIZONTAL_SPLIT, true);
		structSplit.add((JComponent) structNow.getVisualization(GuiBeanAPI.APPLICATION), JSplitPane.LEFT);
		structSplit.add((JComponent) structRetro.getVisualization(GuiBeanAPI.APPLICATION), JSplitPane.RIGHT);
		structSplit.setDividerLocation(230);

		try {
			panel.add((JComponent) new DoubleParameterEditor(retroCostParam), new GridBagConstraints(
					0, 0, 2, 1, 1.0, 1.0, GridBagConstraints.NORTH, GridBagConstraints.HORIZONTAL,
					new Insets(5, 5, 5, 5), 2, 2)
			);
			panel.add((JComponent) new DoubleParameterEditor(discRateParam), new GridBagConstraints(
					0, 1, 1, 1, 1.0, 1.0, GridBagConstraints.NORTH, GridBagConstraints.HORIZONTAL,
					new Insets(5, 5, 5, 5), 2, 2)
			);
			panel.add((JComponent) new DoubleParameterEditor(dsgnLifeParam), new GridBagConstraints(
					1, 1, 1, 1, 1.0, 1.0, GridBagConstraints.NORTH, GridBagConstraints.HORIZONTAL,
					new Insets(5, 5, 5, 5), 2, 2)
			);
			panel.add((JComponent) new StringParameterEditor(descParam), new GridBagConstraints(
					0, 2, 2, 1, 1.0, 1.0, GridBagConstraints.NORTH, GridBagConstraints.HORIZONTAL,
					new Insets(5, 5, 5, 5), 2, 2)
			);
		} catch (Exception ex) {
			ex.printStackTrace();
		}
		

		JSplitPane paramSplit = new JSplitPane(JSplitPane.VERTICAL_SPLIT, structSplit, panel);
		paramSplit.setDividerLocation(250);
		
		ret.add(paramSplit, new GridBagConstraints(0, 0, 1, 1, 1.0, 1.0, GridBagConstraints.CENTER,
				GridBagConstraints.BOTH, new Insets(5, 5, 5, 5), 2, 2));
		ret.setPreferredSize(new Dimension(480, 500));
		ret.setMinimumSize(new Dimension(200, 200));
		ret.setMaximumSize(new Dimension(10000, 10000));
		ret.setSize(ret.getPreferredSize());
		return ret;
	}
	
	private void handleDescriptionChangeEvent(ParameterChangeEvent event) {
		description = (String) event.getNewValue();
	}
	
	private void handleDiscountChangeEvent(ParameterChangeEvent event) {
		discountRate = (Double) event.getNewValue();
	}
	
	private void handleDesignChangeEvent(ParameterChangeEvent event) {
		designLife = (Double) event.getNewValue();
	}
	
	private void handleRetroChangeEvent(ParameterChangeEvent event) {
		retroCost = (Double) event.getNewValue();
	}
	
	private class BenefitCostParameterListener implements ParameterChangeListener, ParameterChangeFailListener {

		public void parameterChange(ParameterChangeEvent event) {
			if(DESC_PARAM.equals(event.getParameterName()))
				handleDescriptionChangeEvent(event);
			else if(DISCOUNT_PARAM.equals(event.getParameterName()))
				handleDiscountChangeEvent(event);
			else if(DESIGN_PARAM.equals(event.getParameterName()))
				handleDesignChangeEvent(event);
			else if(RC_PARAM.equals(event.getParameterName()))
				handleRetroChangeEvent(event);
		}

		public void parameterChangeFailed(ParameterChangeFailEvent event) {
			String message = "The given value of " + event.getBadValue() + " is out of range.";
			JOptionPane.showMessageDialog(null, message, "Failed to Change Value", JOptionPane.ERROR_MESSAGE);
		}
		
	}

}
