import pandas as pd


class BatterySimulator:
    """
    Base class for simulating battery energy storage behavior under varying electricity prices.

    Attributes:
        capacity (float): Total energy capacity of the battery in MWh.
        max_power (float): Maximum power (charge/discharge rate) in MW.
        efficiency (float): Round-trip efficiency of the battery (0 < efficiency <= 1).
        degradation_cost (float): Cost per MWh cycled through the battery due to degradation.
        grid_fee (float): Grid usage fee per MWh charged or discharged.
        soc (float): Current state of charge in MWh.
        results (list): Stores simulation results, each as a dictionary or record per time step.
    """

    def __init__(
        self,
        capacity_mwh,
        power_mw,
        efficiency,
        degradation_cost_per_mwh,
        grid_fee_per_mwh,
    ):
        """
        Initialize the BatterySimulator with technical and economic parameters.

        Args:
            capacity_mwh (float): Battery capacity in megawatt-hours.
            power_mw (float): Max power in megawatts.
            efficiency (float): Charging/discharging efficiency (0-1).
            degradation_cost_per_mwh (float): Cost of battery wear per MWh.
            grid_fee_per_mwh (float): Grid access fee per MWh.
        """
        self.capacity = capacity_mwh
        self.max_power = power_mw
        self.efficiency = efficiency
        self.degradation_cost = degradation_cost_per_mwh
        self.grid_fee = grid_fee_per_mwh
        self.soc = 0.5 * capacity_mwh
        self.results = []

    def reset(self):
        """
        Reset the battery state of charge to 50% and clear previous simulation results.
        """
        self.soc = 0.5 * self.capacity
        self.results = []

    def simulate_day(self, day_prices):
        """
        Abstract method to simulate battery operation for a single day.

        Args:
            day_prices (pd.DataFrame): DataFrame containing price signals for a single day.

        Raises:
            NotImplementedError: Must be implemented in subclasses.
        """
        raise NotImplementedError

    def run_simulation(self, price_df):
        """
        Run battery simulation over multiple days using a DataFrame of price data.

        Args:
            price_df (pd.DataFrame): DataFrame with a 'timestamp' column and price values.
        """
        for day, group in price_df.groupby(price_df["timestamp"].dt.date):
            self.simulate_day(group)

    def to_dataframe(self):
        """
        Convert simulation results to a pandas DataFrame.

        Returns:
            pd.DataFrame: Simulation results stored during the run.
        """
        return pd.DataFrame(self.results)
