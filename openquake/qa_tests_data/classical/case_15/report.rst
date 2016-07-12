Classical PSHA with GMPE logic tree with multiple tectonic region types
=======================================================================

gem-tstation:/home/michele/ssd/calc_22586.hdf5 updated Tue May 31 15:37:27 2016

num_sites = 3, sitecol = 831 B

Parameters
----------
============================ ==================================================================
calculation_mode             'classical'                                                       
number_of_logic_tree_samples 0                                                                 
maximum_distance             {'Stable Continental Crust': 200.0, 'Active Shallow Crust': 200.0}
investigation_time           50.0                                                              
ses_per_logic_tree_path      1                                                                 
truncation_level             3.0                                                               
rupture_mesh_spacing         1.0                                                               
complex_fault_mesh_spacing   1.0                                                               
width_of_mfd_bin             0.1                                                               
area_source_discretization   10.0                                                              
random_seed                  23                                                                
master_seed                  0                                                                 
sites_per_tile               10000                                                             
engine_version               '2.0.0-git4fb4450'                                                
============================ ==================================================================

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
SM1            0.500  `source_model_1.xml <source_model_1.xml>`_ complex(2,2)    4/4             
SM2_a3b1       0.250  `source_model_2.xml <source_model_2.xml>`_ complex(2,2)    2/2             
SM2_a3pt2b0pt8 0.250  `source_model_2.xml <source_model_2.xml>`_ complex(2,2)    2/2             
============== ====== ========================================== =============== ================

Required parameters per tectonic region type
--------------------------------------------
====== =========================================== ========= ========== =================
grp_id gsims                                       distances siteparams ruptparams       
====== =========================================== ========= ========== =================
0      BooreAtkinson2008() CampbellBozorgnia2008() rjb rrup  z2pt5 vs30 ztor mag rake dip
1      Campbell2003() ToroEtAl2002()               rjb rrup             mag              
2      BooreAtkinson2008() CampbellBozorgnia2008() rjb rrup  z2pt5 vs30 ztor mag rake dip
3      BooreAtkinson2008() CampbellBozorgnia2008() rjb rrup  z2pt5 vs30 ztor mag rake dip
====== =========================================== ========= ========== =================

Realizations per (TRT, GSIM)
----------------------------

::

  <RlzsAssoc(size=8, rlzs=8)
  0,BooreAtkinson2008(): ['<0,SM1~BA2008_C2003,w=0.125>', '<1,SM1~BA2008_T2002,w=0.125>']
  0,CampbellBozorgnia2008(): ['<2,SM1~CB2008_C2003,w=0.125>', '<3,SM1~CB2008_T2002,w=0.125>']
  1,Campbell2003(): ['<0,SM1~BA2008_C2003,w=0.125>', '<2,SM1~CB2008_C2003,w=0.125>']
  1,ToroEtAl2002(): ['<1,SM1~BA2008_T2002,w=0.125>', '<3,SM1~CB2008_T2002,w=0.125>']
  2,BooreAtkinson2008(): ['<4,SM2_a3b1~BA2008_@,w=0.125>']
  2,CampbellBozorgnia2008(): ['<5,SM2_a3b1~CB2008_@,w=0.125>']
  3,BooreAtkinson2008(): ['<6,SM2_a3pt2b0pt8~BA2008_@,w=0.125>']
  3,CampbellBozorgnia2008(): ['<7,SM2_a3pt2b0pt8~CB2008_@,w=0.125>']>

Number of ruptures per tectonic region type
-------------------------------------------
================== ====== ======================== =========== ============ ======
source_model       grp_id trt                      num_sources eff_ruptures weight
================== ====== ======================== =========== ============ ======
source_model_1.xml 0      Active Shallow Crust     1           15           0.375 
source_model_1.xml 1      Stable Continental Crust 1           15           0.375 
source_model_2.xml 2      Active Shallow Crust     1           240          6.000 
source_model_2.xml 3      Active Shallow Crust     1           240          6.000 
================== ====== ======================== =========== ============ ======

=============== ===
#TRT models     4  
#sources        4  
#eff_ruptures   510
filtered_weight 12 
=============== ===

Informational data
------------------
======================================== ============
count_eff_ruptures_max_received_per_task 3,231       
count_eff_ruptures_num_tasks             34          
count_eff_ruptures_sent.monitor          101,014     
count_eff_ruptures_sent.rlzs_assoc       70,890      
count_eff_ruptures_sent.sitecol          16,082      
count_eff_ruptures_sent.siteidx          170         
count_eff_ruptures_sent.sources          43,332      
count_eff_ruptures_tot_received          109,854     
hazard.input_weight                      12          
hazard.n_imts                            2           
hazard.n_levels                          8.500       
hazard.n_realizations                    12          
hazard.n_sites                           3           
hazard.n_sources                         0           
hazard.output_weight                     612         
hostname                                 gem-tstation
======================================== ============

Slowest sources
---------------
============ ========= ============ ====== ========= =========== ========== =========
src_group_id source_id source_class weight split_num filter_time split_time calc_time
============ ========= ============ ====== ========= =========== ========== =========
2            1         AreaSource   6.000  16        0.001       0.003      0.0      
3            1         AreaSource   6.000  16        8.309E-04   0.002      0.0      
0            1         PointSource  0.375  1         5.198E-05   0.0        0.0      
1            2         PointSource  0.375  1         3.695E-05   0.0        0.0      
============ ========= ============ ====== ========= =========== ========== =========

Computation times by source typology
------------------------------------
============ =========== ========== ========= ======
source_class filter_time split_time calc_time counts
============ =========== ========== ========= ======
AreaSource   0.002       0.005      0.0       2     
PointSource  8.893E-05   0.0        0.0       2     
============ =========== ========== ========= ======

Information about the tasks
---------------------------
Not available

Slowest operations
------------------
============================== ========= ========= ======
operation                      time_sec  memory_mb counts
============================== ========= ========= ======
managing sources               0.062     0.0       1     
reading composite source model 0.014     0.0       1     
total count_eff_ruptures       0.008     0.0       34    
store source_info              0.006     0.0       1     
splitting sources              0.005     0.0       2     
filtering sources              0.002     0.0       4     
aggregate curves               6.237E-04 0.0       34    
reading site collection        3.314E-05 0.0       1     
============================== ========= ========= ======