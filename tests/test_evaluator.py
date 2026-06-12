from __future__ import annotations

import unittest

from src.evaluator import EvaluacionRAG, EvaluadorRAG


class NormalizacionEvaluadorTests(unittest.TestCase):
    def test_confiable_requiere_scores_altos_y_citas_validas(self) -> None:
        evaluacion = EvaluacionRAG(
            score_faithfulness=5,
            score_relevancia=5,
            tiene_alucinacion=False,
            citas_validas=True,
            problemas_detectados=[],
            veredicto="CONFIABLE",
        )

        resultado = EvaluadorRAG._normalizar_evaluacion(evaluacion, [{"text": "evidencia"}])

        self.assertEqual(resultado["veredicto"], "DUDOSO")

    def test_alucinacion_limita_faithfulness_y_fuerza_veredicto(self) -> None:
        evaluacion = EvaluacionRAG(
            score_faithfulness=9,
            score_relevancia=10,
            tiene_alucinacion=True,
            citas_validas=True,
            problemas_detectados=["Afirmacion sin soporte"],
            veredicto="CONFIABLE",
        )

        resultado = EvaluadorRAG._normalizar_evaluacion(evaluacion, [{"text": "evidencia"}])

        self.assertEqual(resultado["score_faithfulness"], 4)
        self.assertEqual(resultado["veredicto"], "ALUCINACION")

    def test_sin_chunks_invalida_citas_y_registra_problema(self) -> None:
        evaluacion = EvaluacionRAG(
            score_faithfulness=8,
            score_relevancia=8,
            tiene_alucinacion=False,
            citas_validas=True,
            problemas_detectados=[],
            veredicto="CONFIABLE",
        )

        resultado = EvaluadorRAG._normalizar_evaluacion(evaluacion, [])

        self.assertFalse(resultado["citas_validas"])
        self.assertEqual(resultado["veredicto"], "DUDOSO")
        self.assertIn("No se proporciono evidencia", resultado["problemas_detectados"][0])

    def test_resultado_solido_permanece_confiable(self) -> None:
        evaluacion = EvaluacionRAG(
            score_faithfulness=9,
            score_relevancia=8,
            tiene_alucinacion=False,
            citas_validas=True,
            problemas_detectados=[],
            veredicto="DUDOSO",
        )

        resultado = EvaluadorRAG._normalizar_evaluacion(evaluacion, [{"text": "evidencia"}])

        self.assertEqual(resultado["veredicto"], "CONFIABLE")


if __name__ == "__main__":
    unittest.main()
