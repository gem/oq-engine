Classical Hazard QA Test, Case 20
=================================

gem-tstation:/home/michele/ssd/calc_40717.hdf5 updated Mon Aug 22 12:53:28 2016

num_sites = 1, sitecol = 739 B

Parameters
----------
============================ ================================
calculation_mode             'classical'                     
number_of_logic_tree_samples 0                               
maximum_distance             {u'Active Shallow Crust': 200.0}
investigation_time           1.0                             
ses_per_logic_tree_path      1                               
truncation_level             3.0                             
rupture_mesh_spacing         2.0                             
complex_fault_mesh_spacing   2.0                             
width_of_mfd_bin             1.0                             
area_source_discretization   10.0                            
random_seed                  106                             
master_seed                  0                               
sites_per_tile               10000                           
engine_version               '2.1.0-git8cbb23e'              
============================ ================================

Input files
-----------
======================= ==================================================================================================
Name                    File                                                                                              
======================= ==================================================================================================
gsim_logic_tree         `gsim_logic_tree.xml <gsim_logic_tree.xml>`_                                                      
job_ini                 `job.ini <job.ini>`_                                                                              
source                  `
                        
                     <
                        
                    >`_
source                  `
                        
                     <
                        
                    >`_
source                  `
                        
                     <
                        
                    >`_
source                  `
                        
                     <
                        
                    >`_
source                  `
                        
                     <
                        
                    >`_
source                  `
                        
                     <
                        
                    >`_
source                  `
                        
                     <
                        
                    >`_
source                  `source_model.xml <source_model.xml>`_                                                            
source_model_logic_tree `source_model_logic_tree.xml <source_model_logic_tree.xml>`_                                      
======================= ==================================================================================================

Composite source model
----------------------
========================= ====== ====================================== =============== ================
smlt_path                 weight source_model_file                      gsim_logic_tree num_realizations
========================= ====== ====================================== =============== ================
sm1_sg1_cog1_char_complex 0.070  `source_model.xml <source_model.xml>`_ trivial(1)      1/1             
sm1_sg1_cog1_char_plane   0.105  `source_model.xml <source_model.xml>`_ trivial(1)      1/1             
sm1_sg1_cog1_char_simple  0.175  `source_model.xml <source_model.xml>`_ trivial(1)      1/1             
sm1_sg1_cog2_char_complex 0.070  `source_model.xml <source_model.xml>`_ trivial(1)      1/1             
sm1_sg1_cog2_char_plane   0.105  `source_model.xml <source_model.xml>`_ trivial(1)      1/1             
sm1_sg1_cog2_char_simple  0.175  `source_model.xml <source_model.xml>`_ trivial(1)      1/1             
sm1_sg2_cog1_char_complex 0.030  `source_model.xml <source_model.xml>`_ trivial(1)      1/1             
sm1_sg2_cog1_char_plane   0.045  `source_model.xml <source_model.xml>`_ trivial(1)      1/1             
sm1_sg2_cog1_char_simple  0.075  `source_model.xml <source_model.xml>`_ trivial(1)      1/1             
sm1_sg2_cog2_char_complex 0.030  `source_model.xml <source_model.xml>`_ trivial(1)      1/1             
sm1_sg2_cog2_char_plane   0.045  `source_model.xml <source_model.xml>`_ trivial(1)      1/1             
sm1_sg2_cog2_char_simple  0.075  `source_model.xml <source_model.xml>`_ trivial(1)      1/1             
========================= ====== ====================================== =============== ================

