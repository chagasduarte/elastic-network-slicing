import csv
from pathlib import Path
import tempfile
import unittest

from scripts.paired_analysis import analisar


class PairedAnalysisTest(unittest.TestCase):
    def test_pareia_por_scenario_e_exporta_inferencia_ajustada(self):
        with tempfile.TemporaryDirectory() as tmp:
            run = Path(tmp)
            with (run / "todas_execucoes.csv").open("w", encoding="utf-8", newline="") as f:
                campos = ["topology", "load_level", "scenario_id", "algorithm",
                          "scope", "acceptance.acceptance_percent"]
                writer = csv.DictWriter(f, fieldnames=campos)
                writer.writeheader()
                for i, diferenca in enumerate((1.0, 2.0, 3.0)):
                    for algoritmo, valor in (("petic", 50.0), ("aco", 50.0 + diferenca),
                                             ("q-learning", 50.0), ("sa", 49.0)):
                        writer.writerow({"topology": "abilene", "load_level": "l6",
                                         "scenario_id": f"s{i}", "algorithm": algoritmo,
                                         "scope": "summary",
                                         "acceptance.acceptance_percent": valor})

            output = analisar(run, bootstrap=500, seed=1)
            with output.open(encoding="utf-8", newline="") as f:
                rows = list(csv.DictReader(f))
            self.assertEqual(len(rows), 3)
            aco = next(row for row in rows if row["algorithm"] == "aco")
            self.assertEqual(aco["n_scenarios"], "3")
            self.assertEqual(float(aco["mean_difference_pp"]), 2.0)
            self.assertGreater(float(aco["bootstrap_ci95_low"]), 0)
            self.assertGreaterEqual(float(aco["wilcoxon_holm"]), float(aco["wilcoxon_p"]))
            self.assertEqual(float(aco["rank_biserial"]), 1.0)


if __name__ == "__main__":
    unittest.main()
