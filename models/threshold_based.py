from models.base_simulator import BatterySimulator


class ThresholdBasedSimulator(BatterySimulator):
    """
    Threshold-based simulator for battery operation using quantile-based price thresholds.

    Attributes:
        buy_threshold (float): Quantile (0-1) below which prices trigger charging.
        sell_threshold (float): Quantile (0-1) above which prices trigger discharging.
        pv_series (pd.Series): Optional time-indexed PV generation profile.
        load_series (pd.Series): Optional time-indexed load demand profile.
    """

    def __init__(
        self,
        buy_threshold=0.15,
        sell_threshold=0.85,
        pv_series=None,
        load_series=None,
        *args,
        **kwargs,
    ):
        """
        Initialize the simulator with price thresholds and optional PV/load profiles.

        Args:
            buy_threshold (float): Lower price quantile to trigger charging.
            sell_threshold (float): Upper price quantile to trigger discharging.
            pv_series (pd.Series, optional): PV generation indexed by timestamp.
            load_series (pd.Series, optional): Load profile indexed by timestamp.
            *args, **kwargs: Passed to the BatterySimulator base class.
        """
        super().__init__(*args, **kwargs)
        self.pv_series = pv_series
        self.load_series = load_series
        self.buy_threshold = buy_threshold
        self.sell_threshold = sell_threshold

    def simulate_day(self, day_prices):
        """
        Simulate a day's operation by charging/discharging based on dynamic price thresholds.

        - Charge when price is below the buy quantile threshold.
        - Discharge when price is above the sell quantile threshold.
        - Otherwise remain idle, serving load from PV and exporting any surplus.

        Args:
            day_prices (pd.DataFrame): DataFrame with 'price_eur_per_mwh' and 'timestamp' columns.
        """
        soc = self.soc
        buy_threshold = day_prices["price_eur_per_mwh"].quantile(self.buy_threshold)
        sell_threshold = day_prices["price_eur_per_mwh"].quantile(self.sell_threshold)

        for ts, row in day_prices.iterrows():
            price = row["price_eur_per_mwh"]
            timestamp = row["timestamp"]
            pv = self.pv_series.loc[ts] if self.pv_series is not None else 0.0
            load = self.load_series.loc[ts] if self.load_series is not None else 0.0

            action = "idle"
            charge_mwh = discharge_mwh = 0.0
            from_pv = from_grid = to_load = to_grid = pv_export_mwh = 0.0

            if price < buy_threshold:
                available_capacity = self.capacity - soc
                max_charge = min(self.max_power * 0.25, available_capacity)
                surplus = max(pv - load, 0)
                from_pv = min(max_charge, surplus)
                from_grid = max_charge - from_pv
                charge_mwh = from_pv + from_grid
                soc += charge_mwh * self.efficiency
                action = "charge"
                pv_used = from_pv + min(load, pv)
                pv_export_mwh = max(pv - pv_used, 0)

            elif price > sell_threshold:
                max_discharge = min(self.max_power * 0.25, soc)
                to_load = min(max_discharge, load)
                to_grid = max_discharge - to_load
                discharge_mwh = to_load + to_grid
                soc -= discharge_mwh
                action = "discharge"
                pv_used = min(load, pv)
                pv_export_mwh = max(pv - pv_used, 0)

            else:
                pv_used = min(load, pv)
                pv_export_mwh = max(pv - pv_used, 0)

            self.results.append(
                {
                    "timestamp": timestamp,
                    "price_eur_per_mwh": price,
                    "soc": soc,
                    "action": action,
                    "charge_mwh": charge_mwh,
                    "discharge_mwh": discharge_mwh,
                    "from_pv_mwh": from_pv,
                    "from_grid_mwh": from_grid,
                    "to_load_mwh": to_load,
                    "to_grid_mwh": to_grid,
                    "pv_export_mwh": pv_export_mwh,
                }
            )
        self.soc = soc
