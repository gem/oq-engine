SAM int July 2019 A15, 300km
============================

============== ===================
checksum32     3_450_566_160      
date           2020-01-16T05:31:17
engine_version 3.8.0-git83c45f7244
============== ===================

num_sites = 1, num_levels = 15, num_rlzs = 1

Parameters
----------
=============================== ===================
calculation_mode                'preclassical'     
number_of_logic_tree_samples    0                  
maximum_distance                {'default': 1000.0}
investigation_time              1.0                
ses_per_logic_tree_path         1                  
truncation_level                3.0                
rupture_mesh_spacing            20.0               
complex_fault_mesh_spacing      50.0               
width_of_mfd_bin                0.2                
area_source_discretization      None               
pointsource_distance            None               
ground_motion_correlation_model None               
minimum_intensity               {}                 
random_seed                     23                 
master_seed                     0                  
ses_seed                        42                 
=============================== ===================

Input files
-----------
======================= ================================
Name                    File                            
======================= ================================
gsim_logic_tree         `gmmLT_A15.xml <gmmLT_A15.xml>`_
job_ini                 `job.ini <job.ini>`_            
source_model_logic_tree `ssmLT.xml <ssmLT.xml>`_        
======================= ================================

Composite source model
----------------------
========= ======= =============== ================
smlt_path weight  gsim_logic_tree num_realizations
========= ======= =============== ================
b1        1.00000 trivial(1,0)    1               
========= ======= =============== ================

Required parameters per tectonic region type
--------------------------------------------
====== ================================ ========= ============ ==========
grp_id gsims                            distances siteparams   ruptparams
====== ================================ ========= ============ ==========
0      '[AbrahamsonEtAl2015SInterHigh]' rrup      backarc vs30 mag       
====== ================================ ========= ============ ==========

Realizations per (GRP, GSIM)
----------------------------

::

  <RlzsAssoc(size=1, rlzs=1)>

Number of ruptures per source group
-----------------------------------
====== ========= ============ ============
grp_id num_sites num_ruptures eff_ruptures
====== ========= ============ ============
0      0.02108   1_755        1_755       
====== ========= ============ ============

Slowest sources
---------------
========= ====== ==== ============ ========= ========= ============
source_id grp_id code num_ruptures calc_time num_sites eff_ruptures
========= ====== ==== ============ ========= ========= ============
int_2     0      C    1_755        0.03678   0.02108   1_755       
========= ====== ==== ============ ========= ========= ============

Computation times by source typology
------------------------------------
==== =========
code calc_time
==== =========
C    0.03678  
==== =========

Information about the tasks
---------------------------
================== ======= ====== ======= ======= =======
operation-duration mean    stddev min     max     outputs
SourceReader       0.57106 NaN    0.57106 0.57106 1      
preclassical       19      NaN    19      19      1      
================== ======= ====== ======= ======= =======

Data transfer
-------------
============ ========================================== ========
task         sent                                       received
SourceReader                                            36.44 KB
preclassical srcs=34.48 KB params=761 B srcfilter=223 B 366 B   
============ ========================================== ========

Slowest operations
------------------
=========================== ========= ========= ======
calc_43320                  time_sec  memory_mb counts
=========================== ========= ========= ======
total preclassical          19        5.09766   1     
splitting/filtering sources 19        7.09766   1     
composite source model      0.58301   0.00781   1     
total SourceReader          0.57106   0.00781   1     
store source_info           0.00232   0.0       1     
aggregate curves            3.660E-04 0.0       1     
=========================== ========= ========= ======