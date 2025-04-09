# Simple Meridian

<div align="center">
  <img src="./pic/Logo.png" alt="Simple Meridian Logo" width="200">
  <h3>Marketing Analytics Made Simple</h3>
  <p>Powerful marketing mix modeling with zero coding required</p>
  <p>
    <a href="#key-features">Features</a> •
    <a href="#how-it-works">How It Works</a> •
    <a href="#getting-started">Getting Started</a> •
    <a href="#data-requirements">Data Requirements</a> •
    <a href="#built-with">Built With</a>
  </p>
</div>
## Overview

Simple Meridian is a no-code application that makes powerful marketing analytics accessible to everyone. With just a few clicks, you can analyze your marketing effectiveness, understand which channels drive results, and optimize your budget allocation for maximum ROI.

<div align="center">
  <img src="./pic/app.png" alt="Application Screenshot" width="80%">
</div>
## Key Features

- **Zero Coding Required** — Upload your data and click through our intuitive interface
- **Automatic Data Analysis** — Built on Google's Meridian framework for reliable results
- **Channel Effectiveness** — See exactly which marketing channels drive the most value
- **Budget Optimization** — Get AI-powered recommendations to maximize your ROI
- **Interactive Visualizations** — Explore your data through beautiful charts and graphs
- **Shareable Reports** — Export professional reports to share with your team

## How It Works

<div align="center">
  <table>
    <tr>
      <td align="center"><img src="./pic/upload_icon.svg" width="60"><br><b>1. Upload & Run</b></td>
      <td align="center"><img src="./pic/insights_icon.svg" width="60"><br><b>2. Explore Insights</b></td>
      <td align="center"><img src="./pic/optimize_icon.svg" width="60"><br><b>3. Optimize Budget</b></td>
    </tr>
    <tr>
      <td>Upload your marketing data and run the analysis with a single click</td>
      <td>View interactive visualizations showing which channels perform best</td>
      <td>Get recommendations for ideal budget allocation across channels</td>
    </tr>
  </table>
</div>
## Getting Started

### Prerequisites

- Python 3.11+
- Streamlit 1.28.0+
- Google Meridian 1.0.6+
- Other dependencies listed in `requirements.txt`

### Installation

```bash
# Clone the repository
git clone https://github.com/alibb007/simple-meridian.git
cd simple-meridian

# Create virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Launch the app
streamlit run app.py
```

### Docker Installation

```bash
# Build the Docker image
docker build -t simple-meridian .

# Run the container
docker run -p 8501:8501 simple-meridian
```

## Data Requirements

For best results, your data should include:

- **Time Series Data** : Weekly or monthly periods (at least 6 months of data)
- **Target KPI** : Sales, revenue, or conversions you want to analyze
- **Marketing Channels** : Spend amounts and/or metrics (impressions, clicks, etc.)
- **Control Variables** (optional): Seasonality, pricing, promotions, etc.

A sample dataset is included to help you get started quickly.

## What is Marketing Mix Modeling?

Marketing Mix Modeling (MMM) is a statistical analysis technique that helps you understand how marketing activities affect your business results. Simple Meridian puts the power of MMM in your hands without requiring any coding or statistics knowledge.

Simple Meridian answers critical questions like:

- Which marketing channels drive the most sales?
- What's the ROI for each marketing activity?
- How should I allocate my budget for maximum results?
- What would happen if I shifted budget between channels?

## Built With

- [Streamlit](https://streamlit.io/) - The web framework
- [Google Meridian](https://developers.google.com/meridian) - Marketing Mix Modeling engine
- [TensorFlow](https://www.tensorflow.org/) - Machine learning framework
- [Plotly](https://plotly.com/) - Interactive visualizations

## License

This project is licensed under the MIT License - see the [LICENSE](https://claude.ai/chat/LICENSE) file for details.

## About the Developer

<div align="center">
  <img src="./pic/developer.png" alt="Ali Barfi Bafghi" width="100" style="border-radius: 50%;">
  <p>
    <b>Ali Barfi Bafghi</b><br>
    Data Scientist & Marketing Analytics Expert
  </p>
  <p>
    <a href="https://github.com/alibb007">GitHub</a> •
    <a href="https://www.linkedin.com/in/alibarfibafghi/">LinkedIn</a> •
    <a href="mailto:ali.barfib@gmail.com">Email</a>
  </p>
</div>
---

<div align="center">
  <p><i>Simple Meridian uses the open-source Google Meridian library. All rights and trademarks remain with Google.</i></p>
</div>
