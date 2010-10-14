package org.gem.engine.hazard.parsers.crisis;

import java.io.BufferedReader;
import java.io.IOException;
import java.util.regex.Matcher;
import java.util.regex.Pattern;

public class InputFileHeader {

    String comment; // L1 : Comment
    String name; // L3 : Name
    int nRegions; // L4 : Number of Sources
    int nAttMod; // L4 : Number of GMPEs
    int nSpecOrd; // L4 : Number of spectral ordinates
    int nIntLev; // L4 : Number of intensity levels used to compute the Haz.
                 // Curve
    double[][] SpecOrd; // L5 : Spectral ordinate (each row: T, Lower Limit,
                        // Upper Limit)
    String[] SpecOrdUM; // L5 : Units of measure of the spectral ordinate

    double maxDist; // L5+nSpecOrd+1: Maximum distance (considers contributions
                    // coming from shorter distances)
    double ratioTriDist; // L5+nSpecOrd+1: Ratio between triangle size and
                         // maximum distance
    double minTriSize; // L5+nSpecOrd+1: Minimum triangle size [km]
    double retPeriods[]; // L5+nSpecOrd+1: Return periods [yr]
    int dsgDistance; // L5+nSpecOrd+1: Disaggregation distance type
    double latOrig; // L : Latitude of the origin
    double lonOrig; // L : Longitude of the origin
    double deltalat; // L : Step in Latitude
    double deltalon; // L : Step in Longitude
    int nLinesX; // L :
    int nLinesY; // L :
    int nPolygrd; // L5+nSpecOrd+3: Number of polygons where compute the hazard
    String[] gmpeName; // : Names of adopted GMPEs

    /**
     * 
     * @param input
     * @throws IOException
     */
    public InputFileHeader(BufferedReader input) throws IOException {

        // Common variables
        int i;
        String[] strarr;
        String line;

        // Define patterns and matchers
        Pattern BUILT = Pattern.compile("^BUILT");
        Pattern SPACE = Pattern.compile("\\s");
        Pattern NOTNUMBER = Pattern.compile("[^[0-9]]+");
        Pattern INTNUMBER = Pattern.compile("\\d+");
        Matcher matcher;

        // First line
        this.comment = input.readLine();

        // Second line
        line = input.readLine();

        // Third line
        this.name = input.readLine();

        // Fourth line
        strarr = input.readLine().split("\\,");
        this.nRegions = Integer.valueOf(strarr[0]).intValue();
        this.nAttMod = Integer.valueOf(strarr[1]).intValue();
        this.nSpecOrd = Integer.valueOf(strarr[2]).intValue();
        this.nIntLev = Integer.valueOf(strarr[3]).intValue();

        // Reading spectral ordinates
        this.SpecOrd = new double[nSpecOrd][3];
        this.SpecOrdUM = new String[nSpecOrd];
        for (i = 0; i < this.nSpecOrd; i++) {
            strarr = input.readLine().split("\\,");
            this.SpecOrd[i][0] = Double.valueOf(strarr[0]).doubleValue();
            this.SpecOrd[i][1] = Double.valueOf(strarr[1]).doubleValue();
            this.SpecOrd[i][2] = Double.valueOf(strarr[2]).doubleValue();
            this.SpecOrdUM[i] = strarr[3];
        }

        // First line after spectral ordinates: Triangulation and return periods
        strarr = input.readLine().split("\\,");
        this.maxDist = Double.valueOf(strarr[0]).doubleValue();
        this.ratioTriDist = Double.valueOf(strarr[1]).doubleValue();
        this.minTriSize = Double.valueOf(strarr[2]).doubleValue();
        this.retPeriods = new double[8];
        for (i = 3; i < strarr.length - 1; i++) {
            this.retPeriods[i - 3] = Double.valueOf(strarr[i]).doubleValue();
        }

        // Second line after spectral ordinates: Reference grid where compute
        // the hazard
        strarr = input.readLine().split("\\,");
        this.lonOrig = Double.valueOf(strarr[0]).doubleValue();
        this.lonOrig = Double.valueOf(strarr[1]).doubleValue();
        this.deltalon = Double.valueOf(strarr[2]).doubleValue();
        this.deltalat = Double.valueOf(strarr[3]).doubleValue();
        this.nLinesX = Integer.valueOf(strarr[4]).intValue();
        this.nLinesY = Integer.valueOf(strarr[5]).intValue();

        // Number of Polygons where compute hazard
        line = input.readLine();
        matcher = INTNUMBER.matcher(line);
        if (matcher.find()) {
            this.nPolygrd = Integer.valueOf(matcher.group(0)).intValue();
            // Read info about alternative grids
            if (this.nPolygrd > 0) {
                line = input.readLine();
                line = line.trim();
                int eee = Integer.valueOf(line).intValue();
                for (int w = 0; w < eee; w++) {
                    line = input.readLine();
                }
            }
        } else {
            // Error: cannot find the number of
            // TODO
        }

        // Read attenuation relationships
        for (i = 0; i < this.nAttMod; i++) {
            line = input.readLine();
            matcher = BUILT.matcher(line);
            if (matcher.find()) {
                // Reads GMPE parameters
                strarr = input.readLine().split("\\,");
            } else {
                // Do nothing
            }
        }
    }
}
