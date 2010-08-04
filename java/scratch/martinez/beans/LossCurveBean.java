package scratch.martinez.beans;

import java.awt.Component;
import java.awt.Dimension;
import java.awt.GridBagConstraints;
import java.awt.GridBagLayout;
import java.awt.Insets;

import javax.swing.JPanel;

import org.opensha.commons.data.TimeSpan;
import org.opensha.commons.data.function.ArbitrarilyDiscretizedFunc;
import org.opensha.commons.data.function.DiscretizedFuncAPI;
import org.opensha.nshmp.sha.gui.beans.GuiBeanAPI;
import org.opensha.sha.gui.beans.Site_GuiBean;
import org.opensha.sha.gui.beans.TimeSpanGuiBean;

import scratch.martinez.LossCurveCalculator;

public class LossCurveBean implements GuiBeanAPI {

	/* Utility Variables */
	private LossCurveCalculator calculator = null;
	
	/* Variables for the different visualizations */
	private JPanel embedVis = null;

	////////////////////////////////////////////////////////////////////////////////
	//                   Sub-Beans to Help Drive this Bean                        //
	////////////////////////////////////////////////////////////////////////////////
	private VulnerabilityBean vulnBean = null;
	private Site_GuiBean siteBean = null;
	private TimeSpanGuiBean timeBean = null;
	
	////////////////////////////////////////////////////////////////////////////////
	//                Public Constructors to Create new Instances                 //
	////////////////////////////////////////////////////////////////////////////////
	
	/** A convenience constructor that wraps the main constructor */
	public LossCurveBean() {this(null, null, null);}
	/** A convenience constructor that wraps the main constructor */
	public LossCurveBean(VulnerabilityBean vulnBean) {this(vulnBean, null, null);}
	/** A convenience constructor that wraps the main constructor */
	public LossCurveBean(Site_GuiBean siteBean) {this(null, siteBean, null);}
	/** A convenience constructor that wraps the main constructor */
	public LossCurveBean(TimeSpanGuiBean timeBean) {this(null, null, timeBean);}
	/** A convenience constructor that wraps the main constructor */
	public LossCurveBean(VulnerabilityBean vulnBean, Site_GuiBean siteBean) {this(vulnBean, siteBean, null);}
	/** A convenience constructor that wraps the main constructor */
	public LossCurveBean(VulnerabilityBean vulnBean, TimeSpanGuiBean timeBean) {this(vulnBean, null, timeBean);}
	/** A convenience constructor that wraps the main constructor */
	public LossCurveBean(Site_GuiBean siteBean, TimeSpanGuiBean timeBean) {this(null, siteBean, timeBean);}
	/**
	 * Creates a new instance of the <code>LossCurveBean</code>.  The parameters to this constructor
	 * are used as the object parameters for this instance.  Any of the parameters can be left null,
	 * in such a case, a default parameter will be used instead.
	 */
	public LossCurveBean(VulnerabilityBean vulnBean, Site_GuiBean siteBean, TimeSpanGuiBean timeBean) {
		// Initialize the vulnerability
		if(vulnBean == null)
			this.vulnBean = new VulnerabilityBean();
		else
			this.vulnBean = vulnBean;
		
		// Initialize the siteBean
		if(siteBean == null)
			this.siteBean = new Site_GuiBean();
		else
			this.siteBean = siteBean;
		
		// Initialize the timeBean
		if(timeBean == null)
			this.timeBean = new TimeSpanGuiBean();
		else
			this.timeBean = timeBean;
		
		jbInit();
	}
	////////////////////////////////////////////////////////////////////////////////
	//                  Public Functions to Help Use this Bean                    //
	////////////////////////////////////////////////////////////////////////////////
	
	/* Public Utility Functions */
	
