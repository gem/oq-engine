Event Based Risk Lisbon
=======================

gem-tstation:/home/michele/ssd/calc_76.hdf5 updated Wed Apr 27 10:54:49 2016

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
oqlite_version               '0.13.0-gitcbbc4a8'
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
event_based_risk_max_received_per_task 5139          
event_based_risk_num_tasks             7             
event_based_risk_sent.assetcol         11522         
event_based_risk_sent.monitor          18375         
event_based_risk_sent.riskinputs       20260         
event_based_risk_sent.riskmodel        16044         
event_based_risk_sent.rlzs_assoc       47740         
event_based_risk_tot_received          35133         
hostname                               'gem-tstation'
require_epsilons                       True          
====================================== ==============

Specific information for event based
------------------------------------
Total number of ruptures: 7
Total number of events: 7

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
0            0         AreaSource   2,446  2,174     9.880E-04   0.827      49       
2            0         AreaSource   2,446  2,174     0.002       1.079      47       
0            2         AreaSource   1,992  2,748     0.002       1.012      16       
2            2         AreaSource   1,992  2,748     0.002       0.731      15       
3            10        AreaSource   448    1         7.370E-04   0.0        8.140    
1            6         AreaSource   422    1         7.641E-04   0.0        7.381    
3            6         AreaSource   422    1         7.789E-04   0.0        7.321    
0            1         AreaSource   422    1         8.721E-04   0.0        6.874    
1            10        AreaSource   448    1         7.739E-04   0.0        6.869    
2            1         AreaSource   422    1         7.489E-04   0.0        6.838    
3            3         AreaSource   340    1         7.551E-04   0.0        5.516    
1            3         AreaSource   340    1         7.951E-04   0.0        5.022    
1            9         AreaSource   255    1         7.350E-04   0.0        4.723    
3            9         AreaSource   255    1         7.730E-04   0.0        4.641    
1            5         AreaSource   236    1         7.570E-04   0.0        4.133    
3            5         AreaSource   236    1         7.610E-04   0.0        4.058    
1            7         AreaSource   166    1         7.329E-04   0.0        2.797    
3            4         AreaSource   128    1         7.551E-04   0.0        2.584    
1            8         AreaSource   144    1         7.479E-04   0.0        2.564    
1            4         AreaSource   128    1         7.720E-04   0.0        2.290    
============ ========= ============ ====== ========= =========== ========== =========

Slowest operations
------------------
============================== ========= ========= ======
operation                      time_sec  memory_mb counts
============================== ========= ========= ======
total compute_ruptures         214       0.129     36    
managing sources               4.287     0.0       1     
reading composite source model 4.105     0.0       1     
splitting sources              3.649     0.0       4     
store source_info              0.082     0.0       1     
total event_based_risk         0.065     0.0       7     
compute poes                   0.055     0.0       14    
total compute_gmfs_and_curves  0.044     0.359     7     
building hazard                0.032     0.0       7     
computing risk                 0.025     0.0       7     
filtering sources              0.020     0.0       22    
make contexts                  0.016     0.0       14    
saving gmfs                    0.010     0.0       24    
saving ruptures                0.006     0.0       1     
aggregate curves               0.004     0.0       36    
saving event loss tables       0.004     0.0       7     
filtering ruptures             0.003     0.0       8     
reading exposure               0.003     0.0       1     
aggregate losses               0.001     0.0       7     
getting hazard                 7.579E-04 0.0       7     
reading site collection        8.106E-06 0.0       1     
============================== ========= ========= ======