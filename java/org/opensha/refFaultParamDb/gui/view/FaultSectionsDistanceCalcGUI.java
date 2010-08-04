/**
 * 
 */
package org.opensha.refFaultParamDb.gui.view;

import java.awt.GridBagConstraints;
import java.awt.GridBagLayout;
import java.awt.Insets;
import java.awt.event.ActionEvent;
import java.awt.event.ActionListener;
import java.io.FileWriter;
import java.text.DecimalFormat;
import java.util.ArrayList;

import javax.swing.JButton;
import javax.swing.JOptionPane;
import javax.swing.JPanel;

import org.opensha.commons.param.StringParameter;
import org.opensha.commons.param.editor.ConstrainedStringParameterEditor;
import org.opensha.refFaultParamDb.dao.db.DB_AccessAPI;
import org.opensha.refFaultParamDb.dao.db.DB_ConnectionPool;
import org.opensha.refFaultParamDb.dao.db.FaultSectionVer2_DB_DAO;
import org.opensha.refFaultParamDb.dao.db.PrefFaultSectionDataDB_DAO;
import org.opensha.refFaultParamDb.vo.FaultSectionPrefData;
import org.opensha.refFaultParamDb.vo.FaultSectionSummary;
import org.opensha.sha.faultSurface.EvenlyGriddedSurface;
import org.opensha.sha.faultSurface.FaultTrace;
import org.opensha.sha.faultSurface.FrankelGriddedSurface;
import org.opensha.sha.faultSurface.SimpleFaultData;
import org.opensha.sha.faultSurface.StirlingGriddedSurface;

/**
 * @author vipingupta
 *
 */
public class FaultSectionsDistanceCalcGUI extends JPanel implements ActionListener {
	private final static double GRID_SPACING = 1.0;
	private FaultSectionVer2_DB_DAO faultSectionDAO; 
	private PrefFaultSectionDataDB_DAO prefFaultSectionDAO; 
	private StringParameter faultSection1Param, faultSection2Param, faultModelParam;
	private final static String FAULT_SECTION1_PARAM_NAME = "Fault Section 1";
	private final static String FAULT_SECTION2_PARAM_NAME = "Fault Section 2";
	private final static String STIRLING = "Stirling's";
	private final static String FRANKEL = "Frankel's";
	private final static String FAULT_MODEL_PARAM_NAME = "Fault Model Name";
	private ConstrainedStringParameterEditor faultSection1ParamEditor, faultSection2ParamEditor, faultModelParamEditor;
	private JButton calcButton = new JButton("Calculate Distance");
	private DecimalFormat DECIMAL_FORMAT = new DecimalFormat("0.00");
	
	public FaultSectionsDistanceCalcGUI(DB_AccessAPI dbConnection) {
		faultSectionDAO = new FaultSectionVer2_DB_DAO(dbConnection);
		prefFaultSectionDAO = new PrefFaultSectionDataDB_DAO(dbConnection);
		
		makeFaultSectionNamesParamAndEditor();
		makeFaultModelParamAndEditor();
		calcButton.addActionListener(this);
		createGUI();
	}
	
	
	/**
	 * Add GUI components
	 *
	 */
	private void createGUI() {
		setLayout(new GridBagLayout());
		int pos=0;
		add(faultSection1ParamEditor, new GridBagConstraints(0, pos++, 1, 1, 1.0, 1.0
		        , GridBagConstraints.CENTER, GridBagConstraints.HORIZONTAL,
		        new Insets(0, 0, 0, 0), 0, 0));
		add(faultSection2ParamEditor, new GridBagConstraints(0, pos++, 1, 1, 1.0, 1.0
		        , GridBagConstraints.CENTER, GridBagConstraints.HORIZONTAL,
		        new Insets(0, 0, 0, 0), 0, 0));
		add(faultModelParamEditor, new GridBagConstraints(0, pos++, 1, 1, 1.0, 1.0
		        , GridBagConstraints.CENTER, GridBagConstraints.HORIZONTAL,
		        new Insets(0, 0, 0, 0), 0, 0));
		add(calcButton, new GridBagConstraints(0, pos++, 1, 1, 1.0, 1.0
		        , GridBagConstraints.CENTER, GridBagConstraints.HORIZONTAL,
		        new Insets(0, 0, 0, 0), 0, 0));
	}
	
	
	
	/**
	 * Fault section names param and editor
	 *
	 */
	private void makeFaultSectionNamesParamAndEditor() {
		ArrayList faultSectionsSummaryList = faultSectionDAO.getAllFaultSectionsSummary();
		ArrayList faultSectionsList = new ArrayList();
		for(int i=0; i<faultSectionsSummaryList.size(); ++i)
			faultSectionsList.add(((FaultSectionSummary)faultSectionsSummaryList.get(i)).getAsString());
		
		// fault section 1 param and editor
		faultSection1Param = new StringParameter(FAULT_SECTION1_PARAM_NAME, faultSectionsList, (String)faultSectionsList.get(0));
		faultSection1ParamEditor = new ConstrainedStringParameterEditor(faultSection1Param);
		
		// fault section 2 param and editor
		faultSection2Param = new StringParameter(FAULT_SECTION2_PARAM_NAME, faultSectionsList, (String)faultSectionsList.get(0));
		faultSection2ParamEditor = new ConstrainedStringParameterEditor(faultSection2Param);	
	}
	
