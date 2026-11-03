# What the public Python portfolio demonstrates from the BSc thesis

This independent repository accompanies the author's final BSc Physics thesis, *La tormenta geomagnética de mayo de 2024* (Universidad de Granada, 2024/25). The final thesis is a **real-data study**; this GitHub is a **fictional, reproducible Python teaching/portfolio workflow**, not the original scientific dataset, its charts or a substitute for the submitted thesis.

| Research workflow in original thesis (chapter 3) | Public synthetic evidence | Scope |
|---|---|---|
| Magnetic H/X/Y/Z and derived D/I (pp. 19, 24–25, 30–32) | [`analysis.py`](../src/geomag_demo/analysis.py), [`synthetic_component_latitude.svg`](../figures/synthetic_component_latitude.svg), [`synthetic_declination_latitude_time.svg`](../figures/synthetic_declination_latitude_time.svg) | Illustrative computation and visualization; not data from Ebro, San Pablo, NEW/HLP or WNG/KMH |
| Spectral study and comparison of frequency power (pp. 19–22) | [`synthetic_spectrogram.svg`](../figures/synthetic_spectrogram.svg), [`spectrogram.py`](../src/geomag_demo/spectrogram.py) | Correct gap-aware STFT, two fictional example stations, not the thesis's actual four-observatory spectra |
| Event phases, time series, missing data (pp. 22–30) | [`synthetic_time_series.svg`](../figures/synthetic_time_series.svg), [`synthetic_daily_ranges.svg`](../figures/synthetic_daily_ranges.svg), IAGA-style validation | Illustrates response and data quality, **not** real historical onset/main/recovery timing or identical phase-marker algorithms |
| Dependence of H, X, Y, Z on geographic latitude (pp. 30–32) | [`synthetic_component_latitude.svg`](../figures/synthetic_component_latitude.svg) | Peak absolute deviations vs synthetic 9 May daily mean; signed geographic latitude preserved |
| Dependence on longitude and observatory altitude (pp. 32–34) | [`synthetic_longitude_altitude.svg`](../figures/synthetic_longitude_altitude.svg) | Longitude and **explicitly invented** elevation covariate. No physical lack-of-effect conclusion |
| 3D geographic distribution (pp. 34–35) | [`synthetic_zonal_globe.svg`](../figures/synthetic_zonal_globe.svg), [`synthetic_vector_globe.svg`](../figures/synthetic_vector_globe.svg), [offline interactive globe](../figures/interactive_synthetic_globe.html) | Station-supported geometry without invalid global field interpolation |
| H variations vs latitude/longitude **through time** (pp. 35–37) | [`synthetic_latitude_time_response.svg`](../figures/synthetic_latitude_time_response.svg), [`synthetic_longitude_time_response.svg`](../figures/synthetic_longitude_time_response.svg) | Six synthetic days; 9 May same-UTC-hour baseline; three-station-per-band quality threshold |
| D (declination) vs latitude/time (p. 37) | [`synthetic_declination_latitude_time.svg`](../figures/synthetic_declination_latitude_time.svg) | Angular differences in degrees, proper circular wrap and minimum-coverage screens |

## Two distinct baselines — do not conflate them

- The submitted thesis's geographic amplitude plots (Figs. 26–30) use **10 May extrema relative to a quiet-day daily mean from 8 May**.
- This self-contained public demo has no 8 May source day: its new component/longitude/elevation plots use a fully **artificial 9 May daily mean**. Its six-day latitude/longitude temporal heatmaps use **9 May same UTC-hour medians**. All three metrics are specified independently; their numerical outcomes are not directly comparable.

A fictional station's elevation is assigned by a deterministic integer formula and is **not** a model of true geomagnetic observations. Missing synthetic elevation entries are excluded rather than filled. In the actual archive, ambiguous zero-coded elevation must be checked before a physical statement can be made.

## What is *not* claimed

This GitHub does not reproduce the submitted thesis's exact Kp/NOAA graphics, third-party photographs, original station pair plots, four real multi-station spectrograms, full thesis PDF or the reported real storm-phase dates and correlation coefficients. The original thesis and experimental script archive remain separate from the public demonstration; physical results require source provenance, independent calibration and publication-rights review.

For a CV, describe the work as **a reproducible scientific Python portfolio inspired by the author's real-data Physics thesis**, not as a newly verified study of the 2024 storm or an original magnetic-field reconstruction.