	/**
	 * The crowning glory of the <code>LossCurveBean</code>.  A containing application
	 * can call this function to get a loss curve.  Assuming it already has a valid
	 * Hazard Curve to pass to it...
	 * @see HazardCurveBean
	 * @param hazFunc The given Hazard Curve to compute for
	 */
	public DiscretizedFuncAPI computeLossCurve(DiscretizedFuncAPI hazFunc) {
		return calculator.getLossCurve(
				(ArbitrarilyDiscretizedFunc) hazFunc, vulnBean.getCurrentModel());
	}
	
	/* Public Getters */
	
	/**
	 * @return The underlying <code>VulnerabilityBean</code>
	 */
	public VulnerabilityBean getVulnerabilityBean() {return vulnBean;}
	/**
	 * @return The underlying <code>Site_GuiBean</code>
	 */
	public Site_GuiBean getSiteBean() {return siteBean;}
	/**
	 * @return The underlying <code>TimeSpanGuiBean</code>
	 */
	public TimeSpanGuiBean getTimeBean() {return timeBean;}
	
	/* Public Setters */
	
	/**
	 * Sets the underlying <code>VulnerabilityBean</code> for this wrapper bean.
	 * This is not used often.
	 * @param newBean The new bean to use
	 */
	public void setVulnerabilityBean(VulnerabilityBean newBean) {vulnBean = newBean;}
	/**
	 * Sets the underlying <code>Site_GuiBean</code> for this wrapper bean.
	 * This is not used often.
	 * @param newBean The new bean to use
	 */
	public void setSiteBean(Site_GuiBean newBean) {siteBean = newBean;}
	/**
	 * Sets the underlying <code>TimeSpanGuiBean</code> for this wrapper bean.
	 * This is not used often.
	 * @param newBean The new bean to use
	 */
	public void setTimeBean(TimeSpanGuiBean newBean) {timeBean = newBean;}
	/**
	 * Sets the 
	 * @param newTime The new <code>TimeSpan</code> to use.
	 */
	public void setTimeSpan(TimeSpan newTime) {timeBean.setTimeSpan(newTime);}
	
	////////////////////////////////////////////////////////////////////////////////
	//                  Functions to Implement the GuiBeanAPI                     //
	////////////////////////////////////////////////////////////////////////////////
	/** See the general contract in GuiBeanAPI */
	public Object getVisualization(int type) throws IllegalArgumentException {
		if(type == EMBED)
			return getEmbeddableVisualization();
		else
			throw new IllegalArgumentException("The given type is not currently supported.");
	}
	/** See the general contract in GuiBeanAPI */
	public String getVisualizationClassName(int type) {
		if(type == EMBED)
			return "javax.swing.JPanel";
		else
			return null;
	}
	/** See the general contract in GuiBeanAPI */
	public boolean isVisualizationSupported(int type) {
		return (type == EMBED);
	}

	
	////////////////////////////////////////////////////////////////////////////////
	//                 Private Utility Functions to Help Above                    //
	////////////////////////////////////////////////////////////////////////////////
	
	private void jbInit() {
		calculator = new LossCurveCalculator();
	}
	
	private JPanel getEmbeddableVisualization() {
		if(embedVis == null) {
			embedVis = new JPanel(new GridBagLayout());
			embedVis.add((Component) vulnBean.getVisualization(GuiBeanAPI.APPLICATION),
					new GridBagConstraints(0, 0, 1, 1, 1.0, 1.0, GridBagConstraints.CENTER,
					GridBagConstraints.HORIZONTAL, new Insets(2, 2, 2, 2), 2, 2));
			embedVis.add(siteBean, new GridBagConstraints(0, 1, 1, 1, 1.0, 1.0,
					GridBagConstraints.CENTER, GridBagConstraints.HORIZONTAL,
					new Insets(2, 2, 2, 2), 2, 2));
			embedVis.add(timeBean, new GridBagConstraints(0, 2, 1, 1, 1.0, 1.0,
					GridBagConstraints.CENTER, GridBagConstraints.HORIZONTAL, 
					new Insets(2, 2, 2, 2), 2, 2));
			embedVis.setPreferredSize(new Dimension(400, 600));
			embedVis.setSize(embedVis.getPreferredSize());
		}
		return embedVis;
	}
	
}
