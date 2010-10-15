package org.gem.engine.hazard.parsers.crisis;

import java.io.BufferedReader;
import java.io.FileReader;
import java.io.IOException;
import java.util.ArrayList;

/**
 * 
 * This is a container for the information parsed from a crisis PSHA input file
 * 
 * @author marcop
 * 
 */
public class InputFileContent {

    private InputFileHeader head;
    private ArrayList<InputFileSource> source;

    /**
     * Constructor. Parses the content of the Crisis input file
     * 
     * @param filename
     *            - Name of the Crisis input file (2007 format)
     */
    public InputFileContent(String filename) {
        int i;
        boolean info = false;

        // Reading the file
        try {
            // Instantiate a BufferedReader
            BufferedReader input = new BufferedReader(new FileReader(filename));
            try {
                // Reading the header
                this.head = new InputFileHeader(input);
                this.source = new ArrayList<InputFileSource>();
                // Reading sources
                for (i = 0; i < this.head.nRegions; i++) {
                    if (info)
                        System.out.printf("Reading source # %d \n", i);
                    InputFileSource tmpsrc = new InputFileSource(input);
                    this.source.add(tmpsrc);
                    if (info)
                        System.out.printf("  name: %s \n", tmpsrc.getName());
                }
            } finally {
                input.close();
            }
        } catch (IOException ex) {
            ex.printStackTrace();
        }
    }

    /**
     * Return the header of the CrisisInputFile object
     * 
     * @return Returns the Crisis Input Header
     */
    public InputFileHeader getHeader() {
        return this.head;
    }

    /**
     * Return the List of Sources
     * 
     * @return Returns the Crisis Input Header
     */
    public ArrayList<InputFileSource> getSources() {
        return this.source;
    }

    // /**
    // * Return a file with area sources in the GMT format
    // * @param Name of the output file
    // * @return Returns the Crisis Input Header
    // * @throws IOException
    // */
    // public void createGMTfile(String filename) {
    // //
    // int i;
    // // Browse the list of sources
    // ArrayList<CrisisInputSource> criSrc = this.getSources();
    // // Open the output file
    // try {
    // BufferedWriter out = new BufferedWriter(new FileWriter(filename));
    // // Start creating the output file
    // Iterator<CrisisInputSource> iter = criSrc.iterator();
    // while (iter.hasNext()) {
    // CrisisInputSource src = iter.next();
    // // Areal sources
    // if (src.getSrcType() == 0) {
    // out.write(String.format(">\n"));
    // for (i=0; i<src.getnVtx(); i++ ) {
    // out.write(String.format("%7.3f %7.3f %7.3f\n",
    // src.[i][0],src.coords[i][1],-1*src.depth[i]));
    // }
    // }
    // }
    // out.write(String.format(">\n"));
    // out.close();
    // } catch(IOException e) {
    // System.out.println("There was a problem:" + e);
    // }
    // }

}
