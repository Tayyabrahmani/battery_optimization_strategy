import argparse
import os
import pandas as pd
from utils.utils import (
    calculate_profit,
    save_results_to_csv,
    load_price_data,
    get_results_path,
)
from utils.plotting import plot_results
from models.threshold_based import ThresholdBasedSimulator
from models.LP_optimization import LPBasedSimulator
from models.rule_based import TimeWindowRuleBasedSimulator

import logging
from utils.logging_config import setup_logging

# Setup Logging
setup_logging(logging.DEBUG)
logger = logging.getLogger(__name__)

sim_config = {
    "capacity_mwh": 1.0,
    "power_mw": 0.5,
    "efficiency": 0.80,
    "degradation_cost_per_mwh": 0.01 * 1000,
    "grid_fee_per_mwh": 0.04 * 1000,
    "capacity_mw": 5,
    "peak_mw": 8,
}

sim_config["battery_cost_eur"] = sim_config["capacity_mw"] * 500 * 1000

simulator_configs = {
    "Threshold-Based": {"buy_threshold": 0.05, "sell_threshold": 0.95},
    "Rule-Based": {},
    "Linear-Programming": {},
}

def run_simulation(
    model_name,
    simulator_cls,
    price_data,
    sim_config,
    pv_series=None,
    load_series=None,
    rerun_simulation=False,
    **simulator_kwargs,
):
    logger.info(f"Running simulation: {model_name}")
    result_path = get_results_path(model_name)

    if not rerun_simulation and os.path.exists(result_path):
        result_df = pd.read_csv(result_path, parse_dates=["timestamp"])
        logger.info(f"Loaded cached results: {result_path}")

    else:
        filtered_config = {
            k: v for k, v in sim_config.items()
            if k in ['capacity_mwh', 'power_mw', 'efficiency', 'degradation_cost_per_mwh', 'grid_fee_per_mwh']
        }
        logger.debug(f"Filtered simulation config: {filtered_config}")
        logger.debug(f"Simulator kwargs: {simulator_kwargs}")

        sim = simulator_cls(
            pv_series=pv_series,
            load_series=load_series,
            **filtered_config,
            **simulator_kwargs,
        )
        sim.run_simulation(price_data)
        result_df = sim.to_dataframe()
        result_df = calculate_profit(
            df=result_df,
            efficiency=sim_config["efficiency"],
            degradation_cost_per_mwh=sim_config["degradation_cost_per_mwh"],
            grid_fee_per_mwh=sim_config["grid_fee_per_mwh"],
            pv_setup_cost_eur=sim_config.get("pv_setup_cost_eur", 0.0),
        )
        result_df['Model_Name'] = model_name
        save_results_to_csv(result_df, result_path)
        logger.info(f"Simulation complete. Results saved to {result_path}")

    fig = plot_results(result_df, title=f"{model_name} Operation")
    total_profit = result_df['cumulative_profit'].iloc[-1]
    logger.info(f"{model_name} Total Profit: €{total_profit:,.2f}")
    return result_df, fig


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--simulate",
        action="store_true",
        help="Run a new simulation (default: use saved results)",
    )
    parser.add_argument(
        "--data-path",
        type=str,
        required=True,
        help="Path to the CSV file containing price data",
    )
    parser.add_argument(
        "--strategy",
        type=str,
        choices=["Threshold-Based", "Rule-Based", "Linear-Programming"],
        required=True,
        help="Name of the strategy to simulate",
    )
    args = parser.parse_args()
    logger.info(f"Args received: {args}")

    # Registered strategies
    models = {
        "Threshold-Based": ThresholdBasedSimulator,
        "Rule-Based": TimeWindowRuleBasedSimulator,
        "Linear-Programming": LPBasedSimulator,
    }

    price_data = load_price_data(args.data_path)
    logger.debug(f"Loaded price data from {args.data_path}, shape: {price_data.shape}")

    model_name = args.strategy
    simulator_cls = models[model_name]
    result_path = f"results/{model_name.replace(' ', '_')}_results.csv"
    rerun = args.simulate or not os.path.exists(result_path)

    simulator_kwargs = simulator_configs.get(model_name, {})

    result_df, fig = run_simulation(
        model_name=model_name,
        simulator_cls=simulator_cls,
        price_data=price_data,
        sim_config=sim_config,
        rerun_simulation=rerun,
        **simulator_kwargs,
    )

    fig.show()
    logger.info("Simulation complete and figure shown")

if __name__ == "__main__":
    main()
