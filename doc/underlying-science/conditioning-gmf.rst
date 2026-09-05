Conditioning Ground Shaking
===========================

Given an earthquake rupture model, a site model, and a set of ground shaking intensity models (GSIMs), the OpenQuake engine scenario calculator simulates a set of ground motion fields (GMFs) at the target sites for the requested set of intensity measure types (IMTs). This set of GMFs can then be used in the :ref:`scenario-damage-intro` and :ref:`scenario-risk-intro` calculators to estimate the distribution of potential damage, economic losses, fatalities, and other consequences. The scenario calculators are useful for simulating both historical and hypothetical earthquakes.

For historical events, ground motion recordings and macroseismic intensity data ("ground truth") can provide additional constraints on the ground shaking estimates in the region affected by the earthquake. The U.S. Geological Survey ShakeMap system (Worden et al. 2020; Wald et al. 2022) provides near-real-time estimates of ground shaking for earthquakes conditioned on station and macroseismic data where available. Support to read USGS ShakeMaps and simulate GMFs based on the mean and standard deviation values estimated by the ShakeMap — for peak ground acceleration (PGA) and spectral acceleration (SA) at 0.3s, 1.0s, and 3.0s — was added to the OpenQuake engine in 2018, and a link to the `scenario_damage` and `scenario_risk` calculators was added based on the methodology described by Silva & Horspool (2019). Further support for reading ShakeMaps from sources other than the USGS, support for MMI, and performance improvements were introduced to the engine in 2021.

Therefore, starting from OpenQuake engine v3.16, it is possible to condition the ground shaking to observations, such as ground motion recordings and macroseismic intensity observations. The implementation is tightly coupled with the existing scenario calculator.


Methodology
-----------

The main source of uncertainty in the evaluation of earthquake scenarios is the ground shaking component. The estimation of the ground shaking, considering past events or hypothetical future earthquakes, is characterized by two types of uncertainty: epistemic and aleatory. The former is related to our lack of knowledge or data regarding the expected ground shaking in the region, and it is usually incorporated in earthquake scenarios by considering multiple ground motion models or GSIMs. Alternatively, a ground motion model (backbone model) that depends on different parameters (that are region-dependent) can be used. In theory, with additional data, this source of uncertainty could be minimized. The second type of uncertainty is related to the randomness of the ground shaking process and it cannot be completely reduced. A ground shaking intensity measure (IM) at a given site is typically estimated using the following equation:

.. math::

   \log(IM) = \mu(MR\theta) + \zeta

Where `IM` stands for an intensity measure such as peak ground acceleration (PGA), peak ground velocity (PGV), spectral acceleration (SA), amongst others. `μ(MRθ)` represents the mean logarithm of the estimated ground shaking as a function of the magnitude (M), some measure of distance (R), and other parameters (θ) such as local site conditions or faulting mechanism. `ζ` represents the total residual of `\log(IM)`. By treating the total residual as a linear mixed-effects model (Abrahanson and Youngs 1992; Engler et al. 2022), equation above can be re-written as follows:

.. math::

   \log(IM) = \mu(MR\theta) + B + W

Where `B` stands for the between-event residual (i.e., representing the variability in the ground shaking amongst events with the same characteristics) and `W` refers to the within-event residual (i.e., representing the variability within the same event for sites at the same distance and soil conditions). These residuals typically follow a normal distribution and for the assessment of earthquake damage or losses they can be randomly sampled or numerically integrated using the respective standard deviations associated with each ground motion model.

OpenQuake engine implementation
-------------------------------

The implementation of the conditioning of ground motion fields in the OpenQuake engine was performed following closely the procedure proposed by Engler et al. (2022). For additional details, readers are referred to the Appendix A and B of Engler et al. (2022). The module in the OpenQuake engine is similar to the well-established scenario damage or risk calculator in which users have to provide an earthquake rupture, a site model, the list of locations where ground shaking will be calculated, and a single GSIM or a GSIM logic tree. However, for the constraining of the ground shaking, it is necessary to provide additional input files and adjustments to the configuration file as presented in the OpenQuake engine input files section.

The generation of the conditioned cross-spatially correlated ground motion fields was performed in the following steps described below. All variables associated with the target sites (i.e., locations where the ground shaking will be computed) are identified with the subscript “T” while all variables related to the observations at the seismic station are identified with subscript “O”. 

1. The median ground shaking is calculated at the location of the seismic stations considering the set of GMMs selected by the user (and using the GMM library of the OpenQuake engine).

2. The residuals (:math:`\zeta_{IMO}`) at every station location are computed through the difference between the recorded IM and the median IM from the GMMs.

