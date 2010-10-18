package org.gem.engine.hazard.parsers.turkeyEmme;

import java.io.BufferedReader;
import java.io.BufferedWriter;
import java.io.File;
import java.io.FileNotFoundException;
import java.io.FileReader;
import java.io.FileWriter;
import java.io.IOException;
import java.util.ArrayList;
import java.util.Iterator;
import java.util.regex.Matcher;
import java.util.regex.Pattern;

import org.opensha.commons.geo.Location;
import org.opensha.commons.geo.LocationList;

public class TurkeyReadGMLFileSourceZones {

    private ArrayList<String> code;
    private ArrayList<String> name;
    private ArrayList<LocationList> coords;

    /**
     * Constructor
     */
    public TurkeyReadGMLFileSourceZones(BufferedReader input) {
        int i;
        String sCurrentLine;
        String stringa;
        Matcher match;
        String[] strarr;
        Double coo[][];
        double tmpLo, tmpLa;
        LocationList lol;
        boolean info = false;

        // Define patterns
        Pattern NAMEPATT = Pattern.compile("^<fme:NAME>(.+)</fme:NAME>");
        Pattern FAULTPATT =
                Pattern.compile("^<fme:FAULT_NAME>(.+)</fme:FAULT_NAME>");
        Pattern COORTPATT = Pattern.compile("^<gml:posList>(.+)</gml:posList>");

        // Initialize the containers with information relative to sources
        this.setCode(new ArrayList<String>());
        this.setName(new ArrayList<String>());
        this.setCoords(new ArrayList<LocationList>());

        // Reading the file
        try {
            // Instantiate a BufferedReader
            // BufferedReader input = new BufferedReader(new
            // FileReader(fleName));
            // Try to read file
            try {

                // Cycle over lines
                while ((sCurrentLine = input.readLine()) != null) {

                    // Search codes
                    match = NAMEPATT.matcher(sCurrentLine);
                    if (match.find()) {
                        this.getCode().add(match.group(1));
                        if (info)
                            System.out.println(match.group(1));
                    }

                    // Search names
                    match = FAULTPATT.matcher(sCurrentLine);
                    if (match.find()) {
                        String str = match.group(1);
                        str = str.trim();
                        this.getName().add(str);
                        if (info)
                            System.out.println("  " + match.group(1));
                    }

                    match = COORTPATT.matcher(sCurrentLine);
                    if (match.find()) {
                        stringa = match.group(1);
                        stringa = stringa.trim();
                        strarr = stringa.split("\\s+");
                        // Find the number of rows
                        int nrow = Math.round(strarr.length - 2);
                        coo = new Double[nrow][2];
                        // Reading coordinates
                        int cli = 0;
                        lol = new LocationList();
                        for (i = 0; i < strarr.length - 2; i = i + 2) {
                            if (info)
                                System.out.printf("%s %s\n", strarr[i],
                                        strarr[i + 1]);
                            // Create a location <lat,lon>
                            tmpLa = Double.valueOf(strarr[i]).doubleValue();
                            tmpLo = Double.valueOf(strarr[i + 1]).doubleValue();
                            Location loc = new Location(tmpLa, tmpLo);
                            // Add a location <lat,lon>
                            lol.add(loc);
                        }
                        this.getCoords().add(lol);
                    }
                }
            } finally {
                input.close();
            }
        } catch (FileNotFoundException e) {
            e.printStackTrace();
        } catch (IOException e) {
            e.printStackTrace();
        }
    }

