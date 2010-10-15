package org.gem.engine.hazard.parsers.gscFrisk.canada;

import java.io.BufferedReader;
import java.io.IOException;
import java.util.ArrayList;
import java.util.regex.Matcher;
import java.util.regex.Pattern;

public class GscFriskInputAlternative {

    private String commAlt; // L1 Alt : Comment on alternative x
    private int nSrcSets; // L2 Alt : Number of sources
    private int nNuBeta; // L2 Alt : Number of <nu,beta> pairs
    private int nMaxMag; // L2 Alt : NUmber of max magnitude values
    private int nDepths; // L2 Alt : NUmber of depths
    private int nSrcTot; // L2 Alt : Total number of sources in the source set
    private int maxVtx; // L2 Alt : Maximum number of points used to describe a
                        // source
    private double[] maxMagWei; // L3 Alt : Weights for Max Magnitudes
    private double[] nuBetaWei; // L4 Alt : Weights for Nu Beta pairs
    private double[] depthsWei; // L5 Alt : Weight for depths values

    private boolean maxMagFlg; // L1 After Alt: Flag (1 if Mmax is source
                               // dependent)
    private boolean nuBetaFlg; // L1 After Alt: Flag (1 if nuBeta pairs are
                               // dependent)
    private boolean depthsFlg; // L1 After Alt: Flag (1 if depths pairs are
                               // dependent)
    private boolean gmpeFlg; // L1 After Alt: Flag (1 if gmpes pairs are
                             // dependent)

    // Source set
    private ArrayList<GscFriskInputSourceSet> sourceSet;

    /**
     * 
     * @param input
     * @throws IOException
     */
    public GscFriskInputAlternative(BufferedReader input,
            GscFriskInputHeader head) throws IOException {

        this.sourceSet = new ArrayList<GscFriskInputSourceSet>();

        // General variables
        int i;
        int j;
        String[] strarr;
        String line;

        // Define patterns and matchers
        Pattern INTNUM = Pattern.compile("\\d+");
        Pattern FLOATNUM = Pattern.compile("([0-9]+\\.*[0-9]*)");
        Matcher matcher;

        // First line
        this.commAlt = input.readLine();

        // Second line
        line = input.readLine();
        strarr = line.split("\\s+");
        matcher = INTNUM.matcher(strarr[0]);
        if (matcher.find())
            this.nSrcSets = Integer.valueOf(matcher.group(0)).intValue();
        matcher = INTNUM.matcher(strarr[1]);
        if (matcher.find())
            this.nNuBeta = Integer.valueOf(matcher.group(0)).intValue();
        matcher = INTNUM.matcher(strarr[2]);
        if (matcher.find())
            this.nMaxMag = Integer.valueOf(matcher.group(0)).intValue();
        matcher = INTNUM.matcher(strarr[3]);
        if (matcher.find())
            this.nDepths = Integer.valueOf(matcher.group(0)).intValue();
        matcher = INTNUM.matcher(strarr[4]);
        if (matcher.find())
            this.nSrcTot = Integer.valueOf(matcher.group(0)).intValue();
        matcher = INTNUM.matcher(strarr[5]);
        if (matcher.find())
            this.maxVtx = Integer.valueOf(matcher.group(0)).intValue();

        System.out.printf("%2d \n", this.nSrcSets);

        // Third line
        line = input.readLine();
        strarr = line.split("\\s+");
        this.maxMagWei = new double[this.nMaxMag];
        for (j = 0; j < this.nMaxMag; j++) {
            matcher = FLOATNUM.matcher(strarr[j]);
            if (matcher.find()) {
                this.maxMagWei[j] =
                        Double.valueOf(matcher.group(0)).doubleValue();
            } else {
                System.out.print("Max mag weight not found");
            }
        }

        // Fourth line
        line = input.readLine();
        strarr = line.split("\\s+");
        nuBetaWei = new double[this.nNuBeta];
        for (j = 0; j < this.nNuBeta; j++) {
            matcher = FLOATNUM.matcher(strarr[j]);
            if (matcher.find()) {
                this.nuBetaWei[j] =
                        Double.valueOf(matcher.group(0)).doubleValue();
            } else {
                System.out.print("Nu beta weight not found");
            }
        }

        // Fifth line
        line = input.readLine();
        strarr = line.split("\\s+");
        depthsWei = new double[this.nDepths];
        for (j = 0; j < this.nDepths; j++) {
            matcher = FLOATNUM.matcher(strarr[j]);
            if (matcher.find()) {
                this.depthsWei[j] =
                        Double.valueOf(matcher.group(0)).doubleValue();
            } else {
                System.out.print("Depth weight not found");
            }
        }

        // Sixth line
        line = input.readLine();
        strarr = line.split("\\s+");
        matcher = INTNUM.matcher(strarr[0]);
        if (matcher.find()) {
            this.maxMagFlg = false;
            if (Integer.valueOf(matcher.group(0)).intValue() == 1)
                this.maxMagFlg = true;
        }
        //
        matcher = INTNUM.matcher(strarr[1]);
        if (matcher.find()) {
            this.nuBetaFlg = false;
            if (Integer.valueOf(matcher.group(0)).intValue() == 1)
                this.nuBetaFlg = true;
        }
        //
        matcher = INTNUM.matcher(strarr[2]);
        if (matcher.find()) {
            this.depthsFlg = false;
            if (Integer.valueOf(matcher.group(0)).intValue() == 1)
                this.depthsFlg = true;
        }
        //
        matcher = INTNUM.matcher(strarr[3]);
        if (matcher.find()) {
            this.gmpeFlg = false;
            if (Integer.valueOf(matcher.group(0)).intValue() == 1)
                this.gmpeFlg = true;
        }
        //
        // // Reads the source sets
        // for (i = 0; i < this.nSrcSets; i++){
        // // Call the
        // }
    }

