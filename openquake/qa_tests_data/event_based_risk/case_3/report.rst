Event Based Risk Lisbon
=======================

gem-tstation:/home/michele/ssd/calc_16076.hdf5 updated Wed May 11 14:28:40 2016

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
rupture_mesh_spacing         4.0                
complex_fault_mesh_spacing   4.0                
width_of_mfd_bin             0.1                
area_source_discretization   10.0               
random_seed                  23                 
master_seed                  42                 
avg_losses                   False              
oqlite_version               '0.13.0-git7639915'
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
b1        0.600  `SA_RA_CATAL1_00.xml <SA_RA_CATAL1_00.xml>`_ simple(2,0)     2/2             
b2        0.400  `SA_RA_CATAL2_00.xml <SA_RA_CATAL2_00.xml>`_ complex(2,2)    4/4             
========= ====== ============================================ =============== ================

Required parameters per tectonic region type
--------------------------------------------
====== ===================================== ========= ========== ==========
trt_id gsims                                 distances siteparams ruptparams
====== ===================================== ========= ========== ==========
0      AkkarBommer2010() AtkinsonBoore2006() rjb rrup  vs30       rake mag  
2      AkkarBommer2010() AtkinsonBoore2006() rjb rrup  vs30       rake mag  
3      AkkarBommer2010() AtkinsonBoore2006() rjb rrup  vs30       rake mag  
====== ===================================== ========= ========== ==========

Realizations per (TRT, GSIM)
----------------------------

::

  <RlzsAssoc(size=6, rlzs=6)
  0,AkkarBommer2010(): ['<1,b1,b2_@,w=0.18>']
  0,AtkinsonBoore2006(): ['<0,b1,b1_@,w=0.42>']
  2,AkkarBommer2010(): ['<4,b2,b2_b3,w=0.084>', '<5,b2,b2_b4,w=0.036>']
  2,AtkinsonBoore2006(): ['<2,b2,b1_b3,w=0.196>', '<3,b2,b1_b4,w=0.084>']
  3,AkkarBommer2010(): ['<3,b2,b1_b4,w=0.084>', '<5,b2,b2_b4,w=0.036>']
  3,AtkinsonBoore2006(): ['<2,b2,b1_b3,w=0.196>', '<4,b2,b2_b3,w=0.084>']>

Number of ruptures per tectonic region type
-------------------------------------------
=================== ====== ==================== =========== ============ ======
source_model        trt_id trt                  num_sources eff_ruptures weight
=================== ====== ==================== =========== ============ ======
SA_RA_CATAL1_00.xml 0      Active Shallow Crust 3           4            1,213 
SA_RA_CATAL2_00.xml 2      Active Shallow Crust 3           6            1,213 
SA_RA_CATAL2_00.xml 3      Stable Shallow Crust 8           3            534   
=================== ====== ==================== =========== ============ ======

=============== =====
#TRT models     3    
#sources        14   
#eff_ruptures   13   
filtered_weight 2,961
=============== =====

Informational data
------------------
====================================== ==============
event_based_risk_max_received_per_task 4530          
event_based_risk_num_tasks             13            
event_based_risk_sent.assetcol         21398         
event_based_risk_sent.monitor          34281         
event_based_risk_sent.riskinput        37359         
event_based_risk_sent.riskmodel        26728         
event_based_risk_sent.rlzs_assoc       86255         
event_based_risk_tot_received          56827         
hostname                               'gem-tstation'
require_epsilons                       True          
====================================== ==============

Specific information for event based
------------------------------------
======================== =====
Total number of ruptures 13   
Total number of events   13   
Rupture multiplicity     1.000
======================== =====

Maximum memory allocated for the GMFs
-------------------------------------
The largest GMF block is for trt_model_id=2, contains 1 IMT(s), 4 realization(s)
and has a size of 96 B / num_tasks

Estimated data transfer for the avglosses
-----------------------------------------
1 asset(s) x 6 realization(s) x 1 loss type(s) x 1 losses x 8 bytes x 16 tasks = 768 B

