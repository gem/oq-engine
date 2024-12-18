Reusing hazard across engine versions
=====================================

The OpenQuake engine has always had the capability to reuse old hazard
calculations when performing new risk calculations, thanks to the `--hc`
command-line option. However such capability never extended across
different versions of the engine. Here we will document the reasons
for such restriction.

Reusing the GMFs
----------------

While the `--hc` option works for all kind of calculations,
`classical_risk`, `classical_damage` and `classical_bcr` calculations are
less used: what is really important is to reuse the hazard for
scenario and for event based calculations, i.e. to reuse the GMFs.

Reusing the hazard for scenario calculations is relatively
straighforward: it is enough to keep the GMFs in CSV format and to
start from there by using the `gmfs_file` option in the job.ini. This
works across versions already. The reason is that the logic tree is
trivial in this case: internally, the engine assumes that there is a single
realization and automatically creates a fake logic tree object.

1. The difficulty is for event based calculations. The details of the
*logic tree* implementation change frequently. Therefore an apparently
simple question such as "tell me which GMPE was used when computing
the ground motion field for event number 123" is actually very hard to
answer across versions. This is by far the biggest difficulty, since
the logic tree part is expected to change again and in unpredictable
ways, due to the requests of the hazard team.

2. This not the only difficulty. When using the ``--hc`` option the engine
has also to match the risk sites with the hazard sites; this means
that it has to match a *SiteCollection* object coming from an old version
of the engine with a SiteCollection coming from a new version of the
engine. If the SiteCollection has changed (for instance new fields have
been added) this has to be managed in some way and this is not necessarily
easy or event possible.

3. Moreover there is the *events* table which associates event IDs to
realization IDs and to rupture IDs; if the form of the events table
changes across versions (for instance if new fields are added) then we
have an issue. Also, if the management of the logic tree changes (this
is very common) and the associations are different, starting a
calculation from scratch in the new version of the engine will give
different results than reusing an old hazard calculations.

4. The same would happen if the *weighting algorithm* of the realizations
changed (and this happened a couple of times in the past). Moreover at
nearly each release of the engine the details of the algorithm used to
generate the ruptures and/or the *rupture seeds changes*, therefore
again starting a calculation from scratch in the new version of the
engine would give different results than reusing an old hazard.

5. Another difficulty would arise if the association between asset and
hazard sites changed, causing different losses to be computed. This
has neved happened intentionally, but it has happened several times
unintentionally, due to tricky bugs. Bug fixes have changed
the *asset<->site* association logic several times.

6. Reusing an old *exposure* would also also be problematic,
assuming the new exposure had more fields. Changes to the exposure
happened several time in the past, so the problem is not academic.
The solution is to NOT reuse old exposures and to re-import the exposure
at each new risk calculation, thus paying a performance penalty.

7. The same can be said for *vulnerability/fragility functions*: any
change there would make reusing them across versions very hard.
Such a change happened few months ago already. The solution is to
not reuse old risk models and to re-parse them at each new risk
calculation, thus paying a performance penalty.

8. Clearly a bug fix in a GMPE will change the values of the generated
GMFs. Depending on the circumstances, a user may want to use the old GMFs
or not.

9. In the future, it is expected that both the site collection and the events
table will be stored differently in the datastore, in a pandas-friendly
way, for consistency with the way other objects are stored, and
also for memory efficiency. That means that work will be needed to be
able to read both the old and the new versions of such objects. This is
actually the least of the problems mentioned until now.

10. In engine 3.12 the way the object `oqparam` has changed, to support
h5py 3.X. This is yet another origin of breaking changes.

Copying with version-dependency
-------------------------------

The fact that old hazard cannot be reused is a minor issue for GEM people,
since we are using the git version of the engine. Here is a workflow that
works.

1. First of all, run the hazard part of the calculation on a big remote machine
   which is at version X of the code (usually an old version).

2. Then run on the user machine the command `oq importcalc` to dowload the
remote calculation; here is an example:
```
$ oq importcalc 41214
INFO:root:POST https://oq2.wilson.openquake.org//accounts/ajax_login/
INFO:root:GET https://oq2.wilson.openquake.org//v1/calc/41214/extract/oqparam
INFO:root:Saving /home/michele/oqdata/calc_41214.hdf5
Downloaded 58,118,085 bytes
{'checksum32': 1949258781,
 'date': '2021-03-18T15:25:11',
 'engine_version': '3.12.0-gita399903317'}
INFO:root:Imported calculation 41214 successfully
```
3. Go back to version X of the code so that the risk part of the calculation
can be done locally without issues:
```bash
$ git checkout a399903317
$ oq engine --run job.ini --hc 41214
```
That's it. This guarantees consistency and reproducibility, since both
parts of the calculation are performed with the same version of the code.

The elephant in the room
------------------------

We have not talked about the biggest issue of all: the sheer size of the
GMFs dataset. Reusing the GMFs is never going to be practical if we
need to store hundreds of GB of data. The only real solution for
commercial applications would be to store a reduced set of GMFs,
corresponding to a single effective realization, small but still
reproducing with decent accurary the mean results of the full
calculation. Then the risk part of the calculation would be like a
scenario starting from a CSV file.

We could even export three CSV files for the GMFs: one for the mean
field, one for a pessimistic case and one for an optimistic case, thus
allowing the users to explore alternative hazard scenarios.

All this requires internal discussion as it is not easy to achieve.

Starting from the ruptures
--------------------------

Starting from engine 3.10 it is possible to start an event based risk
calculation from a set of ruptures saved in CSV format. While the
feature is still experimental and probably not working properly in all
situations, it is an approach that solves the issue of the sheer size
of the GMFs. The issue with the GMFs is that, as soon as you have a
fine grid for the site model, you may get hundreds of thousands of
sites and hundreds of gigabytes of GMFs. The size of the ruptures
instead is independent from the number of sites and normally around a
few gigabytes. The downside is that starting from the ruptures
requires recomputing the GMFs everytime, so it is computationally
expensive. Also, changes between versions might render the approach
infeasible, for the same reasons reusing the GMFs is problematic.
