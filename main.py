from utils.utils import load_price_data, plot_results
from models.simple_rule import RuleBasedSimulator

def run_simulation(model_name, simulator_cls):
    print(f"Running simulation: {model_name}")
    sim = simulator_cls(
        capacity_mwh=1.0,
        power_mw=0.5,
        efficiency=0.90,
        degradation_cost_per_kwh=0.01,
        grid_fee_per_kwh=0.04
    )
    sim.run_simulation(price_data)
    result_df = sim.to_dataframe()
    plot_results(result_df)
    print(f"{model_name} Total Profit: €", round(result_df['profit'].iloc[-1], 2))

if __name__ == "__main__":
    price_data = load_price_data("data/Day-ahead_prices_202301010000_202501010000_Quarterhour.csv")

    # Register strategies
    models = {
        "Rule-Based": RuleBasedSimulator
    }

    for name, cls in models.items():
        run_simulation(name, cls)

