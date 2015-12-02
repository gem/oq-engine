Event Based PSHA for Lisbon
===========================

num_sites = 1

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
========= ====== ============================================ =============== ================ ===========
smlt_path weight source_model_file                            gsim_logic_tree num_realizations num_sources
========= ====== ============================================ =============== ================ ===========
b1        0.60   `SA_RA_CATAL1_00.xml <SA_RA_CATAL1_00.xml>`_ simple(2,0)     2/2              10191      
b2        0.40   `SA_RA_CATAL2_00.xml <SA_RA_CATAL2_00.xml>`_ complex(2,2)    4/4              10191      
========= ====== ============================================ =============== ================ ===========

Required parameters per tectonic region type
--------------------------------------------
====== ================================= ========= ========== ==========
trt_id gsims                             distances siteparams ruptparams
====== ================================= ========= ========== ==========
0      AkkarBommer2010 AtkinsonBoore2006 rjb rrup  vs30       rake mag  
2      AkkarBommer2010 AtkinsonBoore2006 rjb rrup  vs30       rake mag  
3      AkkarBommer2010 AtkinsonBoore2006 rjb rrup  vs30       rake mag  
====== ================================= ========= ========== ==========

Realizations per (TRT, GSIM)
----------------------------

::

  <RlzsAssoc(6)
  0,AkkarBommer2010: ['<1,b1,b2_@,w=0.18>']
  0,AtkinsonBoore2006: ['<0,b1,b1_@,w=0.42>']
  2,AkkarBommer2010: ['<4,b2,b2_b3,w=0.084>', '<5,b2,b2_b4,w=0.036>']
  2,AtkinsonBoore2006: ['<2,b2,b1_b3,w=0.196>', '<3,b2,b1_b4,w=0.084>']
  3,AkkarBommer2010: ['<3,b2,b1_b4,w=0.084>', '<5,b2,b2_b4,w=0.036>']
  3,AtkinsonBoore2006: ['<2,b2,b1_b3,w=0.196>', '<4,b2,b2_b3,w=0.084>']>

Non-empty rupture collections
-----------------------------
=== ========= ==================== ============
col smlt_path TRT                  num_ruptures
=== ========= ==================== ============
0   b1        Active Shallow Crust 2           
2   b2        Active Shallow Crust 4           
3   b2        Stable Shallow Crust 2           
=== ========= ==================== ============

Collections <-> realizations
----------------------------
=========== ============
Collections Realizations
0           0 1         
2 3         2 3 4 5     
=========== ============

Expected data transfer for the sources
--------------------------------------
================================== =======
Number of tasks to generate        18     
Estimated sources to send          4.32 MB
Estimated hazard curves to receive 9 KB   
================================== =======

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