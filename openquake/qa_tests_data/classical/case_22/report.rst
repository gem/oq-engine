Classical PSHA using Alaska 2007 active shallow crust grid model
================================================================

gem-tstation:/home/michele/ssd/calc_22592.hdf5 updated Tue May 31 15:37:43 2016

num_sites = 21, sitecol = 1.62 KB

Parameters
----------
============================ ===============================
calculation_mode             'classical'                    
number_of_logic_tree_samples 0                              
maximum_distance             {'Active Shallow Crust': 200.0}
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
engine_version               '2.0.0-git4fb4450'             
============================ ===============================

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
Alaska_asc_grid_NSHMP2007.xml 0      Active Shallow Crust 14          1264         31    
============================= ====== ==================== =========== ============ ======

Informational data
------------------
======================================== ============
count_eff_ruptures_max_received_per_task 4,033       
count_eff_ruptures_num_tasks             14          
count_eff_ruptures_sent.monitor          52,850      
count_eff_ruptures_sent.rlzs_assoc       20,062      
count_eff_ruptures_sent.sitecol          11,662      
count_eff_ruptures_sent.siteidx          70          
count_eff_ruptures_sent.sources          21,659      
count_eff_ruptures_tot_received          56,462      
hazard.input_weight                      31          
hazard.n_imts                            6           
hazard.n_levels                          19          
hazard.n_realizations                    4           
hazard.n_sites                           21          
hazard.n_sources                         0           
hazard.output_weight                     9,576       
hostname                                 gem-tstation
======================================== ============

Slowest sources
---------------
============ ========= ============ ====== ========= =========== ========== =========
src_group_id source_id source_class weight split_num filter_time split_time calc_time
============ ========= ============ ====== ========= =========== ========== =========
0            102588    PointSource  2.300  1         1.841E-04   2.003E-05  0.0      
0            106150    PointSource  2.300  1         1.769E-04   1.192E-05  0.0      
0            22285     PointSource  2.300  1         1.569E-04   1.192E-05  0.0      
0            15999     PointSource  2.300  1         1.011E-04   1.097E-05  0.0      
0            8878      PointSource  2.300  1         6.104E-05   9.775E-06  0.0      
0            23947     PointSource  2.300  1         3.600E-05   1.287E-05  0.0      
0            3802      PointSource  2.000  1         4.601E-05   0.0        0.0      
0            70088     PointSource  2.300  1         3.505E-05   1.097E-05  0.0      
0            41060     PointSource  2.300  1         3.386E-05   1.121E-05  0.0      
0            44535     PointSource  2.300  1         3.314E-05   1.001E-05  0.0      
0            6736      PointSource  2.300  1         3.290E-05   1.001E-05  0.0      
0            98725     PointSource  2.300  1         2.599E-05   8.106E-06  0.0      
0            98979     PointSource  2.300  1         2.503E-05   7.868E-06  0.0      
0            428       PointSource  2.000  1         2.909E-05   0.0        0.0      
============ ========= ============ ====== ========= =========== ========== =========

Computation times by source typology
------------------------------------
============ =========== ========== ========= ======
source_class filter_time split_time calc_time counts
============ =========== ========== ========= ======
PointSource  9.770E-04   1.357E-04  0.0       14    
============ =========== ========== ========= ======

Information about the tasks
---------------------------
Not available

Slowest operations
------------------
============================== ========= ========= ======
operation                      time_sec  memory_mb counts
============================== ========= ========= ======
reading composite source model 0.015     0.0       1     
managing sources               0.014     0.0       1     
store source_info              0.004     0.0       1     
total count_eff_ruptures       0.003     0.0       14    
filtering sources              9.770E-04 0.0       14    
aggregate curves               1.817E-04 0.0       14    
splitting sources              1.357E-04 0.0       12    
reading site collection        1.318E-04 0.0       1     
============================== ========= ========= ======