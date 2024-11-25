import pandas as pd
import numpy as np
from typing import Dict, Tuple, List
from src.utils.data_loader import (
    load_bond_info,
    load_govt_rates,
    load_spread_data,
    load_all_bond_data,
)
from src.analysis.pv01_analysis import PV01Analysis


class StressTestAnalysis:
    def __init__(self):
        self.bond_info = load_bond_info()
        self.govt_rates = load_govt_rates()
        self.spreads = load_spread_data()
        self.bond_data = load_all_bond_data()

    def calculate_pv01(self) -> pd.DataFrame:
        pv01_analyzer = PV01Analysis()
        pv01_results = pv01_analyzer.calculate_portfolio_pv01()

        return pd.DataFrame(
            {
                "종목명": pv01_results["종목명"],
                "만기그룹": self.bond_info["만기그룹"],
                "PV01": pv01_results["PV01"],
                "발행액": pv01_results["발행액"],
            }
        )

    def parallel_shift_scenarios(self) -> Dict[str, float]:
        return {
            "baseline": 0.01,  # +100bp
            "bad": 0.02,  # +200bp
            "worst": 0.03,  # +300bp
        }

    def non_parallel_shift_scenarios(self) -> Dict[str, Dict[str, float]]:
        return {
            "short_term": {"1.0": 0.02, "2.0": 0.015, "3.0": 0.01},
            "medium_term": {"2.0": 0.02, "3.0": 0.015, "5.0": 0.01},
            "long_term": {"5.0": 0.015, "10.0": 0.01},
        }

    def calculate_scenario_losses(self) -> pd.DataFrame:
        pv01_data = self.calculate_pv01()
        results = []

        # Parallel shift scenarios
        for scenario, shift in self.parallel_shift_scenarios().items():
            for _, bond in pv01_data.iterrows():
                loss = -bond["PV01"] * shift * bond["발행액"]
                results.append(
                    {
                        "종목명": bond["종목명"],
                        "만기그룹": bond["만기그룹"],
                        "시나리오": f"parallel_{scenario}",
                        "손실액": loss,
                    }
                )

        # Non-parallel shift scenarios
        for scenario, shifts in self.non_parallel_shift_scenarios().items():
            for _, bond in pv01_data.iterrows():
                maturity_group = str(bond["만기그룹"]).split("년")[0]
                if maturity_group in shifts:
                    shift = shifts[maturity_group]
                    loss = -bond["PV01"] * shift * bond["발행액"]
                    results.append(
                        {
                            "종목명": bond["종목명"],
                            "만기그룹": bond["만기그룹"],
                            "시나리오": f"non_parallel_{scenario}",
                            "손실액": loss,
                        }
                    )

        return pd.DataFrame(results)

    def historical_stress_test(self) -> pd.DataFrame:
        covid_period = pd.to_datetime(["2020-03-01", "2020-05-31"])
        inflation_period = pd.to_datetime(["2022-01-01", "2022-12-31"])

        rates_df = self.govt_rates.set_index("일자")
        historical_changes = (
            rates_df[
                (
                    (rates_df.index >= covid_period[0])
                    & (rates_df.index <= covid_period[1])
                )
                | (
                    (rates_df.index >= inflation_period[0])
                    & (rates_df.index <= inflation_period[1])
                )
            ]["국고채권(3년)"]
            .pct_change(fill_method=None)
            .dropna()
        )

        pv01_data = self.calculate_pv01()
        results = []

        for period, label in [(covid_period, "covid"), (inflation_period, "inflation")]:
            period_changes = historical_changes[
                (historical_changes.index >= period[0])
                & (historical_changes.index <= period[1])
            ]
            max_change = period_changes.max()

            for _, bond in pv01_data.iterrows():
                loss = -bond["PV01"] * max_change * bond["발행액"]
                results.append(
                    {
                        "종목명": bond["종목명"],
                        "만기그룹": bond["만기그룹"],
                        "시나리오": f"historical_{label}",
                        "손실액": loss,
                    }
                )

        return pd.DataFrame(results)

    def calculate_var(
        self, confidence_levels: List[float] = [0.95, 0.99]
    ) -> pd.DataFrame:
        results = []

        for _, bond in self.bond_info.iterrows():
            series_code = bond["종목명"].split("우리금융지주")[1]
            price_changes = (
                self.bond_data[series_code]["채권평가사 평균가격_대비"]
                .pct_change(fill_method=None)
                .replace([np.inf, -np.inf], np.nan)
                .dropna()
            )

            for conf_level in confidence_levels:
                var = (
                    -np.percentile(price_changes, (1 - conf_level) * 100)
                    * bond["발행액"]
                )
                results.append(
                    {
                        "종목명": bond["종목명"],
                        "만기그룹": bond["만기그룹"],
                        "신뢰수준": conf_level,
                        "VaR": var,
                    }
                )

        return pd.DataFrame(results)

    def run_full_analysis(self) -> Tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame]:
        scenario_losses = self.calculate_scenario_losses()
        historical_losses = self.historical_stress_test()
        var_results = self.calculate_var()

        return scenario_losses, historical_losses, var_results


if __name__ == "__main__":
    analysis = StressTestAnalysis()
    scenario_losses, historical_losses, var_results = analysis.run_full_analysis()

    print("\nScenario Test Results:")
    print(scenario_losses)
    print("\nHistorical Stress Test Results:")
    print(historical_losses)
    print("\nVaR Analysis Results:")
    print(var_results)