    /**
     * Constructor
     */
    public TurkeyReadGMLFileSourceZones(String filename) {
        int i;
        String sCurrentLine;
        String stringa;
        Matcher match;
        String[] strarr;
        Double coo[][];
        double tmpLo, tmpLa;
        LocationList lol;
        boolean info = false;

        // Define patterns
        Pattern NAMEPATT = Pattern.compile("^<fme:NAME>(.+)</fme:NAME>");
        Pattern FAULTPATT =
                Pattern.compile("^<fme:FAULT_NAME>(.+)</fme:FAULT_NAME>");
        Pattern COORTPATT = Pattern.compile("^<gml:posList>(.+)</gml:posList>");

        // Initialize the containers with information relative to sources
        this.setCode(new ArrayList<String>());
        this.setName(new ArrayList<String>());
        this.setCoords(new ArrayList<LocationList>());

        // Reading the file
        try {
            // Instantiate a BufferedReader
            BufferedReader input = new BufferedReader(new FileReader(filename));
            // Try to read file
            try {

                // Cycle over lines
                while ((sCurrentLine = input.readLine()) != null) {

                    // Search codes
                    match = NAMEPATT.matcher(sCurrentLine);
                    if (match.find()) {
                        this.getCode().add(match.group(1));
                        if (info)
                            System.out.println(match.group(1));
                    }

                    // Search names
                    match = FAULTPATT.matcher(sCurrentLine);
                    if (match.find()) {
                        String str = match.group(1);
                        str = str.trim();
                        this.getName().add(str);
                        if (info)
                            System.out.println("  " + match.group(1));
                    }

                    match = COORTPATT.matcher(sCurrentLine);
                    if (match.find()) {
                        stringa = match.group(1);
                        stringa = stringa.trim();
                        strarr = stringa.split("\\s+");
                        // Find the number of rows
                        int nrow = Math.round(strarr.length - 2);
                        coo = new Double[nrow][2];
                        // Reading coordinates
                        int cli = 0;
                        lol = new LocationList();
                        for (i = 0; i < strarr.length - 2; i = i + 2) {
                            if (info)
                                System.out.printf("%s %s\n", strarr[i],
                                        strarr[i + 1]);
                            // Create a location <lat,lon>
                            tmpLa = Double.valueOf(strarr[i]).doubleValue();
                            tmpLo = Double.valueOf(strarr[i + 1]).doubleValue();
                            Location loc = new Location(tmpLa, tmpLo);
                            // Add a location <lat,lon>
                            lol.add(loc);
                        }
                        this.getCoords().add(lol);
                    }
                }
            } finally {
                input.close();
            }
        } catch (FileNotFoundException e) {
            e.printStackTrace();
        } catch (IOException e) {
            e.printStackTrace();
        }
    }

    public void createGMTfile(String outdir) {

        String filename = outdir + "DatGMT/turkeyAreaSources.gmt";
        String filenameCode = outdir + "DatGMT/turkeyAreaSourcesCodes.gmt";
        //
        int i;
        double sumLo = 0.0, sumLa = 0.0;
        // Browse the list of sources
        ArrayList<LocationList> coor = this.getCoords();
        // Open the output file
        try {
            BufferedWriter out = new BufferedWriter(new FileWriter(filename));
            BufferedWriter outCode =
                    new BufferedWriter(new FileWriter(filenameCode));
            // Start creating the output file
            Iterator<LocationList> iter = coor.iterator();
            //
            int cnt = 0;
            while (iter.hasNext()) {
                LocationList src = iter.next();
                // Area sources
                out.write(String.format("> \n"));
                Iterator<Location> iterLoc = src.iterator();
                int cntPnt = 0;
                sumLo = 0.0;
                sumLa = 0.0;
                while (iterLoc.hasNext()) {
                    Location loc = iterLoc.next();
                    out.write(String.format("%10.5f %10.5f \n",
                            loc.getLongitude(), loc.getLatitude()));
                    sumLo = sumLo + loc.getLongitude();
                    sumLa = sumLa + loc.getLatitude();
                    cntPnt++;
                }
                outCode.write(String.format("%10.5f %10.5f 12 0.0 21 CM %s\n",
                        sumLo / (cntPnt), sumLa / (cntPnt), getCode().get(cnt)));
                cnt++;
            }
            out.write(String.format(">\n"));
            outCode.close();
            out.close();
        } catch (IOException e) {
            System.out.println("There was a problem:" + e);
        }
    }

    public void setCoords(ArrayList<LocationList> coords) {
        this.coords = coords;
    }

    public ArrayList<LocationList> getCoords() {
        return coords;
    }

    public void setName(ArrayList<String> name) {
        this.name = name;
    }

    public ArrayList<String> getName() {
        return name;
    }

    public void setCode(ArrayList<String> code) {
        this.code = code;
    }

    public ArrayList<String> getCode() {
        return code;
    }

}
