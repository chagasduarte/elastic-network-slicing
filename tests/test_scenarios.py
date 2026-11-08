import json
import tempfile
import unittest
from pathlib import Path

from contracts.create_topo import create_test_graph
from contracts.nobel_germany_topology import create_nobel_germany_graph
from experiments.scenarios import (
    DailyProfile, LoadLevel, generate_requests, load_config, uniform_capacity,
)

PROFILE = DailyProfile({"t1": 0.25, "t2": 0.5, "t3": 1.0})


def generate(level=LoadLevel("x", 20), seed=1, graph=None, noise=0.3):
    return generate_requests(
        graph or create_nobel_germany_graph(), level, PROFILE,
        base_bandwidth=40, noise=noise, seed=seed,
    )


class GeradorDeCenariosTest(unittest.TestCase):
    def test_mesma_semente_gera_mesmas_requisicoes(self):
        self.assertEqual(generate(seed=7), generate(seed=7))

    def test_sementes_diferentes_geram_requisicoes_diferentes(self):
        self.assertNotEqual(generate(seed=7), generate(seed=8))

    def test_nunca_origem_igual_ao_destino(self):
        graph = create_test_graph()
        n_pairs = len(graph.nodes) * (len(graph.nodes) - 1)
        requests = generate(LoadLevel("max", n_pairs), graph=graph)
        self.assertTrue(all(r.source != r.destination for r in requests))

    def test_pares_sao_distintos_e_pertencem_a_topologia(self):
        graph = create_nobel_germany_graph()
        requests = generate(LoadLevel("x", 100), graph=graph)
        pairs = {(r.source, r.destination) for r in requests}
        self.assertEqual(len(pairs), 100)
        names = {node for node in graph.nodes}
        self.assertTrue(all(a in names and b in names for a, b in pairs))

    def test_excesso_de_requisicoes_e_erro(self):
        graph = create_test_graph()
        with self.assertRaises(ValueError):
            generate(LoadLevel("x", 12 * 11 + 1), graph=graph)

    def test_formato_das_demandas(self):
        for request in generate():
            self.assertEqual([d.id for d in request.demands], ["t1", "t2", "t3"])
            self.assertTrue(all(isinstance(d.bandwidth, int) and d.bandwidth >= 1
                                for d in request.demands))

    def test_sem_ruido_segue_o_perfil_e_o_multiplicador(self):
        requests = generate(LoadLevel("x", 3, 2.0), noise=0.0)
        for request in requests:
            self.assertEqual([d.bandwidth for d in request.demands], [20, 40, 80])

    def test_ruido_fica_dentro_do_intervalo(self):
        for request in generate(LoadLevel("x", 50), noise=0.3):
            for demand, factor in zip(request.demands, PROFILE.factors.values()):
                self.assertTrue(40 * factor * 0.7 - 1 <= demand.bandwidth
                                <= 40 * factor * 1.3 + 1)

    def test_multiplicador_aumenta_a_demanda_total(self):
        def total(multiplier):
            return sum(d.bandwidth for r in generate(LoadLevel("x", 20, multiplier))
                       for d in r.demands)
        self.assertGreater(total(3.0), total(1.0))

    def test_capacidade_uniforme(self):
        graph = uniform_capacity(create_test_graph(), 800)
        self.assertEqual({link.capacity for link in graph.links}, {800})


class ConfigTest(unittest.TestCase):
    def test_carrega_configuracao_do_repositorio(self):
        config = load_config(Path("experiments/configs/small.json"))
        self.assertEqual(config.link_capacity, 800)
        self.assertEqual(list(config.profile.factors), ["t1", "t2", "t3", "t4"])

    def test_chave_desconhecida_e_erro(self):
        raw = json.loads(Path("experiments/configs/small.json").read_text())
        raw["extra"] = 1
        with tempfile.TemporaryDirectory() as folder:
            path = Path(folder) / "c.json"
            path.write_text(json.dumps(raw))
            with self.assertRaises(ValueError):
                load_config(path)


if __name__ == "__main__":
    unittest.main()
