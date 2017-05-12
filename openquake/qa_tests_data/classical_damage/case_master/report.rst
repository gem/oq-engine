classical damage
================

================================================ ========================
tstation.gem.lan:/mnt/ssd/oqdata/calc_21296.hdf5 Fri May 12 10:45:17 2017
engine_version                                   2.4.0-git59713b5        
hazardlib_version                                0.24.0-git0596dd3       
================================================ ========================

num_sites = 7, sitecol = 1.11 KB

Parameters
----------
=============================== ==================
calculation_mode                'classical_damage'
number_of_logic_tree_samples    0                 
maximum_distance                {'default': 200.0}
investigation_time              1.0               
ses_per_logic_tree_path         1                 
truncation_level                3.0               
rupture_mesh_spacing            2.0               
complex_fault_mesh_spacing      2.0               
width_of_mfd_bin                0.1               
area_source_discretization      10.0              
ground_motion_correlation_model None              
random_seed                     24                
master_seed                     0                 
=============================== ==================

Input files
-----------
======================= ========================================================================
Name                    File                                                                    
======================= ========================================================================
contents_fragility      `contents_fragility_model.xml <contents_fragility_model.xml>`_          
exposure                `exposure_model.xml <exposure_model.xml>`_                              
gsim_logic_tree         `gsim_logic_tree.xml <gsim_logic_tree.xml>`_                            
job_ini                 `job.ini <job.ini>`_                                                    
nonstructural_fragility `nonstructural_fragility_model.xml <nonstructural_fragility_model.xml>`_
source                  `source_model_1.xml <source_model_1.xml>`_                              
source                  `source_model_2.xml <source_model_2.xml>`_                              
source_model_logic_tree `source_model_logic_tree.xml <source_model_logic_tree.xml>`_            
structural_fragility    `structural_fragility_model.xml <structural_fragility_model.xml>`_      
======================= ========================================================================

Composite source model
----------------------
========= ====== ========================================== =============== ================
smlt_path weight source_model_file                          gsim_logic_tree num_realizations
========= ====== ========================================== =============== ================
b1        0.250  `source_model_1.xml <source_model_1.xml>`_ complex(2,2)    4/4             
b2        0.750  `source_model_2.xml <source_model_2.xml>`_ complex(2,2)    4/4             
========= ====== ========================================== =============== ================

Required parameters per tectonic region type
--------------------------------------------
====== ===================================== =========== ======================= =================
grp_id gsims                                 distances   siteparams              ruptparams       
====== ===================================== =========== ======================= =================
0      BooreAtkinson2008() ChiouYoungs2008() rjb rrup rx vs30 vs30measured z1pt0 dip mag rake ztor
1      AkkarBommer2010() ChiouYoungs2008()   rjb rrup rx vs30 vs30measured z1pt0 dip mag rake ztor
2      BooreAtkinson2008() ChiouYoungs2008() rjb rrup rx vs30 vs30measured z1pt0 dip mag rake ztor
3      AkkarBommer2010() ChiouYoungs2008()   rjb rrup rx vs30 vs30measured z1pt0 dip mag rake ztor
====== ===================================== =========== ======================= =================

Realizations per (TRT, GSIM)
----------------------------

::

  <RlzsAssoc(size=8, rlzs=8)
  0,BooreAtkinson2008(): ['<0,b1~b11_b21,w=0.1125>', '<1,b1~b11_b22,w=0.075>']
  0,ChiouYoungs2008(): ['<2,b1~b12_b21,w=0.0375>', '<3,b1~b12_b22,w=0.025>']
  1,AkkarBommer2010(): ['<0,b1~b11_b21,w=0.1125>', '<2,b1~b12_b21,w=0.0375>']
  1,ChiouYoungs2008(): ['<1,b1~b11_b22,w=0.075>', '<3,b1~b12_b22,w=0.025>']
  2,BooreAtkinson2008(): ['<4,b2~b11_b21,w=0.3375>', '<5,b2~b11_b22,w=0.22499999999999998>']
  2,ChiouYoungs2008(): ['<6,b2~b12_b21,w=0.11249999999999999>', '<7,b2~b12_b22,w=0.07500000000000001>']
  3,AkkarBommer2010(): ['<4,b2~b11_b21,w=0.3375>', '<6,b2~b12_b21,w=0.11249999999999999>']
  3,ChiouYoungs2008(): ['<5,b2~b11_b22,w=0.22499999999999998>', '<7,b2~b12_b22,w=0.07500000000000001>']>

