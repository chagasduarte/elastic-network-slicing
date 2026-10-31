import csv
import json
import tempfile
import unittest
from pathlib import Path

from scripts import plots

NIVEIS = [{"name": "l1", "requests": 10, "multiplier": 1.0}, {"name": "l2", "requests": 20, "multiplier": 1.5}]
BASE = "acceptance.acceptance_percent"


def _linhas_sinteticas():
    linhas = []
    for nivel in ("l1", "l2"):
        for alg in plots.ALGORITMOS:
            det = alg == "petic"
            linha = {"topology": "abilene", "load_level": nivel, "algorithm": alg, "scope": "summary", "period": ""}
            linha[f"{BASE}.mean"] = "90.5"
            linha[f"{BASE}.stddev"] = "0.0" if det else "1.25"
            linha[f"{BASE}.ci95_low"] = "90.5" if det else "89.5"
            linha[f"{BASE}.ci95_high"] = "90.5" if det else "91.5"
            linha[f"{BASE}.count"] = "30"
            linhas.append(linha)
    return linhas


class TestFormatacao(unittest.TestCase):
    def test_virgula_decimal(self):
        self.assertEqual(plots.formatar_numero(97.5, 2), "97,50")
        self.assertEqual(plots.formatar_numero(0.0018735, 4), "0,0019")

    def test_ausente(self):
        self.assertEqual(plots.formatar_numero(None, 2), "--")

    def test_num_nan_e_vazio(self):
        self.assertIsNone(plots._num(""))
        self.assertIsNone(plots._num("nan"))
        self.assertEqual(plots._num("1.5"), 1.5)


class TestLeitura(unittest.TestCase):
    def test_le_apenas_summary(self):
        with tempfile.TemporaryDirectory() as d:
            caminho = Path(d) / "a.csv"
            with open(caminho, "w", newline="") as f:
                w = csv.DictWriter(f, fieldnames=["topology", "scope", "x.mean"])
                w.writeheader()
                w.writerow({"topology": "a", "scope": "summary", "x.mean": "1"})
                w.writerow({"topology": "a", "scope": "period", "x.mean": "2"})
            linhas = plots.ler_agregados(caminho)
        self.assertEqual(len(linhas), 1)
        self.assertEqual(plots.estatistica(linhas[0], "x")["mean"], 1.0)
        self.assertIsNone(plots.estatistica(linhas[0], "x")["stddev"])


class TestSaidas(unittest.TestCase):
    def test_figura_pdf(self):
        with tempfile.TemporaryDirectory() as d:
            destino = Path(d) / "f.pdf"
            plots.figura_metrica(_linhas_sinteticas(), NIVEIS, ["abilene"], BASE, "Aceitação (%)", False, destino)
            dados = destino.read_bytes()
            plots.figura_metrica(_linhas_sinteticas(), NIVEIS, ["abilene"], BASE, "Aceitação (%)", False, destino)
            self.assertEqual(dados, destino.read_bytes())  # reprodutível
        self.assertTrue(dados.startswith(b"%PDF"))

    def test_tabela_latex(self):
        tex = plots.tabela_latex(_linhas_sinteticas(), NIVEIS, "abilene", "aceitacao", "results/x/todos_agregados.csv")
        self.assertIn("\\label{tab:aceitacao-abilene}", tex)
        self.assertIn("\\fonte{Elaborado pelo autor.}", tex)
        self.assertIn("% fonte: results/x/todos_agregados.csv, colunas acceptance.acceptance_percent.mean", tex)
        self.assertIn("90,50 $\\pm$ 1,25", tex)
        self.assertIn("[89,50; 91,50]", tex)

    def test_tabela_por_periodo_separa_aceitacao_e_banda(self):
        row = {"topology": "abilene", "load_level": "l6", "algorithm": "petic",
               "period": "t1", "acceptance.acceptance_percent.mean": "92.5",
               "bandwidth.served_percent.mean": "92.1"}
        tex = plots.tabela_periodos([row], NIVEIS + [{"name": "l6", "requests": 80,
                                                       "multiplier": 4.0}],
                                    "abilene", "results/x/todos_agregados.csv")
        self.assertIn("t1", tex)
        self.assertIn("92,50", tex)
        self.assertIn("92,10", tex)
        self.assertTrue(any(line.endswith(" \\\\") for line in tex.splitlines()))


if __name__ == "__main__":
    unittest.main()
