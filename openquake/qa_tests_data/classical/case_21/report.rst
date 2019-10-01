Classical Hazard QA Test, Case 21
=================================

============== ===================
checksum32     2,852,175,627      
date           2019-10-01T07:01:09
engine_version 3.8.0-gitbd71c2f960
============== ===================

num_sites = 1, num_levels = 4, num_rlzs = 27

Parameters
----------
=============================== ==================
calculation_mode                'preclassical'    
number_of_logic_tree_samples    0                 
maximum_distance                {'default': 200.0}
investigation_time              1.0               
ses_per_logic_tree_path         1                 
truncation_level                3.0               
rupture_mesh_spacing            2.0               
complex_fault_mesh_spacing      2.0               
width_of_mfd_bin                1.0               
area_source_discretization      10.0              
ground_motion_correlation_model None              
minimum_intensity               {}                
random_seed                     106               
master_seed                     0                 
ses_seed                        42                
=============================== ==================

Input files
-----------
======================= ============================================================
Name                    File                                                        
======================= ============================================================
gsim_logic_tree         `gsim_logic_tree.xml <gsim_logic_tree.xml>`_                
job_ini                 `job.ini <job.ini>`_                                        
source_model_logic_tree `source_model_logic_tree.xml <source_model_logic_tree.xml>`_
======================= ============================================================

Composite source model
----------------------
====================== ======= =============== ================
smlt_path              weight  gsim_logic_tree num_realizations
====================== ======= =============== ================
b1_mfd1_high_dip_dip30 0.01320 trivial(1)      1               
b1_mfd1_high_dip_dip45 0.03960 trivial(1)      1               
b1_mfd1_high_dip_dip60 0.01320 trivial(1)      1               
b1_mfd1_low_dip_dip30  0.01320 trivial(1)      1               
b1_mfd1_low_dip_dip45  0.03960 trivial(1)      1               
b1_mfd1_low_dip_dip60  0.01320 trivial(1)      1               
b1_mfd1_mid_dip_dip30  0.03960 trivial(1)      1               
b1_mfd1_mid_dip_dip45  0.11880 trivial(1)      1               
b1_mfd1_mid_dip_dip60  0.03960 trivial(1)      1               
b1_mfd2_high_dip_dip30 0.01360 trivial(1)      1               
b1_mfd2_high_dip_dip45 0.04080 trivial(1)      1               
b1_mfd2_high_dip_dip60 0.01360 trivial(1)      1               
b1_mfd2_low_dip_dip30  0.01360 trivial(1)      1               
b1_mfd2_low_dip_dip45  0.04080 trivial(1)      1               
b1_mfd2_low_dip_dip60  0.01360 trivial(1)      1               
b1_mfd2_mid_dip_dip30  0.04080 trivial(1)      1               
b1_mfd2_mid_dip_dip45  0.12240 trivial(1)      1               
b1_mfd2_mid_dip_dip60  0.04080 trivial(1)      1               
b1_mfd3_high_dip_dip30 0.01320 trivial(1)      1               
b1_mfd3_high_dip_dip45 0.03960 trivial(1)      1               
b1_mfd3_high_dip_dip60 0.01320 trivial(1)      1               
b1_mfd3_low_dip_dip30  0.01320 trivial(1)      1               
b1_mfd3_low_dip_dip45  0.03960 trivial(1)      1               
b1_mfd3_low_dip_dip60  0.01320 trivial(1)      1               
b1_mfd3_mid_dip_dip30  0.03960 trivial(1)      1               
b1_mfd3_mid_dip_dip45  0.11880 trivial(1)      1               
b1_mfd3_mid_dip_dip60  0.03960 trivial(1)      1               
====================== ======= =============== ================

Required parameters per tectonic region type
--------------------------------------------
====== ================== ========= ========== ==========
grp_id gsims              distances siteparams ruptparams
====== ================== ========= ========== ==========
0      '[SadighEtAl1997]' rrup      vs30       mag rake  
1      '[SadighEtAl1997]' rrup      vs30       mag rake  
2      '[SadighEtAl1997]' rrup      vs30       mag rake  
3      '[SadighEtAl1997]' rrup      vs30       mag rake  
4      '[SadighEtAl1997]' rrup      vs30       mag rake  
5      '[SadighEtAl1997]' rrup      vs30       mag rake  
6      '[SadighEtAl1997]' rrup      vs30       mag rake  
7      '[SadighEtAl1997]' rrup      vs30       mag rake  
8      '[SadighEtAl1997]' rrup      vs30       mag rake  
9      '[SadighEtAl1997]' rrup      vs30       mag rake  
10     '[SadighEtAl1997]' rrup      vs30       mag rake  
11     '[SadighEtAl1997]' rrup      vs30       mag rake  
12     '[SadighEtAl1997]' rrup      vs30       mag rake  
13     '[SadighEtAl1997]' rrup      vs30       mag rake  
14     '[SadighEtAl1997]' rrup      vs30       mag rake  
15     '[SadighEtAl1997]' rrup      vs30       mag rake  
16     '[SadighEtAl1997]' rrup      vs30       mag rake  
17     '[SadighEtAl1997]' rrup      vs30       mag rake  
18     '[SadighEtAl1997]' rrup      vs30       mag rake  
19     '[SadighEtAl1997]' rrup      vs30       mag rake  
20     '[SadighEtAl1997]' rrup      vs30       mag rake  
21     '[SadighEtAl1997]' rrup      vs30       mag rake  
22     '[SadighEtAl1997]' rrup      vs30       mag rake  
23     '[SadighEtAl1997]' rrup      vs30       mag rake  
24     '[SadighEtAl1997]' rrup      vs30       mag rake  
25     '[SadighEtAl1997]' rrup      vs30       mag rake  
26     '[SadighEtAl1997]' rrup      vs30       mag rake  
====== ================== ========= ========== ==========

