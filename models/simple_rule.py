from .base_simulator import BatterySimulator

class RuleBasedSimulator(BatterySimulator):
    def simulate_day(self, day_prices):
        soc = self.soc
        daily_profit = 0.0
        q25 = day_prices['price_eur_per_kwh'].quantile(0.25)
        q75 = day_prices['price_eur_per_kwh'].quantile(0.75)

        for _, row in day_prices.iterrows():
            price = row['price_eur_per_kwh']
            timestamp = row['timestamp']
            action, profit = 'idle', 0.0

            if price < q25:
                energy = min(self.max_power * 0.25, self.capacity - soc)
                soc += energy * self.efficiency
                cost = energy * price + energy * self.grid_fee + energy * self.degradation_cost
                profit = -cost
                action = 'charge'
            elif price > q75:
                energy = min(self.max_power * 0.25, soc)
                soc -= energy
                revenue = energy * price * self.efficiency - energy * self.degradation_cost
                profit = revenue
                action = 'discharge'

            daily_profit += profit
            self.results.append({
                'timestamp': timestamp,
                'price': price,
                'soc': soc,
                'action': action,
                'profit': daily_profit
            })
        self.soc = soc
