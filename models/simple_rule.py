from models.base_simulator import BatterySimulator

class RuleBasedSimulator(BatterySimulator):
    def simulate_day(self, day_prices):
        soc = self.soc
        q25 = day_prices['price_eur_per_mwh'].quantile(0.15)
        q75 = day_prices['price_eur_per_mwh'].quantile(0.85)
        for _, row in day_prices.iterrows():
            price = row['price_eur_per_mwh']
            timestamp = row['timestamp']
            action = 'idle'
            charge_mwh = discharge_mwh = 0.0
            revenue = cost = degradation = 0.0

            if price < q25:
                charge_mwh = min(self.max_power * 0.25, self.capacity - soc)
                soc += charge_mwh * self.efficiency
                action = 'charge'

            elif price > q75:
                discharge_mwh = min(self.max_power * 0.25, soc)
                soc -= discharge_mwh
                action = 'discharge'

            self.results.append({
                'timestamp': timestamp,
                'price_eur_per_mwh': price,
                'soc': soc,
                'action': action,
                'charge_mwh': charge_mwh,
                'discharge_mwh': discharge_mwh,
            })
        self.soc = soc