3. A covariance matrix (:math:`\Sigma_{WOWO}`) is computed for all IMs and station locations using the within-event sigma (W). Since each GMM has its own uncertainty, this step is repeated for each GMM.

4. The mean (:math:`\mu_{BIM}`) and variance (:math:`\sigma^2_{BIM}`) of the between-event residual conditioned on the observations from the seismic stations for each IM (:math:`BIM`) is computed using the formulae below (Worden et al. 2018). This parameter is used to adjust the ground shaking (per IM) for the entire affected region, thus allowing the possibility of not sampling the between-event residual.
   
   .. math::

      \mu_{BIM} = \frac{Z^T \Sigma_{WOWO}^{-1} \zeta_{IMO}}{\tau_{IM}^{-2} + Z^T \Sigma_{WOWO}^{-1} Z}

   .. math::

      \sigma^2_{BIM} = \frac{1}{\tau_{IM}^{-2} + Z^T \Sigma_{WOWO}^{-1} Z}

   Where Z is a column vector of ones (Jayaram and Baker 2010).

5. The conditioned between-event residual can now be used to adjust the total residuals calculated in Step 2 as presented below. Since the between-event component has now been removed from :math:`\zeta_{IMO}`, we are left with the residuals due to the within-event component (:math:`w_O`).
   
   .. math::

      w_O = \zeta_{IMO} - \mu_{BIM}

6. With the calculation of :math:`w_O`, it is now necessary to compute the covariance matrix between the target IMs (in general, considering the intensity measures used by the vulnerability or fragility functions) and the target locations (:math:`\Sigma_{WTWT}`) as well as the covariance matrix considering both the target/observed IMs and target/observed locations (:math:`\Sigma_{WTWO}`) and vice-versa (:math:`\Sigma_{WOWT}`).

7. Finally, the mean (:math:`\mu_{TIM|O}`) and covariance (:math:`\Sigma_{WTWT|O}`) of the ground shaking for the target IMs and locations conditioned on the observations can be computed using the following formulae:
   
   .. math::

      \mu_{TIM|O} = \mu_{TIM} + \mu_{BIM} + \Sigma_{WTWO} \Sigma_{WOWO}^{-1} w_O

   .. math::

      \Sigma_{WTWT|O} = \Sigma_{WTWT} - \Sigma_{WTWO} \Sigma_{WOWO}^{-1} \Sigma_{WOWT}

We can assume that the ground shaking for the various IMs are multivariate random variables, and these two parameters can be used to randomly sample cross-spatially correlated ground motion fields conditioned on the observations.

In addition to the generation of cross-spatially correlated ground motion fields conditioned on data from seismic stations, it is also possible to constrain the resulting ground shaking based on observational data usually characterized using macroseismic intensity. This option can be advantageous for regions with poor seismic networks or when considering older events for which strong motion data might also be limited. This process requires the conversion of macroseismic intensity into ground motion, which will inevitably introduce additional uncertainty. As a result, the ground shaking converted from macroseismic intensity will be represented not only by a single value (as done when a seismic station is used) but by a mean and standard deviation. This variability can be taken from the chosen conversion equation. The incorporation of macroseismic intensity in this procedure has also been implemented within the OpenQuake engine. Additional details about the mathematical formulation of this procedure can be found in Worden et al. (2018).

Correlation models
------------------

The within-event and between-event correlation models used for conditioning
are selected with ``within_event_correlation_model`` and
``between_event_correlation_model``. A within-event model can describe spatial
correlation only or directly describe joint spatial and cross-IMT correlation.
The latter avoids assuming that spatial and cross-IMT dependence are separable.
See :doc:`correlation-models` for the model interfaces and configuration.

For compatibility, a spatial-only model is currently combined with a fixed
Baker and Jayaram (2008) cross-IMT model using a separable approximation. Since
Baker and Jayaram (2008) describes total-residual rather than within-event
correlation, this is a legacy approximation rather than a direct model of the
required covariance. A direct joint model bypasses that approximation.

The model library currently has a limited selection for station-conditioned,
multi-IMT calculations. Direct spatial-cross-IMT models should be used when
available because they provide the complete target-to-observation covariance
without the separable legacy approximation.

Nominal bias in the joint formulation
-------------------------------------

The partitioned formulation of Engler et al. (2022) first computes the
posterior distribution of the normalized between-event residual. Let
:math:`H` denote that residual, let :math:`T_D` and :math:`T_Y` scale it by
the appropriate GSIM :math:`\tau` values at the observations and targets,
and let :math:`\zeta_D = y_D - \mu_D`. The posterior mean is

.. math::

   \widehat H = \Sigma_{HH} T_D^{\mathsf T} \Sigma_D^{+} \zeta_D,

