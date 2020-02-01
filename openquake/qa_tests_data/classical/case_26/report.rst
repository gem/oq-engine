Classical PSHA — Area Source
============================

============== ===================
checksum32     396_512_399        
date           2020-01-16T05:31:12
engine_version 3.8.0-git83c45f7244
============== ===================

num_sites = 1, num_levels = 19, num_rlzs = 1

Parameters
----------
=============================== ==================
calculation_mode                'preclassical'    
number_of_logic_tree_samples    0                 
maximum_distance                {'default': 200.0}
investigation_time              50.0              
ses_per_logic_tree_path         1                 
truncation_level                3.0               
rupture_mesh_spacing            2.0               
complex_fault_mesh_spacing      2.0               
width_of_mfd_bin                0.2               
area_source_discretization      5.0               
pointsource_distance            None              
ground_motion_correlation_model None              
minimum_intensity               {}                
random_seed                     23                
master_seed                     0                 
ses_seed                        42                
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
========= ======= =============== ================
smlt_path weight  gsim_logic_tree num_realizations
========= ======= =============== ================
b1        1.00000 trivial(1)      1               
========= ======= =============== ================

Required parameters per tectonic region type
--------------------------------------------
====== ===================== ========= ========== ==========
grp_id gsims                 distances siteparams ruptparams
====== ===================== ========= ========== ==========
0      '[BooreAtkinson2008]' rjb       vs30       mag rake  
====== ===================== ========= ========== ==========

Realizations per (GRP, GSIM)
----------------------------

::

  <RlzsAssoc(size=1, rlzs=1)>

Number of ruptures per source group
-----------------------------------
====== ========= ============ ============
grp_id num_sites num_ruptures eff_ruptures
====== ========= ============ ============
0      0.04348   11_132       11_132      
====== ========= ============ ============

Slowest sources
---------------
========= ====== ==== ============ ========= ========= ============
source_id grp_id code num_ruptures calc_time num_sites eff_ruptures
========= ====== ==== ============ ========= ========= ============
1         0      A    11_132       0.05589   0.04348   11_132      
========= ====== ==== ============ ========= ========= ============

Computation times by source typology
------------------------------------
==== =========
code calc_time
==== =========
A    0.05589  
==== =========

Information about the tasks
---------------------------
================== ======= ====== ======= ======= =======
operation-duration mean    stddev min     max     outputs
SourceReader       0.03674 NaN    0.03674 0.03674 1      
preclassical       0.12955 NaN    0.12955 0.12955 1      
================== ======= ====== ======= ======= =======

Data transfer
-------------
============ ========================================= ========
task         sent                                      received
SourceReader                                           3.02 KB 
preclassical srcs=1.99 KB params=797 B srcfilter=223 B 366 B   
============ ========================================= ========

Slowest operations
------------------
=========================== ========= ========= ======
calc_43300                  time_sec  memory_mb counts
=========================== ========= ========= ======
total preclassical          0.12955   0.0       1     
splitting/filtering sources 0.06941   0.0       1     
composite source model      0.04563   0.0       1     
total SourceReader          0.03674   0.0       1     
store source_info           0.00231   0.0       1     
aggregate curves            2.201E-04 0.0       1     
=========================== ========= ========= ======