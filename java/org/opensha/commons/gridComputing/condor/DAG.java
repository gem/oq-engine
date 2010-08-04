package org.opensha.commons.gridComputing.condor;

import java.io.FileWriter;
import java.io.IOException;
import java.text.DateFormat;
import java.text.SimpleDateFormat;
import java.util.ArrayList;
import java.util.Date;
import java.util.NoSuchElementException;

/**
 * This class represents a Condor (high throughput computing) DAG.
 * 
 * It has the ability to handle Job dependencies, Pre/Post scripts, job retry,
 * and .dot file generation.
 * 
 * @author kevin
 *
 */
public class DAG {
	
	public enum DAG_ADD_LOCATION {
		
		BEFORE_ALL("before"),
		AFTER_ALL("after"),
		PARALLEL("parallel");
		
		private String loc;
		
		private DAG_ADD_LOCATION(String loc) {
			this.loc = loc;
		}
	}
	
	public static DateFormat df = new SimpleDateFormat("EEE MMM dd HH:mm:ss z yyyy");
	
	private ArrayList<SubmitScriptForDAG> scripts = new ArrayList<SubmitScriptForDAG>();
	private ArrayList<ParentChildRelationship> relationships = new ArrayList<ParentChildRelationship>();
	
	private String globalComments = "";
	
	private String dotFileName = null;
	private boolean dotUpdate = true;
	
	public DAG() {
		
	}
	
	public void addJob(SubmitScriptForDAG script) {
		validateJobName(script.getJobName());
		verifyDoesntExist(script.getJobName());
		this.scripts.add(script);
	}
	
	public void addJob(SubmitScriptForDAG script, String comment) {
		addJob(script);
		script.setComment(comment);
	}
	
	public ArrayList<SubmitScriptForDAG> getJobs() {
		return scripts;
	}
	
	public ArrayList<ParentChildRelationship> getRelationships() {
		return relationships;
	}
	
	public void addParentChildRelationship(ParentChildRelationship relationship) {
		boolean hasParent = false;
		boolean hasChild = false;
		for (SubmitScriptForDAG script : scripts) {
			if (script.getJobName().equals(relationship.getParent().getJobName()))
				hasParent = true;
			if (script.getJobName().equals(relationship.getChild().getJobName()))
				hasChild = true;
			if (hasParent && hasChild)
				break;
		}
		if (!hasParent)
			throw new IllegalArgumentException("Parent job '" + relationship.getParent().getJobName()
					+ " is not yet part of this DAG!");
		if (!hasChild)
			throw new IllegalArgumentException("Child job '" + relationship.getChild().getJobName()
					+ " is not yet part of this DAG!");
		this.relationships.add(relationship);
	}
	
	public void addParentChildRelationship(SubmitScriptForDAG parent, SubmitScriptForDAG child) {
		this.addParentChildRelationship(new ParentChildRelationship(parent, child));
	}
	
	public void addParentChildRelationship(SubmitScriptForDAG parent, SubmitScriptForDAG child,
			String comment) {
		ParentChildRelationship relationship = new ParentChildRelationship(parent, child);
		relationship.setComment(comment);
		this.addParentChildRelationship(relationship);
	}
	
	public void addDAG(DAG dag, DAG_ADD_LOCATION location) {
		if (location == null)
			throw new NullPointerException("You must specify an add location for the new DAG!");
		// first make sure none of these jobs are duplicates
		for (SubmitScriptForDAG newScript : dag.scripts) {
			verifyDoesntExist(newScript.getJobName());
		}
		ArrayList<ParentChildRelationship> newRelationships = new ArrayList<ParentChildRelationship>();
		if (location == DAG_ADD_LOCATION.BEFORE_ALL) {
			// set all bottom level jobs from new DAG to be parents of all top level jobs from current DAG
			for (SubmitScriptForDAG newScript : dag.scripts) {
				if (!dag.isBottomLevel(newScript.getJobName()))
					continue; // we can skip this new job if it has children
				for (SubmitScriptForDAG oldScript : scripts) {
					if (!isTopLevel(oldScript.getJobName()))
						continue; // we can skip this old job if it has parents
					newRelationships.add(new ParentChildRelationship(newScript, oldScript));
				}
			}
		} else if (location == DAG_ADD_LOCATION.AFTER_ALL) {
			// set all top level jobs from new DAG to be children of all bottom level jobs from current DAG
			for (SubmitScriptForDAG newScript : dag.scripts) {
				if (!dag.isTopLevel(newScript.getJobName()))
					continue; // we can skip this new job if it has parents
				for (SubmitScriptForDAG oldScript : scripts) {
					if (!isBottomLevel(oldScript.getJobName()))
						continue; // we can skip this old job if it has children
					newRelationships.add(new ParentChildRelationship(oldScript, newScript));
				}
			}
		}
		// add the jobs
		scripts.addAll(dag.scripts);
		// add p/c relationships from new DAG
		relationships.addAll(dag.relationships);
		// add all of our new p/c relationships
		relationships.addAll(newRelationships);
	}
	
