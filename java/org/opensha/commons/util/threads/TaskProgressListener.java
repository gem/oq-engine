package org.opensha.commons.util.threads;

public interface TaskProgressListener {
	
	public void taskProgressUpdate(int tasksDone, int tasksLeft, int totalTasks);

}
