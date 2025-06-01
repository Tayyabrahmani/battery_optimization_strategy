# models/lp_optimizer.py
import pandas as pd
import numpy as np
import cvxpy as cp

class LPBasedSimulator:
    def __init__(self, capacity_mwh, power_mw, efficiency, degradation_cost_per_mwh, grid_fee_per_mwh, pv_series=None, load_series=None, **kwargs):
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
        self.soc = 0.5 * self.capacity
        self.results = []

    def simulate_day(self, day_prices: pd.DataFrame):
        n = len(day_prices)
        dt = 0.25  # 15 min in hours (Converting)

        # Input price and optionally PV and load
        prices = day_prices['price_eur_per_mwh'].values
        pv = self.pv_series.loc[day_prices.index].values if self.pv_series is not None else np.zeros(n)
        load = self.load_series.loc[day_prices.index].values if self.load_series is not None else np.zeros(n)

        # Decision variables
        charge_from_pv = cp.Variable(n, nonneg=True)
        charge_from_grid = cp.Variable(n, nonneg=True)
        charge = charge_from_pv + charge_from_grid

        discharge = cp.Variable(n, nonneg=True)
        soc = cp.Variable(n+1)

        constraints = [soc[0] == self.soc]
        for t in range(n):
            net_surplus = pv[t] - load[t]  # +ve = excess energy, -ve = net demand

            constraints += [
                soc[t + 1] == soc[t] + charge[t] * self.efficiency * dt - discharge[t] / self.efficiency * dt,
                charge_from_pv[t] <= max(pv[t] - load[t], 0),
                charge_from_grid[t] <= self.max_power * dt,
                charge[t] <= self.max_power * dt,
                discharge[t] <= self.max_power * dt,
                soc[t+1] >= 0,
                soc[t+1] <= self.capacity
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

        profit = cp.sum(revenue - grid_cost - degradation)
        problem = cp.Problem(cp.Maximize(profit), constraints)


        problem.solve(solver=cp.ECOS, feastol=1e-6, abstol=1e-4, reltol=1e-4)

        if problem.status != cp.OPTIMAL:
            raise ValueError("LP optimization failed.")

        self.soc = soc.value[-1]
        for i in range(n):
            action = 'charge' if charge.value[i] > 1e-5 else 'discharge' if discharge.value[i] > 1e-5 else 'idle'

            from_pv = min(charge.value[i], max(pv[i] - load[i], 0))
            from_grid = charge.value[i] - from_pv

            to_load = min(discharge.value[i], load[i])
            to_grid = max(discharge.value[i] - to_load, 0)

            self.results.append({
                'timestamp': day_prices.iloc[i]['timestamp'],
                'price_eur_per_mwh': prices[i],
                'soc': soc.value[i+1],
                'action': action,
                'charge_mwh': charge.value[i],
                'discharge_mwh': discharge.value[i],
                'from_pv_mwh': from_pv,
                'from_grid_mwh': from_grid,
                'to_load_mwh': to_load,
                'to_grid_mwh': to_grid                
            })

    def run_simulation(self, price_df):
        for day, group in price_df.groupby(price_df['timestamp'].dt.date):
            self.simulate_day(group)

    def to_dataframe(self):
        return pd.DataFrame(self.results)