Required parameters per tectonic region type
--------------------------------------------
====== ==================== ============= ============= ==========
grp_id gsims                distances     siteparams    ruptparams
====== ==================== ============= ============= ==========
0      ['SadighEtAl1997()'] set(['rrup']) set(['vs30']) rake mag  
1      ['SadighEtAl1997()'] set(['rrup']) set(['vs30']) rake mag  
2      ['SadighEtAl1997()'] set(['rrup']) set(['vs30']) rake mag  
3      ['SadighEtAl1997()'] set(['rrup']) set(['vs30']) rake mag  
4      ['SadighEtAl1997()'] set(['rrup']) set(['vs30']) rake mag  
5      ['SadighEtAl1997()'] set(['rrup']) set(['vs30']) rake mag  
6      ['SadighEtAl1997()'] set(['rrup']) set(['vs30']) rake mag  
7      ['SadighEtAl1997()'] set(['rrup']) set(['vs30']) rake mag  
8      ['SadighEtAl1997()'] set(['rrup']) set(['vs30']) rake mag  
9      ['SadighEtAl1997()'] set(['rrup']) set(['vs30']) rake mag  
10     ['SadighEtAl1997()'] set(['rrup']) set(['vs30']) rake mag  
11     ['SadighEtAl1997()'] set(['rrup']) set(['vs30']) rake mag  
====== ==================== ============= ============= ==========

Realizations per (TRT, GSIM)
----------------------------

::

  <RlzsAssoc(size=12, rlzs=12)
  0,SadighEtAl1997(): ['<0,sm1_sg1_cog1_char_complex~Sad1997,w=0.0700000005588>']
  1,SadighEtAl1997(): ['<1,sm1_sg1_cog1_char_plane~Sad1997,w=0.104999997113>']
  2,SadighEtAl1997(): ['<2,sm1_sg1_cog1_char_simple~Sad1997,w=0.174999997672>']
  3,SadighEtAl1997(): ['<3,sm1_sg1_cog2_char_complex~Sad1997,w=0.0700000005588>']
  4,SadighEtAl1997(): ['<4,sm1_sg1_cog2_char_plane~Sad1997,w=0.104999997113>']
  5,SadighEtAl1997(): ['<5,sm1_sg1_cog2_char_simple~Sad1997,w=0.174999997672>']
  6,SadighEtAl1997(): ['<6,sm1_sg2_cog1_char_complex~Sad1997,w=0.0299999994412>']
  7,SadighEtAl1997(): ['<7,sm1_sg2_cog1_char_plane~Sad1997,w=0.0450000019558>']
  8,SadighEtAl1997(): ['<8,sm1_sg2_cog1_char_simple~Sad1997,w=0.0750000032596>']
  9,SadighEtAl1997(): ['<9,sm1_sg2_cog2_char_complex~Sad1997,w=0.0299999994412>']
  10,SadighEtAl1997(): ['<10,sm1_sg2_cog2_char_plane~Sad1997,w=0.0450000019558>']
  11,SadighEtAl1997(): ['<11,sm1_sg2_cog2_char_simple~Sad1997,w=0.0750000032596>']>

Number of ruptures per tectonic region type
-------------------------------------------
================ ====== ==================== =========== ============ ======
source_model     grp_id trt                  num_sources eff_ruptures weight
================ ====== ==================== =========== ============ ======
source_model.xml 0      Active Shallow Crust 3           86           86    
source_model.xml 1      Active Shallow Crust 3           86           86    
source_model.xml 2      Active Shallow Crust 3           86           86    
source_model.xml 3      Active Shallow Crust 3           119          119   
source_model.xml 4      Active Shallow Crust 3           119          119   
source_model.xml 5      Active Shallow Crust 3           119          119   
source_model.xml 6      Active Shallow Crust 3           88           88    
source_model.xml 7      Active Shallow Crust 3           88           88    
source_model.xml 8      Active Shallow Crust 3           88           88    
source_model.xml 9      Active Shallow Crust 3           121          121   
source_model.xml 10     Active Shallow Crust 3           121          121   
source_model.xml 11     Active Shallow Crust 3           121          121   
================ ====== ==================== =========== ============ ======

=============== =====
#TRT models     12   
#sources        36   
#eff_ruptures   1,242
filtered_weight 1,242
=============== =====

Informational data
------------------
=============================== ============
classical_max_received_per_task 1,826       
classical_num_tasks             24          
classical_sent.monitor          19,584      
classical_sent.rlzs_by_gsim     13,464      
classical_sent.sitecol          10,392      
classical_sent.sources          100,996     
classical_tot_received          43,644      
hazard.input_weight             1,242       
hazard.n_imts                   1           
hazard.n_levels                 4.000       
hazard.n_realizations           12          
hazard.n_sites                  1           
hazard.n_sources                36          
hazard.output_weight            48          
hostname                        gem-tstation
=============================== ============

