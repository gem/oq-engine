Classical PSHA using Alaska 2007 active shallow crust grid model
================================================================

gem-tstation:/home/michele/ssd/calc_41677.hdf5 updated Tue Aug 23 19:27:40 2016

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
engine_version               '2.1.0-gitc83a72d'              
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
Alaska_asc_grid_NSHMP2007.xml 0      Active Shallow Crust 14          1264         31    
============================= ====== ==================== =========== ============ ======

Informational data
------------------
======================================== ============
count_eff_ruptures_max_received_per_task 2,374       
count_eff_ruptures_num_tasks             14          
count_eff_ruptures_sent.monitor          28,756      
count_eff_ruptures_sent.rlzs_by_gsim     16,478      
count_eff_ruptures_sent.sitecol          11,662      
count_eff_ruptures_sent.sources          21,797      
count_eff_ruptures_tot_received          33,236      
hazard.input_weight                      31          
hazard.n_imts                            6           
hazard.n_levels                          19          
hazard.n_realizations                    4           
hazard.n_sites                           21          
hazard.n_sources                         14          
hazard.output_weight                     9,576       
hostname                                 gem-tstation
======================================== ============

Slowest sources
---------------
============ ========= ============ ====== ========= =========== ========== ============= ============= =========
src_group_id source_id source_class weight split_num filter_time split_time cum_calc_time max_calc_time num_tasks
============ ========= ============ ====== ========= =========== ========== ============= ============= =========
0            106150    PointSource  2.300  1         1.841E-04   1.812E-05  0.0           0.0           0        
0            102588    PointSource  2.300  1         1.240E-04   2.313E-05  0.0           0.0           0        
0            44535     PointSource  2.300  1         1.140E-04   1.383E-05  0.0           0.0           0        
0            15999     PointSource  2.300  1         8.011E-05   1.407E-05  0.0           0.0           0        
0            22285     PointSource  2.300  1         4.005E-05   1.597E-05  0.0           0.0           0        
0            41060     PointSource  2.300  1         4.005E-05   1.502E-05  0.0           0.0           0        
0            6736      PointSource  2.300  1         4.101E-05   1.407E-05  0.0           0.0           0        
0            23947     PointSource  2.300  1         4.005E-05   1.407E-05  0.0           0.0           0        
0            98725     PointSource  2.300  1         4.101E-05   1.287E-05  0.0           0.0           0        
0            70088     PointSource  2.300  1         3.886E-05   1.407E-05  0.0           0.0           0        
0            98979     PointSource  2.300  1         3.695E-05   1.502E-05  0.0           0.0           0        
0            3802      PointSource  2.000  1         5.102E-05   0.0        0.0           0.0           0        
0            8878      PointSource  2.300  1         3.910E-05   1.192E-05  0.0           0.0           0        
0            428       PointSource  2.000  1         2.885E-05   0.0        0.0           0.0           0        
============ ========= ============ ====== ========= =========== ========== ============= ============= =========

Computation times by source typology
------------------------------------
============ =========== ========== ============= ============= ========= ======
source_class filter_time split_time cum_calc_time max_calc_time num_tasks counts
============ =========== ========== ============= ============= ========= ======
PointSource  8.991E-04   1.822E-04  0.0           0.0           0         14    
============ =========== ========== ============= ============= ========= ======

Information about the tasks
---------------------------
Not available

Slowest operations
------------------
============================== ========= ========= ======
operation                      time_sec  memory_mb counts
============================== ========= ========= ======
managing sources               0.020     0.0       1     
reading composite source model 0.016     0.0       1     
store source_info              0.005     0.0       1     
total count_eff_ruptures       0.004     0.0       14    
filtering sources              8.991E-04 0.0       14    
aggregate curves               1.884E-04 0.0       14    
splitting sources              1.822E-04 0.0       12    
reading site collection        1.528E-04 0.0       1     
saving probability maps        2.480E-05 0.0       1     
============================== ========= ========= ======