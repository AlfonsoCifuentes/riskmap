"""
Script para leer y analizar las bases de datos existentes
"""
import sqlite3
import os

def analyze_database(db_path):
    """Analiza una base de datos SQLite y muestra su estructura y contenido"""
    if not os.path.exists(db_path):
        print(f"❌ Base de datos no encontrada: {db_path}")
        return
    
    print(f"📊 ANALIZANDO: {db_path}")
    print("=" * 60)
    
    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        # Obtener todas las tablas
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
        tables = cursor.fetchall()
        
        if not tables:
            print("❌ No se encontraron tablas en la base de datos")
            return
        
        print(f"🗂️  TABLAS ENCONTRADAS: {len(tables)}")
        print()
        
        for table_tuple in tables:
            table_name = table_tuple[0]
            print(f"📋 TABLA: {table_name}")
            print("-" * 40)
            
            # Obtener esquema de la tabla
            cursor.execute(f"PRAGMA table_info({table_name})")
            columns = cursor.fetchall()
            
            print("🏗️  ESTRUCTURA:")
            for col in columns:
                col_name = col[1]
                col_type = col[2]
                is_pk = " (PRIMARY KEY)" if col[5] else ""
                not_null = " NOT NULL" if col[3] else ""
                print(f"   - {col_name}: {col_type}{not_null}{is_pk}")
            
            # Contar registros
            cursor.execute(f"SELECT COUNT(*) FROM {table_name}")
            count = cursor.fetchone()[0]
            print(f"📊 REGISTROS: {count}")
            
            # Mostrar algunos ejemplos si hay datos
            if count > 0:
                cursor.execute(f"SELECT * FROM {table_name} LIMIT 3")
                samples = cursor.fetchall()
                
                print("🔍 EJEMPLOS DE DATOS:")
                for i, row in enumerate(samples, 1):
                    print(f"   Registro {i}: {row}")
                
                if count > 3:
                    print(f"   ... y {count - 3} registros más")
            
            print()
        
        conn.close()
        
    except Exception as e:
        print(f"❌ Error al leer la base de datos: {e}")
    
    print("=" * 60)
    print()

if __name__ == "__main__":
    # Rutas a las bases de datos
    db1 = r"E:\Proyectos\VisualStudio\Upgrade_Data_AI\riskmap\src\dashboard\data\geopolitical_intel.db"
    db2 = r"E:\Proyectos\VisualStudio\Upgrade_Data_AI\riskmap\src\dashboard\data\geopolitical_intelligence.db"
    
    print("🔍 ANÁLISIS DE BASES DE DATOS EXISTENTES")
    print("=" * 80)
    print()
    
    # Analizar primera base de datos
    analyze_database(db1)
    
    # Analizar segunda base de datos
    analyze_database(db2)
    
    print("✅ Análisis completado")
