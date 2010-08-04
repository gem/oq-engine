package scratch.martinez.applications;

import java.util.ArrayList;

import org.opensha.nshmp.sha.gui.beans.ExceptionBean;
import org.opensha.nshmp.util.BatchFileReader;


public class TestApp {
	/*public static void main(String[] args) {
		String[] gldintdb = {"oracle.jdbc.OracleDriver", "gldintdb.cr.usgs.gov", 
				"1523", "TEAMT", "hc_owner", "ham23*ret"};
		DBAccessor db = new DBAccessor(gldintdb, true);
		if(db.hasValidConnection()) {
			String sql = "SELECT * FROM HC_ANALYSIS_OPT ORDER BY DISPLAY_SEQ";
			ArrayList<TreeMap<String, String>> result = db.doQuery(sql);
			doPrint(result);
		} else {
			System.err.println("Failed to get connection!");
		}
	}
	
	private static void doPrint(ArrayList<TreeMap<String, String>> result) {
		System.out.println("Analysis Options");
		for(int i = 0; i < result.size(); ++i) {
				System.out.println(result.get(i).get("ANALYSIS_OPT_DISPLAY"));
		}
	}*/
	/*public static void main(String args[]) {
		PropertiesBean props = PropertiesBean.createInstance("TestApp");
		DataMiner miner = new DataMiner();
		props.addPropertyTab("Data Mining", miner.getPropertyPane());
		JFrame app = new JFrame("Application");
		JMenu menu = new JMenu("File");
		menu.add((JMenuItem) props.getVisualization(GuiBeanAPI.MENUOPT));
		JMenuBar menubar = new JMenuBar();
		menubar.add(menu);
		app.setJMenuBar(menubar);
		app.pack();
		app.setVisible(true);
	}*/
	public static void main(String args[]) throws InterruptedException {
		String filename = "/Users/emartinez/Desktop/workbook1.xls";
		BatchFileReader bfr = new BatchFileReader(filename);
		//BatchFileReader bfr = BatchFileReader.createReaderFromGui();
		if(bfr.ready()) {
			ArrayList<Double> lats = bfr.getColumnVals((short)0, 0);
			ArrayList<Double> lons = bfr.getColumnVals((short)1, 0);
			
			if(lats.size() != lons.size()) {
				ExceptionBean.showSplashException(
					"Something went funny.  The sizes differ!", "Sizes Differ!", null);
			} else {
				System.out.println("Here is what I got...");
				for(int i = 0; i < lats.size(); ++i)
					System.out.println("\t"+lats.get(i)+"\t"+lons.get(i));
				System.out.println("<<END>>");
			}
		}
	}
}
