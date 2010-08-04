package scratch.kevin;

import java.io.File;
import java.io.FileNotFoundException;
import java.io.FileWriter;
import java.io.IOException;
import java.util.ArrayList;
import java.util.StringTokenizer;

import org.opensha.commons.data.function.ArbitrarilyDiscretizedFunc;
import org.opensha.commons.util.FileUtils;

public class HazardMapVerifier {
	
	boolean percents = true;
	
	public HazardMapVerifier() {
		
	}
	
	public void verify(String refDir, String testDir) {
		File masterDir = new File(testDir);
		File[] dirList=masterDir.listFiles();
		
		ArrayList<VerificationResults> results = new ArrayList<VerificationResults>();
		
		// for each file in the list
		for(File dir : dirList){
			// make sure it's a subdirectory
			if (dir.isDirectory() && !dir.getName().endsWith(".")) {
				File[] subDirList=dir.listFiles();
				for(File file : subDirList) {
					//only taking the files into consideration
					if(file.isFile()){
						String fileName = file.getName();
						//files that ends with ".txt"
						if(fileName.endsWith(".txt")){
							
							int index = fileName.indexOf("_");
							Double latVal = new Double(fileName.substring(0,index).trim());
							int lastIndex = fileName.lastIndexOf(".");
							Double lonVal = new Double(fileName.substring(index+1,lastIndex).trim());
							
							String refFileName = refDir + "/" + dir.getName() + "/" + fileName;
							File refFile = new File(refFileName);
							
							if (refFile.exists()) {
								VerificationResults result = compareFiles(refFile, file);
								if (result != null) {
									result.lat = latVal;
									result.lon = lonVal;
									results.add(result);
								}
							}
						}
					}
				}
			}
		}
		
		int totalDiffCurves = 0;
		int totalDiffVals = 0;
		int totalPoints = 0;
		double totalAvgVariance = 0;
		double diffAvgVariance = 0;
		double maxVariance = 0;
		int num = results.size();
		double lat = 0;
		double lon = 0;
		for (VerificationResults result : results) {
			if (result.numDifferent > 0) {
				totalDiffCurves++;
				totalDiffVals += result.numDifferent;
				totalAvgVariance += result.getTotalAvgVariance();
				diffAvgVariance += result.getDiffAvgVariance();
				if (result.maxVariance > maxVariance) {
					maxVariance = result.maxVariance;
					lat = result.lat;
					lon = result.lon;
				}
			}
			totalPoints += result.total;
		}
		
		System.out.println("**** Verification Results ****");
		System.out.println("Curves Compared: " + num);
		System.out.println("Number of Curves With Variance: " + totalDiffCurves);
		System.out.println("Total of Different Values Found: " + totalDiffVals + " (of " + totalPoints + ")");
		System.out.print("Average variance per point: " + (totalAvgVariance / (double)num));
		if (percents)
			System.out.println(" %");
		else
			System.out.println();
		System.out.print("Average variance per different point: " + (diffAvgVariance / (double)num));
		if (percents)
			System.out.println(" %");
		else
			System.out.println();
		System.out.print("Max Variance at a single point: " + maxVariance);
		if (percents)
			System.out.println(" %" + " (" + lat +", " + lon + ")");
		else
			System.out.println(" (" + lat +", " + lon + ")");
	}
	
	public VerificationResults compareFiles(File ref, File test) {
		try {
			ArbitrarilyDiscretizedFunc refFunc = getFunc(ref.getAbsolutePath());
			ArbitrarilyDiscretizedFunc testFunc = getFunc(test.getAbsolutePath());
			
			double maxVariance = 0;
			int different = 0;
			int num = refFunc.getNum();
			double totalVariance = 0;
			
			for (int i=0; i<num; i++) {
				double refY = refFunc.getY(i);
				double testY = testFunc.getY(i);
				if (testY != refY) {
					double var = 0;
					if (percents)
						var = Math.abs(testY - refY) / refY;
					else 
						var = Math.abs(testY - refY);
					if (var > maxVariance)
						maxVariance = var;
					totalVariance += var;
					different++;
				}
			}
			return new VerificationResults(maxVariance, totalVariance, different, num);
			
		} catch (FileNotFoundException e) {
			// TODO Auto-generated catch block
			e.printStackTrace();
		} catch (IOException e) {
			// TODO Auto-generated catch block
			e.printStackTrace();
		}
		return null;
	}
	
	public ArbitrarilyDiscretizedFunc getFunc(String fileName) throws FileNotFoundException, IOException {
		ArrayList fileLines = FileUtils.loadFile(fileName);
		String dataLine;
		StringTokenizer st;
		ArbitrarilyDiscretizedFunc func = new ArbitrarilyDiscretizedFunc();

		for(int i=0;i<fileLines.size();++i) {
			dataLine=(String)fileLines.get(i);
			st=new StringTokenizer(dataLine);
			//using the currentIML and currentProb we interpolate the iml or prob
			//value entered by the user.
			double currentIML = Double.parseDouble(st.nextToken());
			double currentProb= Double.parseDouble(st.nextToken());
			func.set(currentIML, currentProb);
		}
		return func;
	}
	
	class VerificationResults {
		
		double maxVariance = 0;
		int numDifferent = 0;
		int total = 0;
		double totalVariance = 0;
		double lat = 0;
		double lon = 0;
		
		public VerificationResults(double max, double totVar, int diff, int total) {
			this.maxVariance = max;
			this.numDifferent = diff;
			this.total = total;
			this.totalVariance = totVar;
		}
		
		public double getTotalAvgVariance() {
			return totalVariance / (double)total;
		}
		
		public double getDiffAvgVariance() {
			return totalVariance / (double)numDifferent;
		}
	}
	
	public void moveCurvesToNewFormat(String oldDir, String newDir) {
		File newDirFile = new File(newDir);
		if (!newDirFile.exists())
			newDirFile.mkdir();
		
		File masterDir = new File(oldDir);
		File[] dirList=masterDir.listFiles();
		
		for (File file : dirList) {
			String fileName = file.getName();
			if (fileName.contains(".txt")) {
				int index = fileName.indexOf("_");
				String lat = fileName.substring(0,index).trim();
				int lastIndex = fileName.lastIndexOf(".");
				String lon = fileName.substring(index+1,lastIndex).trim();
				
				String newFolderName = newDir + "/" + lat;
				File newFolder = new File(newFolderName);
				if (!newFolder.exists())
					newFolder.mkdir();
				
				try {
					FileWriter fw = new FileWriter(newFolderName + "/" + fileName);
					ArrayList<String> oldFile = FileUtils.loadFile(file.getAbsolutePath());
					
					for (String line : oldFile) {
						fw.write(line + "\n");;
					}
					fw.close();
				} catch (IOException e) {
					e.printStackTrace();
				}
			}
		}
	}

	/**
	 * @param args
	 */
	public static void main(String[] args) {
		HazardMapVerifier ver = new HazardMapVerifier();
		String refDir = "/home/kevin/OpenSHA/condor/oldRuns/verifyMap/01667/boore_cvm_orig/curves";
		String testDir = "/home/kevin/OpenSHA/condor/verify/paper/SRL3_F_PGA_new";
		ver.moveCurvesToNewFormat("/home/kevin/OpenSHA/condor/oldRuns/verifyMap/01667/boore_cvm_orig/oldCurves", refDir);
//		ver.verify(refDir, testDir);
		System.exit(0);
	}

}
