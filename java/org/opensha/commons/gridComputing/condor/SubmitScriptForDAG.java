package org.opensha.commons.gridComputing.condor;

import java.io.File;
import java.io.IOException;

/**
 * This is a {@link SubmitScript} that also contains metadata needed for {@link DAG}
 * generation (such as pre/post scripts, job names, retries, and comments.
 * 
 * @author kevin
 *
 */
public class SubmitScriptForDAG extends SubmitScript {
	
	private String preScript = null;
	private String postScript = null;
	
	private String jobName;
	
	private String comment = null;
	
	private int retries = 3;
	
	public SubmitScriptForDAG(String jobName, String exedutable, String arguments,
			String remoteInitialDir, Universe universe, String logFile,
			String outFile, String errFile) {
		super(exedutable, arguments, remoteInitialDir, universe, logFile, outFile, errFile);
		this.jobName = jobName;
	}
	
	public SubmitScriptForDAG(String jobName, String executable, String arguments,
			String remoteInitialDir, Universe universe, boolean outSubDirs) {
		super(executable, arguments, remoteInitialDir, universe, jobName, outSubDirs);
		this.jobName = jobName;
	}

	public boolean hasPreScript() {
		return preScript != null && preScript.length() > 0;
	}
	
	public String getPreScript() {
		return preScript;
	}

	public void setPreScript(String preScript) {
		this.preScript = preScript;
	}

	public boolean hasPostScript() {
		return postScript != null && postScript.length() > 0;
	}
	
	public String getPostScript() {
		return postScript;
	}

	public void setPostScript(String postScript) {
		this.postScript = postScript;
	}
	
	public boolean hasRetries() {
		return retries > 0;
	}

	public int getRetries() {
		return retries;
	}

	public void setRetries(int retries) {
		this.retries = retries;
	}
	
	public boolean hasComment() {
		return comment != null && comment.length() > 0;
	}
	
	public String getComment() {
		return comment;
	}

	public void setComment(String comment) {
		if (comment != null && comment.length() > 0 && !comment.startsWith("#"))
			comment = "#" + comment;
		this.comment = comment;
	}
	
	public String getJobName() {
		return jobName;
	}
	
	public void setJobName(String jobName) {
		this.jobName = jobName;
	}
	
	public void writeScriptInDir(String dir) throws IOException {
		if (!dir.endsWith(File.separator))
			dir += File.separator;
		this.writeScript(dir + getJobName() + ".sub");
	}

}