where

.. math::

   \Sigma_D = \Sigma_{W_DW_D} +
              T_D \Sigma_{HH} T_D^{\mathsf T}.

Observation-error variance, when present, is included in
:math:`\Sigma_{W_DW_D}`. The target-specific shift
:math:`T_Y\widehat H` is the analogue of the *nominal bias*. The scalar
``nominal_bias_mean`` reported by the historical implementation is only a
summary obtained by averaging the corresponding station shifts; the actual
mean calculation uses the full target term.

The partitioned conditional mean is

.. math::

   \mu_{Y|D} = \mu_Y + T_Y\widehat H +
   \Sigma_{W_YW_D}\Sigma_{W_DW_D}^{+}
   (\zeta_D - T_D\widehat H).

The OpenQuake engine's joint path absorbs the same between-event shift and the
within-event kriging adjustment into one regression:

.. math::

   \mu_{Y|D} = \mu_Y +
   (\Sigma_{W_YW_D} + T_Y\Sigma_{HH}T_D^{\mathsf T})
   \Sigma_D^{+}\zeta_D.

For nonsingular, or compatible singular, covariance systems these expressions
are algebraically equivalent. The nominal-bias effect is therefore retained,
although the joint path does not expose a separately labelled posterior
between-event field or scalar bias statistic.

Scalable conditional simulation
--------------------------------

Direct sampling from the conditional covariance in Step 7 requires a dense
matrix whose dimensions are the number of targets multiplied by the number of
IMTs. This is retained as a reference for small calculations but is infeasible
for realistic regional grids.

For sufficiently large regular grids and compatible joint models, the engine
therefore uses circulant embedding to generate an unconditional target field
and Matheron substitution to condition it. Paired unconditional values are
generated at the target grid and station locations; the difference between
the observed and simulated station values is then propagated to the target
field with the same covariance weights used for the conditional mean. This
applies the conditional-Gaussian transform without forming its dense target
covariance.

This follows the same broad strategy used by Engler et al. (2025) for
post-earthquake impact modelling: generate an unconditional within-event
field with circulant embedding and condition it on the observations through
kriging. The OpenQuake engine expresses the complete between- and within-event
update as the joint Matheron substitution above, rather than realizing the
conditional components in separate stages.

Stations that coincide with grid cells share their simulated values exactly.
Off-grid stations use the fourth-order local-kriging approximation proposed by
Bailey et al. (2022). Stations occupying the same grid box are simulated
jointly across all IMTs, while conditional errors belonging to different grid
boxes are treated as independent. Regression weights and GMFs are processed
in batches governed by ``memory.conditioned_gmf_gb``.

``DuNing2021`` is currently enabled for this scalable joint path. Other joint
models retain dense sampling until their structured embeddings have been
validated.

The scalable joint path currently supports untruncated Gaussian conditioning.
Finite truncated multivariate-normal sampling is not available for joint
spatial-cross-IMT conditioning.


References
----------

- Worden, C. B., Thompson, E. M., Hearne, M. G., & Wald, D. J. (2020). ShakeMap Manual Online: technical manual, user’s guide, and software guide. U.S. Geological Survey. URL: http://usgs.github.io/shakemap/. DOI: https://doi.org/10.5066/F7D21VPQ.

- Wald, D. J., Worden, C. B., Thompson, E. M., & Hearne, M. G. (2022). ShakeMap operations, policies, and procedures. Earthquake Spectra, 38(1), 756–777. DOI: https://doi.org/10.1177/87552930211030298.

- Silva, V., & Horspool, N. (2019). Combining USGS ShakeMaps and the OpenQuake-engine for damage and loss assessment. Earthquake Engineering and Structural Dynamics, 48(6), 634–652. DOI: https://doi.org/10.1002/eqe.3154.

- Engler, D. T., Worden, C. B., Thompson, E. M., & Jaiswal, K. S. (2022). Partitioning Ground Motion Uncertainty When Conditioned on Station Data. Bulletin of the Seismological Society of America, 112(2), 1060–1079. DOI: https://doi.org/10.1785/0120210177.

- Engler, D. T., Jaiswal, K. S., & Ganesh, M. (2025). Evaluating the impact of uncertainty in ground motion forecasts for post-earthquake impact modeling applications. Earthquake Spectra, 41(1), 524–546. DOI: https://doi.org/10.1177/87552930241283201.

- Bailey, M. D., Bandyopadhyay, S., Nychka, D. W., Thompson, E. M., & Worden, C. B. (2022). Adapting conditional simulation using circulant embedding for irregularly spaced spatial data. Stat, 11(1), e446. DOI: https://doi.org/10.1002/sta4.446.
