import contextlib
import csv
import io
import json
from pathlib import Path
import tempfile
import unittest

from experiments import run_all
from experiments.estimativa import extrapolar, ler_medicoes
from experiments.scenarios import load_config

CONFIG_MINUSCULA = {
    "topologies": ["abilene"],
    "link_capacity": 800,
    "seed": 7,
    "repetitions": 2,
    "algorithms": ["petic", "q-learning"],
    "base_bandwidth": 40,
    "noise": 0.3,
    "profile": {"t1": 0.5, "t2": 1.0},
    "load_levels": [
        {"name": "a", "requests": 2, "multiplier": 1.0},
        {"name": "b", "requests": 3, "multiplier": 2.0},
    ],
    "parameters": {"q-learning": {"episodes": 5}},
}


def rodar(*argumentos):
    saida = io.StringIO()
    with contextlib.redirect_stdout(saida):
        run_all.main(list(argumentos))
    return saida.getvalue()


class RunAllTest(unittest.TestCase):
    def setUp(self):
        self._tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self._tmp.cleanup)
        self.tmp = Path(self._tmp.name)
        self.config = self.tmp / "config.json"
        self.config.write_text(json.dumps(CONFIG_MINUSCULA), encoding="utf-8")
        self.raiz = self.tmp / "saida"

    def execucao(self):
        pastas = [p for p in self.raiz.iterdir() if p.is_dir()]
        self.assertEqual(len(pastas), 1)
        return pastas[0]

    def test_estrutura_de_saida_e_metadados(self):
        rodar("--config", str(self.config), "--output-root", str(self.raiz))
        pasta = self.execucao()
        self.assertRegex(pasta.name, r"^\d{8}-\d{6}$")
        for nome in ("config_usada.json", "metadados.json",
                     "todas_execucoes.csv", "todos_agregados.csv"):
            self.assertTrue((pasta / nome).is_file(), nome)
        for nivel in ("a", "b"):
            for nome in ("runs.json", "runs.csv", "aggregates.csv", "celula.json"):
                self.assertTrue((pasta / "abilene" / nivel / nome).is_file())
        self.assertEqual(
            json.loads((pasta / "config_usada.json").read_text(encoding="utf-8")),
            CONFIG_MINUSCULA,
        )
        meta = json.loads((pasta / "metadados.json").read_text(encoding="utf-8"))
        self.assertIn("commit", meta["git"])
        self.assertIn("arvore_suja", meta["git"])
        self.assertIn(".", meta["python"])
        self.assertTrue(meta["data_hora"])
        self.assertFalse(list(pasta.glob(".tmp-*")))

    def test_consolidados_tem_topologia_e_nivel(self):
        rodar("--config", str(self.config), "--output-root", str(self.raiz))
        pasta = self.execucao()
        with (pasta / "todas_execucoes.csv").open(encoding="utf-8", newline="") as f:
            linhas = list(csv.DictReader(f))
        self.assertEqual({l["load_level"] for l in linhas}, {"a", "b"})
        self.assertEqual({l["topology"] for l in linhas}, {"abilene"})
        resumos = [l for l in linhas if l["scope"] == "summary"]
        # 2 níveis x 2 algoritmos x 2 repetições
        self.assertEqual(len(resumos), 8)
        with (pasta / "todos_agregados.csv").open(encoding="utf-8", newline="") as f:
            agregados = list(csv.DictReader(f))
        self.assertEqual({l["load_level"] for l in agregados}, {"a", "b"})

    def test_dry_run_nao_grava(self):
        saida = rodar("--config", str(self.config), "--output-root", str(self.raiz),
                      "--dry-run", "--repetitions", "3")
        self.assertFalse(self.raiz.exists())
        self.assertIn("abilene/a", saida)
        self.assertIn("abilene/b", saida)
        self.assertIn("3 rep. x 2 alg. = 6", saida)

    def test_sobrescritas(self):
        rodar("--config", str(self.config), "--output-root", str(self.raiz),
              "--algorithms", "petic", "--repetitions", "1")
        pasta = self.execucao()
        with (pasta / "todas_execucoes.csv").open(encoding="utf-8", newline="") as f:
            linhas = [l for l in csv.DictReader(f) if l["scope"] == "summary"]
        self.assertEqual({l["algorithm"] for l in linhas}, {"petic"})
        self.assertEqual(len(linhas), 2)

    def test_resume_pula_celulas_gravadas(self):
        rodar("--config", str(self.config), "--output-root", str(self.raiz))
        pasta = self.execucao()
        # Simula interrupção: remove a segunda célula e deixa lixo temporário.
        import shutil
        shutil.rmtree(pasta / "abilene" / "b")
        (pasta / ".tmp-abilene-b").mkdir()
        marcador = pasta / "abilene" / "a" / "celula.json"
        antes = marcador.read_text(encoding="utf-8")
        saida = rodar("--config", str(self.config), "--output-root", str(self.raiz),
                      "--resume")
        self.assertIn("[pulada] abilene/a", saida)
        self.assertNotIn("[pulada] abilene/b", saida)
        self.assertEqual(marcador.read_text(encoding="utf-8"), antes)
        self.assertTrue((pasta / "abilene" / "b" / "runs.csv").is_file())
        self.assertFalse(list(pasta.glob(".tmp-*")))
        with (pasta / "todas_execucoes.csv").open(encoding="utf-8", newline="") as f:
            niveis = {l["load_level"] for l in csv.DictReader(f)}
        self.assertEqual(niveis, {"a", "b"})
        meta = json.loads((pasta / "metadados.json").read_text(encoding="utf-8"))
        self.assertEqual(len(meta["retomadas"]), 1)

    def test_resume_refaz_celula_com_assinatura_diferente(self):
        rodar("--config", str(self.config), "--output-root", str(self.raiz),
              "--repetitions", "1")
        saida = rodar("--config", str(self.config), "--output-root", str(self.raiz),
                      "--resume", "--repetitions", "2")
        self.assertNotIn("[pulada]", saida)

    def test_dry_run_com_resume_indica_puladas(self):
        rodar("--config", str(self.config), "--output-root", str(self.raiz))
        saida = rodar("--config", str(self.config), "--output-root", str(self.raiz),
                      "--resume", "--dry-run")
        self.assertIn("pularia", saida)
        self.assertIn("0 execuções de algoritmo", saida)

    def test_resultados_reprodutiveis_por_semente(self):
        rodar("--config", str(self.config), "--output-root", str(self.raiz / "x"),
              "--algorithms", "petic", "q-learning")
        rodar("--config", str(self.config), "--output-root", str(self.raiz / "y"),
              "--algorithms", "petic", "q-learning")

        def aceitacao(pasta):
            arquivo = next(pasta.iterdir()) / "todos_agregados.csv"
            with arquivo.open(encoding="utf-8", newline="") as f:
                return [(l["algorithm"], l["load_level"],
                         l["acceptance.acceptance_percent.mean"]) for l in csv.DictReader(f)]

        self.assertEqual(aceitacao(self.raiz / "x"), aceitacao(self.raiz / "y"))

    def test_estimativa_extrapola_a_partir_do_medido(self):
        rodar("--config", str(self.config), "--output-root", str(self.raiz),
              "--estimar")
        pasta = self.execucao()
        self.assertTrue(pasta.name.endswith("-estimativa"))
        self.assertTrue((pasta / "estimativa.json").is_file())
        config = load_config(self.config)
        medicoes = ler_medicoes(pasta)
        resultado = extrapolar(medicoes, config, ["abilene"], ["petic", "q-learning"])
        central, baixo, alto = resultado["geral"]
        self.assertLessEqual(baixo, central)
        self.assertLessEqual(central, alto)

    def test_interpolacao(self):
        from experiments.estimativa import _interpolar
        self.assertEqual(_interpolar([(10, 1.0), (30, 3.0)], 20), (2.0, 1.0, 3.0))
        self.assertEqual(_interpolar([(10, 1.0), (30, 3.0)], 30), (3.0, 3.0, 3.0))


if __name__ == "__main__":
    unittest.main()
