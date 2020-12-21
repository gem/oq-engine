North Africa PSHA
=================

============== ====================
checksum32     1_331_502_781       
date           2020-11-02T09:37:32 
engine_version 3.11.0-git82b78631ac
============== ====================

num_sites = 2, num_levels = 133, num_rlzs = 2

Parameters
----------
=============================== ==========================================
calculation_mode                'preclassical'                            
number_of_logic_tree_samples    0                                         
maximum_distance                {'default': [(1.0, 200.0), (10.0, 200.0)]}
investigation_time              50.0                                      
ses_per_logic_tree_path         1                                         
truncation_level                3.0                                       
rupture_mesh_spacing            2.0                                       
complex_fault_mesh_spacing      2.0                                       
width_of_mfd_bin                0.1                                       
area_source_discretization      10.0                                      
pointsource_distance            None                                      
ground_motion_correlation_model None                                      
minimum_intensity               {}                                        
random_seed                     19                                        
master_seed                     0                                         
ses_seed                        42                                        
=============================== ==========================================

Input files
-----------
======================= ============================================================
Name                    File                                                        
======================= ============================================================
gsim_logic_tree         `gmpe_logic_tree.xml <gmpe_logic_tree.xml>`_                
job_ini                 `job.ini <job.ini>`_                                        
sites                   `sites.csv <sites.csv>`_                                    
source_model_logic_tree `source_model_logic_tree.xml <source_model_logic_tree.xml>`_
======================= ============================================================

Composite source model
----------------------
====== ================================================================================================================================================================================================================================================================================== ======
grp_id gsim                                                                                                                                                                                                                                                                               rlzs  
====== ================================================================================================================================================================================================================================================================================== ======
0      '[AvgGMPE.GROUP_B_GMPE_0.ChiouYoungs2014]\nweight = 0.25\n\n[AvgGMPE.GROUP_B_GMPE_1.AkkarEtAlRjb2014]\nadjustment_factor = 1.0\nweight = 0.25\n\n[AvgGMPE.GROUP_B_GMPE_2.AtkinsonBoore2006Modified2011]\nweight = 0.25\n\n[AvgGMPE.GROUP_B_GMPE_3.PezeshkEtAl2011]\nweight = 0.25' [0, 1]
====== ================================================================================================================================================================================================================================================================================== ======

Required parameters per tectonic region type
--------------------------------------------
===== ================================================================================================================================================================================================================================================================================== =========== ======================= =================
et_id gsims                                                                                                                                                                                                                                                                              distances   siteparams              ruptparams       
===== ================================================================================================================================================================================================================================================================================== =========== ======================= =================
0     '[AvgGMPE.GROUP_B_GMPE_0.ChiouYoungs2014]\nweight = 0.25\n\n[AvgGMPE.GROUP_B_GMPE_1.AkkarEtAlRjb2014]\nadjustment_factor = 1.0\nweight = 0.25\n\n[AvgGMPE.GROUP_B_GMPE_2.AtkinsonBoore2006Modified2011]\nweight = 0.25\n\n[AvgGMPE.GROUP_B_GMPE_3.PezeshkEtAl2011]\nweight = 0.25' rjb rrup rx vs30 vs30measured z1pt0 dip mag rake ztor
1     '[AvgGMPE.GROUP_B_GMPE_0.ChiouYoungs2014]\nweight = 0.25\n\n[AvgGMPE.GROUP_B_GMPE_1.AkkarEtAlRjb2014]\nadjustment_factor = 1.0\nweight = 0.25\n\n[AvgGMPE.GROUP_B_GMPE_2.AtkinsonBoore2006Modified2011]\nweight = 0.25\n\n[AvgGMPE.GROUP_B_GMPE_3.PezeshkEtAl2011]\nweight = 0.25' rjb rrup rx vs30 vs30measured z1pt0 dip mag rake ztor
===== ================================================================================================================================================================================================================================================================================== =========== ======================= =================

Slowest sources
---------------
========= ==== ========= ========= ============
source_id code calc_time num_sites eff_ruptures
========= ==== ========= ========= ============
21        M    3.638E-04 1         460         
========= ==== ========= ========= ============

Computation times by source typology
------------------------------------
==== =========
code calc_time
==== =========
M    3.638E-04
==== =========

Information about the tasks
---------------------------
================== ====== ========= ====== ========= =========
operation-duration counts mean      stddev min       max      
preclassical       1      7.832E-04 nan    7.832E-04 7.832E-04
read_source_model  1      0.00224   nan    0.00224   0.00224  
================== ====== ========= ====== ========= =========

Data transfer
-------------
================= ==== ========
task              sent received
read_source_model      1.82 KB 
preclassical           240 B   
================= ==== ========

Slowest operations
------------------
========================= ========= ========= ======
calc_47367, maxmem=0.3 GB time_sec  memory_mb counts
========================= ========= ========= ======
importing inputs          0.06166   0.0       1     
composite source model    0.05647   0.0       1     
total read_source_model   0.00224   0.0       1     
total preclassical        7.832E-04 0.0       1     
========================= ========= ========= ======