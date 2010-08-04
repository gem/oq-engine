package scratch.kevin;

import java.io.FileNotFoundException;
import java.io.FileWriter;
import java.io.IOException;
import java.util.ArrayList;
import java.util.StringTokenizer;

import org.opensha.commons.util.FileUtils;
import org.opensha.commons.util.XYZHashMap;

public class XYZSubtractor {
	
	public XYZSubtractor() {
		
	}
	
	public void subtract(String file1, String file2, String outFile, boolean abs) throws FileNotFoundException, IOException {
		XYZHashMap map = new XYZHashMap(file1);
		
		ArrayList<String> lines = FileUtils.loadFile(file2);
		
		FileWriter fw = new FileWriter(outFile);
		
		for (String line : lines) {
			line = line.trim();
			if (line.length() < 2)
				continue;
			StringTokenizer tok = new StringTokenizer(line);
			double lat = Double.parseDouble(tok.nextToken());
			double lon = Double.parseDouble(tok.nextToken());
			double val2 = Double.parseDouble(tok.nextToken());
			
			double val1 = map.get(lat, lon);
			
			double sub;
			
			if (abs)
				sub = Math.abs(val1 - val2);
			else
				sub = val1 - val2;
			
			fw.write(lat + " " + lon + " " + sub + "\n");
		}
		
		fw.close();
	}

	/**
	 * @param args
	 */
	public static void main(String[] args) {
		XYZSubtractor sub = new XYZSubtractor();
		
		String file1 = "/home/kevin/CyberShake/scatterMap/base_cb.txt";
		String file2 = "/home/kevin/CyberShake/scatterMap/base_ba.txt";
		String outFile = "/home/kevin/CyberShake/scatterMap/diff.txt";
		
		try {
			sub.subtract(file1, file2, outFile, true);
		} catch (FileNotFoundException e) {
			// TODO Auto-generated catch block
			e.printStackTrace();
		} catch (IOException e) {
			// TODO Auto-generated catch block
			e.printStackTrace();
		}
	}

}
