### Diff example
```bash
$ diff -urN /etc/openquake/openquake.cfg /etc/openquake/openquake.cfg.new_in_this_release
```
### Result
```patch
--- /etc/openquake/openquake.cfg	2014-03-10 10:35:32.000000000 +0000
+++ /etc/openquake/openquake.cfg.new_in_this_release	2014-06-03 07:06:44.995410536 +0000
@@ -1,4 +1,4 @@
-# Copyright (c) 2010-2012, GEM Foundation.
+# Copyright (c) 2010-2014, GEM Foundation.
 #
 # OpenQuake is free software: you can redistribute it and/or modify it
 # under the terms of the GNU Affero General Public License as published
@@ -18,6 +18,11 @@
 # this is good for a single user situation, but turn this off on a cluster
 # otherwise a CTRL-C will kill the computations of other users
 
 [amqp]
 host = localhost
 port = 5672
@@ -42,23 +47,12 @@
 # The number of tasks to be in queue at any given time.
 # Ideally, this would be set to at least number of available worker processes.
 # In some cases, we found that it's actually best to have a number of tasks in
-# queue equal to 2 * the number of worker processes. This makes a big difference
-# in large calculations.
+# queue equal to 2 * the number of worker processes.
+# This makes a big difference in large calculations.
 concurrent_tasks = 64
 
 [risk]
-# The number of work items (assets) per task. This affects both the
-# RAM usage (the more, the more) and the performance of the
-# computation (but not linearly).
-block_size = 100
-
-# The same considerations for hazard applies here.
-# FIXME(lp). Why do we need two different parameter now that the
-# distribution logic is shared?
-concurrent_tasks = 64
-
-[statistics]
-# This setting should only be enabled during development but be omitted/turned
-# off in production. It enables statistics counters for debugging purposes. At
-# least one Q/A test requires these.
-debug = true
+# change the following parameter to 'fast' if you have
+# memory issues with the epsilon matrix; beware however that you will
+# introduce a stronger seed dependency
+epsilons_management = full
```