Realizations per (GRP, GSIM)
----------------------------

::

  <RlzsAssoc(size=27, rlzs=27)>

Number of ruptures per source group
-----------------------------------
====== ========= ============ ============
grp_id num_sites num_ruptures eff_ruptures
====== ========= ============ ============
0      2.00000   444          444         
1      2.00000   208          208         
2      2.00000   149          149         
3      2.00000   534          534         
4      2.00000   298          298         
5      2.00000   239          239         
6      2.00000   474          474         
7      2.00000   238          238         
8      2.00000   179          179         
9      2.00000   409          409         
10     2.00000   173          173         
11     2.00000   114          114         
12     2.00000   465          465         
13     2.00000   229          229         
14     2.00000   170          170         
15     2.00000   411          411         
16     2.00000   175          175         
17     2.00000   116          116         
18     2.00000   483          483         
19     2.00000   247          247         
20     2.00000   188          188         
21     2.00000   582          582         
22     2.00000   346          346         
23     2.00000   287          287         
24     2.00000   516          516         
25     2.00000   280          280         
26     2.00000   221          221         
====== ========= ============ ============

Slowest sources
---------------
========= ====== ==== ============ ========= ========= ============ =======
source_id grp_id code num_ruptures calc_time num_sites eff_ruptures speed  
========= ====== ==== ============ ========= ========= ============ =======
SFLT1     3      S    150          0.00623   1.00000   150          24,063 
SFLT1     24     S    132          0.00528   1.00000   132          24,993 
SFLT2     10     S    148          0.00494   1.00000   148          29,972 
SFLT2     3      S    384          0.00491   1.00000   384          78,128 
SFLT2     20     S    89           0.00490   1.00000   89           18,159 
SFLT1     4      S    150          0.00464   1.00000   150          32,302 
SFLT1     1      S    60           0.00436   1.00000   60           13,774 
SFLT2     15     S    384          0.00423   1.00000   384          90,734 
SFLT1     5      S    150          0.00420   1.00000   150          35,688 
SFLT1     16     S    27           0.00412   1.00000   27           6,553  
SFLT2     8      S    89           0.00411   1.00000   89           21,633 
SFLT1     7      S    90           0.00406   1.00000   90           22,147 
SFLT1     26     S    132          0.00386   1.00000   132          34,186 
SFLT1     23     S    198          0.00376   1.00000   198          52,675 
SFLT2     0      S    384          0.00356   1.00000   384          107,892
SFLT2     24     S    384          0.00341   1.00000   384          112,701
SFLT1     15     S    27           0.00337   1.00000   27           8,015  
SFLT1     22     S    198          0.00334   1.00000   198          59,281 
SFLT2     21     S    384          0.00323   1.00000   384          118,908
SFLT1     19     S    99           0.00320   1.00000   99           30,916 
========= ====== ==== ============ ========= ========= ============ =======

Computation times by source typology
------------------------------------
==== ========= ======
code calc_time counts
==== ========= ======
S    0.15626   54    
==== ========= ======

Duplicated sources
------------------
Found 0 unique sources and 12 duplicate sources with multiplicity 4.5: ['SFLT1' 'SFLT1' 'SFLT1' 'SFLT1' 'SFLT1' 'SFLT1' 'SFLT1' 'SFLT1' 'SFLT1'
 'SFLT2' 'SFLT2' 'SFLT2']

Information about the tasks
---------------------------
================== ======= ======= ======= ======= =======
operation-duration mean    stddev  min     max     outputs
SourceReader       0.04879 0.01343 0.03482 0.08852 27     
preclassical       0.00621 0.00290 0.00287 0.01312 27     
================== ======= ======= ======= ======= =======

Data transfer
-------------
============ ================================================ ========
task         sent                                             received
SourceReader apply_unc=52.47 KB ltmodel=5.62 KB fname=2.74 KB 97.19 KB
preclassical srcs=38.84 KB params=13.87 KB srcfilter=5.85 KB  10.25 KB
============ ================================================ ========

Slowest operations
------------------
====================== ======== ========= ======
calc_6631              time_sec memory_mb counts
====================== ======== ========= ======
total SourceReader     1.31744  0.25000   27    
composite source model 0.21957  0.0       1     
total preclassical     0.16766  0.25391   27    
aggregate curves       0.00756  0.0       27    
store source_info      0.00292  0.0       1     
====================== ======== ========= ======