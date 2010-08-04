package scratch.martinez;

import java.awt.GridBagConstraints;
import java.awt.GridBagLayout;
import java.awt.Insets;
import java.awt.event.ActionEvent;
import java.awt.event.ActionListener;

import javax.swing.JButton;
import javax.swing.JFrame;
import javax.swing.JPanel;

import org.opensha.nshmp.sha.gui.beans.GuiBeanAPI;

import scratch.martinez.beans.BenefitCostBean;

/**
 * A testing aplication to see how the BenefitCostBean will look and gather information
 * when plugged into a larger application.
 * 
 * @author emartinez
 */
public class Visual {
	private JFrame frame = null;
	private BenefitCostBean bean = null;
	
	public static void main(String args[]) {
		Visual app = new Visual();
		app.frame.setVisible(true);
	}
	
	public Visual() {
		bean = new BenefitCostBean();
		JPanel panel = (JPanel) bean.getVisualization(GuiBeanAPI.APPLICATION);
		
		JButton showData = new JButton("Show Data");
		showData.addActionListener(new ActionListener() {
			public void actionPerformed(ActionEvent e) {
				String data = getDataFromBean();
				System.out.println(data);
			}
		});
		
		JPanel content = new JPanel(new GridBagLayout());
		content.add(panel, new GridBagConstraints(0, 0, 1, 1, 1.0, 1.0, GridBagConstraints.NORTH,
				GridBagConstraints.BOTH, new Insets(5, 5, 5, 5), 2, 2)
		);
		content.add(showData, new GridBagConstraints(0, 1, 1, 1, 1.0, 1.0, GridBagConstraints.CENTER,
				GridBagConstraints.NONE, new Insets(5, 5, 5, 5), 2, 2)
		);
		
		frame = new JFrame("Test Frame");
		frame.add(content);
		frame.setLocation(500, 500);
		frame.pack();
	}

	private String getDataFromBean() {
		StringBuffer sbuf = new StringBuffer();
		
		sbuf.append("Current Conditions:\n");
		sbuf.append("\tVulnerabilityModel = \"" + bean.getCurrentVulnModel().getDisplayName() + "\"\n");
		sbuf.append("\tIntensity Type = \"" + bean.getCurrentVulnModel().getIMT() + "\"\n");
		sbuf.append("\tPeriod = " + bean.getCurrentVulnModel().getPeriod() + "\n");
		//sbuf.append("\tInitial Cost = $" + bean.getCurrentInitialCost() + "\n");
		sbuf.append("\tReplace Cost = $" + bean.getCurrentReplaceCost() + "\n\n");
		
		sbuf.append("RetroFit Conditions:\n");
		sbuf.append("\tVulnerabilityModel = \"" + bean.getRetroVulnModel().getDisplayName() + "\"\n");
		sbuf.append("\tIntensity Type = \"" + bean.getRetroVulnModel().getIMT() + "\"\n");
		sbuf.append("\tPeriod = " + bean.getRetroVulnModel().getPeriod() + "\n");
		//sbuf.append("\tInitial Cost = $" + bean.getRetroInitialCost() + "\n");
		sbuf.append("\tReplace Cost = $" + bean.getRetroReplaceCost() + "\n\n");
		
		sbuf.append("Discount Rate: " + bean.getDiscountRate() + "%\n");
		sbuf.append("Design Life: " + bean.getDesignLife() + " years\n");
		sbuf.append("Description: " + bean.getDescription() + "\n");
		
		return sbuf.toString();
	}
}