Exposure model
--------------
=========== =
#assets     1
#taxonomies 1
=========== =

======== ===== ====== === === ========= ==========
taxonomy mean  stddev min max num_sites num_assets
M1_2_PC  1.000 NaN    1   1   1         1         
======== ===== ====== === === ========= ==========

Slowest sources
---------------
============ ========= ============ ====== ========= =========== ========== =========
trt_model_id source_id source_class weight split_num filter_time split_time calc_time
============ ========= ============ ====== ========= =========== ========== =========
0            0         AreaSource   610    543       0.002       0.187      7.368    
2            0         AreaSource   610    543       8.600E-04   0.145      6.968    
2            2         AreaSource   498    687       8.430E-04   0.153      2.365    
0            2         AreaSource   498    687       8.659E-04   0.135      2.303    
1            10        AreaSource   112    1         7.031E-04   0.0        1.167    
3            10        AreaSource   112    1         7.060E-04   0.0        1.091    
1            6         AreaSource   103    1         6.919E-04   0.0        1.088    
0            1         AreaSource   104    1         7.720E-04   0.0        1.084    
2            1         AreaSource   104    1         7.250E-04   0.0        1.082    
3            6         AreaSource   103    1         6.931E-04   0.0        1.070    
1            3         AreaSource   87     1         6.990E-04   0.0        0.909    
3            3         AreaSource   87     1         6.828E-04   0.0        0.907    
1            9         AreaSource   62     1         6.709E-04   0.0        0.703    
3            9         AreaSource   62     1         6.671E-04   0.0        0.627    
1            5         AreaSource   58     1         7.050E-04   0.0        0.603    
3            5         AreaSource   58     1         6.840E-04   0.0        0.597    
3            7         AreaSource   42     1         6.721E-04   0.0        0.431    
1            4         AreaSource   32     1         7.010E-04   0.0        0.416    
3            4         AreaSource   32     1         6.709E-04   0.0        0.411    
1            7         AreaSource   42     1         6.630E-04   0.0        0.395    
============ ========= ============ ====== ========= =========== ========== =========

Computation times by source typology
------------------------------------
============ =========== ========== ========= ======
source_class filter_time split_time calc_time counts
============ =========== ========== ========= ======
AreaSource   0.017       0.620      32        22    
============ =========== ========== ========= ======

Information about the tasks
---------------------------
================================= ===== ====== ===== ===== =========
measurement                       mean  stddev min   max   num_tasks
compute_ruptures.time_sec         0.899 0.393  0.002 1.364 36       
compute_ruptures.memory_mb        0.001 0.002  0.0   0.004 36       
compute_gmfs_and_curves.time_sec  0.004 0.001  0.002 0.005 13       
compute_gmfs_and_curves.memory_mb 0.0   0.0    0.0   0.0   13       
event_based_risk.time_sec         0.007 0.002  0.004 0.009 13       
event_based_risk.memory_mb        0.0   0.0    0.0   0.0   13       
================================= ===== ====== ===== ===== =========

Slowest operations
------------------
============================== ========= ========= ======
operation                      time_sec  memory_mb counts
============================== ========= ========= ======
total compute_ruptures         32        0.004     36    
managing sources               1.835     0.0       1     
reading composite source model 1.244     0.0       1     
splitting sources              0.620     0.0       4     
total event_based_risk         0.094     0.0       13    
compute poes                   0.073     0.0       26    
building hazard                0.054     0.0       13    
total compute_gmfs_and_curves  0.052     0.0       13    
computing riskmodel            0.030     0.0       13    
store source_info              0.028     0.0       1     
make contexts                  0.024     0.0       26    
saving gmfs                    0.023     0.0       44    
filtering sources              0.017     0.0       22    
saving ruptures                0.012     0.0       1     
aggregate losses               0.008     0.0       13    
aggregate curves               0.004     0.0       36    
filtering ruptures             0.003     0.0       14    
reading exposure               0.003     0.0       1     
saving event loss tables       0.003     0.0       13    
reading site collection        6.914E-06 0.0       1     
============================== ========= ========= ======