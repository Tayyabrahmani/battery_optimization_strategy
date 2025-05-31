import argparse
from utils.utils import (
    calculate_profit,
    save_results_to_csv,
    load_price_data,
    plot_results,
)
from models.simple_rule import RuleBasedSimulator
from models.LP_optimization import LPBasedSimulator
from models.heuristic_optimizer import HeuristicOptimizerSimulator
from models.greedy_algorithm import GreedySimulator
import os
import pandas as pd

capacity_mwh = 1.0
power_mw = 0.5
efficiency = 0.80
degradation_cost_per_mwh = 0.01 / 1000
grid_fee_per_mwh = 0.04 / 1000


def run_simulation(model_name, simulator_cls, price_data):
    print(f"Running simulation: {model_name}")
    sim = simulator_cls(
        capacity_mwh=capacity_mwh,
        power_mw=power_mw,
        efficiency=efficiency,
        degradation_cost_per_mwh=degradation_cost_per_mwh,
        grid_fee_per_mwh=grid_fee_per_mwh,
    )
    sim.run_simulation(price_data)
    result_df = sim.to_dataframe()
    result_df = calculate_profit(
        df=result_df,
        efficiency=efficiency,
        degradation_cost_per_mwh=degradation_cost_per_mwh,
        grid_fee_per_mwh=grid_fee_per_mwh,
    )
    save_results_to_csv(result_df, model_name)
    return result_df


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--simulate",
        action="store_true",
        help="Run a new simulation (default: use saved results)",
    )
    args = parser.parse_args()

    # Registered strategies
    models = {
        # "Linear-Programming": LPBasedSimulator,
        # "Rule-Based": RuleBasedSimulator,
        # "Heuristic-Optimizer": HeuristicOptimizerSimulator,
        "Greedy-Simulator": GreedySimulator,
    }

    for name, cls in models.items():
        result_path = f"results/{name.replace(' ', '_')}_results.csv"
        if args.simulate or not os.path.exists(result_path):
            price_data = load_price_data(
                "data/Day-ahead_prices_202301010000_202501010000_Quarterhour.csv"
            )
            result_df = run_simulation(name, cls, price_data)
        else:
            result_df = pd.read_csv(result_path, parse_dates=["timestamp"])
            print(f"Loaded cached results: {result_path}")

        plot_results(result_df, title=f"{name} Operation")
        print(f"{name} Total Profit: €{result_df['cumulative_profit'].iloc[-1]:,.2f}")
