Classical PSHA — Area Source
============================

============== ===================
checksum32     347_027_509        
date           2020-01-16T05:31:15
engine_version 3.8.0-git83c45f7244
============== ===================

num_sites = 16, num_levels = 45, num_rlzs = 1

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
area_source_discretization      50.0              
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
====== ==================================================================== ========= ========== ==========
grp_id gsims                                                                distances siteparams ruptparams
====== ==================================================================== ========= ========== ==========
0      '[NGAEastGMPETotalSigma]\ngmpe_table="NGAEast_YENIER_ATKINSON.hdf5"' rrup      vs30       mag       
====== ==================================================================== ========= ========== ==========

Realizations per (GRP, GSIM)
----------------------------

::

  <RlzsAssoc(size=1, rlzs=1)>

Number of ruptures per source group
-----------------------------------
====== ========= ============ ============
grp_id num_sites num_ruptures eff_ruptures
====== ========= ============ ============
0      2.00000   8            8.00000     
====== ========= ============ ============

Slowest sources
---------------
========= ====== ==== ============ ========= ========= ============
source_id grp_id code num_ruptures calc_time num_sites eff_ruptures
========= ====== ==== ============ ========= ========= ============
1         0      A    8            0.00280   2.00000   8.00000     
========= ====== ==== ============ ========= ========= ============

Computation times by source typology
------------------------------------
==== =========
code calc_time
==== =========
A    0.00280  
==== =========

Information about the tasks
---------------------------
================== ======= ====== ======= ======= =======
operation-duration mean    stddev min     max     outputs
SourceReader       0.00315 NaN    0.00315 0.00315 1      
preclassical       0.00639 NaN    0.00639 0.00639 1      
================== ======= ====== ======= ======= =======

Data transfer
-------------
============ ======================================== ========
task         sent                                     received
SourceReader                                          2.87 KB 
preclassical gsims=1.12 MB srcs=1.93 KB params=1006 B 366 B   
============ ======================================== ========

Slowest operations
------------------
=========================== ========= ========= ======
calc_43314                  time_sec  memory_mb counts
=========================== ========= ========= ======
composite source model      0.02036   1.03125   1     
total preclassical          0.00639   0.25781   1     
total SourceReader          0.00315   0.0       1     
store source_info           0.00251   0.0       1     
splitting/filtering sources 0.00227   0.0       1     
aggregate curves            1.976E-04 0.0       1     
=========================== ========= ========= ======