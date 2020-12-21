Reduced Hazard Italy
====================

============== ====================
checksum32     237_210_023         
date           2020-11-02T09:36:09 
engine_version 3.11.0-git82b78631ac
============== ====================

num_sites = 148, num_levels = 3, num_rlzs = 4

Parameters
----------
=============================== ======================================
calculation_mode                'preclassical'                        
number_of_logic_tree_samples    0                                     
maximum_distance                {'default': [(1.0, 300), (10.0, 300)]}
investigation_time              200.0                                 
ses_per_logic_tree_path         1                                     
truncation_level                3.0                                   
rupture_mesh_spacing            5.0                                   
complex_fault_mesh_spacing      10.0                                  
width_of_mfd_bin                0.2                                   
area_source_discretization      20.0                                  
pointsource_distance            None                                  
ground_motion_correlation_model None                                  
minimum_intensity               {}                                    
random_seed                     113                                   
master_seed                     0                                     
ses_seed                        42                                    
=============================== ======================================

Input files
-----------
======================= ============================================================
Name                    File                                                        
======================= ============================================================
amplification           `amplification.csv <amplification.csv>`_                    
exposure                `exposure.xml <exposure.xml>`_                              
gsim_logic_tree         `gmpe_logic_tree.xml <gmpe_logic_tree.xml>`_                
job_ini                 `job.ini <job.ini>`_                                        
site_model              `site_model.csv <site_model.csv>`_                          
source_model_logic_tree `source_model_logic_tree.xml <source_model_logic_tree.xml>`_
======================= ============================================================

Composite source model
----------------------
====== ====================== ====
grp_id gsim                   rlzs
====== ====================== ====
0      '[AkkarBommer2010]'    [0] 
0      '[CauzziFaccioli2008]' [1] 
0      '[ChiouYoungs2008]'    [2] 
0      '[ZhaoEtAl2006Asc]'    [3] 
====== ====================== ====

Required parameters per tectonic region type
--------------------------------------------
===== ================================================================================== ================= ======================= ============================
et_id gsims                                                                              distances         siteparams              ruptparams                  
===== ================================================================================== ================= ======================= ============================
0     '[AkkarBommer2010]' '[CauzziFaccioli2008]' '[ChiouYoungs2008]' '[ZhaoEtAl2006Asc]' rhypo rjb rrup rx vs30 vs30measured z1pt0 dip hypo_depth mag rake ztor
===== ================================================================================== ================= ======================= ============================

Exposure model
--------------
=========== ===
#assets     151
#taxonomies 17 
=========== ===

================= ========== ======= ====== === === =========
taxonomy          num_assets mean    stddev min max num_sites
CR/CDN/HBET:1-2   8          1.00000 0%     1   1   8        
CR/CDM/HBET:1-2   13         1.00000 0%     1   1   13       
CR/CDM/HBET:3-5   14         1.00000 0%     1   1   14       
CR/CDN/H:4        2          1.00000 0%     1   1   2        
MUR/LWAL/HBET:5-8 6          1.00000 0%     1   1   6        
CR/CDM/HBET:6-8   3          1.00000 0%     1   1   3        
MUR/LWAL/H:3      18         1.00000 0%     1   1   18       
CR/CDM/SOS        10         1.00000 0%     1   1   10       
MUR/LWAL/HBET:1-2 17         1.00000 0%     1   1   17       
CR/CDN/SOS        10         1.00000 0%     1   1   10       
W/CDN/HBET:1-3    14         1.00000 0%     1   1   14       
CR/CDH/HBET:1-2   11         1.00000 0%     1   1   11       
CR/CDH/HBET:6-8   3          1.00000 0%     1   1   3        
MUR/LWAL/H:4      8          1.00000 0%     1   1   8        
CR/CDH/HBET:3-5   9          1.00000 0%     1   1   9        
S/CDM/HBET:4-8    2          1.00000 0%     1   1   2        
CR/CDN/H:3        3          1.00000 0%     1   1   3        
*ALL*             148        1.02027 13%    1   2   151      
================= ========== ======= ====== === === =========

Slowest sources
---------------
========== ==== ========= ========= ============
source_id  code calc_time num_sites eff_ruptures
========== ==== ========= ========= ============
AS_HRAS083 A    1.564E-04 28        2_295       
========== ==== ========= ========= ============

Computation times by source typology
------------------------------------
==== =========
code calc_time
==== =========
A    1.564E-04
==== =========

Information about the tasks
---------------------------
================== ====== ========= ====== ========= =========
operation-duration counts mean      stddev min       max      
preclassical       1      7.145E-04 nan    7.145E-04 7.145E-04
read_source_model  1      0.00378   nan    0.00378   0.00378  
================== ====== ========= ====== ========= =========

Data transfer
-------------
================= ==== ========
task              sent received
read_source_model      2.07 KB 
preclassical           248 B   
================= ==== ========

Slowest operations
------------------
========================= ========= ========= ======
calc_47288, maxmem=0.3 GB time_sec  memory_mb counts
========================= ========= ========= ======
importing inputs          0.15511   0.07422   1     
composite source model    0.09332   0.0       1     
total read_source_model   0.00378   0.0       1     
reading exposure          0.00329   0.0       1     
total preclassical        7.145E-04 0.0       1     
========================= ========= ========= ======