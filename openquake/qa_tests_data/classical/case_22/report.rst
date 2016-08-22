Classical PSHA using Alaska 2007 active shallow crust grid model
================================================================

gem-tstation:/home/michele/ssd/calc_40708.hdf5 updated Mon Aug 22 12:50:53 2016

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
engine_version               '2.1.0-git8cbb23e'              
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
====== ==================================================================================================== ========= ============= ============
grp_id gsims                                                                                                distances siteparams    ruptparams  
====== ==================================================================================================== ========= ============= ============
0      AbrahamsonSilva1997() BooreEtAl1997GeometricMean() CampbellBozorgnia2003NSHMP2007() SadighEtAl1997() rjb rrup  set(['vs30']) rake dip mag
====== ==================================================================================================== ========= ============= ============

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
Alaska_asc_grid_NSHMP2007.xml 0      Active Shallow Crust 14          196          31    
============================= ====== ==================== =========== ============ ======

Informational data
------------------
=============================== ============
classical_max_received_per_task 10,376      
classical_num_tasks             14          
classical_sent.monitor          28,756      
classical_sent.rlzs_by_gsim     16,478      
classical_sent.sitecol          11,662      
classical_sent.sources          21,797      
classical_tot_received          54,202      
hazard.input_weight             31          
hazard.n_imts                   6           
hazard.n_levels                 19          
hazard.n_realizations           4           
hazard.n_sites                  21          
hazard.n_sources                14          
hazard.output_weight            9,576       
hostname                        gem-tstation
=============================== ============

Slowest sources
---------------
============ ========= ============ ====== ========= =========== ========== ============= ============= =========
src_group_id source_id source_class weight split_num filter_time split_time cum_calc_time max_calc_time num_tasks
============ ========= ============ ====== ========= =========== ========== ============= ============= =========
0            8878      PointSource  2.300  1         6.104E-05   1.907E-05  0.320         0.320         1        
0            70088     PointSource  2.300  1         6.413E-05   1.907E-05  0.294         0.294         1        
0            6736      PointSource  2.300  1         9.990E-05   2.193E-05  0.108         0.108         1        
0            98725     PointSource  2.300  1         5.913E-05   1.907E-05  0.0           0.0           0        
0            3802      PointSource  2.000  1         4.411E-05   0.0        0.0           0.0           0        
0            15999     PointSource  2.300  1         3.791E-05   1.192E-05  0.0           0.0           0        
0            98979     PointSource  2.300  1         5.913E-05   1.884E-05  0.0           0.0           0        
0            44535     PointSource  2.300  1         1.111E-04   3.099E-05  0.0           0.0           0        
0            428       PointSource  2.000  1         2.503E-05   0.0        0.0           0.0           0        
0            23947     PointSource  2.300  1         1.049E-04   1.311E-05  0.0           0.0           0        
0            106150    PointSource  2.300  1         8.821E-05   1.192E-05  0.0           0.0           0        
0            41060     PointSource  2.300  1         1.910E-04   1.407E-05  0.0           0.0           0        
0            22285     PointSource  2.300  1         3.195E-05   1.097E-05  0.0           0.0           0        
0            102588    PointSource  2.300  1         1.240E-04   1.788E-05  0.0           0.0           0        
============ ========= ============ ====== ========= =========== ========== ============= ============= =========

Computation times by source typology
------------------------------------
============ =========== ========== ============= ============= ========= ======
source_class filter_time split_time cum_calc_time max_calc_time num_tasks counts
============ =========== ========== ============= ============= ========= ======
PointSource  0.001       2.089E-04  0.723         0.723         3         14    
============ =========== ========== ============= ============= ========= ======

Information about the tasks
---------------------------
=================== ===== ====== ========= ===== =========
measurement         mean  stddev min       max   num_tasks
classical.time_sec  0.052 0.112  3.338E-04 0.320 14       
classical.memory_mb 0.336 0.797  0.0       2.262 14       
=================== ===== ====== ========= ===== =========

Slowest operations
------------------
============================== ========= ========= ======
operation                      time_sec  memory_mb counts
============================== ========= ========= ======
total classical                0.731     2.262     14    
computing poes                 0.479     0.0       196   
making contexts                0.136     0.0       276   
managing sources               0.028     0.0       1     
store source_info              0.014     0.0       1     
reading composite source model 0.013     0.0       1     
saving probability maps        0.002     0.0       1     
read poes                      0.001     0.0       1     
filtering sources              0.001     0.0       14    
aggregate curves               2.952E-04 0.0       14    
splitting sources              2.089E-04 0.0       12    
reading site collection        1.380E-04 0.0       1     
============================== ========= ========= ======