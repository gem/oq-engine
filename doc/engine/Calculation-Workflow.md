### Calculation Workflow

Calculation workflows are broken into 6 distinct phases. In order of execution, they are: pre-execute, execute, post-execute, post-process, export, and cleanup. The purpose of each phase is defined below.

### Pre-execute

The pre-execution phase in intended for:
- parsing and preparing inputs (“unzipping” input XML files, for example)
- initialising the calculation “work packages”

### Execute

The execution phase is where the bulk of the calculation work happens. During this phase, the control node manages task queuing and waits all of the workers to finish the calculation. In this phase the majority of the control node’s time is spent waiting for “completed task” signals from the worker, which indicates that a new task can be enqueued. When there are no more tasks left to enqueue, the control node will simply wait for all of the tasks to finish.

### Post-execute

The purpose of the post-execution phase is to expand, copy, or otherwise transform calculation results from any “intermediate” state to a final state, in preparation for post-processing and export.

### Post-process

As part of the calculation configuration, a user may wish to turn on various post-processing options. Post-processing steps are intended to be relatively lightweight calculations based on the results produced in the “execute” phase. The calculations are intended to take place on the control node, unless it is deemed necessary to distribute this work to the worker pool. (This all depends on the size and type of the post-processing task.)

The post-processing options available depend on the calculation mode. Here are some examples:

- Classical PSHA hazard calculations primarily produce hazard curves. Post processing artefacts for CPSHA include mean hazard curves, quantile hazard curves, hazard maps, and uniform hazard spectra.
- Event-Based hazard calculations primarily produce stochastic event sets and (optionally) ground motion fields. Post processing artefacts for Event-Based calculations include hazard curves computed from a set of ground motion fields. (This method of producing hazard curves is an alternative to the Classical approach. Given enough ground motion field realisations, in theory the hazard curves produced from GMFs will converge to the curves produced through the Classical approach.)

### Export

If a user specifies the `--exports` option on the command line, all calculation results will automatically be exported from the storage to NRML XML.

If the user does not specify this option, it is still possible to export results manually using the `--export-output` command line option.

### Cleanup

Perform any kind of cleanup required once all calculations and exports have concluded.
