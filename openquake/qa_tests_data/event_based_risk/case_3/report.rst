Event Based PSHA for Lisbon
===========================

num_sites = 1, sitecol = 684 B

Parameters
----------
============================ ===========
calculation_mode             event_based
number_of_logic_tree_samples 0          
maximum_distance             400.0      
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
============================ ===========

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
b1        0.60   `SA_RA_CATAL1_00.xml <SA_RA_CATAL1_00.xml>`_ complex(2,2)    4/4             
b2        0.40   `SA_RA_CATAL2_00.xml <SA_RA_CATAL2_00.xml>`_ simple(2,0)     2/2             
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

  <RlzsAssoc(6)
  0,AkkarBommer2010: ['<2,b1,b2_b3,w=0.126>', '<3,b1,b2_b4,w=0.054>']
  0,AtkinsonBoore2006: ['<0,b1,b1_b3,w=0.294>', '<1,b1,b1_b4,w=0.126>']
  1,AkkarBommer2010: ['<1,b1,b1_b4,w=0.126>', '<3,b1,b2_b4,w=0.054>']
  1,AtkinsonBoore2006: ['<0,b1,b1_b3,w=0.294>', '<2,b1,b2_b3,w=0.126>']
  2,AkkarBommer2010: ['<5,b2,b2_@,w=0.12>']
  2,AtkinsonBoore2006: ['<4,b2,b1_@,w=0.28>']>

Non-empty rupture collections
-----------------------------
=== ========= ==================== ============
col smlt_path TRT                  num_ruptures
=== ========= ==================== ============
0   b1        Active Shallow Crust 3           
1   b1        Stable Shallow Crust 2           
2   b2        Active Shallow Crust 2           
=== ========= ==================== ============

Collections <-> realizations
----------------------------
=========== ============
Collections Realizations
0 1         0 1 2 3     
2           4 5         
=========== ============

Expected data transfer for the sources
--------------------------------------
=========================== =========
Number of tasks to generate 20       
Sent data                   4.57 MB  
Total received data         176.83 KB
Maximum received per task   18.28 KB 
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
============ ========= ============ ======= ========= =========== ========== =========
trt_model_id source_id source_class weight  split_num filter_time split_time calc_time
============ ========= ============ ======= ========= =========== ========== =========
2            0         AreaSource   2445.75 2174      0.00234604  1.70342    84.352   
0            0         AreaSource   2445.75 2174      0.00371408  1.80017    82.9555  
0            2         AreaSource   1992.3  2748      0.00226307  1.5158     25.5874  
2            2         AreaSource   1992.3  2748      0.00228119  1.62972    25.1383  
1            10        AreaSource   448.2   1         0.00170302  0.0        10.8714  
3            10        AreaSource   448.2   1         0.00162315  0.0        10.3096  
0            1         AreaSource   422.05  1         0.00195694  0.0        10.0521  
3            6         AreaSource   422.375 1         0.0016799   0.0        9.69501  
1            6         AreaSource   422.375 1         0.00176907  0.0        8.70533  
2            1         AreaSource   422.05  1         0.00167012  0.0        8.69409  
3            3         AreaSource   340.025 1         0.00166082  0.0        8.62094  
3            5         AreaSource   236.35  1         0.0016892   0.0        7.26119  
1            3         AreaSource   340.025 1         0.001652    0.0        6.9538   
3            9         AreaSource   255.6   1         0.00168419  0.0        6.10319  
1            5         AreaSource   236.35  1         0.00166988  0.0        6.01634  
1            9         AreaSource   255.6   1         0.00167489  0.0        5.39486  
3            8         AreaSource   144.45  1         0.001863    0.0        4.87072  
1            7         AreaSource   166.725 1         0.00169683  0.0        4.74342  
1            4         AreaSource   128.25  1         0.00169396  0.0        3.83895  
3            7         AreaSource   166.725 1         0.00176907  0.0        3.82069  
============ ========= ============ ======= ========= =========== ========== =========