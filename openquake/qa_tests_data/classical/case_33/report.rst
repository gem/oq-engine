Etna No Topo
============

============== ===================
checksum32     380_532_669        
date           2020-01-16T05:31:50
engine_version 3.8.0-git83c45f7244
============== ===================

num_sites = 1, num_levels = 28, num_rlzs = 1

Parameters
----------
=============================== =================
calculation_mode                'preclassical'   
number_of_logic_tree_samples    0                
maximum_distance                {'default': 50.0}
investigation_time              50.0             
ses_per_logic_tree_path         1                
truncation_level                3.0              
rupture_mesh_spacing            1.0              
complex_fault_mesh_spacing      1.0              
width_of_mfd_bin                0.1              
area_source_discretization      1.0              
pointsource_distance            None             
ground_motion_correlation_model None             
minimum_intensity               {}               
random_seed                     23               
master_seed                     0                
ses_seed                        42               
=============================== =================

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
========= ======= =============== ================
smlt_path weight  gsim_logic_tree num_realizations
========= ======= =============== ================
b1        1.00000 trivial(1)      1               
========= ======= =============== ================

Required parameters per tectonic region type
--------------------------------------------
====== ======================= ========= ========== ==========
grp_id gsims                   distances siteparams ruptparams
====== ======================= ========= ========== ==========
0      '[TusaLanger2016Rhypo]' rhypo     vs30       mag       
====== ======================= ========= ========== ==========

Realizations per (GRP, GSIM)
----------------------------

::

  <RlzsAssoc(size=1, rlzs=1)>

Number of ruptures per source group
-----------------------------------
====== ========= ============ ============
grp_id num_sites num_ruptures eff_ruptures
====== ========= ============ ============
0      0.06000   150          150         
====== ========= ============ ============

Slowest sources
---------------
========= ====== ==== ============ ========= ========= ============
source_id grp_id code num_ruptures calc_time num_sites eff_ruptures
========= ====== ==== ============ ========= ========= ============
SVF       0      S    150          0.02331   0.06000   150         
========= ====== ==== ============ ========= ========= ============

Computation times by source typology
------------------------------------
==== =========
code calc_time
==== =========
S    0.02331  
==== =========

Information about the tasks
---------------------------
================== ======= ====== ======= ======= =======
operation-duration mean    stddev min     max     outputs
SourceReader       0.00341 NaN    0.00341 0.00341 1      
preclassical       0.02464 NaN    0.02464 0.02464 1      
================== ======= ====== ======= ======= =======

Data transfer
-------------
============ ========================================= ========
task         sent                                      received
SourceReader                                           2.58 KB 
preclassical srcs=1.41 KB params=865 B srcfilter=223 B 366 B   
============ ========================================= ========

Slowest operations
------------------
=========================== ========= ========= ======
calc_43334                  time_sec  memory_mb counts
=========================== ========= ========= ======
total preclassical          0.02464   0.0       1     
composite source model      0.01233   0.0       1     
total SourceReader          0.00341   0.0       1     
store source_info           0.00194   0.0       1     
splitting/filtering sources 5.844E-04 0.0       1     
aggregate curves            2.303E-04 0.0       1     
=========================== ========= ========= ======