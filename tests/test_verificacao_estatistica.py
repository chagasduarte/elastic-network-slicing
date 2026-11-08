import unittest

from scripts.verificacao_estatistica import holm, sinal_exato, wilcoxon_exato


class VerificacaoEstatisticaTest(unittest.TestCase):
    def test_wilcoxon_exato_tabela_conhecida(self):
        p, n = wilcoxon_exato([1, 2, 3, 4, 5])
        self.assertEqual(n, 5)
        self.assertAlmostEqual(p, 0.0625)

    def test_wilcoxon_exato_com_sinais_mistos(self):
        # W+ = 15 de 21; subconjuntos com soma <= 6: 14 de 64.
        p, _ = wilcoxon_exato([1, -2, 3, -4, 5, 6])
        self.assertAlmostEqual(p, 2 * 14 / 64)

    def test_zeros_sao_descartados(self):
        self.assertEqual(wilcoxon_exato([0, 0, 0]), (1.0, 0))

    def test_sinal_exato(self):
        self.assertAlmostEqual(sinal_exato([1, 1, 1, 1, 1, -1]), 0.21875)

    def test_holm(self):
        self.assertEqual(holm([0.01, 0.04, 0.03]), [0.03, 0.06, 0.06])


if __name__ == "__main__":
    unittest.main()
