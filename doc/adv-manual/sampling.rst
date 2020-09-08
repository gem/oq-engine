Logic tree sampling strategies
==============================

Stating from version 3.10, the OpenQuake engine suppports 4 different
strategies for sampling the logic tree. They are called, respectively,
``early_weights``, ``late_weights``, ``early_latin``, ``late_latin``.
Here we will discuss how they work.

First of all, logic tree sampling is controlled by two parameters in
the job.ini:

- number_of_logic_tree_samples (default 0, no sampling)
- sampling_method (default ``early_weights``)
