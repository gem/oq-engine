package scratch.kevin;

import java.io.File;
import java.io.FileNotFoundException;
import java.io.IOException;
import java.math.BigDecimal;
import java.text.DecimalFormat;
import java.util.ArrayList;

import org.opensha.commons.util.FileUtils;

public class IMRFilesCheck {
	
	private static DecimalFormat decimalFormat = new DecimalFormat("0.000000##");
	private static DecimalFormat percentFormat = new DecimalFormat("0.00");

	public IMRFilesCheck(String file1, String file2) throws FileNotFoundException, IOException {
		ArrayList<String> lines1 = FileUtils.loadFile(file1, false);
		ArrayList<String> lines2 = FileUtils.loadFile(file2, false);
		
		String file1Name = new File(file1).getName();

		boolean truncMatch = true;
		boolean roundMatch = true;
		
		int truncFails = 0;
		int roundFails = 0;
		
		int count = 0;
		
		double maxAbsDiff = 0;
		double maxPercentDiff = 0;

		for (int i=0; i<lines1.size(); i++) {
			String line1 = lines1.get(i);
			String line2 = lines2.get(i);
			
			if (!line1.startsWith("GetValue"))
				continue;

			String val1 = getValStrFromLine(line1);
			double dval1 = Double.parseDouble(val1);
			String val2 = getValStrFromLine(line2);
			double dval2 = Double.parseDouble(val2);
			
			double absDiff = Math.abs(dval1 - dval2);
			if (absDiff > maxAbsDiff)
				maxAbsDiff = absDiff;
			double percentDiff = (absDiff / dval1) * 100d;
			if (percentDiff > maxPercentDiff)
				maxPercentDiff = percentDiff;
 
			if (!val1.substring(0, 5).equals(val2.substring(0, 5))) {
				if (truncMatch)
					truncMatch = false;
				truncFails++;
//				System.out.println("**TRUNC FAIL: " + val1 + ", " + val2);
			}
			double round1 = round(val1, 3);
			double round2 = round(val2, 3);
			if (round1 != round2) {
				if (roundMatch)
					roundMatch = false;
				roundFails++;
				System.out.println("**ROUND FAIL: " + val1 + ", " + val2 + " (" + file1Name + ":" + (i+1) + ")"
						+ " absDiff: " + decimalFormat.format(absDiff) +
						" (" + percentFormat.format(percentDiff) + " %)");
			}
			count++;
		}
		
		System.out.println("Max Diffs: " + decimalFormat.format(maxAbsDiff) +
						" (" + percentFormat.format(maxPercentDiff) + " %)");
		
		System.out.println("Trunc Match? " + truncMatch + " (" + truncFails + "/" + count + " fails)");
		System.out.println("Round Match? " + roundMatch + " (" + roundFails + "/" + count + " fails)");
	}

	private String getValStrFromLine(String line) {
		line = line.substring(line.indexOf("=")+1);
		line = line.trim();
		return line;
	}

	public static double round(String d, int decimalPlace){
		// see the Javadoc about why we use a String in the constructor
		// http://java.sun.com/j2se/1.5.0/docs/api/java/math/BigDecimal.html#BigDecimal(double)
		BigDecimal bd = new BigDecimal(d);
		bd = bd.setScale(decimalPlace,BigDecimal.ROUND_HALF_UP);
		return bd.doubleValue();
	}
	
	public static void main(String args[]) throws FileNotFoundException, IOException {
//		String file1 = "/home/kevin/workspace/OpenSHA/org/opensha/sha/imr/attenRelImpl/test/AttenRelResultSetFiles/BOORE.txt";
//		String file2 = "/home/kevin/workspace/OpenSHA/org/opensha/sha/imr/attenRelImpl/test/AttenRelResultSetFiles/BOORE.txt_new.txt.good_round";
		
		File dirFile = new File("/home/kevin/workspace/OpenSHA/org/opensha/sha/imr/attenRelImpl/test/AttenRelResultSetFiles/");
		File[] files = dirFile.listFiles();
		
		for (File file : files) {
			if (!file.getName().endsWith(".txt") || file.getName().contains("_new"))
				continue;
			File compFile = new File(file.getAbsolutePath() + "_new.txt");
			if (!compFile.exists())
				continue;
			System.out.println("Comparing: " + file.getName() + " with " + compFile.getName());
			new IMRFilesCheck(file.getAbsolutePath(), compFile.getAbsolutePath());
		}
	}

}
