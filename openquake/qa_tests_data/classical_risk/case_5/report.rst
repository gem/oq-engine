Hazard Calculation for end-to-end hazard+risk
=============================================

num_sites = 1, sitecol = 684 B

Parameters
----------
============================ =========
calculation_mode             classical
number_of_logic_tree_samples 0        
maximum_distance             300.0    
investigation_time           15.0     
ses_per_logic_tree_path      1        
truncation_level             4.0      
rupture_mesh_spacing         20.0     
complex_fault_mesh_spacing   20.0     
width_of_mfd_bin             0.2      
area_source_discretization   10.0     
random_seed                  1024     
master_seed                  0        
concurrent_tasks             16       
sites_per_tile               1000     
============================ =========

Input files
-----------
======================= ============================================================
Name                    File                                                        
======================= ============================================================
gsim_logic_tree         `gsim_logic_tree.xml <gsim_logic_tree.xml>`_                
job_ini                 `job_h.ini <job_h.ini>`_                                    
source                  `source_model.xml <source_model.xml>`_                      
source_model_logic_tree `source_model_logic_tree.xml <source_model_logic_tree.xml>`_
======================= ============================================================

Composite source model
----------------------
========= ====== ====================================== =============== ================
smlt_path weight source_model_file                      gsim_logic_tree num_realizations
========= ====== ====================================== =============== ================
b1        1.0    `source_model.xml <source_model.xml>`_ simple(1,4)     4/4             
========= ====== ====================================== =============== ================

Required parameters per tectonic region type
--------------------------------------------
====== ================================================================================ ========== ========== ==============
trt_id gsims                                                                            distances  siteparams ruptparams    
====== ================================================================================ ========== ========== ==============
0      AkkarBommer2010                                                                  rjb        vs30       rake mag      
1      AtkinsonBoore2003SInter LinLee2008SInter YoungsEtAl1997SInter ZhaoEtAl2006SInter rhypo rrup vs30       hypo_depth mag
====== ================================================================================ ========== ========== ==============

Realizations per (TRT, GSIM)
----------------------------

::

  <RlzsAssoc(5)
  0,AkkarBommer2010: ['<0,b1,b1_b5,w=0.25>', '<1,b1,b1_b6,w=0.25>', '<2,b1,b1_b7,w=0.25>', '<3,b1,b1_b8,w=0.25>']
  1,AtkinsonBoore2003SInter: ['<1,b1,b1_b6,w=0.25>']
  1,LinLee2008SInter: ['<3,b1,b1_b8,w=0.25>']
  1,YoungsEtAl1997SInter: ['<2,b1,b1_b7,w=0.25>']
  1,ZhaoEtAl2006SInter: ['<0,b1,b1_b5,w=0.25>']>

Number of ruptures per tectonic region type
-------------------------------------------
================ ====== ==================== =========== ============ ==============
source_model     trt_id trt                  num_sources eff_ruptures weight        
================ ====== ==================== =========== ============ ==============
source_model.xml 0      Active Shallow Crust 1           23           0.574999988079
source_model.xml 1      Subduction Interface 1           23           0.574999988079
================ ====== ==================== =========== ============ ==============

=============== =============
#TRT models     2            
#sources        2            
#eff_ruptures   46           
filtered_weight 1.14999997616
=============== =============

Expected data transfer for the sources
--------------------------------------
=========================== ========
Number of tasks to generate 2       
Sent data                   16.23 KB
=========================== ========

Slowest sources
---------------
============ ========= ============ ====== ========= =========== ========== =========
trt_model_id source_id source_class weight split_num filter_time split_time calc_time
============ ========= ============ ====== ========= =========== ========== =========
0            A         PointSource  0.575  1         0.00018096  0.0        0.0      
1            B         PointSource  0.575  1         0.000118017 0.0        0.0      
============ ========= ============ ====== ========= =========== ========== =========