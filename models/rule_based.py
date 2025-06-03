from models.base_simulator import BatterySimulator
import pandas as pd

class TimeWindowRuleBasedSimulator(BatterySimulator):
    def __init__(self, pv_series=None, load_series=None, buy_hours=[12, 14], sell_hours=[19, 21], *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.pv_series = pv_series
        self.load_series = load_series
        self.buy_hours = buy_hours
        self.sell_hours = sell_hours

    def simulate_day(self, day_prices: pd.DataFrame):
        soc = self.soc
        for ts, row in day_prices.iterrows():
            price = row['price_eur_per_mwh']
            timestamp = row['timestamp']
            pv = self.pv_series.loc[ts] if self.pv_series is not None else 0.0
            load = self.load_series.loc[ts] if self.load_series is not None else 0.0

            action = 'idle'
            charge_mwh = discharge_mwh = 0.0
            from_pv = from_grid = to_load = to_grid = pv_export_mwh = 0.0

            if self.buy_hours[0] <= timestamp.hour < self.buy_hours[1]:
                available_capacity = self.capacity - soc
                max_charge = min(self.max_power * 0.25, available_capacity)
                surplus = max(pv - load, 0)
                from_pv = min(max_charge, surplus)
                from_grid = max_charge - from_pv
                charge_mwh = from_pv + from_grid
                soc += charge_mwh * self.efficiency
                action = 'charge'
                pv_used = from_pv + min(load, pv)
                pv_export_mwh = max(pv - pv_used, 0)

            elif self.sell_hours[0] <= timestamp.hour < self.sell_hours[1]:
                max_discharge = min(self.max_power * 0.25, soc)
                to_load = min(max_discharge, load)
                to_grid = max_discharge - to_load
                discharge_mwh = to_load + to_grid
                soc -= discharge_mwh
                action = 'discharge'
                pv_used = min(load, pv)
                pv_export_mwh = max(pv - pv_used, 0)

            else:
                pv_used = min(load, pv)
                pv_export_mwh = max(pv - pv_used, 0)

            self.results.append({
                'timestamp': timestamp,
                'price_eur_per_mwh': price,
                'soc': soc,
                'action': action,
                'charge_mwh': charge_mwh,
                'discharge_mwh': discharge_mwh,
                'from_pv_mwh': from_pv,
                'from_grid_mwh': from_grid,
                'to_load_mwh': to_load,
                'to_grid_mwh': to_grid,
                'pv_export_mwh': pv_export_mwh,
            })

        self.soc = soc