	/**
	 * Make fault model name param and editor
	 * It specifies whether Frankel's is chosen or Stirling's is chosen
	 *
	 */
	private void makeFaultModelParamAndEditor() {
		ArrayList faultModels = new ArrayList();
		faultModels.add(FRANKEL);
		faultModels.add(STIRLING);
		faultModelParam = new StringParameter(FAULT_MODEL_PARAM_NAME, faultModels, (String)faultModels.get(0));
		faultModelParamEditor = new ConstrainedStringParameterEditor(faultModelParam);
	}
	
	/**
	 * Calculate minimum distance  on fault trace and full 3D distance
	 *
	 */
	private void calculateDistances() {
		// first fault section
		FaultSectionSummary faultSection1Summary = FaultSectionSummary.getFaultSectionSummary((String)faultSection1Param.getValue());
		FaultSectionPrefData faultSection1PrefData = prefFaultSectionDAO.getFaultSectionPrefData(faultSection1Summary.getSectionId());
		
		// second fault section
		FaultSectionSummary faultSection2Summary = FaultSectionSummary.getFaultSectionSummary((String)faultSection2Param.getValue());
		FaultSectionPrefData faultSection2PrefData = prefFaultSectionDAO.getFaultSectionPrefData(faultSection2Summary.getSectionId());
		
		// get the fault traces
		FaultTrace faultTrace1 = faultSection1PrefData.getFaultTrace();
		FaultTrace faultTrace2 = faultSection2PrefData.getFaultTrace();
		
		
		// get the surface
		EvenlyGriddedSurface surface1 = getEvenlyGriddedSurface(faultSection1PrefData);
		EvenlyGriddedSurface surface2 = getEvenlyGriddedSurface(faultSection2PrefData);
		
		
		JOptionPane.showMessageDialog(this, "Minimum Fault Trace distance="+DECIMAL_FORMAT.format(faultTrace1.getMinDistance(faultTrace2,1.0))+" km\n"+
				"Minimum 3D distance="+DECIMAL_FORMAT.format(surface1.getMinDistance(surface2))+" km");
	}
	
	/**
	 * Get the surface from fault section data
	 * 
	 * @param faultSectionPrefData
	 * @return
	 */
	private EvenlyGriddedSurface getEvenlyGriddedSurface(FaultSectionPrefData faultSectionPrefData) {
		SimpleFaultData simpleFaultData = faultSectionPrefData.getSimpleFaultData(false);
		String selectedFaultModel = (String)this.faultModelParam.getValue();
		// frankel and stirling surface
		if(selectedFaultModel.equalsIgnoreCase(FRANKEL)) {
			return new FrankelGriddedSurface(simpleFaultData, GRID_SPACING);
		} else {
			return new StirlingGriddedSurface(simpleFaultData, GRID_SPACING);
		}
	}

	/**
	 * This function is called when Calculate button is clicked
	 * @param event
	 */
	public void actionPerformed(ActionEvent event) {
		Object source = event.getSource();
		if(source == this.calcButton) { // calculate distances
			this.calculateDistances();
		}	
	}
	
	public static void main(String[] args) {
		 // Write file needed by Natanya Black.
		 // File consists of each fault section pair and minimum 3-D distance between them
		
		// get all fault sections from database
		PrefFaultSectionDataDB_DAO prefFaultSectionDAO = new PrefFaultSectionDataDB_DAO(DB_ConnectionPool.getLatestReadWriteConn()); 
		ArrayList<FaultSectionPrefData> prefFaultSectionsList = prefFaultSectionDAO.getAllFaultSectionPrefData();
		ArrayList<EvenlyGriddedSurface> surfaceList = new ArrayList<EvenlyGriddedSurface>();
		
		// make surfaces from faultsections
		for(int i=0; i<prefFaultSectionsList.size(); ++i) {
			SimpleFaultData simpleFaultData = prefFaultSectionsList.get(i).getSimpleFaultData(false);
			surfaceList.add(new StirlingGriddedSurface(simpleFaultData, GRID_SPACING));
		}
		
		try {
			// now calculate distancd between each pair of surface and write to file
			FileWriter fw = new FileWriter("FaultSectionDist.txt");
			for(int i=0; i<surfaceList.size(); ++i) {
				for(int j=i+1; j<surfaceList.size(); ++j) {
					fw.write(prefFaultSectionsList.get(i).getSectionName()+";"+
							prefFaultSectionsList.get(j).getSectionName() + ";"+
							surfaceList.get(i).getMinDistance(surfaceList.get(j))+"\n");
				}
			}
			fw.close();
		}catch(Exception e) {
			e.printStackTrace();
		}
		 
	}
}
