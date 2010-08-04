package scratch.kevin;

import java.io.IOException;
import java.io.OutputStream;
import java.io.PrintStream;

import org.opensha.commons.data.TimeSpan;
import org.opensha.commons.param.ParameterAPI;
import org.opensha.commons.util.FileUtils;
import org.opensha.sha.earthquake.EqkRupForecastAPI;
import org.opensha.sha.earthquake.rupForecastImpl.WGCEP_UCERF_2_3.UCERF2;
import org.opensha.sha.earthquake.rupForecastImpl.WGCEP_UCERF_2_3.MeanUCERF2.MeanUCERF2;

public class ERFSaveAndSerializeTest {
	
	public ERFSaveAndSerializeTest() {
		EqkRupForecastAPI erf = new MeanUCERF2();
		ParameterAPI backgroundParam = erf.getAdjustableParameterList().getParameter(UCERF2.BACK_SEIS_NAME);
		backgroundParam.setValue(UCERF2.BACK_SEIS_INCLUDE);
		System.out.println("Background Seismicity: " + backgroundParam.getValue());
		
//		EqkRupForecastAPI erf = new Frankel02_AdjustableEqkRupForecast();
//		ParameterAPI backgroundParam = erf.getAdjustableParameterList().getParameter(Frankel02_AdjustableEqkRupForecast.BACK_SEIS_NAME);
//		backgroundParam.setValue(Frankel02_AdjustableEqkRupForecast.BACK_SEIS_INCLUDE);
//		System.out.println("Background Seismicity: " + backgroundParam.getValue());
		
		TimeSpan time = new TimeSpan(TimeSpan.YEARS, TimeSpan.YEARS);
		time.setStartTime(2007);
		time.setDuration(30);
		erf.setTimeSpan(time);
		erf.updateForecast();
		//System.out.println("Sources: " + erf.getNumSources());
		try {
			FileUtils.saveObjectInFile("erf.obj", erf);
			EqkRupForecastAPI erf2 = null;
			System.out.println("TRYING...");
			erf2 = (EqkRupForecastAPI)FileUtils.loadObject("erf.obj");
			System.out.println("WOW DID THIS ACTUALLY WORK????");
			System.out.println("Equals? " + erf.equals(erf2));
			//System.out.println("Loaded Sources: " + erf2.getNumSources());
		} catch (Exception e) {
			CloneStream err = new CloneStream(new FakeOutputStream());
			PrintStream oldErr = System.err;
			System.setErr(err);
			Serialize serial = new Serialize("/home/kevin/workspace/jQuake/");
			//serial.handleException(e.getStackTrace());
			e.printStackTrace();
			try {
				Thread.sleep(500);
				//System.out.println(err.getOutput());
				String output = err.getOutput();
				System.setErr(oldErr);
				serial.handleException(output);
			} catch (InterruptedException e1) {
				System.out.println("AHHHHHHHH!");
				System.exit(1);
			}
		}
	}

	
	
	private class FakeOutputStream extends OutputStream {
		public void write(int arg0) throws IOException {}
	}
	
	private class CloneStream extends PrintStream {
		String output = "";
		
		CloneStream(OutputStream s) {
			super(s);
		}
		
		private void printIt(String it) {
			output += it;
		}
		
		public void clear() {
			output = "";
		}
		
		public String getOutput() {
			return output;
		}

		//replace all print methods
		public void print(int arg) {
			printIt(arg + "");
		}
		public void print(float arg) {
			printIt(arg + "");
		}
		public void print(double arg) {
			printIt(arg + "");
		}
		public void print(long arg) {
			printIt(arg + "");
		}
		public void print(char arg) {
			printIt(arg + "");
		}
		public void print(char[] arg) {
			printIt(String.valueOf(arg) + "");
		}
		public void print(boolean arg) {
			printIt(arg + "");
		}
		public void print(Object arg) {
			printIt(arg + "");
		}
		public void print(String arg) {
			printIt(arg + "");
		}
		
//		replace all println methods
		public void println() {
			printIt("\n");
		}
		public void println(int arg) {
			printIt(arg + "\n");
		}
		public void println(float arg) {
			printIt(arg + "\n");
		}
		public void println(double arg) {
			printIt(arg + "\n");
		}
		public void println(long arg) {
			printIt(arg + "\n");
		}
		public void println(char arg) {
			printIt(arg + "\n");
		}
		public void println(char[] arg) {
			printIt(String.valueOf(arg) + "\n");
		}
		public void println(boolean arg) {
			printIt(arg + "\n");
		}
		public void println(Object arg) {
			printIt(arg + "\n");
		}
		public void println(String arg) {
			printIt(arg + "\n");
		}
	}
	
	/**
	 * @param args
	 */
	public static void main(String[] args) {
		new ERFSaveAndSerializeTest();
		System.exit(0);
	}

}
