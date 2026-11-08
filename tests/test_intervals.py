import unittest

from metrics.intervals import confidence_interval_95, sample_stddev, t_critical_95

try:
    from scipy.stats import t as scipy_t
except ImportError:  # scipy só existe em requirements-dev.txt
    scipy_t = None


class IntervalosTest(unittest.TestCase):
    def test_desvio_amostral_usa_n_menos_1(self):
        self.assertAlmostEqual(sample_stddev([2, 4, 4, 4, 5, 5, 7, 9]), (32 / 7) ** 0.5)

    def test_menos_de_duas_observacoes_nao_tem_desvio_nem_intervalo(self):
        self.assertIsNone(sample_stddev([1.0]))
        self.assertIsNone(confidence_interval_95([1.0]))
        self.assertIsNone(confidence_interval_95([]))

    def test_intervalo_calculado_a_mao(self):
        # n=4: média 5, s = sqrt(20/3), t(3 gl) = 3,182.
        low, high = confidence_interval_95([2, 4, 6, 8])
        half = 3.182 * (20 / 3) ** 0.5 / 2
        self.assertAlmostEqual(low, 5 - half)
        self.assertAlmostEqual(high, 5 + half)

    def test_valores_identicos_dao_intervalo_degenerado(self):
        self.assertEqual(confidence_interval_95([3, 3, 3]), (3, 3))

    def test_graus_de_liberdade_invalidos(self):
        with self.assertRaises(ValueError):
            t_critical_95(0)

    @unittest.skipIf(scipy_t is None, "scipy não instalado")
    def test_quantis_conferem_com_scipy(self):
        for df in list(range(1, 31)):
            self.assertAlmostEqual(t_critical_95(df), scipy_t.ppf(0.975, df), places=3)
        for df in (31, 40, 60, 120, 1000):
            self.assertAlmostEqual(t_critical_95(df), scipy_t.ppf(0.975, df), places=3)


if __name__ == "__main__":
    unittest.main()
