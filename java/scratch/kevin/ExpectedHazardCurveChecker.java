package scratch.kevin;

import java.io.File;
import java.io.IOException;
import java.text.Collator;
import java.util.ArrayList;
import java.util.Arrays;
import java.util.Comparator;
import java.util.StringTokenizer;

import org.opensha.commons.util.FileUtils;


public class ExpectedHazardCurveChecker {
	
	String curveDir;
	String expectedDir;

	public ExpectedHazardCurveChecker(String curveDir, String expectedDir){
		
		this.curveDir = curveDir;
		this.expectedDir = expectedDir;
		
	}
	
	public ArrayList<int[]> checkCurves() throws IOException {
		ArrayList<int[]> badJobs = new ArrayList<int[]>();
		
		// get and list the dir
		File masterDir = new File(expectedDir);
		File[] dirList=masterDir.listFiles();

		Arrays.sort(dirList, new FileComparator());

		int count = 0;

		// for each file in the list
		for(File file : dirList) {
			//only taking the files into consideration
			if(file.isFile()){
				String fileName = file.getAbsolutePath();
				//files that ends with ".txt"
				if(fileName.endsWith(".txt")){
					ArrayList fileLines = FileUtils.loadFile(fileName);
//					System.out.println("numlines: " + fileLines.size());
//					System.out.println("Checing " + fileName);
					boolean bad = true;
					for (String line : (ArrayList<String>)fileLines) {
//						if (count == 0)
//						System.err.println(line);
						if (line.startsWith("#"))
							continue;
						bad = false;
						File newFile = new File(curveDir + line.trim());
						if (!newFile.exists()) {
							System.out.println("Not Complete: " + fileName);
							
							//get the indices
							StringTokenizer tok = new StringTokenizer(file.getName(), "_.");
							
							// "Job"
							tok.nextToken();
							int start = Integer.parseInt(tok.nextToken());
							int end = Integer.parseInt(tok.nextToken());
							
							System.out.println("Start: " + start + " End: " + end);
							
							int indices[] = {start, end};
							badJobs.add(indices);
							
							bad = true;
							break;
						}
					}
					if (!bad)
						System.out.println("Complete: " + fileName);
					count++;
				}
			}
		}

		System.out.println("DONE");
		
		return badJobs;
	}

	private static class FileComparator implements Comparator {
		private Collator c = Collator.getInstance();

		public int compare(Object o1, Object o2) {
			if(o1 == o2)
				return 0;

			File f1 = (File) o1;
			File f2 = (File) o2;

			if(f1.isDirectory() && f2.isFile())
				return -1;
			if(f1.isFile() && f2.isDirectory())
				return 1;



			return c.compare(invertFileName(f1.getName()), invertFileName(f2.getName()));
		}

		public String invertFileName(String fileName) {
			int index = fileName.indexOf("_");
			int firstIndex = fileName.indexOf(".");
			int lastIndex = fileName.lastIndexOf(".");
			// Hazard data files have 3 "." in their names
			//And leaving the rest of the files which contains only 1"." in their names
			if(firstIndex != lastIndex){

				//getting the lat and Lon values from file names
				String lat = fileName.substring(0,index).trim();
				String lon = fileName.substring(index+1,lastIndex).trim();

				return lon + "_" + lat;
			}
			return fileName;
		}
	}

	public static void main(String args[]) {
		try {
//			String curveDir = "/home/kevin/OpenSHA/condor/test_results";
			String curveDir = "/home/kevin/OpenSHA/condor/oldRuns/verifyMap/01667/ucerf_field_nocvm/curves/";
//			String curveDir = "/home/kevin/OpenSHA/condor/oldRuns/verifyMap/UCERF/hpc/";
			String expectedDir = "/home/kevin/OpenSHA/condor/oldRuns/verifyMap/UCERF/expected/";
//			String curveDir = "/home/kevin/OpenSHA/condor/frankel_0.1";
//			String outfile = "xyzCurves.txt";
			ExpectedHazardCurveChecker maker = new ExpectedHazardCurveChecker(curveDir, expectedDir);
			maker.checkCurves();
		} catch (IOException e) {
			e.printStackTrace();
		}
	}
}

