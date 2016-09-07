Classical PSHA using Alaska 2007 active shallow crust grid model
================================================================

============================================== ================================
gem-tstation:/home/michele/ssd/calc_48283.hdf5 updated Wed Sep  7 15:56:31 2016
engine_version                                 2.1.0-git3a14ca6                
hazardlib_version                              0.21.0-git89bccaf               
============================================== ================================

num_sites = 21, sitecol = 1.62 KB

Parameters
----------
============================ ================================
calculation_mode             'classical'                     
number_of_logic_tree_samples 0                               
maximum_distance             {u'Active Shallow Crust': 200.0}
investigation_time           50.0                            
ses_per_logic_tree_path      1                               
truncation_level             3.0                             
rupture_mesh_spacing         4.0                             
complex_fault_mesh_spacing   4.0                             
width_of_mfd_bin             0.1                             
area_source_discretization   10.0                            
random_seed                  23                              
master_seed                  0                               
sites_per_tile               10000                           
============================ ================================

Input files
-----------
======================= ================================================================
Name                    File                                                            
======================= ================================================================
gsim_logic_tree         `gmpe_logic_tree.xml <gmpe_logic_tree.xml>`_                    
job_ini                 `job.ini <job.ini>`_                                            
sites                   `sites.csv <sites.csv>`_                                        
source                  `Alaska_asc_grid_NSHMP2007.xml <Alaska_asc_grid_NSHMP2007.xml>`_
source_model_logic_tree `source_model_logic_tree.xml <source_model_logic_tree.xml>`_    
======================= ================================================================

Composite source model
----------------------
========================= ====== ================================================================ =============== ================
smlt_path                 weight source_model_file                                                gsim_logic_tree num_realizations
========================= ====== ================================================================ =============== ================
Alaska_asc_grid_NSHMP2007 1.000  `Alaska_asc_grid_NSHMP2007.xml <Alaska_asc_grid_NSHMP2007.xml>`_ simple(4)       4/4             
========================= ====== ================================================================ =============== ================

Required parameters per tectonic region type
--------------------------------------------
====== ==================================================================================================== ========= ========== ============
grp_id gsims                                                                                                distances siteparams ruptparams  
====== ==================================================================================================== ========= ========== ============
0      AbrahamsonSilva1997() BooreEtAl1997GeometricMean() CampbellBozorgnia2003NSHMP2007() SadighEtAl1997() rjb rrup  vs30       rake dip mag
====== ==================================================================================================== ========= ========== ============

Realizations per (TRT, GSIM)
----------------------------

::

  <RlzsAssoc(size=4, rlzs=4)
  0,AbrahamsonSilva1997(): ['<0,Alaska_asc_grid_NSHMP2007~Abrahamson_Silva_1997,w=0.25>']
  0,BooreEtAl1997GeometricMean(): ['<1,Alaska_asc_grid_NSHMP2007~Boore_et_al_1997,w=0.25>']
  0,CampbellBozorgnia2003NSHMP2007(): ['<2,Alaska_asc_grid_NSHMP2007~Campbell_Bozorgnia_2003,w=0.25>']
  0,SadighEtAl1997(): ['<3,Alaska_asc_grid_NSHMP2007~Sadigh_et_al_1997,w=0.25>']>

Number of ruptures per tectonic region type
-------------------------------------------
============================= ====== ==================== =========== ============ ======
source_model                  grp_id trt                  num_sources eff_ruptures weight
============================= ====== ==================== =========== ============ ======
Alaska_asc_grid_NSHMP2007.xml 0      Active Shallow Crust 5           436          10    
============================= ====== ==================== =========== ============ ======

Informational data
------------------
======================================== ============
count_eff_ruptures_max_received_per_task 2,367       
count_eff_ruptures_num_tasks             5           
count_eff_ruptures_sent.gsims            1,690       
count_eff_ruptures_sent.monitor          10,735      
count_eff_ruptures_sent.sitecol          4,605       
count_eff_ruptures_sent.sources          7,728       
count_eff_ruptures_tot_received          11,823      
hazard.input_weight                      31          
hazard.n_imts                            6           
hazard.n_levels                          114         
hazard.n_realizations                    4           
hazard.n_sites                           21          
hazard.n_sources                         14          
hazard.output_weight                     57,456      
hostname                                 gem-tstation
======================================== ============

Slowest sources
---------------
============ ========= ============ ====== ========= =========== ========== ============= ============= =========
src_group_id source_id source_class weight split_num filter_time split_time cum_calc_time max_calc_time num_tasks
============ ========= ============ ====== ========= =========== ========== ============= ============= =========
0            8878      PointSource  2.300  1         0.0         3.071E-04  0.0           0.0           0        
0            70088     PointSource  2.300  1         0.0         2.451E-04  0.0           0.0           0        
0            6736      PointSource  2.300  1         0.0         2.050E-04  0.0           0.0           0        
0            3802      PointSource  2.000  0         6.199E-05   0.0        0.0           0.0           0        
0            428       PointSource  2.000  0         3.719E-05   0.0        0.0           0.0           0        
============ ========= ============ ====== ========= =========== ========== ============= ============= =========

Computation times by source typology
------------------------------------
============ =========== ========== ============= ============= ========= ======
source_class filter_time split_time cum_calc_time max_calc_time num_tasks counts
============ =========== ========== ============= ============= ========= ======
PointSource  9.918E-05   7.572E-04  0.0           0.0           0         5     
============ =========== ========== ============= ============= ========= ======

Information about the tasks
---------------------------
================== ========= ========= ========= ========= =========
operation-duration mean      stddev    min       max       num_tasks
count_eff_ruptures 6.371E-04 1.787E-04 4.501E-04 8.440E-04 5        
================== ========= ========= ========= ========= =========

Slowest operations
------------------
============================== ========= ========= ======
operation                      time_sec  memory_mb counts
============================== ========= ========= ======
reading composite source model 0.018     0.0       1     
managing sources               0.011     0.0       1     
total count_eff_ruptures       0.003     0.156     5     
reading site collection        1.640E-04 0.0       1     
filtering sources              9.918E-05 0.0       2     
aggregate curves               8.225E-05 0.0       5     
saving probability maps        2.599E-05 0.0       1     
store source_info              9.060E-06 0.0       1     
============================== ========= ========= ======