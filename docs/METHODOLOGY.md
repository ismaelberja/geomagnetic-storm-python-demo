# Scientific methodology, synthetic provenance and limits

**This project is a software demonstration, not a geophysical research result.** Every coordinate, station identifier, X/Y/Z value and data gap is constructed mathematically. The 9–15 May 2024 labels are convenient test timestamps; the series are not measurements of the 2024 storm, and none of the original scientific thesis files have been copied.

## Data generation

- **56 fabricated stations** named `SIM-001` to `SIM-056`, distributed deterministically across northern and southern geographic latitudes. No station matches a real IAGA name or uses a curated real observatory position list.
- X points **geographic north**, Y **geographic east** and Z **down**, in illustrative nT. The background values are trigonometric equations of latitude, longitude and UTC minute, with a fabricated transition on 10 May.
- A deliberately complete missing day for `SIM-002` on 13 May; a 45-minute gap for `SIM-007` on 11 May; and missing 17:00–18:00 samples for `SIM-012` and `SIM-037` on 10 May. Every missing component is treated as absent (sentinel `99999.0` in exported minute fixtures). No zeros are inserted, and no interpolation is applied.
- All pseudo-data use deterministic formulas in [`synthetic.py`](../src/geomag_demo/synthetic.py), with no random seeds or network calls. Generated `*.min` files are **not versioned** and are ignored by Git.

## Time comparison

Each valid fictional station contributes its own components at the **same UTC minute** on two artificial dates:

- `H(t) = sqrt(X(t)^2 + Y(t)^2)`
- `F(t) = sqrt(X(t)^2 + Y(t)^2 + Z(t)^2)`
- `ΔH(t) = H(10 May, t UTC) − H(9 May, t UTC)`
- `ΔB = (ΔX, ΔY, ΔZ)`, `|ΔB| = sqrt(ΔX² + ΔY² + ΔZ²)`

The same-time comparison is an algorithmic demonstration. It does **not** prove causal attribution, field calibration, storm intensity or timing.

## Spectral example: short-time Fourier transform (STFT)

The additional [spectrogram](../figures/synthetic_spectrogram.svg) is **100% artificial**. For the fictional stations `SIM-001` and `SIM-012`, the signal is the generator's own **H(10 May) − H(9 May)** at each matching UTC minute, **plus two *explicitly injected* oscillations** whose frequency-bin centres are **2.34375 and 4.296875 mHz**. Their amplitudes are multiplied by a fictional envelope peaking near 18:30 UTC. These waves were introduced specifically for this signal-processing tutorial; they were **not observed**, are **not present** in the other gallery figures or the fictional station `.min` fixture, and must not be used for physical interpretation.

- Sampling rate: **one sample per 60 seconds**, so the Nyquist frequency is **8.333 mHz**.
- STFT: **128 contiguous minutes** per Hann-tapered window, evaluated every **20 minutes**, using an explicitly implemented, standard-library **radix-2 FFT**.
- Prior to each transform, subtract the best-fitting straight line in the 128 samples; the aim is to reduce slowly varying baselines before visualizing the injected oscillations.
- One-sided periodogram: for interior positive-frequency bin *k*, `PSD[k] = 2 |FFT(Hann × detrended signal)[k]|² / (fs × Σ Hann²)`, with `fs = 1/60 Hz`. This has units **nT²/Hz**. The heatmap shows **10·log10(PSD / (1 nT²/Hz))**, with fixed display scaling across stations; the colour scale is not a standardized geomagnetic index.
- **Strict gap rejection:** *any* absent UTC minute in the entire 128-minute window invalidates that STFT column. `SIM-012` deliberately lacks readings 17:00–18:00 UTC, creating a hatched area broader than the one-hour outage because each invalid analysis window overlaps it. No values are set to zero, joined or interpolated.
- The 128-minute window has approximate Fourier-bin spacing `1/(128×60) = 0.1302 mHz`; its finite time resolution means this is **not** a precise measurement of the event onset. The 0–24-hour x-axis is the fictional UTC date and the y-axis is frequency in **mHz**.

The power patterns and transients are designed to teach **reproducible spectral processing, missing-data safety and plot interpretation**, not to reproduce a real INTERMAGNET or Kyoto spectrogram.

## Geographic zones and 3D rendering

- Geographic latitude remains **signed**, from −90° to +90°; longitude is between −180° and +180°.
- Thirty-degree latitude bands crossed with sixty-degree longitude bands make **36 fixed cells**. Each cell's median ΔH is shown as a coloured tile only if **at least two** distinct fictional stations fall inside that cell. Single-station cells are points without a shaded region; zero-station cells remain empty.
- The static globes use an **orthographic projection** and finite clipped polygons. Spheres and meridians are graphic aids, not data. The stations' arrows use an explicitly calculated local north/east/down basis, projected onto the screen. **Arrow length is normalized**, so the graphic encodes vector direction and illustrative magnitude colours, not physical field-line trajectories.
- The [interactive viewer](../figures/interactive_synthetic_globe.html) contains HTML, CSS, JavaScript and synthetic point samples inline. It works without CDN, online maps, external geospatial tiles or telemetry.

## Validity checks and reproducibility

The built-in unittest suite exercises duplicate minute stamps, day-of-year validation, source format and fictional-provenance enforcement, missing values, scalar/vector arithmetic, hemisphere positioning, zone data sufficiency, SVG parsing, self-contained HTML and README image links. The GitHub Actions matrix runs on Python 3.11 and 3.12 and **rebuilds the complete gallery in a scratch directory**, byte-comparing its results to committed outputs.

To reconstruct the charts:

```bash
python scripts/build_gallery.py
```

To create complete fictional IAGA-style training files locally:

```bash
python scripts/generate_iaga_demo.py
```

The latter creates 3 fictional stations × 7 UTC days × 1,440 minute rows under a fresh `outputs/FICTIONAL_XYZ_...` folder. It never needs the private thesis archive.

## What's not included

There are **no INTERMAGNET observations, original thesis programs, images, real 2024 Dst or Kp index files, original observatory coordinates, real-data-derived plots or numeric source tables**. The MIT license in this new demonstration does not cover any separate scientific thesis material or source observations.
