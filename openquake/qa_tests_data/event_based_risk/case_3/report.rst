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

Expected data transfer for the sources
--------------------------------------
=========================== =========
Number of tasks to generate 36       
Sent data                   4.79 MB  
Total received data         258.45 KB
Maximum received per task   12.07 KB 
=========================== =========

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
0            0         AreaSource   2,446  2,174     0.002       1.065      50       
2            0         AreaSource   2,446  2,174     9.260E-04   0.626      44       
0            2         AreaSource   1,992  2,748     0.002       0.698      16       
2            2         AreaSource   1,992  2,748     0.002       0.923      14       
1            10        AreaSource   448    1         7.091E-04   0.0        7.452    
3            10        AreaSource   448    1         7.081E-04   0.0        7.234    
1            6         AreaSource   422    1         8.051E-04   0.0        6.605    
0            1         AreaSource   422    1         8.080E-04   0.0        6.587    
2            1         AreaSource   422    1         6.990E-04   0.0        6.123    
3            6         AreaSource   422    1         7.229E-04   0.0        5.425    
3            3         AreaSource   340    1         7.508E-04   0.0        5.100    
3            9         AreaSource   255    1         6.790E-04   0.0        4.407    
1            9         AreaSource   255    1         6.750E-04   0.0        4.402    
1            3         AreaSource   340    1         7.050E-04   0.0        4.309    
3            5         AreaSource   236    1         7.160E-04   0.0        4.257    
1            5         AreaSource   236    1         6.981E-04   0.0        4.232    
3            7         AreaSource   166    1         6.721E-04   0.0        2.953    
1            4         AreaSource   128    1         7.050E-04   0.0        2.551    
3            4         AreaSource   128    1         6.971E-04   0.0        2.498    
3            8         AreaSource   144    1         7.601E-04   0.0        2.321    
============ ========= ============ ====== ========= =========== ========== =========

Slowest operations
------------------
============================== ========= ========= ======
operation                      time_sec  memory_mb counts
============================== ========= ========= ======
total compute_ruptures         207       0.059     36    
managing sources               3.980     0.0       1     
reading composite source model 3.952     0.0       1     
splitting sources              3.311     0.0       4     
store source_info              0.089     0.0       1     
total compute_gmfs_and_curves  0.023     0.062     7     
filtering sources              0.019     0.0       22    
compute poes                   0.013     0.0       7     
saving gmfs                    0.010     0.0       7     
make contexts                  0.007     0.0       7     
saving ruptures                0.007     0.0       1     
aggregate curves               0.004     0.0       36    
reading exposure               0.003     0.0       1     
reading site collection        6.914E-06 0.0       1     
============================== ========= ========= ======