    public void addSourceSet(GscFriskInputSourceSet srcSet) {
        this.sourceSet.add(srcSet);
    }

    public GscFriskInputSourceSet getSourceSet(int idx) {
        return this.sourceSet.get(idx);
    }

    public String getComment() {
        return this.commAlt;
    }

    public void setComment(String comm) {
        this.commAlt = comm;
    }

    public int getNumberSourceSets() {
        return this.nSrcSets;
    }

    public void setNumberSourceSets(int nsrc) {
        this.nSrcSets = nsrc;
    }

    public int getNumberNuBeta() {
        return this.nNuBeta;
    }

    public void setNumberNuBeta(int nub) {
        this.nNuBeta = nub;
    }

    public int getNumberMaxMag() {
        return this.nMaxMag;
    }

    public void setNumberMaxMag(int numm) {
        this.nMaxMag = numm;
    }

    public int getNumberDepths() {
        return this.nDepths;
    }

    public void setNumberDepths(int numm) {
        this.nDepths = numm;
    }

    public int getNumberSources() {
        return this.nSrcTot;
    }

    public void setNumberSources(int numm) {
        this.nSrcTot = numm;
    }

    public int getMaxNumberVtx() {
        return this.maxVtx;
    }

    public void setMaxNumberVtx(int numm) {
        this.maxVtx = numm;
    }

    public double[] getMaxMagWeights() {
        return this.maxMagWei;
    }

    public void setMaxMagWeights(double[] numm) {
        this.maxMagWei = numm;
    }

    public double[] getNuBetaWeights() {
        return this.nuBetaWei;
    }

    public void setNuBetaWeights(double[] numm) {
        this.nuBetaWei = numm;
    }

    public double[] getDepthsWeights() {
        return this.depthsWei;
    }

    public void setDepthsWeights(double[] numm) {
        this.depthsWei = numm;
    }

    public boolean getMaxMagFlg() {
        return this.maxMagFlg;
    }

    public void setMaxMagFlg(boolean flg) {
        this.maxMagFlg = flg;
    }

    public boolean getNuBetaFlg() {
        return this.nuBetaFlg;
    }

    public void setNuBetaFlg(boolean flg) {
        this.nuBetaFlg = flg;
    }

    public boolean getDepthsFlg() {
        return this.depthsFlg;
    }

    public void setDepthsFlg(boolean flg) {
        this.depthsFlg = flg;
    }

    public boolean getGmpeFlg() {
        return this.gmpeFlg;
    }

    public void setGmpeFlg(boolean flg) {
        this.gmpeFlg = flg;
    }

}
