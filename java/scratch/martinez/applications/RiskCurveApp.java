package scratch.martinez.applications;

// ==============================
// Note: This application is NOT the current app.
// ==============================
import java.awt.Component;
import java.awt.Dimension;
import java.awt.FlowLayout;
import java.awt.GridBagConstraints;
import java.awt.GridBagLayout;
import java.awt.Insets;
import java.awt.Toolkit;
import java.awt.event.ActionEvent;
import java.awt.event.ActionListener;
import java.util.ArrayList;

import javax.swing.JButton;
import javax.swing.JFrame;
import javax.swing.JLabel;
import javax.swing.JPanel;
import javax.swing.JSplitPane;
import javax.swing.JTabbedPane;
import javax.swing.SwingConstants;

import org.opensha.commons.data.function.ArbitrarilyDiscretizedFunc;
import org.opensha.commons.data.function.DiscretizedFuncAPI;
import org.opensha.nshmp.sha.gui.beans.GuiBeanAPI;
import org.opensha.sha.gui.beans.Site_GuiBean;

import scratch.martinez.beans.CreditBean;
import scratch.martinez.beans.GraphPane;
import scratch.martinez.beans.HazardCurveBean;
import scratch.martinez.beans.LossCurveBean;

@SuppressWarnings("serial")
public class RiskCurveApp extends JFrame implements Runnable {
	/* For credit purposes only */
	private CreditBean credit = null;
	private static final String[] credits = {
		CreditBean.USGS_RES, CreditBean.OPENSHA, CreditBean.AGORA };
	
	/* Beans to drive this application */
	private Site_GuiBean siteBean = null;
	private LossCurveBean lossBean = null;
	private HazardCurveBean hazBean = null;
	private JPanel graphBean = null;
	
	/* Utility components for display purposes */
	private JSplitPane ioSplit = null;
	private JTabbedPane inputPanel = null;
	private JPanel btnPanel = null;
	private JSplitPane mainSplit = null;
	private JButton btnCalc = null;
	private JButton btnClear = null;
	
	/* Other Variables for the Application */
	ArrayList<DiscretizedFuncAPI> lossFuncs = null;
	
	/**
	 * Entry point for the Risk Curve Application.  This will
	 * instantiate an object of type <code>RiskCurveApp</code>
	 * and then run that application.
	 */
	public static void main(String[] args) {
		RiskCurveApp application = new RiskCurveApp();
		// Start an annonymous thread for the application to run in
		new Thread(application).start();
	}
	
	public RiskCurveApp() {
		// Give credit where credit's due
		credit = new CreditBean(this, credits, "...");
		
		credit.setVisible(true);
		jbInit();
		credit.setVisible(false);
	}
	
	/**
	 * A method required to implement the <code>Runnable</code> interface.
	 */
	public void run() {
		pack();
		setVisible(true);
	}
	
	private void jbInit() {
		lossFuncs = new ArrayList<DiscretizedFuncAPI>();
		siteBean = new Site_GuiBean();
		lossBean = new LossCurveBean(siteBean);
		hazBean = new HazardCurveBean(siteBean);
		graphBean = createGraphBean();
		inputPanel = new JTabbedPane(JTabbedPane.TOP, JTabbedPane.SCROLL_TAB_LAYOUT);
		inputPanel.addTab("Loss Curve Selection", null, (Component)lossBean.getVisualization(GuiBeanAPI.EMBED), "Input Loss Curve Parameters");
		inputPanel.addTab("Hazard Curve Selection", null, (Component) hazBean.getVisualization(GuiBeanAPI.EMBED), "Input Hazard Curve Parameters");
		ioSplit = new JSplitPane(JSplitPane.HORIZONTAL_SPLIT, true, graphBean, inputPanel);
		btnCalc = new JButton("Compute");
		btnCalc.addActionListener(new ActionListener() {
			public void actionPerformed(ActionEvent arg0) {
				btnCalc_actionPerformed();
			}
		});
		btnClear = new JButton("Clear Output");
		btnClear.addActionListener(new ActionListener() {
			public void actionPerformed(ActionEvent e) {
				btnClear_actionPerformed();
			}
		});
		btnPanel = new JPanel(new FlowLayout());
		btnPanel.add(btnCalc, 0);
		btnPanel.add(btnClear, 0);
		btnPanel.add((Component) credit.getVisualization(GuiBeanAPI.EMBED), 2);
		mainSplit = new JSplitPane(JSplitPane.VERTICAL_SPLIT, ioSplit, btnPanel);
		add(mainSplit);
		pack();
		Dimension dim = Toolkit.getDefaultToolkit().getScreenSize();
		setLocation( (dim.width - getWidth()) / 2, (dim.height - getHeight()) / 2);
	}
	
	private JPanel createGraphBean() {
		JPanel newBean = null;
		if(lossFuncs.size() == 0) {
			newBean = new JPanel(new GridBagLayout());
			newBean.add(new JLabel("No Data to Output", SwingConstants.CENTER), new GridBagConstraints(
					0, 0, 1, 1, 1.0, 1.0, GridBagConstraints.CENTER, GridBagConstraints.NONE,
					new Insets(5, 5, 5, 5), 2, 2));
		} else {
			newBean = new GraphPane(lossFuncs);
		}
		return newBean;
	}
	
	private void btnClear_actionPerformed() {
		lossFuncs.clear();
		ioSplit.remove(graphBean);
		graphBean = createGraphBean();
		graphBean.repaint();
		ioSplit.add(graphBean, JSplitPane.LEFT);
	}
	
	private void btnCalc_actionPerformed() {
		ArbitrarilyDiscretizedFunc hazFunc = (ArbitrarilyDiscretizedFunc) hazBean.computeHazardCurve(
				lossBean.getVulnerabilityBean().getCurrentModel().getIMLVals());
		ArbitrarilyDiscretizedFunc losFunc = (ArbitrarilyDiscretizedFunc) lossBean.computeLossCurve(hazFunc);
		lossFuncs.add(losFunc);
		ioSplit.remove(graphBean);
		graphBean = createGraphBean();
		graphBean.repaint();
		ioSplit.add(graphBean, JSplitPane.LEFT);
	}
}
