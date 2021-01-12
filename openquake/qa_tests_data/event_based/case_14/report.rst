Hazard South Africa
===================

============== ====================
checksum32     745_203_157         
date           2020-11-02T09:36:11 
engine_version 3.11.0-git82b78631ac
============== ====================

num_sites = 10, num_levels = 1, num_rlzs = 3

Parameters
----------
=============================== ================================
calculation_mode                'preclassical'                  
number_of_logic_tree_samples    3                               
maximum_distance                {'default': [(6, 50), (8, 200)]}
investigation_time              100.0                           
ses_per_logic_tree_path         2                               
truncation_level                3.0                             
rupture_mesh_spacing            5.0                             
complex_fault_mesh_spacing      10.0                            
width_of_mfd_bin                0.1                             
area_source_discretization      20.0                            
pointsource_distance            None                            
ground_motion_correlation_model None                            
minimum_intensity               {}                              
random_seed                     113                             
master_seed                     0                               
ses_seed                        23                              
=============================== ================================

Input files
-----------
======================= ============================================================
Name                    File                                                        
======================= ============================================================
gsim_logic_tree         `gmmLT.xml <gmmLT.xml>`_                                    
job_ini                 `job.ini <job.ini>`_                                        
site_model              `Site_model_South_Africa.xml <Site_model_South_Africa.xml>`_
source_model_logic_tree `ssmLT.xml <ssmLT.xml>`_                                    
======================= ============================================================

Composite source model
----------------------
====== ===================== ======
grp_id gsim                  rlzs  
====== ===================== ======
0      '[AkkarEtAlRjb2014]'  [0]   
1      '[AkkarEtAlRjb2014]'  [0]   
1      '[BooreAtkinson2008]' [1]   
2      '[AkkarEtAlRjb2014]'  [0]   
2      '[BooreAtkinson2008]' [2]   
3      '[BooreAtkinson2008]' [1]   
4      '[BooreAtkinson2008]' [1, 2]
5      '[BooreAtkinson2008]' [2]   
====== ===================== ======

Required parameters per tectonic region type
--------------------------------------------
===== ========================================== ========= ========== ==========
et_id gsims                                      distances siteparams ruptparams
===== ========================================== ========= ========== ==========
0     '[AkkarEtAlRjb2014]' '[BooreAtkinson2008]' rjb       vs30       mag rake  
1     '[AkkarEtAlRjb2014]' '[BooreAtkinson2008]' rjb       vs30       mag rake  
2     '[AkkarEtAlRjb2014]' '[BooreAtkinson2008]' rjb       vs30       mag rake  
===== ========================================== ========= ========== ==========

Slowest sources
---------------
========= ==== ========= ========= ============
source_id code calc_time num_sites eff_ruptures
========= ==== ========= ========= ============
18;0      A    1.643E-04 2         320         
18;2      A    1.576E-04 2         320         
22;0      A    1.526E-04 2         12          
20;0      A    1.512E-04 2         12_654      
21;1      A    1.500E-04 3         56          
18;1      A    1.493E-04 2         480         
21;0      A    1.469E-04 3         56          
19;0      A    1.457E-04 1         12_690      
19;1      A    1.431E-04 1         10_152      
22;1      A    1.426E-04 2         12          
20;1      A    1.354E-04 2         23_199      
22;2      A    1.221E-04 2         8           
========= ==== ========= ========= ============

Computation times by source typology
------------------------------------
==== =========
code calc_time
==== =========
A    0.00176  
==== =========

Information about the tasks
---------------------------
================== ====== ========= ====== ========= =========
operation-duration counts mean      stddev min       max      
preclassical       12     6.245E-04 5%     5.436E-04 6.690E-04
read_source_model  5      0.00249   3%     0.00237   0.00261  
================== ====== ========= ====== ========= =========

Data transfer
-------------
================= ================================ ========
task              sent                             received
read_source_model converter=1.62 KB fname=495 B    9.53 KB 
preclassical      srcs=28.96 KB srcfilter=17.74 KB 2.84 KB 
================= ================================ ========

Slowest operations
------------------
========================= ======== ========= ======
calc_47291, maxmem=1.5 GB time_sec memory_mb counts
========================= ======== ========= ======
importing inputs          2.07733  0.0       1     
composite source model    2.06808  0.0       1     
total read_source_model   0.01246  0.46094   5     
total preclassical        0.00749  0.43750   12    
========================= ======== ========= ======