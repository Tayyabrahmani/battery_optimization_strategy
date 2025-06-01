import argparse
import os
import pandas as pd
from utils.utils import (
    calculate_profit,
    save_results_to_csv,
    load_price_data,
    plot_results,
    get_results_path,
)
from models.simple_rule import RuleBasedSimulator
from models.LP_optimization import LPBasedSimulator

sim_config = {
    "capacity_mwh": 1.0,
    "power_mw": 0.5,
    "efficiency": 0.80,
    "degradation_cost_per_mwh": 0.01 * 1000,
    "grid_fee_per_mwh": 0.04 * 1000,
    "pv_setup_cost_eur": 6000.0,
    "capacity_mw": 5,
    "peak_mw": 8,
}

simulator_kwargs = {"buy_threshold": 0.05, "sell_threshold": 0.96}


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
    print(f"Running simulation: {model_name}")
    result_path = get_results_path(model_name)

    if not rerun_simulation and os.path.exists(result_path):
        result_df = pd.read_csv(result_path, parse_dates=["timestamp"])
        print(f"Loaded cached results: {result_path}")

    else:
        sim = simulator_cls(
            pv_series=pv_series,
            load_series=load_series,
            **sim_config,
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
        save_results_to_csv(result_df, result_path)

    plot_results(result_df, title=f"{model_name} Operation")
    print(f"{model_name} Total Profit: €{result_df['cumulative_profit'].iloc[-1]:,.2f}")
    return result_df


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--simulate",
        action="store_true",
        help="Run a new simulation (default: use saved results)",
    )
    args = parser.parse_args()

    # Registered strategies
    models = {
        "Linear-Programming": LPBasedSimulator,
        "Rule-Based": RuleBasedSimulator,
    }

    price_data = load_price_data(
        "data/Day-ahead_prices_202301010000_202501010000_Quarterhour.csv"
    )

    for name, cls in models.items():
        result_path = f"results/{name.replace(' ', '_')}_results.csv"
        rerun = args.simulate or not os.path.exists(result_path)

        run_simulation(
            model_name=name,
            simulator_cls=cls,
            price_data=price_data,
            sim_config=sim_config,
            rerun_simulation=rerun,
            **simulator_kwargs,
        )


if __name__ == "__main__":
    main()
