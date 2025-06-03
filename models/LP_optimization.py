# models/lp_optimizer.py
import cvxpy as cp
import numpy as np
import pandas as pd


class LPBasedSimulator:
    """
    Linear programming-based simulator for battery energy storage systems with optional PV and load inputs.

    Attributes:
        capacity (float): Total energy capacity in MWh.
        max_power (float): Maximum charge/discharge power in MW.
        efficiency (float): Round-trip efficiency (0 < efficiency <= 1).
        degradation_cost (float): Cost per MWh due to battery degradation.
        grid_fee (float): Grid usage fee per MWh.
        pv_series (pd.Series): Optional time-indexed series of PV generation in MW.
        load_series (pd.Series): Optional time-indexed series of load demand in MW.
        soc (float): Current state of charge in MWh.
        results (list): List of dictionaries containing simulation results per timestep.
    """

    def __init__(
        self,
        capacity_mwh,
        power_mw,
        efficiency,
        degradation_cost_per_mwh,
        grid_fee_per_mwh,
        pv_series=None,
        load_series=None,
        **kwargs,
    ):
        """
        Initialize the simulator with technical parameters and optional PV/load profiles.

        Args:
            capacity_mwh (float): Energy storage capacity in MWh.
            power_mw (float): Max charge/discharge power in MW.
            efficiency (float): Round-trip energy efficiency (0-1).
            degradation_cost_per_mwh (float): Cost of degradation per MWh throughput.
            grid_fee_per_mwh (float): Cost of using the grid per MWh.
            pv_series (pd.Series, optional): Time-indexed PV generation profile.
            load_series (pd.Series, optional): Time-indexed load profile.
            **kwargs: Ignored keyword arguments for future extensions.
        """
        self.capacity = capacity_mwh
        self.max_power = power_mw
        self.efficiency = efficiency
        self.degradation_cost = degradation_cost_per_mwh
        self.grid_fee = grid_fee_per_mwh
        self.pv_series = pv_series
        self.load_series = load_series
        self.soc = 0.5 * capacity_mwh
        self.results = []

    def reset(self):
        """
        Reset the state of charge to 50% and clear all simulation results.
        """
        self.soc = 0.5 * self.capacity
        self.results = []

    def simulate_day(self, day_prices: pd.DataFrame):
        """
        Simulate one day of operation using linear programming optimization.

        Args:
            day_prices (pd.DataFrame): Price data for the day with 'price_eur_per_mwh' and 'timestamp' columns.

        Raises:
            ValueError: If the optimization problem fails to find a solution.
        """
        n = len(day_prices)
        dt = 0.25  # 15 min in hours (Converting)

        # Input price and optionally PV and load
        prices = day_prices["price_eur_per_mwh"].values
        pv = (
            self.pv_series.loc[day_prices.index].values
            if self.pv_series is not None
            else np.zeros(n)
        )
        load = (
            self.load_series.loc[day_prices.index].values
            if self.load_series is not None
            else np.zeros(n)
        )

        # Decision variables
        export_pv_to_grid = cp.Variable(n, nonneg=True)
        charge_from_pv = cp.Variable(n, nonneg=True)
        charge_from_grid = cp.Variable(n, nonneg=True)
        charge = charge_from_pv + charge_from_grid

        discharge = cp.Variable(n, nonneg=True)
        soc = cp.Variable(n + 1)

        constraints = [soc[0] == self.soc]
        for t in range(n):
            net_surplus = pv[t] - load[t]  # +ve = excess energy, -ve = net demand
            surplus = max(pv[t] - load[t], 0)

            constraints += [
                soc[t + 1]
                == soc[t]
                + charge[t] * self.efficiency * dt
                - discharge[t] / self.efficiency * dt,  # SoC at every stage
                charge_from_pv[t] + export_pv_to_grid[t]
                <= surplus,  # Capacity constraint for PV, total energy used or sold not exceed surplus energy
                charge_from_grid[t]
                <= self.max_power
                * dt,  # Energy from grid should not exceed maximum battery charge level per interval
                charge[t]
                <= self.max_power
                * dt,  # Total charges from all sources should not exceed maximum battery charge level per interval
                discharge[t]
                <= self.max_power
                * dt,  # Total discharges from all sources should not exceed maximum battery charge level per interval
                soc[t + 1] >= 0,  # SoC should never be negative
                soc[t + 1] <= self.capacity,  # SoC should not exceed capacity
            ]

            # Limit charging from grid if PV surplus is available
            if net_surplus > 0:
                constraints.append(charge[t] <= net_surplus)

            # If there's net load, battery can serve it partially
            if load[t] > 0:
                constraints.append(discharge[t] <= load[t])

        degradation = cp.multiply(self.degradation_cost, charge + discharge)
        grid_cost = cp.multiply(charge_from_grid, prices + self.grid_fee)
        revenue = cp.multiply(discharge * self.efficiency, prices)
        pv_export_revenue = cp.multiply(export_pv_to_grid, prices)

        profit = cp.sum(revenue + pv_export_revenue - grid_cost - degradation)
        problem = cp.Problem(cp.Maximize(profit), constraints)

        problem.solve(solver=cp.ECOS, feastol=1e-6, abstol=1e-4, reltol=1e-4)

        if problem.status != cp.OPTIMAL:
            raise ValueError("LP optimization failed.")

        self.soc = soc.value[-1]
        for i in range(n):
            action = (
                "charge"
                if charge.value[i] > 1e-5
                else "discharge" if discharge.value[i] > 1e-5 else "idle"
            )

            from_pv = charge_from_pv.value[i]
            from_grid = charge_from_grid.value[i]
            to_load = min(discharge.value[i], load[i])
            to_grid = max(discharge.value[i] - to_load, 0)

            self.results.append(
                {
                    "timestamp": day_prices.iloc[i]["timestamp"],
                    "price_eur_per_mwh": prices[i],
                    "soc": soc.value[i + 1],
                    "action": action,
                    "charge_mwh": charge.value[i],
                    "discharge_mwh": discharge.value[i],
                    "from_pv_mwh": from_pv,
                    "from_grid_mwh": from_grid,
                    "to_load_mwh": to_load,
                    "to_grid_mwh": to_grid,
                    "pv_export_mwh": export_pv_to_grid.value[i],
                }
            )

    def run_simulation(self, price_df):
        """
        Run simulation over all days in the provided price DataFrame.

        Args:
            price_df (pd.DataFrame): Time-series price data with a 'timestamp' column.
        """
        for day, group in price_df.groupby(price_df["timestamp"].dt.date):
            self.simulate_day(group)

    def to_dataframe(self):
        """
        Convert simulation results into a pandas DataFrame.

        Returns:
            pd.DataFrame: A DataFrame where each row represents a timestep's results.
        """
        return pd.DataFrame(self.results)
