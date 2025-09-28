import pandas as pd
from extrae_csv import extrae_csv
from extrae_pdf import extraer_total_de_factura

df = extrae_csv('../files/test.csv')
total = extraer_total_de_factura('../files/factura_incorrecta.pdf')


def compara_totales(total_pdf, df_csv):
    """
    Compara el total extraído del PDF con los totales en el DataFrame del CSV.

    Args:
        total_pdf: El total extraído de la factura.
        df_csv: Un DataFrame con los datos del CSV y el total de la columna tarifa
    """
    if total_pdf is None or df_csv is None:
        print("❌ No se puede comparar porque uno de los valores es None.")
        return

    total_csv = float(df_csv['tarifa'].sum())

    print(f"Total extraído del PDF: {total_pdf}")
    print(f"Total calculado del CSV: {total_csv}")

    if total_pdf == total_csv:
        print("✅ Los totales coinciden.")
        return True
    else:
        print("❌ Los totales NO coinciden.")
        return False
    

resultado = compara_totales(total, df)
print("Resultado de la comparación:", resultado)
