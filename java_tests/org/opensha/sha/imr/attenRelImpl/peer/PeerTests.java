//package org.opensha.sha.imr.attenRelImpl.peer;
//
//import java.io.File;
//import java.io.FileWriter;
//import java.util.ArrayList;
//
//import org.opensha.commons.data.function.DiscretizedFuncAPI;
//import org.opensha.sha.gui.infoTools.ExceptionWindow;
//
//public class PeerTests {
//
//	/**
//	 * @param args
//	 */
//	public static void main(String[] args) {
//		// TODO Auto-generated method stub
//
//	}
//
//	
//	private void runTests() {
//		
//		//if (this.runAllPeerTestsCP.runAllPEER_TestCases()) {
//			try {
//				//progressCheckBox.setSelected(false);
//				//String peerDirName = "PEER_TESTS/";
//				// creating the peer directory in which we put all the peer
//				// related files
//				//File peerDir = new File(peerDirName);
//				//if (!peerDir.isDirectory()) { // if main directory does not
//												// exist
//				//	boolean success = (new File(peerDirName)).mkdir();
//				//}
//				
//				// output dir
//				String peerDirName = "PEER_TESTS/";
//				File peerDir = new File(peerDirName);
//				peerDir.mkdirs();
//				
//				// ArrayList testCases =
//				// this.peerTestsControlPanel.getPEER_SetTwoTestCasesNames();
//				ArrayList testCases = this.peerTestsControlPanel
//						.getPEER_SetOneTestCasesNames();
//
//				int size = testCases.size();
//				/*
//				 * if(epistemicControlPanel == null) epistemicControlPanel =
//				 * new ERF_EpistemicListControlPanel(this,this);
//				 * epistemicControlPanel.setCustomFractileValue(05);
//				 * epistemicControlPanel.setVisible(false);
//				 */
//				// System.out.println("size="+testCases.size());
//				setAverageSelected(true);
//				/*
//				 * size=106 for Set 1 Case1: 0-6 Case2: 7-13 Case3: 14-20
//				 * Case4: 21-27 Case5 28-34 Case6: 35-41 Case7: 42-48
//				 * Case8a: 49-55 Case8b: 56-62 Case8c: 63-69 Case9a: 70-76
//				 * Case9b: 77-83 Case9c: 84-90 Case10: 91-95 Case11: 96-99
//				 * Case12: 100-106
//				 * 
//				 * DOING ALL TAKES ~24 HOURS?
//				 */
//				for (int i = 0; i < size; ++i) {
//					// for(int i=35 ;i < 35; ++i){
//					System.out.println("Working on # " + (i + 1) + " of "
//							+ size);
//
//					// first do PGA
//					peerTestsControlPanel
//							.setTestCaseAndSite((String) testCases.get(i));
//					calculate();
//
//					FileWriter peerFile = new FileWriter(peerDirName
//							+ (String) testCases.get(i)
//							+ "-PGA_OpenSHA.txt");
//					DiscretizedFuncAPI func = (DiscretizedFuncAPI) functionList
//							.get(0);
//					for (int j = 0; j < func.getNum(); ++j)
//						peerFile.write(func.get(j).getX() + "\t"
//								+ func.get(j).getY() + "\n");
//					peerFile.close();
//					clearPlot();
//
//					// now do SA
//					/*
//					 * imtGuiBean.getParameterList().getParameter(IMT_GuiBean
//					 * .IMT_PARAM_NAME).setValue(SA_Param.NAME);
//					 * imtGuiBean.getParameterList
//					 * ().getParameter(PeriodParam.NAME).setValue(new
//					 * Double(1.0)); addButton(); peerFile = new
//					 * FileWriter(peerDirName
//					 * +(String)testCasesTwo.get(i)+"-1secSA_OpenSHA.dat");
//					 * for(int j=0; j<totalProbFuncs.get(0).getNum();++j)
//					 * peerFile
//					 * .write(totalProbFuncs.get(0).get(j).getX()+" "
//					 * +totalProbFuncs.get(0).get(j).getY()+"\n");
//					 * peerFile.close(); this.clearPlot(true);
//					 */
//
//				}
//				System.exit(101);
//				// peerResultsFile.close();
//			} catch (Exception ee) {
//				ExceptionWindow bugWindow = new ExceptionWindow(this, ee,
//						getParametersInfoAsString());
//				bugWindow.setVisible(true);
//				bugWindow.pack();
//			}
//		//}
//
//	}
//}
