# algeria24-training

Training materials for an ITU course provided as part of the following event focusing on network infrastructure analysis and planning:

[ITU Regional Workshop Towards Universal and Meaningful Connectivity for Arab Region](https://www.itu.int/en/ITU-D/Regional-Presence/ArabStates/Pages/Events/2024/MeaningfulConnectivity/MConn.aspx), Algiers – Algeria, 11-12 November 2024

<a href="https://ibb.co/ftvCtyQ"><img src="https://i.ibb.co/3Wz0Wjk/Screenshot-2024-11-11-at-10-01-42.png" alt="Screenshot-2024-11-11-at-10-01-42" border="0"></a>

_Figure: Fiber path simulation in Sidi Bel Abbès, Algeria_

## Overview

This repository contains Jupyter notebooks and supporting materials for analyzing and modeling network infrastructure in Algeria. The course covers data standardization, coverage analysis, fiber modeling, and cost estimation.

## Repository structure

- `0_eda_standardization.ipynb`: Data exploration and standardization procedures
- `1_proximity_coverage_demand.ipynb`: Analysis of coverage proximity and demand mapping
- `2_visibility_analysis.ipynb`: Visibility and line-of-sight analysis for network planning
- `3_fiber_modeling.ipynb`: Fiber network modeling and optimization
- `4_cost_modelling.ipynb`: Cost estimation and financial modeling
- `environment.yml`: Conda environment specification
- `.gitignore`: Git ignore rules for the project

## Pre-requisites

To run these notebooks on **Google Colab**, you'll need:
- A Google account (e.g. a Gmail account).

To run these notebooks **locally**, you'll need:

- Python 3.9
- Jupyter Notebook/Lab

## Setup instructions

### To run locally

1. Clone the repository:

```bash
git clone https://github.com/sg-peytrignet/algeria24-training.git
cd algeria24-training
```

2. Create and activate the Conda environment:

```bash
conda env create -f environment.yml
conda activate inframaptraining
```

3. Launch Jupyter:

```bash
jupyter lab
```

### To run on Google Colab

All notebooks are created using Google Colab for easy accessibility. In order to run them on [Google Colab](https://colab.research.google.com/), you will need to sign in with a Google account. If you are unfamiliar with Google Colab, please watch this [introductory video](https://www.youtube.com/watch?v=inN8seMm7UI).

1. Navigate to each notebook in the repository
2. At the top of each notebook, click on the **Open in Colab** button.

<a href="https://colab.research.google.com/github/sg-peytrignet/algeria24-training/blob/main/3_fiber_modeling.ipynb" target="_parent"><img src="https://colab.research.google.com/assets/colab-badge.svg" alt="Open In Colab"/></a>

## Usage notes

Follow the notebooks in numerical order for the best learning experience.

## Contributing

Please submit a pull request to contribute to this repository.

## License

Please refer to our [license](LICENSE).

## Contact

For questions or support, please create an issue in this repository or get in touch at fns@itu.int.

## Acknowledgements

We would like to thank South Korea's Ministry of Science and ICT for their support.

![sponsor](https://i.ibb.co/tXQqP2S/image.jpg)
