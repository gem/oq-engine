package org.gem.engine.hazard.parsers.crisis;

import java.io.BufferedReader;
import java.io.IOException;
import java.util.regex.Matcher;
import java.util.regex.Pattern;

public class InputFileSource {

    private String name; // L1 : Name
    private int occMod; // L2 : Occurrence model index: 1 - Poisson, 2-
                        // Characteristic
    private int srcType; // L2 : Source typology: 0 - Area, 1 - Fault, 2 - Point
    private int attMod; // L2 : Index of the GMPEs to be used with this source
    boolean active; // L2 : Switch for activating a source (true = fault active)
    private double rupRad1; // L2 : Parameter for rupture radius calculation
    private double rupRad2; // L2 : Parameter for rupture radius calculation
    private int nVtx; // L3 : Number of vertexes
    private double[][] coords; // L4 : <Lat,Lon>
    private double[] depth; // L4 : Depth of each vertex

    private double occRate; // Lx : Rate of occurrence for earthquakes above the
                            // mmin
    private double betaGR; // Lx : Expected value of the Beta of the ln MFD
    private double betaGRcov; // Lx : betaGRexp coefficient of variation
    private double muUn; // Lx : Mu (Magnitude Upper) un-truncated expected
                         // value
    private double muUnCov; // Lx : muUnTexp coefficient of variation
    private double muMin; // Lx : Mu Lower limit
    private double mmin; // Lx : Minimum magnitude (threshold)
    private double muMax; // Lx : Mu Upper limit

    private double medianRate; // : Median rate of occurrence
    private double timeSinceLast; // : Time since last event
    private double sigmaMChar; // : Sigma of Characteristic Eqk.
    private double mCharMin; // : M Char Min
    private double mCharMax; // : M Char Max
    private double mCharExp; // : M Char Expected value
    private double factSlip; // : Factor for slip dependence

    public double getMedianRate() {
        return this.medianRate;
    }

    public double getTimeSinceLast() {
        return this.timeSinceLast;
    }

    public double getSigmaMChar() {
        return this.sigmaMChar;
    }

    public double getMCharMin() {
        return this.mCharMin;
    }

    public double getMCharMax() {
        return this.mCharMax;
    }

    public double getMCharExp() {
        return this.mCharExp;
    }

    public double factSlip() {
        return this.factSlip;
    }

    public String getName() {
        return name;
    }

    public int getOccMod() {
        return occMod;
    }

    public int getSrcType() {
        return srcType;
    }

    public double getRupRad1() {
        return rupRad1;
    }

    public double getRupRad2() {
        return rupRad2;
    }

    public void setnVtx(int nVtx) {
        this.nVtx = nVtx;
    }

    public double[][] getCoords() {
        return coords;
    }

    public double[] getDepth() {
        return depth;
    }

    public double getOccRate() {
        return occRate;
    }

    public double getBetaGR() {
        return betaGR;
    }

    public double getBetaGRcov() {
        return betaGRcov;
    }

    public double getMuUn() {
        return muUn;
    }

    public double getMuUnCov() {
        return muUnCov;
    }

    public double getMuMin() {
        return muMin;
    }

    public double getMmin() {
        return mmin;
    }

    public double getMuMax() {
        return muMax;
    }

    int boh1; // Lx+1 : Unknown parameter

    /**
     * 
     * @param input
     * @throws IOException
     */
    public InputFileSource(BufferedReader input) throws IOException {

        // Common variables
        int i;
        String[] strarr;
        String line;

        // Define patterns and matchers
        Pattern INTNUM = Pattern.compile("\\d+");
        Pattern UPPCWORD = Pattern.compile("[A-Z]+");
        Pattern FLOATNUM = Pattern.compile("\\d+\\.\\d+");
        Matcher matcher;

        // First line
        this.name = input.readLine();

        // Second line
        line = input.readLine();
        strarr = line.split("\\,");

        // Occurrence model
        matcher = INTNUM.matcher(strarr[0]);
        if (matcher.find())
            this.occMod = Integer.valueOf(matcher.group(0)).intValue();
        // Source type
        matcher = INTNUM.matcher(strarr[1]);
        if (matcher.find())
            this.srcType = Integer.valueOf(matcher.group(0)).intValue();
        // Attenuation model
        matcher = INTNUM.matcher(strarr[2]);
        if (matcher.find())
            this.attMod = Integer.valueOf(matcher.group(0)).intValue();

        matcher = UPPCWORD.matcher(strarr[3]);
        matcher = FLOATNUM.matcher(strarr[4]);

        // if (matcher.find()) this.attMod =
        // Integer.valueOf(matcher.group(0)).intValue();
        // if (matcher.find()) this.attMod =
        // Integer.valueOf(matcher.group(0)).intValue();

        // this.occMod = Integer.valueOf(strarr[0]).intValue();
        // this.srcType = Integer.valueOf(strarr[1]).intValue();
        // this.attMod = Integer.valueOf(strarr[2]).intValue();
        // TODO - There are three params missing we need to read in the first
        // line
        // - Add checks when reading the parameters

        // Third line
        line = input.readLine();
        matcher = INTNUM.matcher(line);
        if (matcher.find())
            this.nVtx = Integer.valueOf(matcher.group(0)).intValue();
        this.coords = new double[this.nVtx][2];
        this.depth = new double[this.nVtx];

        // Read source vertex block
        for (i = 0; i < this.nVtx; i++) {
            strarr = input.readLine().split("\\,");
            this.coords[i][0] = Double.valueOf(strarr[0]).doubleValue();
            this.coords[i][1] = Double.valueOf(strarr[1]).doubleValue();
            this.depth[i] = Double.valueOf(strarr[2]).doubleValue();
        }

        // Reads the two lines below the coordinates block
        if (this.occMod == 1) {
            strarr = input.readLine().split("\\,");
            this.occRate = Double.valueOf(strarr[0]).doubleValue();
            this.betaGR = Double.valueOf(strarr[1]).doubleValue();
            this.betaGRcov = Double.valueOf(strarr[2]).doubleValue();
            this.muUn = Double.valueOf(strarr[3]).doubleValue();
            this.muUnCov = Double.valueOf(strarr[4]).doubleValue();
            this.muMin = Double.valueOf(strarr[5]).doubleValue();
            this.mmin = Double.valueOf(strarr[6]).doubleValue();
            this.muMax = Double.valueOf(strarr[7]).doubleValue();
        } else if (this.occMod == 2) {
            strarr = input.readLine().split("\\,");
            this.medianRate = Double.valueOf(strarr[0]).doubleValue();
            this.timeSinceLast = Double.valueOf(strarr[1]).doubleValue();
            this.mCharExp = Double.valueOf(strarr[2]).doubleValue();
            this.factSlip = Double.valueOf(strarr[3]).doubleValue();
            this.sigmaMChar = Double.valueOf(strarr[4]).doubleValue();
            this.mCharMin = Double.valueOf(strarr[5]).doubleValue();
            this.mCharMax = Double.valueOf(strarr[6]).doubleValue();
        } else {
            //
        }
        // Last line
        line = input.readLine();

    }
}
