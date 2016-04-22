Event Based Risk Lisbon
=======================

gem-tstation:/home/michele/ssd/calc_12016.hdf5 updated Fri Apr 22 04:09:57 2016

num_sites = 1, sitecol = 739 B

Parameters
----------
============================ ===================
calculation_mode             'event_based_risk' 
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
master_seed                  42                 
avg_losses                   False              
oqlite_version               '0.13.0-gitd746861'
============================ ===================

Input files
-----------
======================== ============================================================
Name                     File                                                        
======================== ============================================================
exposure                 `exposure_model_1asset.xml <exposure_model_1asset.xml>`_    
gsim_logic_tree          `gsim_logic_tree.xml <gsim_logic_tree.xml>`_                
job_ini                  `job.ini <job.ini>`_                                        
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
====================================== ==============
event_based_risk_max_received_per_task 4982          
event_based_risk_num_tasks             7             
event_based_risk_sent.assetcol         11522         
event_based_risk_sent.monitor          18305         
event_based_risk_sent.riskinputs       21380         
event_based_risk_sent.riskmodel        16044         
event_based_risk_sent.rlzs_assoc       47740         
event_based_risk_tot_received          34034         
hostname                               'gem-tstation'
require_epsilons                       True          
====================================== ==============

Maximum memory allocated for the GMFs
-------------------------------------
The largest GMF block is for trt_model_id=0, contains 1 IMT(s), 4 realization(s)
and has a size of 48 B / num_tasks

Estimated data transfer for the avglosses
-----------------------------------------
1 asset(s) x 6 realization(s) x 1 loss type(s) x 1 losses x 8 bytes x 16 tasks = 768 B

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
0            0         AreaSource   2,446  2,174     0.001       0.596      49       
2            0         AreaSource   2,446  2,174     9.179E-04   0.666      45       
0            2         AreaSource   1,992  2,748     8.862E-04   0.532      16       
2            2         AreaSource   1,992  2,748     0.002       1.004      15       
1            10        AreaSource   448    1         7.501E-04   0.0        7.813    
3            10        AreaSource   448    1         6.759E-04   0.0        7.597    
0            1         AreaSource   422    1         7.939E-04   0.0        6.910    
2            1         AreaSource   422    1         6.831E-04   0.0        6.858    
1            6         AreaSource   422    1         6.931E-04   0.0        6.368    
3            3         AreaSource   340    1         6.909E-04   0.0        5.851    
3            6         AreaSource   422    1         7.041E-04   0.0        5.646    
3            9         AreaSource   255    1         6.709E-04   0.0        4.511    
1            9         AreaSource   255    1         7.570E-04   0.0        4.321    
1            3         AreaSource   340    1         7.079E-04   0.0        4.231    
3            5         AreaSource   236    1         6.881E-04   0.0        4.153    
1            5         AreaSource   236    1         6.928E-04   0.0        3.449    
1            7         AreaSource   166    1         6.702E-04   0.0        2.988    
3            8         AreaSource   144    1         6.711E-04   0.0        2.569    
1            8         AreaSource   144    1         6.721E-04   0.0        2.517    
3            7         AreaSource   166    1         6.661E-04   0.0        2.353    
============ ========= ============ ====== ========= =========== ========== =========

Slowest operations
------------------
============================== ========= ========= ======
operation                      time_sec  memory_mb counts
============================== ========= ========= ======
total compute_ruptures         208       0.062     36    
reading composite source model 3.916     0.0       1     
managing sources               3.386     0.0       1     
splitting sources              2.799     0.0       4     
store source_info              0.090     0.0       1     
total event_based_risk         0.060     0.0       7     
compute poes                   0.035     0.0       14    
total compute_gmfs_and_curves  0.030     0.0       7     
getting hazard                 0.028     0.0       7     
computing individual risk      0.026     0.0       7     
filtering sources              0.017     0.0       22    
make contexts                  0.017     0.0       14    
saving gmfs                    0.007     0.0       7     
saving ruptures                0.007     0.0       1     
reading exposure               0.005     0.0       1     
saving event loss tables       0.005     0.0       7     
aggregate curves               0.004     0.0       36    
filtering ruptures             0.003     0.0       8     
aggregate losses               0.001     0.0       7     
reading site collection        1.311E-05 0.0       1     
============================== ========= ========= ======