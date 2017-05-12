Germany_SHARE Combined Model event_based
========================================

================================================ ========================
tstation.gem.lan:/mnt/ssd/oqdata/calc_20460.hdf5 Fri May 12 06:38:35 2017
engine_version                                   2.4.0-giteadb85d        
hazardlib_version                                0.24.0-git0596dd3       
================================================ ========================

num_sites = 100, sitecol = 6.03 KB

Parameters
----------
=============================== =================
calculation_mode                'event_based'    
number_of_logic_tree_samples    0                
maximum_distance                {'default': 80.0}
investigation_time              30.0             
ses_per_logic_tree_path         1                
truncation_level                3.0              
rupture_mesh_spacing            5.0              
complex_fault_mesh_spacing      5.0              
width_of_mfd_bin                0.1              
area_source_discretization      10.0             
ground_motion_correlation_model None             
random_seed                     42               
master_seed                     0                
=============================== =================

Input files
-----------
======================= ==============================================================================
Name                    File                                                                          
======================= ==============================================================================
gsim_logic_tree         `complete_gmpe_logic_tree.xml <complete_gmpe_logic_tree.xml>`_                
job_ini                 `job.ini <job.ini>`_                                                          
sites                   `sites.csv <sites.csv>`_                                                      
source                  `as_model.xml <as_model.xml>`_                                                
source                  `fs_bg_source_model.xml <fs_bg_source_model.xml>`_                            
source                  `ss_model_final_250km_Buffer.xml <ss_model_final_250km_Buffer.xml>`_          
source_model_logic_tree `combined_logic-tree-source-model.xml <combined_logic-tree-source-model.xml>`_
======================= ==============================================================================

Composite source model
----------------------
========= ====== ================================================================================================ ================ ================
smlt_path weight source_model_file                                                                                gsim_logic_tree  num_realizations
========= ====== ================================================================================================ ================ ================
b1        0.500  `source_models/as_model.xml <source_models/as_model.xml>`_                                       complex(5,2,4,1) 1/1             
b2        0.200  `source_models/fs_bg_source_model.xml <source_models/fs_bg_source_model.xml>`_                   complex(5,2,4,1) 5/5             
b3        0.300  `source_models/ss_model_final_250km_Buffer.xml <source_models/ss_model_final_250km_Buffer.xml>`_ complex(5,2,4,1) 0/0             
========= ====== ================================================================================================ ================ ================

Required parameters per tectonic region type
--------------------------------------------
====== ================================================================================================ ================= ======================= =================
grp_id gsims                                                                                            distances         siteparams              ruptparams       
====== ================================================================================================ ================= ======================= =================
1      FaccioliEtAl2010()                                                                               rrup              vs30                    mag rake         
4      AkkarBommer2010() Campbell2003SHARE() CauzziFaccioli2008() ChiouYoungs2008() ToroEtAl2002SHARE() rrup rx rjb rhypo vs30 vs30measured z1pt0 dip mag rake ztor
====== ================================================================================================ ================= ======================= =================

Realizations per (TRT, GSIM)
----------------------------

::

  <RlzsAssoc(size=6, rlzs=6)
  1,FaccioliEtAl2010(): ['<0,b1~@_@_@_b4_1,w=0.7142857112446609>']
  4,AkkarBommer2010(): ['<1,b2~@_b2_1_@_@,w=0.057142857751067797>']
  4,Campbell2003SHARE(): ['<5,b2~@_b2_5_@_@,w=0.057142857751067797>']
  4,CauzziFaccioli2008(): ['<2,b2~@_b2_2_@_@,w=0.057142857751067797>']
  4,ChiouYoungs2008(): ['<3,b2~@_b2_3_@_@,w=0.057142857751067797>']
  4,ToroEtAl2002SHARE(): ['<4,b2~@_b2_4_@_@,w=0.057142857751067797>']>

Number of ruptures per tectonic region type
-------------------------------------------
==================================== ====== ==================== =========== ============ ============
source_model                         grp_id trt                  num_sources eff_ruptures tot_ruptures
==================================== ====== ==================== =========== ============ ============
source_models/as_model.xml           1      Volcanic             2           2            84          
source_models/fs_bg_source_model.xml 4      Stable Shallow Crust 49          3            440,748     
==================================== ====== ==================== =========== ============ ============

============= =======
#TRT models   2      
#sources      51     
#eff_ruptures 5      
#tot_ruptures 440,832
#tot_weight   54,740 
============= =======

Informational data
------------------
============================ =================================================================================
compute_ruptures.received    tot 16.03 KB, max_per_task 5.14 KB                                               
compute_ruptures.sent        sources 2.14 MB, src_filter 27.09 KB, monitor 6.21 KB, gsims 1.86 KB, param 520 B
hazard.input_weight          54,739                                                                           
hazard.n_imts                1 B                                                                              
hazard.n_levels              1 B                                                                              
hazard.n_realizations        120 B                                                                            
hazard.n_sites               100 B                                                                            
hazard.n_sources             142 B                                                                            
hazard.output_weight         3,600                                                                            
hostname                     tstation.gem.lan                                                                 
require_epsilons             0 B                                                                              
============================ =================================================================================

Slowest sources
---------------
====== ========= ================= ============ ========= ========= =========
grp_id source_id source_class      num_ruptures calc_time num_sites num_split
====== ========= ================= ============ ========= ========= =========
4      325       AreaSource        34,932       0.0       0         0        
4      253       AreaSource        1,092        0.0       0         0        
7      330046    PointSource       20           0.0       0         0        
6      323893    PointSource       6            0.0       0         0        
3      297       SimpleFaultSource 44           0.0       0         0        
7      330070    PointSource       12           0.0       0         0        
7      330071    PointSource       12           0.0       0         0        
3      357       SimpleFaultSource 50           0.0       0         0        
4      20        SimpleFaultSource 31           0.0       0         0        
4      257       AreaSource        348          0.0       0         0        
4      255       AreaSource        11,064       0.0       0         0        
3      419       SimpleFaultSource 68           0.0       0         0        
6      323949    PointSource       6            0.0       0         0        
4      252       AreaSource        1,092        0.0       0         0        
7      330075    PointSource       16           0.0       0         0        
4      331       AreaSource        2,256        0.0       0         0        
3      30        SimpleFaultSource 158          0.0       0         0        
7      330068    PointSource       18           0.0       0         0        
7      330050    PointSource       28           0.0       0         0        
3      345       SimpleFaultSource 35           0.0       0         0        
====== ========= ================= ============ ========= ========= =========

Computation times by source typology
------------------------------------
================= ========= ======
source_class      calc_time counts
================= ========= ======
AreaSource        0.0       51    
PointSource       0.0       51    
SimpleFaultSource 0.0       40    
================= ========= ======

Information about the tasks
---------------------------
================== ===== ====== ===== === =========
operation-duration mean  stddev min   max num_tasks
compute_ruptures   7.088 19     0.001 55  8        
================== ===== ====== ===== === =========

Slowest operations
------------------
================================ ========= ========= ======
operation                        time_sec  memory_mb counts
================================ ========= ========= ======
total compute_ruptures           56        0.469     8     
reading composite source model   9.272     0.0       1     
managing sources                 0.015     0.0       1     
saving ruptures                  0.011     0.0       8     
setting event years              0.004     0.0       1     
store source_info                0.003     0.0       1     
filtering ruptures               0.003     0.0       8     
reading site collection          5.832E-04 0.0       1     
filtering composite source model 2.742E-05 0.0       1     
================================ ========= ========= ======