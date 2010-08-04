/*******************************************************************************
 * Copyright 2009 OpenSHA.org in partnership with
 * the Southern California Earthquake Center (SCEC, http://www.scec.org)
 * at the University of Southern California and the UnitedStates Geological
 * Survey (USGS; http://www.usgs.gov)
 * 
 * Licensed under the Apache License, Version 2.0 (the "License");
 * you may not use this file except in compliance with the License.
 * You may obtain a copy of the License at
 * 
 *   http://www.apache.org/licenses/LICENSE-2.0
 * 
 * Unless required by applicable law or agreed to in writing, software
 * distributed under the License is distributed on an "AS IS" BASIS,
 * WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
 * See the License for the specific language governing permissions and
 * limitations under the License.
 ******************************************************************************/

package org.opensha.commons.gui;

import java.io.IOException;
import java.io.OutputStream;
import java.io.PrintStream;

import javax.swing.JDialog;
import javax.swing.JFrame;
import javax.swing.JScrollPane;
import javax.swing.JTextArea;

public class ConsoleWindow {
	
	private JDialog frame;
	private JTextArea text = new JTextArea();
	private JScrollPane scroll = new JScrollPane(text);
	
	public ConsoleWindow() {
		System.setErr(new ConsoleStream(System.err));
		System.setOut(new ConsoleStream(System.out));
		initGUI();
	}
	
	public void initGUI() {
		frame = new JDialog(new JFrame(), "Console Window");
		frame.setLocationRelativeTo(null);
		frame.setSize(800,500);
		frame.add(scroll);
		text.setEditable(false);
	}
	
	public void setVisible(boolean show) {
		frame.setLocationRelativeTo(null);
		text.setCaretPosition(0);
		text.setCaretPosition(text.getText().length());
		frame.setVisible(show);
	}
	
	private class ConsoleStream extends PrintStream {
		
		public ConsoleStream(OutputStream stream) {
			super(stream);
		}
		
		private void write(String s) {
			// I hope text is synchronized
			text.append(s);
			text.setCaretPosition(text.getText().length());
		}
		
		public void write(int i) {
			write(new String(new byte[]{(byte)i}));
			super.write(i);
	    }

	    public void write(byte[] bytes, int i, int j) {
	    	write(new String(bytes,i,j));
	    	super.write(bytes,i,j);
	    }

	    public void write(byte[] bytes) throws IOException {
	    	write(new String(bytes));
	        super.write(bytes);
	    }
	}
}
