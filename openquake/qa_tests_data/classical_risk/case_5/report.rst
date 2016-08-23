Hazard Calculation for end-to-end hazard+risk
=============================================

gem-tstation:/home/michele/ssd/calc_41554.hdf5 updated Tue Aug 23 17:46:14 2016

num_sites = 1, sitecol = 739 B

Parameters
----------
============================ ================================================================
calculation_mode             'classical'                                                     
number_of_logic_tree_samples 0                                                               
maximum_distance             {u'Subduction Interface': 300.0, u'Active Shallow Crust': 300.0}
investigation_time           15.0                                                            
ses_per_logic_tree_path      1                                                               
truncation_level             4.0                                                             
rupture_mesh_spacing         20.0                                                            
complex_fault_mesh_spacing   20.0                                                            
width_of_mfd_bin             0.2                                                             
area_source_discretization   10.0                                                            
random_seed                  1024                                                            
master_seed                  0                                                               
sites_per_tile               10000                                                           
engine_version               '2.1.0-git5b04a6e'                                              
============================ ================================================================

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
b1        1.000  `source_model.xml <source_model.xml>`_ simple(1,4)     4/4             
========= ====== ====================================== =============== ================

Required parameters per tectonic region type
--------------------------------------------
====== ======================================================================================== ========== ========== ==============
grp_id gsims                                                                                    distances  siteparams ruptparams    
====== ======================================================================================== ========== ========== ==============
0      AkkarBommer2010()                                                                        rjb        vs30       rake mag      
1      AtkinsonBoore2003SInter() LinLee2008SInter() YoungsEtAl1997SInter() ZhaoEtAl2006SInter() rhypo rrup vs30       hypo_depth mag
====== ======================================================================================== ========== ========== ==============

Realizations per (TRT, GSIM)
----------------------------

::

  <RlzsAssoc(size=5, rlzs=4)
  0,AkkarBommer2010(): ['<0,b1~b1_b5,w=0.25>', '<1,b1~b1_b6,w=0.25>', '<2,b1~b1_b7,w=0.25>', '<3,b1~b1_b8,w=0.25>']
  1,AtkinsonBoore2003SInter(): ['<1,b1~b1_b6,w=0.25>']
  1,LinLee2008SInter(): ['<3,b1~b1_b8,w=0.25>']
  1,YoungsEtAl1997SInter(): ['<2,b1~b1_b7,w=0.25>']
  1,ZhaoEtAl2006SInter(): ['<0,b1~b1_b5,w=0.25>']>

Number of ruptures per tectonic region type
-------------------------------------------
================ ====== ==================== =========== ============ ======
source_model     grp_id trt                  num_sources eff_ruptures weight
================ ====== ==================== =========== ============ ======
source_model.xml 0      Active Shallow Crust 1           23           0.575 
source_model.xml 1      Subduction Interface 1           23           0.575 
================ ====== ==================== =========== ============ ======

=============== =====
#TRT models     2    
#sources        2    
#eff_ruptures   46   
filtered_weight 1.150
=============== =====

Informational data
------------------
======================================== ============
count_eff_ruptures_max_received_per_task 1,549       
count_eff_ruptures_num_tasks             2           
count_eff_ruptures_sent.monitor          2,460       
count_eff_ruptures_sent.rlzs_by_gsim     2,295       
count_eff_ruptures_sent.sitecol          866         
count_eff_ruptures_sent.sources          2,394       
count_eff_ruptures_tot_received          3,098       
hazard.input_weight                      1.150       
hazard.n_imts                            1           
hazard.n_levels                          50          
hazard.n_realizations                    4           
hazard.n_sites                           1           
hazard.n_sources                         2           
hazard.output_weight                     200         
hostname                                 gem-tstation
======================================== ============

Slowest sources
---------------
============ ========= ============ ====== ========= =========== ========== ============= ============= =========
src_group_id source_id source_class weight split_num filter_time split_time cum_calc_time max_calc_time num_tasks
============ ========= ============ ====== ========= =========== ========== ============= ============= =========
0            A         PointSource  0.575  1         7.510E-05   0.0        0.0           0.0           0        
1            B         PointSource  0.575  1         4.911E-05   0.0        0.0           0.0           0        
============ ========= ============ ====== ========= =========== ========== ============= ============= =========

Computation times by source typology
------------------------------------
============ =========== ========== ============= ============= ========= ======
source_class filter_time split_time cum_calc_time max_calc_time num_tasks counts
============ =========== ========== ============= ============= ========= ======
PointSource  1.242E-04   0.0        0.0           0.0           0         2     
============ =========== ========== ============= ============= ========= ======

Information about the tasks
---------------------------
Not available

Slowest operations
------------------
============================== ========= ========= ======
operation                      time_sec  memory_mb counts
============================== ========= ========= ======
store source_info              0.010     0.0       1     
reading composite source model 0.008     0.0       1     
managing sources               0.005     0.0       1     
total count_eff_ruptures       5.670E-04 0.0       2     
filtering sources              1.242E-04 0.0       2     
reading site collection        3.600E-05 0.0       1     
aggregate curves               3.481E-05 0.0       2     
saving probability maps        2.384E-05 0.0       1     
============================== ========= ========= ======