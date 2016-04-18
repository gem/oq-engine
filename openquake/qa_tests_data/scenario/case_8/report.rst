Scenario QA Test with AtkinsonBoore2003SInter
=============================================

num_sites = 2, sitecol = 785 B

Parameters
----------
============================ ================
calculation_mode             'scenario'      
number_of_logic_tree_samples 0               
maximum_distance             {'default': 200}
investigation_time           None            
ses_per_logic_tree_path      1               
truncation_level             None            
rupture_mesh_spacing         1.0             
complex_fault_mesh_spacing   1.0             
width_of_mfd_bin             None            
area_source_discretization   None            
random_seed                  3               
master_seed                  0               
concurrent_tasks             40              
============================ ================

Input files
-----------
============= ========================================
Name          File                                    
============= ========================================
job_ini       `job.ini <job.ini>`_                    
rupture_model `rupture_model.xml <rupture_model.xml>`_
============= ========================================

Realizations per (TRT, GSIM)
----------------------------

::

  <RlzsAssoc(1)
  0,AtkinsonBoore2003SInter: ['AtkinsonBoore2003SInter']>

Slowest operations
------------------
======================= ========= ========= ======
operation               time_sec  memory_mb counts
======================= ========= ========= ======
filtering sites         0.009     0.0       1     
computing gmfs          5.801E-04 0.0       1     
reading site collection 2.980E-05 0.0       1     
======================= ========= ========= ======