package org.opensha.commons.gridComputing.condor;

import java.io.File;
import java.io.FileWriter;
import java.io.IOException;

/**
 * This represents a Condor submit script. This means a single execution of
 * a program/script with arguments. This can either be in a local Condor
 * pool or over the grid, with the 'grid' universe.
 * 
 * @author kevin
 *
 */
public class SubmitScript {
	
	public enum Universe {
		/** Grid universe. */
		GRID("grid"),
		
		/** Grid universe. */
		VANILLA("vanilla"),
		
		/** Grid universe. */
		SCHEDULER("scheduler");
		
		private String name;
		
		private Universe(String name) {
			this.name = name;
		}
		
		@Override
		public String toString() {
			return name;
		}
	}
	
	private String exedutable;
	private String arguments;
	private String remoteInitialDir;
	private Universe universe;
	private String logFile;
	private String outFile;
	private String errFile;
	
	private String environment;
	private String fileName = null;
	private String requirements = null;
	
	private boolean transferExecutable = false;
	
	public SubmitScript(String exedutable,
			String arguments,
			String remoteInitialDir,
			Universe universe,
			String logFile,
			String outFile,
			String errFile) {
		this.exedutable = exedutable;
		this.arguments = arguments;
		this.remoteInitialDir = remoteInitialDir;
		this.universe = universe;
		this.logFile = logFile;
		this.outFile = outFile;
		this.errFile = errFile;
	}
	
	public SubmitScript(String exedutable,
			String arguments,
			String remoteInitialDir,
			Universe universe,
			String outPrefix,
			boolean outSubDirs) {
		this.exedutable = exedutable;
		this.arguments = arguments;
		this.remoteInitialDir = remoteInitialDir;
		this.universe = universe;
		if (outSubDirs) {
			this.logFile = "log" + File.separator + outPrefix + ".log";
			this.outFile = "out" + File.separator + outPrefix + ".out";
			this.errFile = "err" + File.separator + outPrefix + ".err";
		} else {
			this.logFile = outPrefix + ".log";
			this.outFile = outPrefix + ".out";
			this.errFile = outPrefix + ".err";
		}
	}
	
	public String getScript() {
		String script = "";
		script += "universe\t=\t" + universe + "\n";
		script += "executable\t=\t" + exedutable + "\n";
		if (arguments != null && arguments.length() > 0)
			script += "arguments\t=\t" + arguments + "\n";
		if (environment != null && environment.length() > 0)
			script += "environment\t=\t" + environment + "\n";
		if (requirements != null && requirements.length() > 0)
			script += "requirements\t=\t" + requirements + "\n";
		script += "notification\t=\tNEVER\n";
		script += "should_transfer_files\t=\tYES\n";
		script += "when_to_transfer_output\t=\tON_EXIT\n";
		script += "copy_to_spool\t=\tfalse\n";
		script += "log\t=\t" + logFile + "\n";
		script += "error\t=\t" + errFile + "\n";
		script += "output\t=\t" + outFile + "\n";
		script += "transfer_executable\t=\t" + transferExecutable + "\n";
		script += "transfer_error\t=\ttrue\n";
		script += "transfer_output\t=\ttrue\n";
		script += "periodic_release\t=\t(NumSystemHolds <= 3)\n";
		script += "periodic_remove\t=\t(NumSystemHolds > 3)\n";
		script += "remote_initialdir\t=\t" + remoteInitialDir + "\n";
		script += "queue\n";
		
		return script;
	}
	
	public void writeScript(String fileName) throws IOException {
		this.fileName = fileName;
		writeScript();
	}
	
	public void writeScript() throws IOException {
		if (fileName == null)
			throw new NullPointerException("Condor submit script file name was not set before writeScript()!");
		String script = getScript();
		
		FileWriter fw = new FileWriter(fileName);
		
		fw.write(script);
		
		fw.close();
	}

	public String getFileName() {
		return fileName;
	}

	public void setFileName(String fileName) {
		this.fileName = fileName;
	}

	public boolean isTransferExecutable() {
		return transferExecutable;
	}

	public void setTransferExecutable(boolean transferExecutable) {
		this.transferExecutable = transferExecutable;
	}
	
	public String getEnvironment() {
		return environment;
	}
	
	public void setEnvironment(String environment) {
		this.environment = environment;
	}
	
	public void setRequirements(String requirements) {
		this.requirements = requirements;
	}
	
	public String getRequirements() {
		return requirements;
	}
}
