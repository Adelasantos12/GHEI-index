import sys
import os
import time

# Asegurar que podemos importar desde src
sys.path.append(os.getcwd())

def print_step(title, description):
    print("\n" + "="*60)
    print(f"PASO: {title}")
    print("="*60)
    print(description)
    print("-" * 60)
    time.sleep(1)

def run():
    print("\n🚀 INICIANDO PIPELINE DE EXPERIMENTACIÓN GHEI (DEMO DINÁMICA)\n")

    try:
        from src.ingest_validate import validate
        from src.panel_build import build_panel
        from src.missing_normalize import handle_missing, normalize
        from src.index_model import pillar_scores, final_index, wpi_adjust
        from src.cas_module import model_pillarD, lagged_dynamics, dependency_network
        from src.sensitivity import monte_carlo
        from src.report import make_codebook, export_final
    except ImportError as e:
        print(f"Error al importar módulos del pipeline: {e}")
        return

    print_step("1. Ingesta y Validación",
               "Se cargan los archivos crudos (Excel/CSV) y se verifica que cumplan con el esquema esperado (ISO, años, rangos).")
    data = validate()
    print("✅ Validación completada con éxito.")

    print_step("2. Construcción del Panel",
               "Se unifican todas las fuentes de datos en un panel único país-año.")
    panel = build_panel(data)
    print(f"✅ Panel construido con {len(panel)} registros.")

    print_step("3. Tratamiento de Datos Faltantes y Normalización",
               "Se imputan valores faltantes (mean/carry forward) y se escalan las variables a un rango [0, 1].")
    panel = handle_missing(panel)
    panel = normalize(panel)
    print("✅ Normalización (Global y por Año) terminada.")

    print_step("4. Cálculo de Puntajes de Pilares e Índice",
               "Se calculan los pilares A, B, C y D. Se aplica la fórmula del GHEI y se ajusta por poder estructural (WPI).")
    panel = pillar_scores(panel, norm_suffix='_mm_global', efforts_variant='A')
    panel = final_index(panel, pillar_variant='eq', lambda_penalty=1.0)
    panel = wpi_adjust(panel)
    print("✅ Índice GHEI calculado y ajustado por WPI (Poder Estructural).")

    print_step("5. Analítica CAS (Sistemas Adaptativos Complejos)",
               "Se calculan valores SHAP para explicar el Pilar D, dinámicas de rezago y redes de dependencia.")
    panel = model_pillarD(panel)
    panel = lagged_dynamics(panel)
    panel = dependency_network(panel)
    print("✅ Análisis de SHAP y dependencias no lineales completado.")

    print_step("6. Análisis de Sensibilidad (Monte Carlo)",
               "Se realizan 200 iteraciones para evaluar la estabilidad del ranking (Probabilidad Top-K).")
    monte_carlo(panel, n_iter=200, top_k=10)
    print("✅ Análisis de robustez terminado.")

    print_step("7. Exportación y Reporte",
               "Se genera el diccionario de datos (codebook) y se exportan los datasets finales que consume el dashboard.")
    make_codebook()
    export_final(panel)
    print("\n🏁 PIPELINE COMPLETADO EXITOSAMENTE.")
    print("Los resultados han sido regenerados y están listos en 'final_panel.csv'.")

if __name__ == "__main__":
    run()
