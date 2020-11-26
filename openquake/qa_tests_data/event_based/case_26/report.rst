Landslide analysis in Cali for source int_col
=============================================

============== ====================
checksum32     3_343_822_746       
date           2020-09-17T14:07:29 
engine_version 3.10.0-git74161545cd
============== ====================

num_sites = 4169, num_levels = 1, num_rlzs = 3

Parameters
----------
=============================== ==================================
calculation_mode                'preclassical'                    
number_of_logic_tree_samples    0                                 
maximum_distance                {'default': [(1, 200), (10, 200)]}
investigation_time              1.0                               
ses_per_logic_tree_path         100                               
truncation_level                0.0                               
rupture_mesh_spacing            5.0                               
complex_fault_mesh_spacing      20.0                              
width_of_mfd_bin                0.5                               
area_source_discretization      None                              
pointsource_distance            None                              
ground_motion_correlation_model None                              
minimum_intensity               {'PGA': 0.04, 'default': 0.04}    
random_seed                     69                                
master_seed                     0                                 
ses_seed                        42                                
=============================== ==================================

Input files
-----------
======================= ==========================================================
Name                    File                                                      
======================= ==========================================================
gsim_logic_tree         `gmmLT_2019.xml <gmmLT_2019.xml>`_                        
job_ini                 `job.ini <job.ini>`_                                      
site_model              `cali_newmark_decimated.csv <cali_newmark_decimated.csv>`_
source_model_logic_tree `ssmLT_2019.xml <ssmLT_2019.xml>`_                        
======================= ==========================================================

Composite source model
----------------------
========= ======= ================
smlt_path weight  num_realizations
========= ======= ================
b1        1.00000 3               
========= ======= ================

Required parameters per tectonic region type
--------------------------------------------
====== ======================================================================================= ========= ============ ==============
grp_id gsims                                                                                   distances siteparams   ruptparams    
====== ======================================================================================= ========= ============ ==============
0      '[AbrahamsonEtAl2015SInter]' '[MontalvaEtAl2017SInter]' '[ZhaoEtAl2006SInterNSHMP2008]' rrup      backarc vs30 hypo_depth mag
====== ======================================================================================= ========= ============ ==============

Slowest sources
---------------
========= ==== ============ ========= ========= ============
source_id code multiplicity calc_time num_sites eff_ruptures
========= ==== ============ ========= ========= ============
int_col   C    1            0.03773   53        860         
========= ==== ============ ========= ========= ============

Computation times by source typology
------------------------------------
==== =========
code calc_time
==== =========
C    0.03773  
==== =========

Information about the tasks
---------------------------
================== ======= ====== ======= ======= =======
operation-duration mean    stddev min     max     outputs
preclassical       4.54674 NaN    4.54674 4.54674 1      
read_source_model  0.07523 NaN    0.07523 0.07523 1      
================== ======= ====== ======= ======= =======

Data transfer
-------------
================= ========================================== ========
task              sent                                       received
read_source_model                                            20.52 KB
preclassical      srcs=20.65 KB params=550 B srcfilter=484 B 875 B   
classical                                                    0 B     
================= ========================================== ========

Slowest operations
------------------
=========================== ========= ========= ======
calc_46974                  time_sec  memory_mb counts
=========================== ========= ========= ======
total preclassical          4.54674   4.30469   1     
splitting/filtering sources 4.50749   2.60938   1     
importing inputs            0.24386   3.52344   1     
composite source model      0.17837   1.41797   1     
total read_source_model     0.07523   0.01562   1     
store source_info           0.00119   0.0       1     
aggregate curves            7.670E-04 0.0       1     
=========================== ========= ========= ======