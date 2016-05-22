Event Based Risk Lisbon
=======================

gem-tstation:/home/michele/ssd/calc_16375.hdf5 updated Wed May 18 18:18:35 2016

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
oqlite_version               '0.13.0-git034c0a0'
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
  0,AkkarBommer2010(): ['<1,b1,b2_@,w=0.180000001788>']
  0,AtkinsonBoore2006(): ['<0,b1,b1_@,w=0.420000004172>']
  2,AkkarBommer2010(): ['<4,b2,b2_b3,w=0.0839999987483>', '<5,b2,b2_b4,w=0.0359999994636>']
  2,AtkinsonBoore2006(): ['<2,b2,b1_b3,w=0.195999997079>', '<3,b2,b1_b4,w=0.0839999987483>']
  3,AkkarBommer2010(): ['<3,b2,b1_b4,w=0.0839999987483>', '<5,b2,b2_b4,w=0.0359999994636>']
  3,AtkinsonBoore2006(): ['<2,b2,b1_b3,w=0.195999997079>', '<4,b2,b2_b3,w=0.0839999987483>']>

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
event_based_risk_sent.riskinput        37645         
event_based_risk_sent.riskmodel        26728         
event_based_risk_sent.rlzs_assoc       126490        
event_based_risk_tot_received          54889         
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
0            0         AreaSource   610    543       0.002       0.172      6.543    
2            0         AreaSource   610    543       9.129E-04   0.143      6.328    
2            2         AreaSource   498    687       8.919E-04   0.133      2.196    
0            2         AreaSource   498    687       8.881E-04   0.132      2.172    
1            3         AreaSource   87     1         6.530E-04   0.0        1.152    
3            3         AreaSource   87     1         6.611E-04   0.0        1.151    
3            10        AreaSource   112    1         6.289E-04   0.0        1.110    
1            10        AreaSource   112    1         6.640E-04   0.0        1.094    
2            1         AreaSource   104    1         6.390E-04   0.0        1.031    
1            6         AreaSource   103    1         6.680E-04   0.0        1.023    
0            1         AreaSource   104    1         7.541E-04   0.0        1.003    
3            6         AreaSource   103    1         6.740E-04   0.0        0.881    
3            9         AreaSource   62     1         6.361E-04   0.0        0.582    
1            5         AreaSource   58     1         6.561E-04   0.0        0.558    
1            9         AreaSource   62     1         6.261E-04   0.0        0.552    
3            5         AreaSource   58     1         6.499E-04   0.0        0.507    
1            7         AreaSource   42     1         6.320E-04   0.0        0.453    
1            4         AreaSource   32     1         6.602E-04   0.0        0.384    
3            7         AreaSource   42     1         6.480E-04   0.0        0.367    
1            8         AreaSource   36     1         6.340E-04   0.0        0.349    
============ ========= ============ ====== ========= =========== ========== =========

Computation times by source typology
------------------------------------
============ =========== ========== ========= ======
source_class filter_time split_time calc_time counts
============ =========== ========== ========= ======
AreaSource   0.016       0.579      30        22    
============ =========== ========== ========= ======

Information about the tasks
---------------------------
================================= ===== ====== ===== ===== =========
measurement                       mean  stddev min   max   num_tasks
compute_ruptures.time_sec         0.837 0.365  0.002 1.206 36       
compute_ruptures.memory_mb        0.023 0.085  0.0   0.438 36       
compute_gmfs_and_curves.time_sec  0.008 0.002  0.004 0.011 13       
compute_gmfs_and_curves.memory_mb 0.065 0.063  0.0   0.160 13       
event_based_risk.time_sec         0.008 0.002  0.006 0.012 13       
event_based_risk.memory_mb        0.0   0.0    0.0   0.0   13       
================================= ===== ====== ===== ===== =========

Slowest operations
------------------
============================== ========= ========= ======
operation                      time_sec  memory_mb counts
============================== ========= ========= ======
total compute_ruptures         30        0.438     36    
reading composite source model 0.934     0.0       1     
managing sources               0.738     0.0       1     
splitting sources              0.579     0.0       4     
compute poes                   0.160     0.0       26    
total compute_gmfs_and_curves  0.103     0.160     13    
total event_based_risk         0.103     0.0       13    
building hazard                0.088     0.0       13    
building riskinputs            0.036     0.0       1     
store source_info              0.033     0.0       1     
saving gmfs                    0.027     0.0       44    
make contexts                  0.021     0.0       26    
saving ruptures                0.016     0.0       1     
filtering sources              0.016     0.0       22    
computing riskmodel            0.007     0.0       13    
aggregate curves               0.005     0.0       36    
saving event loss tables       0.005     0.0       13    
reading exposure               0.004     0.0       1     
filtering ruptures             0.004     0.0       14    
aggregate losses               0.002     0.0       13    
reading site collection        8.106E-06 0.0       1     
============================== ========= ========= ======