	public boolean containsJob(String jobName) {
		for (SubmitScriptForDAG oldScript : scripts) {
			if (oldScript.getJobName().equals(jobName))
				return true;
		}
		return false;
	}
	
	private void validateJobName(String jobName) {
		if (jobName == null) {
			throw new NullPointerException("Script job name cannot be null!");
		}
		String[] forbidden = { " ", ",", "\n", "\t", "/", "\\", "<", ">" };
		for (String badStr : forbidden) {
			if (jobName.contains(badStr))
				throw new IllegalArgumentException("jobName '"+jobName+"' cannot contain '" + badStr + "'");
		}
	}
	
	private void verifyDoesntExist(String jobName) throws NoSuchElementException {
		if (containsJob(jobName))
			throw new IllegalArgumentException("A script already exists in this DAG with the name " +
					"'" + jobName + "'");
	}
	
	private void verifyExists(String jobName) throws NoSuchElementException {
		if (!containsJob(jobName))
			throw new NoSuchElementException("Job '" + jobName + "' doesn't exist in this DAG!");
	}
	
	/**
	 * Returns true if the specified job has no parents
	 * @param jobName
	 * @return
	 */
	public boolean isTopLevel(String jobName) {
		verifyExists(jobName);
		for (ParentChildRelationship rel : relationships) {
			if (rel.getChild().getJobName().equals(jobName))
				return false;
		}
		return true;
	}
	
	/**
	 * Returns true if the specified job has no children
	 * @param jobName
	 * @return
	 */
	public boolean isBottomLevel(String jobName) {
		verifyExists(jobName);
		for (ParentChildRelationship rel : relationships) {
			if (rel.getParent().getJobName().equals(jobName))
				return false;
		}
		return true;
	}
	
	public String getDAG() {
		String dag = "";
		
		dag += "# Condor DAG automatically generated by " + this.getClass().getCanonicalName() + "\n";
		dag += "# date: " + df.format(new Date()) + "\n";
		dag += "\n";
		if (globalComments != null && globalComments.length() > 0)
			dag += globalComments + "\n";
		
		dag += "\t## Condor Submit Scripts ##\n\n";
		for (SubmitScriptForDAG script : scripts) {
			if (script.hasComment()) {
				String comment = script.getComment();
				dag += checkAddNewline(comment);
			}
			String fileName = script.getFileName();
			if (fileName == null || fileName.length() <= 0)
				throw new NullPointerException("Job '" + script.getJobName() + "' has no file name!");
			dag += "JOB " + script.getJobName() + " " + fileName + "\n";
			if (script.hasPreScript()) {
				dag += "SCRIPT PRE " + script.getJobName() + " " + checkAddNewline(script.getPreScript());
			}
			if (script.hasPostScript()) {
				dag += "SCRIPT POST " + script.getJobName() + " " + checkAddNewline(script.getPostScript());
			}
			if (script.hasRetries()) {
				dag += "RETRY " + script.getJobName() + " " + script.getRetries() + "\n";
			}
		}
		
		dag +="\n\t## Parent Child Relationships ##\n\n";
		for (ParentChildRelationship relationship : relationships) {
			dag += relationship.toString() + "\n";
		}
		
		dag += "\n";
		
		if (this.dotFileName != null && dotFileName.length() > 0) {
			dag += "DOT " + dotFileName;
			if (dotUpdate)
				dag += " UPDATE";
			dag += "\n";
		}
		
		dag += "\n## END DAG ##\n";
		
		return dag;
	}
	
	public void writeDag(String fileName) throws IOException {
		FileWriter fw = new FileWriter(fileName);
		
		fw.write(getDAG());
		
		fw.close();
	}
	
	public static String checkAddNewline(String line) {
		if (!line.endsWith("\n"))
			line += "\n";
		return line;
	}
	
	public void setGlobalComments(String globalComments) {
		if (globalComments != null && globalComments.length() > 0 && !globalComments.startsWith("#"))
			globalComments = "#" + globalComments;
		this.globalComments = globalComments;
	}
	
	public void setDotFile(String dotFileName) {
		this.dotFileName = dotFileName;
	}
	
	public void setDotFile(String dotFileName, boolean dotUpdate) {
		setDotFile(dotFileName);
		this.dotUpdate = dotUpdate;
	}
	
	public int getNumJobs() {
		return scripts.size();
	}

}
