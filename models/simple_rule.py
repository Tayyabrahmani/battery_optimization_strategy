from models.base_simulator import BatterySimulator

class RuleBasedSimulator(BatterySimulator):
    def __init__(self, buy_threshold=0.15, sell_threshold=0.85, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.buy_threshold = buy_threshold
        self.sell_threshold = sell_threshold

    def simulate_day(self, day_prices):
        soc = self.soc
        buy_threshold = day_prices['price_eur_per_mwh'].quantile(self.buy_threshold)
        sell_threshold = day_prices['price_eur_per_mwh'].quantile(self.sell_threshold)
        for _, row in day_prices.iterrows():
            price = row['price_eur_per_mwh']
            timestamp = row['timestamp']
            action = 'idle'
            charge_mwh = discharge_mwh = 0.0

            if price < buy_threshold:
                charge_mwh = min(self.max_power * 0.25, self.capacity - soc)
                soc += charge_mwh * self.efficiency
                action = 'charge'

            elif price > sell_threshold:
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