Number of ruptures per tectonic region type
-------------------------------------------
================== ====== ==================== =========== ============ ============
source_model       grp_id trt                  num_sources eff_ruptures tot_ruptures
================== ====== ==================== =========== ============ ============
source_model_1.xml 0      Active Shallow Crust 1           482          482         
source_model_1.xml 1      Stable Shallow Crust 1           4            4           
source_model_2.xml 2      Active Shallow Crust 1           482          482         
source_model_2.xml 3      Stable Shallow Crust 1           1            1           
================== ====== ==================== =========== ============ ============

============= ===
#TRT models   4  
#sources      4  
#eff_ruptures 969
#tot_ruptures 969
#tot_weight   969
============= ===

Informational data
------------------
============================== =============================================================================
count_eff_ruptures.received    tot 7.24 KB, max_per_task 1.81 KB                                            
count_eff_ruptures.sent        sources 13.9 KB, monitor 6.29 KB, srcfilter 3.33 KB, gsims 708 B, param 260 B
hazard.input_weight            969                                                                          
hazard.n_imts                  3 B                                                                          
hazard.n_levels                79 B                                                                         
hazard.n_realizations          8 B                                                                          
hazard.n_sites                 7 B                                                                          
hazard.n_sources               4 B                                                                          
hazard.output_weight           2,212                                                                        
hostname                       tstation.gem.lan                                                             
require_epsilons               0 B                                                                          
============================== =============================================================================

Exposure model
--------------
=============== ========
#assets         7       
#taxonomies     3       
deductibile     absolute
insurance_limit absolute
=============== ========

======== ===== ====== === === ========= ==========
taxonomy mean  stddev min max num_sites num_assets
tax1     1.000 0.0    1   1   4         4         
tax2     1.000 0.0    1   1   2         2         
tax3     1.000 NaN    1   1   1         1         
*ALL*    1.000 0.0    1   1   7         7         
======== ===== ====== === === ========= ==========

Slowest sources
---------------
====== ========= ========================= ============ ========= ========= =========
grp_id source_id source_class              num_ruptures calc_time num_sites num_split
====== ========= ========================= ============ ========= ========= =========
1      2         SimpleFaultSource         4            0.004     7         1        
3      2         CharacteristicFaultSource 1            0.003     7         1        
0      1         SimpleFaultSource         482          0.003     7         1        
2      1         SimpleFaultSource         482          0.002     7         1        
====== ========= ========================= ============ ========= ========= =========

Computation times by source typology
------------------------------------
========================= ========= ======
source_class              calc_time counts
========================= ========= ======
CharacteristicFaultSource 0.003     1     
SimpleFaultSource         0.008     3     
========================= ========= ======

Information about the tasks
---------------------------
================== ===== ========= ===== ===== =========
operation-duration mean  stddev    min   max   num_tasks
count_eff_ruptures 0.004 9.113E-04 0.002 0.005 4        
================== ===== ========= ===== ===== =========

Slowest operations
------------------
================================ ========= ========= ======
operation                        time_sec  memory_mb counts
================================ ========= ========= ======
total count_eff_ruptures         0.015     0.066     4     
reading composite source model   0.013     0.0       1     
reading exposure                 0.006     0.0       1     
managing sources                 0.003     0.0       1     
store source_info                0.001     0.0       1     
aggregate curves                 1.340E-04 0.0       4     
saving probability maps          5.007E-05 0.0       1     
filtering composite source model 4.768E-05 0.0       1     
reading site collection          5.245E-06 0.0       1     
================================ ========= ========= ======