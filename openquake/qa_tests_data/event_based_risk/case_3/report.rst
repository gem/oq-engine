Event Based PSHA for Lisbon
===========================

num_sites = 1, sitecol = 739 B

Parameters
----------
============================ ==================
calculation_mode             'event_based'     
number_of_logic_tree_samples 0                 
maximum_distance             {'default': 400.0}
investigation_time           2.0               
ses_per_logic_tree_path      1                 
truncation_level             5.0               
rupture_mesh_spacing         2.0               
complex_fault_mesh_spacing   2.0               
width_of_mfd_bin             0.1               
area_source_discretization   5.0               
random_seed                  23                
master_seed                  0                 
concurrent_tasks             16                
============================ ==================

Input files
-----------
======================== ============================================================
Name                     File                                                        
======================== ============================================================
exposure                 `exposure_model_1asset.xml <exposure_model_1asset.xml>`_    
gsim_logic_tree          `gsim_logic_tree.xml <gsim_logic_tree.xml>`_                
job_ini                  `job_haz.ini <job_haz.ini>`_                                
source                   `SA_RA_CATAL1_00.xml <SA_RA_CATAL1_00.xml>`_                
source                   `SA_RA_CATAL2_00.xml <SA_RA_CATAL2_00.xml>`_                
source_model_logic_tree  `source_model_logic_tree.xml <source_model_logic_tree.xml>`_
structural_vulnerability `vulnerability_model2013.xml <vulnerability_model2013.xml>`_
======================== ============================================================

Composite source model
----------------------
========= ====== ============================================ =============== ================
smlt_path weight source_model_file                            gsim_logic_tree num_realizations
========= ====== ============================================ =============== ================
b1        0.600  `SA_RA_CATAL1_00.xml <SA_RA_CATAL1_00.xml>`_ complex(2,2)    4/4             
b2        0.400  `SA_RA_CATAL2_00.xml <SA_RA_CATAL2_00.xml>`_ simple(2,0)     2/2             
========= ====== ============================================ =============== ================

Required parameters per tectonic region type
--------------------------------------------
====== ================================= ========= ========== ==========
trt_id gsims                             distances siteparams ruptparams
====== ================================= ========= ========== ==========
0      AkkarBommer2010 AtkinsonBoore2006 rjb rrup  vs30       rake mag  
1      AkkarBommer2010 AtkinsonBoore2006 rjb rrup  vs30       rake mag  
2      AkkarBommer2010 AtkinsonBoore2006 rjb rrup  vs30       rake mag  
====== ================================= ========= ========== ==========

Realizations per (TRT, GSIM)
----------------------------

::

  <RlzsAssoc(size=6, rlzs=6)
  0,AkkarBommer2010: ['<2,b1,b2_b3,w=0.126>', '<3,b1,b2_b4,w=0.054>']
  0,AtkinsonBoore2006: ['<0,b1,b1_b3,w=0.294>', '<1,b1,b1_b4,w=0.126>']
  1,AkkarBommer2010: ['<1,b1,b1_b4,w=0.126>', '<3,b1,b2_b4,w=0.054>']
  1,AtkinsonBoore2006: ['<0,b1,b1_b3,w=0.294>', '<2,b1,b2_b3,w=0.126>']
  2,AkkarBommer2010: ['<5,b2,b2_@,w=0.12>']
  2,AtkinsonBoore2006: ['<4,b2,b1_@,w=0.28>']>

Number of ruptures per tectonic region type
-------------------------------------------
=================== ====== ==================== =========== ============ ======
source_model        trt_id trt                  num_sources eff_ruptures weight
=================== ====== ==================== =========== ============ ======
SA_RA_CATAL1_00.xml 0      Active Shallow Crust 3           3            4,860 
SA_RA_CATAL1_00.xml 1      Stable Shallow Crust 8           2            2,142 
SA_RA_CATAL2_00.xml 2      Active Shallow Crust 3           2            4,860 
=================== ====== ==================== =========== ============ ======

=============== ======
#TRT models     3     
#sources        14    
#eff_ruptures   7     
filtered_weight 11,862
=============== ======

Informational data
------------------
====================================== ==================
compute_ruptures_max_received_per_task 12667             
compute_ruptures_sent.Monitor          125568            
compute_ruptures_sent.RlzsAssoc        270828            
compute_ruptures_sent.SiteCollection   15732             
compute_ruptures_sent.WeightedSequence 4609292           
compute_ruptures_sent.int              180               
compute_ruptures_tot_received          271435            
hazard.input_weight                    14004.150000000001
hazard.n_imts                          1                 
hazard.n_levels                        40.0              
hazard.n_realizations                  8                 
hazard.n_sites                         1                 
hazard.n_sources                       0                 
hazard.output_weight                   0.16              
====================================== ==================

Exposure model
--------------
=========== =
#assets     1
#taxonomies 1
=========== =

======== =======
Taxonomy #Assets
======== =======
M1_2_PC  1      
======== =======

Slowest sources
---------------
============ ========= ============ ====== ========= =========== ========== =========
trt_model_id source_id source_class weight split_num filter_time split_time calc_time
============ ========= ============ ====== ========= =========== ========== =========
0            0         AreaSource   2,446  2,174     0.002       1.062      48       
2            0         AreaSource   2,446  2,174     0.002       0.722      40       
0            2         AreaSource   1,992  2,748     0.002       0.667      15       
2            2         AreaSource   1,992  2,748     8.910E-04   0.526      15       
1            10        AreaSource   448    1         8.121E-04   0.0        7.471    
2            1         AreaSource   422    1         8.419E-04   0.0        6.922    
3            6         AreaSource   422    1         7.432E-04   0.0        6.875    
3            10        AreaSource   448    1         7.839E-04   0.0        6.806    
0            1         AreaSource   422    1         8.469E-04   0.0        6.780    
1            6         AreaSource   422    1         7.448E-04   0.0        6.723    
3            3         AreaSource   340    1         7.980E-04   0.0        5.083    
1            9         AreaSource   255    1         7.930E-04   0.0        4.560    
1            5         AreaSource   236    1         7.381E-04   0.0        4.163    
3            5         AreaSource   236    1         7.360E-04   0.0        4.077    
1            3         AreaSource   340    1         7.389E-04   0.0        3.858    
3            9         AreaSource   255    1         7.591E-04   0.0        3.042    
1            7         AreaSource   166    1         7.660E-04   0.0        2.996    
1            8         AreaSource   144    1         8.221E-04   0.0        2.582    
1            4         AreaSource   128    1         7.579E-04   0.0        2.515    
3            8         AreaSource   144    1         7.401E-04   0.0        2.492    
============ ========= ============ ====== ========= =========== ========== =========

Slowest operations
------------------
============================== ========= ========= ======
operation                      time_sec  memory_mb counts
============================== ========= ========= ======
total compute_ruptures         202       0.070     36    
reading composite source model 3.878     0.0       1     
managing sources               3.582     0.0       1     
splitting sources              2.977     0.0       4     
store source_info              0.092     0.0       1     
total compute_gmfs_and_curves  0.025     0.004     7     
filtering sources              0.020     0.0       22    
compute poes                   0.015     0.0       7     
saving gmfs                    0.011     0.0       7     
make contexts                  0.007     0.0       7     
saving ruptures                0.006     0.0       1     
aggregate curves               0.004     0.0       36    
filtering ruptures             0.003     0.0       8     
reading exposure               0.003     0.0       1     
reading site collection        8.106E-06 0.0       1     
============================== ========= ========= ======