Test the use of the `shift_hypo` option
=======================================

============== ===================
checksum32     478_114_332        
date           2020-01-16T05:31:00
engine_version 3.8.0-git83c45f7244
============== ===================

num_sites = 1, num_levels = 20, num_rlzs = 5000

Parameters
----------
=============================== ==================
calculation_mode                'preclassical'    
number_of_logic_tree_samples    5000              
maximum_distance                {'default': 200.0}
investigation_time              1.0               
ses_per_logic_tree_path         1                 
truncation_level                3.0               
rupture_mesh_spacing            2.0               
complex_fault_mesh_spacing      2.0               
width_of_mfd_bin                0.2               
area_source_discretization      10.0              
pointsource_distance            None              
ground_motion_correlation_model None              
minimum_intensity               {}                
random_seed                     23                
master_seed                     0                 
ses_seed                        24                
=============================== ==================

Input files
-----------
======================= ============================================================
Name                    File                                                        
======================= ============================================================
gsim_logic_tree         `gmpe_logic_tree.xml <gmpe_logic_tree.xml>`_                
job_ini                 `job.ini <job.ini>`_                                        
source_model_logic_tree `source_model_logic_tree.xml <source_model_logic_tree.xml>`_
======================= ============================================================

Composite source model
----------------------
========= ========= =============== ================
smlt_path weight    gsim_logic_tree num_realizations
========= ========= =============== ================
b1        2.000E-04 trivial(1)      1               
========= ========= =============== ================

Required parameters per tectonic region type
--------------------------------------------
====== ================ ========= ========== ==========
grp_id gsims            distances siteparams ruptparams
====== ================ ========= ========== ==========
0      '[Atkinson2015]' rhypo                mag       
====== ================ ========= ========== ==========

Realizations per (GRP, GSIM)
----------------------------

::

  <RlzsAssoc(size=1, rlzs=5000)>

Number of ruptures per source group
-----------------------------------
====== ========= ============ ============
grp_id num_sites num_ruptures eff_ruptures
====== ========= ============ ============
0      0.02000   200          200         
====== ========= ============ ============

Slowest sources
---------------
========= ====== ==== ============ ========= ========= ============
source_id grp_id code num_ruptures calc_time num_sites eff_ruptures
========= ====== ==== ============ ========= ========= ============
1         0      A    200          0.00276   0.02000   200         
========= ====== ==== ============ ========= ========= ============

Computation times by source typology
------------------------------------
==== =========
code calc_time
==== =========
A    0.00276  
==== =========

Information about the tasks
---------------------------
================== ======= ====== ======= ======= =======
operation-duration mean    stddev min     max     outputs
SourceReader       0.00276 NaN    0.00276 0.00276 1      
preclassical       0.00612 NaN    0.00612 0.00612 1      
================== ======= ====== ======= ======= =======

Data transfer
-------------
============ ========================================= ========
task         sent                                      received
SourceReader                                           2.96 KB 
preclassical srcs=2.02 KB params=801 B srcfilter=223 B 366 B   
============ ========================================= ========

Slowest operations
------------------
=========================== ========= ========= ======
calc_43275                  time_sec  memory_mb counts
=========================== ========= ========= ======
composite source model      0.49265   0.25391   1     
total preclassical          0.00612   0.0       1     
total SourceReader          0.00276   0.0       1     
splitting/filtering sources 0.00249   0.0       1     
store source_info           0.00214   0.0       1     
aggregate curves            1.540E-04 0.0       1     
=========================== ========= ========= ======