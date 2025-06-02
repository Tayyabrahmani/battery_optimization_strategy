from models.base_simulator import BatterySimulator
import pandas as pd

class TimeWindowRuleBasedSimulator(BatterySimulator):
    def __init__(self, pv_series=None, load_series=None, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.pv_series = pv_series
        self.load_series = load_series

    def simulate_day(self, day_prices: pd.DataFrame):
        soc = self.soc
        for _, row in day_prices.iterrows():
            timestamp = row['timestamp']
            hour = timestamp.hour
            price = row['price_eur_per_mwh']
            charge_mwh = discharge_mwh = 0.0
            action = 'idle'

            if 12 <= hour < 14:
                # Charging
                charge_mwh = min(self.max_power * 0.25, self.capacity - soc)
                soc += charge_mwh * self.efficiency
                action = 'charge'

            elif 19 <= hour < 21:
                # Discharging
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
