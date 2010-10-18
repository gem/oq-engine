package org.gem.engine.hazard.parsers.gscFrisk.canada;

import java.io.BufferedReader;
import java.io.IOException;
import java.util.regex.Matcher;
import java.util.regex.Pattern;

public class GscFriskInputHeader {

    String[] comm; // L1+L2+L4 : Title
    int npexc; // L3 : Number of Probabilities of exceedance
    double[] prbexc; // L3 : Probabilities of exceedance
    int natt; // L5 : Number of GMPEs
    int nstep; // L5 : Number of steps used in the integration
    double vIncr; // L5 : Vertical increment along a fault surface [km]
    double hIncr; // L5 : Horizontal increment used for floating ruptures [km]
    double amStep; // L5 : Increment for integration over magnitude []
    int nRupL; // L5 : Number of rupture lengths to account of m-length
               // variability
    int outContrl; // L5 : Output control param

    int nVals; // L6 : Number of GM values to use in the calculation
    double[] vals; // L6 : Values of Ground motion

    String sTypes; // L8 : Source types used (F - fault; A - Area; B - Both)

    String[] gmpeComm; // L9 : GMPE comment
    String[][] gmpePar; // L10 : GMPE params

    int nGloAlt; // L1 aft GMPE : Number of Global Alternatives
    double[] weiAlt; // L1 aft GMPE : Weights of alternatives

    /**
     * 
     * @param input
     * @throws IOException
     */
    public GscFriskInputHeader(BufferedReader input) throws IOException {

        // General variables
        int i;
        int j;
        String[] strarr;
        String line;

        // Define patterns and matchers
        Pattern INTNUM = Pattern.compile("\\d+");
        Pattern UPPCWORD = Pattern.compile("[A-Z]+");
        // Pattern FLOATNUM = Pattern.compile("[A-Z]+");
        Pattern FLOATNUM = Pattern.compile("\\d+\\.\\d+");
        Matcher matcher;

        // First line
        this.comm = new String[3];
        this.comm[0] = input.readLine();
        // Second line
        this.comm[1] = input.readLine();
        // Third line
        strarr = input.readLine().split("\\s+");
        matcher = INTNUM.matcher(strarr[0]);
        if (matcher.find())
            this.npexc = Integer.valueOf(matcher.group(0)).intValue();
        this.prbexc = new double[this.npexc];
        for (i = 0; i < this.npexc; i++) {
            matcher = FLOATNUM.matcher(strarr[i]);
            this.prbexc[i] = Double.valueOf(strarr[i + 1]).doubleValue();
        }
        // Fourth line
        this.comm[2] = input.readLine();
        // Fifth line
        line = input.readLine();
        strarr = line.split("\\s+");
        matcher = INTNUM.matcher(strarr[0]);
        if (matcher.find())
            this.natt = Integer.valueOf(matcher.group(0)).intValue();
        if (INTNUM.matcher(strarr[1]).find())
            this.nstep = Integer.valueOf(matcher.group(0)).intValue();
        if (FLOATNUM.matcher(strarr[2]).find())
            this.vIncr = Double.valueOf(matcher.group(0)).doubleValue();
        if (FLOATNUM.matcher(strarr[3]).find())
            this.hIncr = Double.valueOf(matcher.group(0)).doubleValue();
        if (INTNUM.matcher(strarr[4]).find())
            this.nRupL = Integer.valueOf(matcher.group(0)).intValue();
        if (INTNUM.matcher(strarr[5]).find())
            this.outContrl = Integer.valueOf(matcher.group(0)).intValue();
        // Sixth line
        strarr = input.readLine().split("\\s+");
        if (INTNUM.matcher(strarr[0]).find())
            this.nVals = Integer.valueOf(matcher.group(0)).intValue();
        this.vals = new double[this.nVals];
        for (i = 0; i < this.nVals; i++) {
            matcher = FLOATNUM.matcher(strarr[i]);
            this.vals[i] = Double.valueOf(strarr[i + 1]).doubleValue();
        }
        // Seventh line
        // TODO
        line = input.readLine();
        // Eighth line
        this.sTypes = input.readLine();
        // GMPE blocks
        this.gmpeComm = new String[this.natt];
        for (i = 0; i < this.natt; i++) {
            this.gmpeComm[i] = input.readLine();
            // I don't read the params of the GMPE because I don't need it
            line = input.readLine();
        }
        // 1st line - Global alternatives block
        line = input.readLine();
        System.out.println(line);
        strarr = line.split("\\s+");
        matcher = INTNUM.matcher(strarr[0]);
        if (matcher.find())
            this.nGloAlt = Integer.valueOf(matcher.group(0)).intValue();
        this.weiAlt = new double[this.nGloAlt];
        for (i = 0; i < this.nGloAlt; i++) {
            matcher = FLOATNUM.matcher(strarr[i]);
            this.weiAlt[i] = Double.valueOf(strarr[i + 1]).doubleValue();
        }

    }
}
