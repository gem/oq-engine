package scratch.matt;

import java.util.ArrayList;
import java.util.StringTokenizer;

import org.opensha.commons.util.FileUtils;

/**
 * <p>Title: </p>
 * <p>Description: </p>
 * <p>Copyright: Copyright (c) 2002</p>
 * <p>Company: </p>
 * @author unascribed
 * @version 1.0
 */

public class Test {



  public Test() {
    ArrayList backGroundRates = new ArrayList();
    try{
    ArrayList frankel96bg = FileUtils.loadFile("/home/matt/daily_rates.txt");
    for(int readLoop = 0;readLoop<frankel96bg.size();++readLoop){
      StringTokenizer st = new StringTokenizer((String)frankel96bg.get(readLoop));
      double[] backGroundRatesLine = new double[64];
      int i = 0;
      while(st.hasMoreTokens()){
      backGroundRatesLine[i++] = Double.parseDouble(st.nextToken().trim());
          }
       backGroundRates.add(backGroundRatesLine);
    }
    }
    catch(Exception e){e.printStackTrace();
    }
  }
  public static void main(String[] args) {
    Test test1 = new Test();
  }

}
