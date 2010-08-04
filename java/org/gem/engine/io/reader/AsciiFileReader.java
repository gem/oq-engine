/*
 * [COPYRIGHT]
 *
 * [NAME] is free software; you can redistribute it and/or modify it
 * under the terms of the GNU Lesser General Public License as
 * published by the Free Software Foundation; either version 2.1 of
 * the License, or (at your option) any later version.
 *
 * This software is distributed in the hope that it will be useful,
 * but WITHOUT ANY WARRANTY; without even the implied warranty of
 * MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the GNU
 * Lesser General Public License for more details.
 *
 * You should have received a copy of the GNU Lesser General Public
 * License along with this software; if not, write to the Free
 * Software Foundation, Inc., 51 Franklin St, Fifth Floor, Boston, MA
 * 02110-1301 USA, or see the FSF site: http://www.fsf.org.
 */

package org.gem.engine.io.reader;

import java.io.BufferedReader;
import java.io.FileInputStream;
import java.io.FileNotFoundException;
import java.io.IOException;
import java.io.InputStreamReader;
import java.util.ArrayList;
import java.util.List;

/**
 * An utility class to read ascii files.
 * 
 * @author Andrea Cerisara
 * @version $Id: AsciiFileReader.java 537 2010-06-16 18:29:36Z acerisara $
 */
public class AsciiFileReader implements LineReader
{

    /**
     * Filters a single line.
     * 
     * @author Andrea Cerisara
     * @version $Id: AsciiFileReader.java 537 2010-06-16 18:29:36Z acerisara $
     */
    public interface LineFilter
    {

        /**
         * Filters the passed line.
         * 
         * @param line the line to be filtered
         * @return the filtered line
         */
        public String filter(String line);

    }

    /**
     * Parses a single line.
     * 
     * @author Andrea Cerisara
     * @version $Id: AsciiFileReader.java 537 2010-06-16 18:29:36Z acerisara $
     * @param <T> the type of object produced by this parser
     */
    public interface LineParser<T>
    {

        /**
         * Parses the passed line.
         * 
         * @param line the line to be parsed
         * @return the object created by the parsing process
         */
        public T parse(String line);

    }

    /**
     * Executes a bunch of code using the passed line.
     * 
     * @author Andrea Cerisara
     * @version $Id: AsciiFileReader.java 537 2010-06-16 18:29:36Z acerisara $
     */
    public interface LineBlock
    {

        /**
         * Executes this block of code using the passed line.
         * 
         * @param line the current line
         */
        public void execute(String line);

    }

    private String filename;
    private BufferedReader reader;

    /**
     * @param filename the name of the file to read
     */
    public AsciiFileReader(String filename)
    {
        this.filename = filename;
    }

    /**
     * Opens this reader.
     * 
     * @return this reader
     */
    public AsciiFileReader open()
    {
        try
        {
            reader = new BufferedReader(new InputStreamReader(new FileInputStream(filename)));
        }
        catch (FileNotFoundException e)
        {
            throw new RuntimeException(e);
        }

        return this;
    }

    /**
     * Selects and parses all the lines. Closes the reader when the end of file has been reached.
     * 
     * @param parser the parser to use
     * @param <T> the type of object produced by the parser
     * @return the list of objects produced by the parser
     */
    public <T> List<T> selectAllAndClose(LineParser<T> parser)
    {
        try
        {
            return select(-1, parser);
        }
        finally
        {
            close();
        }
    }

    /**
     * Executes the passed block of code for each line of the file.
     * 
     * @param block the block of code to execute
     * @return this reader
     */
    public AsciiFileReader forEachLineDo(LineBlock block)
    {
        String line = null;

        try
        {
            while ((line = reader.readLine()) != null)
            {
                block.execute(line);
            }
        }
        catch (Exception e)
        {
            throw new RuntimeException(e);
        }

        return this;
    }

    /**
     * Closes this reader.
     */
    public void close()
    {
        try
        {
            reader.close();
        }
        catch (IOException e)
        {
            throw new RuntimeException(e);
        }
    }

    /**
     * Skips some lines of code from the file.
     * 
     * @param numberOfLinesToSkip the number of lines to skip
     * @return this reader
     */
    public AsciiFileReader skipLines(Integer numberOfLinesToSkip)
    {
        for (int i = 0; i < numberOfLinesToSkip; i++)
        {
            try
            {
                reader.readLine();
            }
            catch (IOException e)
            {
                throw new RuntimeException(e);
            }
        }

        return this;
    }

    /**
     * Parses the next line of the file.
     * 
     * @param delimiter the string to use as splitter
     * @return the splitted line
     */
    public String[] parseNextLine(String delimiter)
    {
        return parseNextLine(delimiter, new LineFilter()
        {

            @Override
            public String filter(String aLine)
            {
                return aLine; // empty filter
            }
        });
    }

    /**
     * Parses the next line of the file.
     * 
     * @param delimiter the string to use as splitter
     * @param filter the filter to use before splitting the line
     * @return the splitted line
     */
    public String[] parseNextLine(String delimiter, LineFilter filter)
    {
        try
        {
            String line = reader.readLine();
            return line != null ? filter.filter(line).split(delimiter) : null;
        }
        catch (IOException e)
        {
            throw new RuntimeException(e);
        }
    }

    /**
     * Parses the next line of the file and closes the reader.
     * 
     * @param delimiter the string to use as splitter
     * @return the splitted line
     */
    public String[] parseNextLineAndClose(String delimiter)
    {
        try
        {
            return parseNextLine(delimiter);
        }
        finally
        {
            close();
        }
    }

    /**
     * Opens, reads and splits a single line from the file.
     * Closes the reader when the line has been readed.
     * 
     * @param row the number of row to read
     * @param delimiter the string to use as splitter
     * @return the parsed line
     */
    @Override
    public String[] readAndSplit(int row, String delimiter)
    {
        return open().skipLines(row - 1).parseNextLineAndClose("\t");
    }

    /**
     * Selects a sequential subset of the lines from the file.
     * 
     * @param parser the parser to use
     * @param linesToRead the number of lines to read
     * @param <T> the type of object produced by the parser
     * @return the list of objects produced by the parser
     */
    public <T> List<T> select(int linesToRead, LineParser<T> parser)
    {
        String line = null;
        List<T> result = new ArrayList<T>();
        int linesToReadCounter = linesToRead;

        try
        {
            while ((line = reader.readLine()) != null && (linesToReadCounter > 0 || linesToRead == -1))
            {
                linesToReadCounter--;
                result.add(parser.parse(line));
            }

            return result;
        }
        catch (Exception e)
        {
            throw new RuntimeException(e);
        }
    }

}
