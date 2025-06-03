# Battery Optimization Strategy

This project explores and implements multiple strategies for battery optimization, including rule-based, threshold-based, and linear programming (LP) approaches. It provides a modular framework for simulation, evaluation, and sensitivity analysis of these strategies.

## 📁 Project Structure

```
battery_optimization_strategy-dev/
├── main.py                    # Main entry point
├── models/                   # Optimization strategies
│   ├── LP_optimization.py
│   ├── rule_based.py
│   ├── threshold_based.py
│   └── base_simulator.py     # Common simulation base
├── utils/                    # Utility functions
│   ├── plotting.py
│   └── utils.py
├── notebooks/                # Jupyter notebooks for analysis
│   ├── Battery_optimisation_strategy.ipynb
│   ├── EDA.ipynb
│   └── Sensitivity_Analysis.ipynb
└── .gitignore
```

## 🚀 Getting Started

### Prerequisites

Ensure you have Python 3.8+ installed.

1. **Install `uv` package manager**:
```bash
pip install uv
```

2. **Create a new environment using `uv`**:
```bash
uv venv
```

3. **Activate the environment**:
- On macOS/Linux:
```bash
source .venv/bin/activate
```
- On Windows:
```bash
.venv\Scripts\activate
```

4. **Install the required packages**:
```bash
uv pip install .
```

5. **Install ecos package separately**:
```
pip install ecos
```

*This project uses `pyproject.toml` to manage dependencies with `uv`.*

### Data Preparation

Ensure that all required input data is placed in the `data/` directory at the project root.

### Running the Project

#### Command-Line Arguments

The `main.py` script accepts the following argument:

- `--simulate`: *(optional)*  
  Run a new simulation instead of using saved results.

- `--data-path`: *(required)*  
  Path to the CSV file containing price data. Example: `data/Day-ahead_prices.csv`

- `--strategy`: *(required)*  
  Name of the strategy to simulate. Choices:
  - `Threshold-Based`
  - `Rule-Based`
  - `Linear-Programming`

#### Example Usage

```bash
python main.py --simulate \
               --data-path data/Day-ahead_prices.csv \
               --strategy Linear-Programming
```

## ⚙️ Optimization Models

- **Rule-Based Strategy:** Simple heuristics for charging/discharging based on predefined rules.
- **Threshold-Based Strategy:** Uses upper/lower thresholds for decision-making.
- **LP Optimization:** Applies Linear Programming to optimize energy storage/usage cost-effectively.

Each strategy is implemented in a modular fashion under `models/`.

## 📊 Notebooks

- `EDA.ipynb`: Exploratory Data Analysis of the input data.
- `Battery_optimisation_strategy.ipynb`: Demonstrates strategy simulations and visualizations.
- `Sensitivity_Analysis.ipynb`: Examines robustness of strategies to parameter variations.

## 📈 Visualizations

Custom plots and charts for performance evaluation are handled via `utils/plotting.py`.

## 📦 Utilities

Helper functions are available in `utils/utils.py` for common tasks like data handling, metrics, and logging.

## 🧠 Contributing

Contributions are welcome! Please fork the repo, create a feature branch, and submit a pull request.

To ensure code quality and consistency, this project uses **[pre-commit](https://pre-commit.com/)** for automatic code formatting and static checks.

## 🔧 Pre-commit Setup

1. **Install pre-commit** (once per machine):

   ```bash
   pip install pre-commit
   ```

2. **Install the Git hook** (once per repo):

   ```bash
   pre-commit install
   ```

3. **Run all checks manually** (optional):

   ```bash
   pre-commit run --all-files
   ```

This will automatically run formatters like `black`, `isort`, and type checks (`mypy`) before every commit. Please make sure all checks pass before pushing.

## 📝 License

This project is licensed under the MIT License — see the [LICENSE](LICENSE) file for details.