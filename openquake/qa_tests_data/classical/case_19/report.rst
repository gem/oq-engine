SHARE OpenQuake Computational Settings
======================================

gem-tstation:/home/michele/ssd/calc_40732.hdf5 updated Mon Aug 22 13:03:38 2016

num_sites = 1, sitecol = 739 B

Parameters
----------
============================ ==============================================================================================================================================================================================
calculation_mode             'classical'                                                                                                                                                                                   
number_of_logic_tree_samples 0                                                                                                                                                                                             
maximum_distance             {u'Volcanic': 200.0, u'Shield': 200.0, u'Active Shallow Crust': 200.0, u'Subduction Interface': 200.0, u'Stable Shallow Crust': 200.0, u'Subduction Deep': 200.0, u'Subduction Inslab': 200.0}
investigation_time           50.0                                                                                                                                                                                          
ses_per_logic_tree_path      1                                                                                                                                                                                             
truncation_level             3.0                                                                                                                                                                                           
rupture_mesh_spacing         5.0                                                                                                                                                                                           
complex_fault_mesh_spacing   5.0                                                                                                                                                                                           
width_of_mfd_bin             0.2                                                                                                                                                                                           
area_source_discretization   10.0                                                                                                                                                                                          
random_seed                  23                                                                                                                                                                                            
master_seed                  0                                                                                                                                                                                             
sites_per_tile               10000                                                                                                                                                                                         
engine_version               '2.1.0-git8cbb23e'                                                                                                                                                                            
============================ ==============================================================================================================================================================================================

Input files
-----------
======================= ==========================================================================
Name                    File                                                                      
======================= ==========================================================================
gsim_logic_tree         `complete_gmpe_logic_tree.xml <complete_gmpe_logic_tree.xml>`_            
job_ini                 `job.ini <job.ini>`_                                                      
source                  `simple_area_source_model.xml <simple_area_source_model.xml>`_            
source_model_logic_tree `simple_source_model_logic_tree.xml <simple_source_model_logic_tree.xml>`_
======================= ==========================================================================

Composite source model
----------------------
========= ====== ============================================================== ====================== ================
smlt_path weight source_model_file                                              gsim_logic_tree        num_realizations
========= ====== ============================================================== ====================== ================
b1        1.000  `simple_area_source_model.xml <simple_area_source_model.xml>`_ complex(4,4,1,0,0,5,2) 4/4             
========= ====== ============================================================== ====================== ================

Required parameters per tectonic region type
--------------------------------------------
====== ==================================================================================== ========== ============= ==============
grp_id gsims                                                                                distances  siteparams    ruptparams    
====== ==================================================================================== ========== ============= ==============
4      AtkinsonBoore2003SSlab() LinLee2008SSlab() YoungsEtAl1997SSlab() ZhaoEtAl2006SSlab() rhypo rrup set(['vs30']) hypo_depth mag
====== ==================================================================================== ========== ============= ==============

Realizations per (TRT, GSIM)
----------------------------

::

  <RlzsAssoc(size=4, rlzs=4)
  4,AtkinsonBoore2003SSlab(): ['<0,b1~@_@_@_@_b51_@_@,w=0.2>']
  4,LinLee2008SSlab(): ['<1,b1~@_@_@_@_b52_@_@,w=0.2>']
  4,YoungsEtAl1997SSlab(): ['<2,b1~@_@_@_@_b53_@_@,w=0.2>']
  4,ZhaoEtAl2006SSlab(): ['<3,b1~@_@_@_@_b54_@_@,w=0.4>']>

Number of ruptures per tectonic region type
-------------------------------------------
============================ ====== ================= =========== ============ ======
source_model                 grp_id trt               num_sources eff_ruptures weight
============================ ====== ================= =========== ============ ======
simple_area_source_model.xml 4      Subduction Inslab 1           7770         194   
============================ ====== ================= =========== ============ ======

Informational data
------------------
=============================== ============
classical_max_received_per_task 5,175       
classical_num_tasks             1           
classical_sent.monitor          1,721       
classical_sent.rlzs_by_gsim     29,506      
classical_sent.sitecol          433         
classical_sent.sources          2,816       
classical_tot_received          5,175       
hazard.input_weight             49,409      
hazard.n_imts                   3           
hazard.n_levels                 26          
hazard.n_realizations           1,280       
hazard.n_sites                  1           
hazard.n_sources                18          
hazard.output_weight            99,840      
hostname                        gem-tstation
=============================== ============

Slowest sources
---------------
============ ========= ============ ====== ========= =========== ========== ============= ============= =========
src_group_id source_id source_class weight split_num filter_time split_time cum_calc_time max_calc_time num_tasks
============ ========= ============ ====== ========= =========== ========== ============= ============= =========
4            s46       AreaSource   194    1         9.210E-04   0.0        14            14            1        
============ ========= ============ ====== ========= =========== ========== ============= ============= =========

Computation times by source typology
------------------------------------
============ =========== ========== ============= ============= ========= ======
source_class filter_time split_time cum_calc_time max_calc_time num_tasks counts
============ =========== ========== ============= ============= ========= ======
AreaSource   9.210E-04   0.0        14            14            1         1     
============ =========== ========== ============= ============= ========= ======

Information about the tasks
---------------------------
=================== ==== ====== === === =========
measurement         mean stddev min max num_tasks
classical.time_sec  14   NaN    14  14  1        
classical.memory_mb 0.0  NaN    0.0 0.0 1        
=================== ==== ====== === === =========

Slowest operations
------------------
============================== ========= ========= ======
operation                      time_sec  memory_mb counts
============================== ========= ========= ======
total classical                14        0.0       1     
computing poes                 9.253     0.0       7,770 
reading composite source model 4.725     0.0       1     
making contexts                3.318     0.0       7,770 
managing sources               0.113     0.0       1     
filtering sources              0.022     0.0       18    
store source_info              0.010     0.0       1     
saving probability maps        0.002     0.0       1     
read poes                      6.218E-04 0.0       1     
aggregate curves               3.791E-05 0.0       1     
reading site collection        3.600E-05 0.0       1     
============================== ========= ========= ======