QA test for disaggregation case_2
=================================

gem-tstation:/home/michele/ssd/calc_42038.hdf5 updated Wed Aug 24 08:05:16 2016

num_sites = 2, sitecol = 785 B

Parameters
----------
============================ ================================================================
calculation_mode             'disaggregation'                                                
number_of_logic_tree_samples 0                                                               
maximum_distance             {u'Subduction IntraSlab': 200.0, u'Active Shallow Crust': 200.0}
investigation_time           1.0                                                             
ses_per_logic_tree_path      1                                                               
truncation_level             3.0                                                             
rupture_mesh_spacing         4.0                                                             
complex_fault_mesh_spacing   4.0                                                             
width_of_mfd_bin             0.1                                                             
area_source_discretization   10.0                                                            
random_seed                  23                                                              
master_seed                  0                                                               
engine_version               '2.1.0-git46eb8e0'                                              
============================ ================================================================

Input files
-----------
======================= ============================================================
Name                    File                                                        
======================= ============================================================
gsim_logic_tree         `gmpe_logic_tree.xml <gmpe_logic_tree.xml>`_                
job_ini                 `job.ini <job.ini>`_                                        
source                  `source_model_1.xml <source_model_1.xml>`_                  
source                  `source_model_2.xml <source_model_2.xml>`_                  
source_model_logic_tree `source_model_logic_tree.xml <source_model_logic_tree.xml>`_
======================= ============================================================

Composite source model
----------------------
============== ====== ========================================== =============== ================
smlt_path      weight source_model_file                          gsim_logic_tree num_realizations
============== ====== ========================================== =============== ================
source_model_1 0.500  `source_model_1.xml <source_model_1.xml>`_ simple(2,1)     2/2             
source_model_2 0.500  `source_model_2.xml <source_model_2.xml>`_ simple(2,1)     2/2             
============== ====== ========================================== =============== ================

Required parameters per tectonic region type
--------------------------------------------
====== ===================================== =========== ======================= =================
grp_id gsims                                 distances   siteparams              ruptparams       
====== ===================================== =========== ======================= =================
0      YoungsEtAl1997SSlab()                 rrup        vs30                    hypo_depth mag   
1      BooreAtkinson2008() ChiouYoungs2008() rx rjb rrup vs30measured z1pt0 vs30 ztor mag rake dip
2      BooreAtkinson2008() ChiouYoungs2008() rx rjb rrup vs30measured z1pt0 vs30 ztor mag rake dip
====== ===================================== =========== ======================= =================

Realizations per (TRT, GSIM)
----------------------------

::

  <RlzsAssoc(size=5, rlzs=4)
  0,YoungsEtAl1997SSlab(): ['<0,source_model_1~BooreAtkinson2008_YoungsEtAl1997SSlab,w=0.25>', '<1,source_model_1~ChiouYoungs2008_YoungsEtAl1997SSlab,w=0.25>']
  1,BooreAtkinson2008(): ['<0,source_model_1~BooreAtkinson2008_YoungsEtAl1997SSlab,w=0.25>']
  1,ChiouYoungs2008(): ['<1,source_model_1~ChiouYoungs2008_YoungsEtAl1997SSlab,w=0.25>']
  2,BooreAtkinson2008(): ['<2,source_model_2~BooreAtkinson2008_@,w=0.25>']
  2,ChiouYoungs2008(): ['<3,source_model_2~ChiouYoungs2008_@,w=0.25>']>

Number of ruptures per tectonic region type
-------------------------------------------
================== ====== ==================== =========== ============ ======
source_model       grp_id trt                  num_sources eff_ruptures weight
================== ====== ==================== =========== ============ ======
source_model_1.xml 0      Subduction Intraslab 1           1815         45    
source_model_1.xml 1      Active Shallow Crust 2           3630         90    
source_model_2.xml 2      Active Shallow Crust 1           1420         1,420 
================== ====== ==================== =========== ============ ======

=============== =====
#TRT models     3    
#sources        4    
#eff_ruptures   6,865
filtered_weight 1,556
=============== =====

Informational data
------------------
======================================== ============
count_eff_ruptures_max_received_per_task 1,370       
count_eff_ruptures_num_tasks             14          
count_eff_ruptures_sent.monitor          14,602      
count_eff_ruptures_sent.rlzs_by_gsim     11,913      
count_eff_ruptures_sent.sitecol          6,342       
count_eff_ruptures_sent.sources          18,296      
count_eff_ruptures_tot_received          19,168      
hazard.input_weight                      1,556       
hazard.n_imts                            1           
hazard.n_levels                          19          
hazard.n_realizations                    4           
hazard.n_sites                           2           
hazard.n_sources                         4           
hazard.output_weight                     152         
hostname                                 gem-tstation
======================================== ============

Slowest sources
---------------
============ ========= ================= ====== ========= =========== ========== ============= ============= =========
src_group_id source_id source_class      weight split_num filter_time split_time cum_calc_time max_calc_time num_tasks
============ ========= ================= ====== ========= =========== ========== ============= ============= =========
2            1         SimpleFaultSource 1,420  15        0.002       0.079      0.0           0.0           0        
0            2         AreaSource        45     1         7.410E-04   0.0        0.0           0.0           0        
1            1         AreaSource        45     1         6.659E-04   0.0        0.0           0.0           0        
1            3         AreaSource        45     1         6.611E-04   0.0        0.0           0.0           0        
============ ========= ================= ====== ========= =========== ========== ============= ============= =========

Computation times by source typology
------------------------------------
================= =========== ========== ============= ============= ========= ======
source_class      filter_time split_time cum_calc_time max_calc_time num_tasks counts
================= =========== ========== ============= ============= ========= ======
AreaSource        0.002       0.0        0.0           0.0           0         3     
SimpleFaultSource 0.002       0.079      0.0           0.0           0         1     
================= =========== ========== ============= ============= ========= ======

Information about the tasks
---------------------------
Not available

Slowest operations
------------------
============================== ========= ========= ======
operation                      time_sec  memory_mb counts
============================== ========= ========= ======
managing sources               0.104     0.0       1     
splitting sources              0.079     0.0       1     
reading composite source model 0.044     0.0       1     
store source_info              0.006     0.0       1     
total count_eff_ruptures       0.004     0.0       14    
filtering sources              0.004     0.0       4     
aggregate curves               3.123E-04 0.0       14    
saving probability maps        3.314E-05 0.0       1     
reading site collection        2.599E-05 0.0       1     
============================== ========= ========= ======