Slowest sources
---------------
============ ========= ================== ====== ========= =========== ========== ============= ============= =========
src_group_id source_id source_class       weight split_num filter_time split_time cum_calc_time max_calc_time num_tasks
============ ========= ================== ====== ========= =========== ========== ============= ============= =========
4            COMFLT1   ComplexFaultSource 62     1         0.001       0.0        0.986         0.986         1        
9            COMFLT1   ComplexFaultSource 62     1         0.001       0.0        0.754         0.754         1        
3            COMFLT1   ComplexFaultSource 62     1         0.001       0.0        0.736         0.736         1        
5            COMFLT1   ComplexFaultSource 62     1         0.001       0.0        0.657         0.657         1        
11           COMFLT1   ComplexFaultSource 62     1         0.001       0.0        0.615         0.615         1        
10           COMFLT1   ComplexFaultSource 62     1         0.001       0.0        0.610         0.610         1        
1            COMFLT1   ComplexFaultSource 29     1         0.001       0.0        0.467         0.467         1        
0            COMFLT1   ComplexFaultSource 29     1         0.001       0.0        0.461         0.461         1        
9            SFLT1     SimpleFaultSource  58     1         0.001       0.0        0.442         0.442         1        
4            SFLT1     SimpleFaultSource  56     1         0.001       0.0        0.441         0.441         1        
7            SFLT1     SimpleFaultSource  58     1         0.001       0.0        0.436         0.436         1        
3            SFLT1     SimpleFaultSource  56     1         0.001       0.0        0.406         0.406         1        
7            COMFLT1   ComplexFaultSource 29     1         0.001       0.0        0.400         0.400         1        
8            SFLT1     SimpleFaultSource  58     1         0.001       0.0        0.399         0.399         1        
6            SFLT1     SimpleFaultSource  58     1         0.001       0.0        0.375         0.375         1        
1            SFLT1     SimpleFaultSource  56     1         0.001       0.0        0.348         0.348         1        
0            SFLT1     SimpleFaultSource  56     1         0.001       0.0        0.314         0.314         1        
2            SFLT1     SimpleFaultSource  56     1         0.001       0.0        0.308         0.308         1        
10           SFLT1     SimpleFaultSource  58     1         0.001       0.0        0.307         0.307         1        
6            COMFLT1   ComplexFaultSource 29     1         0.001       0.0        0.306         0.306         1        
============ ========= ================== ====== ========= =========== ========== ============= ============= =========

Computation times by source typology
------------------------------------
========================= =========== ========== ============= ============= ========= ======
source_class              filter_time split_time cum_calc_time max_calc_time num_tasks counts
========================= =========== ========== ============= ============= ========= ======
CharacteristicFaultSource 0.014       0.0        0.012         0.012         12        12    
ComplexFaultSource        0.014       0.0        6.562         6.562         12        12    
SimpleFaultSource         0.016       0.0        4.373         4.373         12        12    
========================= =========== ========== ============= ============= ========= ======

Information about the tasks
---------------------------
=================== ===== ====== ===== ===== =========
measurement         mean  stddev min   max   num_tasks
classical.time_sec  0.459 0.183  0.269 0.991 24       
classical.memory_mb 0.0   0.0    0.0   0.0   24       
=================== ===== ====== ===== ===== =========

Slowest operations
------------------
============================== ========= ========= ======
operation                      time_sec  memory_mb counts
============================== ========= ========= ======
total classical                11        0.0       24    
making contexts                6.993     0.0       1,242 
reading composite source model 0.794     0.0       1     
computing poes                 0.220     0.0       1,242 
managing sources               0.089     0.0       1     
filtering sources              0.044     0.0       36    
store source_info              0.020     0.0       1     
saving probability maps        0.018     0.0       1     
read poes                      0.006     0.0       1     
aggregate curves               6.049E-04 0.0       24    
reading site collection        3.719E-05 0.0       1     
============================== ========= ========= ======