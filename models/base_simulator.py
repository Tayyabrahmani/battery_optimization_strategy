import pandas as pd

class BatterySimulator:
    def __init__(self, capacity_mwh, power_mw, efficiency, degradation_cost_per_kwh, grid_fee_per_kwh):
        self.capacity = capacity_mwh
        self.max_power = power_mw
        self.efficiency = efficiency
        self.degradation_cost = degradation_cost_per_kwh
        self.grid_fee = grid_fee_per_kwh
        self.soc = 0.5 * capacity_mwh
        self.results = []

    def reset(self):
        self.soc = 0.5 * self.capacity
        self.results = []

    def simulate_day(self, day_prices):
        raise NotImplementedError

    def run_simulation(self, price_df):
        for day, group in price_df.groupby(price_df['timestamp'].dt.date):
            self.simulate_day(group)

    def to_dataframe(self):      
        return pd.DataFrame(self.results)
