package junk;

import java.io.BufferedReader;
import java.io.BufferedWriter;
import java.io.FileReader;
import java.io.FileWriter;
import java.util.StringTokenizer;

/**
 * <p>Title: GenerateBasinDepth</p>
 * <p>Description: </p>
 * <p>Copyright: Copyright (c) 2002</p>
 * <p>Company: </p>
 * @author unascribed
 * @version 1.0
 */

public class GenerateBasinDepth {

  public GenerateBasinDepth(){
    boolean flag = false;
    try{
      FileWriter fw = new FileWriter("/Users/nitingupta/test_cvmfiles/basindepth_OpenSHA_temp.txt");
      BufferedWriter bw = new BufferedWriter(fw);
      FileReader fr = new FileReader("/Users/nitingupta/cvmfiles/OpenSHA8.txt");
      BufferedReader  br = new BufferedReader(fr);
      String line = br.readLine();
      StringTokenizer st = new StringTokenizer(line);
      double lat1=  Double.parseDouble(st.nextToken());
      double lon1 = Double.parseDouble(st.nextToken());
      double depth1 = Double.parseDouble(st.nextToken());
      st.nextToken();
      double velocity1 = Double.parseDouble(st.nextToken());
      while(line!=null){
        if(depth1 == 0 && velocity1 >2500){
          bw.write(lat1+" "+lon1+" "+"0"+"\n");
          flag = true;
        }
        else if(velocity1 == 2500){
          bw.write(lat1+" "+lon1+" "+depth1+"\n");
          flag = true;
        }
        else{
          line = br.readLine();
          st = new StringTokenizer(line);
          double lat2 = Double.parseDouble(st.nextToken());
          double lon2 = Double.parseDouble(st.nextToken());
          double depth2 = Double.parseDouble(st.nextToken());
          st.nextToken();
          double velocity2 = Double.parseDouble(st.nextToken());
          if(velocity1<2500 && velocity2>2500){
            //does interpolation of the depth1 and depth2
            double depth = ((2500 - velocity1)*(depth2 -depth1)/(velocity2-velocity1))+depth1;
            bw.write(lat2+" "+lon2+" "+depth+"\n");
            flag= true;
          }
          else{
            lat1 = lat2;
            lon1 = lon2;
            depth1 = depth2;
            velocity1 = velocity2;
            flag = false;
          }
        }
        if(flag){
          line = br.readLine();
          st = new StringTokenizer(line);
          double lat3 = Double.parseDouble(st.nextToken());
          double lon3 = Double.parseDouble(st.nextToken());
          while(lat3==lat1 && lon3==lon1){
            line = br.readLine();
            if(line ==null){
              bw.flush();
              bw.close();
              fw.close();
              br.close();
              fr.close();
              System.exit(101);
            }
            st = new StringTokenizer(line);
            lat3 = Double.parseDouble(st.nextToken());
            lon3 = Double.parseDouble(st.nextToken());
          }
          lat1 = lat3;
          lon1 = lon3;
          depth1  = Double.parseDouble(st.nextToken());
          st.nextToken();
          velocity1 = Double.parseDouble(st.nextToken());
        }
      }
      System.out.println("closing all files");
      bw.flush();
      bw.close();
      fw.close();
      br.close();
      fr.close();
    }catch(Exception e){
      e.printStackTrace();
    }
  }


  public static void main(String args[]){
    new GenerateBasinDepth();
  }

}
