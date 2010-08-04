package org.opensha.commons.gridComputing.condor;

import static org.junit.Assert.*;

import java.io.File;
import java.io.IOException;
import java.util.ArrayList;

import org.junit.Before;
import org.junit.Test;
import org.opensha.commons.gridComputing.condor.DAG.DAG_ADD_LOCATION;
import org.opensha.commons.util.FileUtils;

public class TestDAGAddition {

	private DAG mainDAG;
	private DAG addDAG;
	private ArrayList<String> tops = new ArrayList<String>();
	private ArrayList<String> bottoms = new ArrayList<String>();
	
	@Before
	public void setUp() throws Exception {
		mainDAG = TestDAGCreation.createSimpleTestDAG("/tmp");
		addDAG = TestDAGCreation.createSimpleTestDAG("/tmp");
		
		for (SubmitScriptForDAG job : addDAG.getJobs()) {
			job.setJobName("add_"+job.getJobName());
			job.setFileName("/tmp/test.sub");
		}
		for (SubmitScriptForDAG job : mainDAG.getJobs()) {
			String jobName = job.getJobName();
			if (mainDAG.isTopLevel(jobName))
				tops.add(jobName);
			if (mainDAG.isBottomLevel(jobName))
				bottoms.add(jobName);
			job.setFileName("/tmp/test.sub");
		}
	}
	
	@Test
	public void testTopBottomDetection() {
		assertEquals("should be 4 jobs initially", 4, mainDAG.getNumJobs());
		assertEquals("should be 1 top job", 1, tops.size());
		assertEquals("should be 1 bottom job", 1, bottoms.size());
		assertEquals("should be 4 p/c rels before", 4, mainDAG.getRelationships().size());
	}
	
	@Test
	public void testAddBefore() throws IOException {
//		writeDAGToTempDir(mainDAG);
		mainDAG.addDAG(addDAG, DAG_ADD_LOCATION.BEFORE_ALL);
		System.out.println(mainDAG.getDAG());
//		writeDAGToTempDir(mainDAG);
		assertEquals("should be 8 jobs after add", 8, mainDAG.getNumJobs());
		assertEquals("should be 9 p/c rels after", 9, mainDAG.getRelationships().size());
		boolean hasCorrectBetween = false;
		for (ParentChildRelationship rel : mainDAG.getRelationships()) {
			if (rel.getParent().getJobName().equals("add_"+bottoms.get(0))
					&& rel.getChild().getJobName().equals(tops.get(0))) {
				hasCorrectBetween = true;
			}
		}
		assertTrue("add before has incorrect p/c relationship", hasCorrectBetween);
	}
	
	@Test
	public void testAddAfter() throws IOException {
//		writeDAGToTempDir(mainDAG);
		mainDAG.addDAG(addDAG, DAG_ADD_LOCATION.AFTER_ALL);
		System.out.println(mainDAG.getDAG());
//		writeDAGToTempDir(mainDAG);
		assertEquals("should be 8 jobs after add", 8, mainDAG.getNumJobs());
		assertEquals("should be 9 p/c rels after", 9, mainDAG.getRelationships().size());
		boolean hasCorrectBetween = false;
		for (ParentChildRelationship rel : mainDAG.getRelationships()) {
			if (rel.getParent().getJobName().equals(bottoms.get(0))
					&& rel.getChild().getJobName().equals("add_"+tops.get(0))) {
				hasCorrectBetween = true;
			}
		}
		assertTrue("add before has incorrect p/c relationship", hasCorrectBetween);
	}
	
	@Test
	public void testParallel() throws IOException {
//		writeDAGToTempDir(mainDAG);
		mainDAG.addDAG(addDAG, DAG_ADD_LOCATION.PARALLEL);
		System.out.println(mainDAG.getDAG());
//		writeDAGToTempDir(mainDAG);
		assertEquals("should be 8 jobs after add", 8, mainDAG.getNumJobs());
		assertEquals("should be 8 p/c rels after", 8, mainDAG.getRelationships().size());
	}
	
	private static void writeDAGToTempDir(DAG dag) throws IOException {
		File tempDir = FileUtils.createTempDir();
		String dir = tempDir.getAbsolutePath() + File.separator;
		
		System.out.println("DIR: " + dir);
		
		for (SubmitScriptForDAG job : dag.getJobs()) {
			job.writeScriptInDir(dir);
		}
		
		dag.writeDag(dir + "main.dag");
	}

}
