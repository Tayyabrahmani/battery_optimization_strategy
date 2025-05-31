# models/lp_optimizer.py
import pandas as pd
import numpy as np
import cvxpy as cp

class LPBasedSimulator:
    def __init__(self, capacity_mwh, power_mw, efficiency, degradation_cost_per_mwh, grid_fee_per_mwh):
        self.capacity = capacity_mwh
        self.max_power = power_mw
        self.efficiency = efficiency
        self.degradation_cost = degradation_cost_per_mwh
        self.grid_fee = grid_fee_per_mwh
        self.soc = 0.5 * capacity_mwh
        self.results = []

    def reset(self):
        self.soc = 0.5 * self.capacity
        self.results = []

    def simulate_day(self, day_prices: pd.DataFrame):
        n = len(day_prices)
        dt = 0.25  # 15 min in hours (Converting)

        charge = cp.Variable(n, nonneg=True)
        discharge = cp.Variable(n, nonneg=True)
        soc = cp.Variable(n+1)

        prices = day_prices['price_eur_per_mwh'].values

        constraints = [soc[0] == self.soc]
        for t in range(n):
            constraints += [
                soc[t+1] == soc[t] + charge[t] * self.efficiency * dt - discharge[t] / self.efficiency * dt,
                charge[t] <= self.max_power * dt,
                discharge[t] <= self.max_power * dt,
                soc[t+1] >= 0,
                soc[t+1] <= self.capacity
            ]

        degradation = cp.multiply(self.degradation_cost, charge + discharge)
        grid_cost = cp.multiply(charge, prices + self.grid_fee)
        revenue = cp.multiply(discharge * self.efficiency, prices)

        profit = cp.sum(revenue - grid_cost - degradation)
        problem = cp.Problem(cp.Maximize(profit), constraints)

        # problem.solve(solver=cp.ECOS, feastol=1e-4, abstol=1e-2, reltol=1e-2)
        problem.solve(solver=cp.ECOS, feastol=1e-6, abstol=1e-4, reltol=1e-4)
        
        if problem.status != cp.OPTIMAL:
            raise ValueError("LP optimization failed.")

        self.soc = soc.value[-1]
        for i in range(n):
            action = 'charge' if charge.value[i] > 1e-5 else 'discharge' if discharge.value[i] > 1e-5 else 'idle'
            self.results.append({
                'timestamp': day_prices.iloc[i]['timestamp'],
                'price_eur_per_mwh': prices[i],
                'soc': soc.value[i+1],
                'action': action,
                'charge_mwh': charge.value[i],
                'discharge_mwh': discharge.value[i],
            })

    def run_simulation(self, price_df):
        for day, group in price_df.groupby(price_df['timestamp'].dt.date):
            self.simulate_day(group)

    def to_dataframe(self):
        return pd.DataFrame(self.results)
