package scratch.kevin;

import java.io.FileWriter;
import java.io.IOException;

import org.opensha.sha.earthquake.calc.recurInterval.BPT_DistCalc;

public class BPT_PlotForTom {

	public static void main(String args[]) throws IOException {
		BPT_DistCalc bpt = new BPT_DistCalc();
		
		double aperiodicity = 0.5;
//		int nYr = 30;
		int nYr = 5;
		
		int inc = 1;
		
//		bpt.setAll((1/rate[i]), aperiodicity);
//		double prob = bpt.getCondProb(timeSinceLast,nYr);
		
		FileWriter fw = new FileWriter("/tmp/bpt_vals.txt");
		
		for (double timeSinceLast=0; timeSinceLast<=600; timeSinceLast+=inc) {
			for (double recurranceInterval=0; recurranceInterval<=600; recurranceInterval+=inc) {
				
				System.out.println("calc for timeSinceLast=" + timeSinceLast + ", recurranceInterval=" + recurranceInterval);
				
				bpt.setAll((recurranceInterval), aperiodicity);
				double prob;
				try {
					prob = bpt.getCondProb(timeSinceLast,nYr);
				} catch (Exception e) {
					e.printStackTrace();
					continue;
				}
				
				fw.write((int)recurranceInterval + "\t" + (int)timeSinceLast + "\t" + prob + "\n");
			}
		}
		
		fw.close();
	}
}
